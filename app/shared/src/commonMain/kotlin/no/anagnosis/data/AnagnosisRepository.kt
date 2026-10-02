package no.anagnosis.data

import no.anagnosis.DriverFactory
import no.anagnosis.db.AnagnosisDatabase
import no.anagnosis.db.Documents
import no.anagnosis.db.Tokens
import no.anagnosis.inflate
import no.anagnosis.lexdb.LexiconDatabase

class AnagnosisRepository(private val driverFactory: DriverFactory) {
    private val lexicon by lazy { LexiconDatabase(driverFactory.createDriver("lexicon")) }
    private val textDbs = HashMap<String, AnagnosisDatabase>()

    private fun textDb(slug: String): AnagnosisDatabase =
        textDbs.getOrPut(slug) { AnagnosisDatabase(driverFactory.createDriver(slug)) }

    /** The texts this app knows about, installed ones marked. */
    fun catalog(): List<CatalogEntry> {
        val installed = driverFactory.installedTexts().toSet()
        val json = driverFactory.readCatalog()
        val entries = if (json != null) parseCatalog(json) else emptyList()
        val listed = entries.map { it.slug }.toSet()
        // installed texts missing from the catalog (e.g. a downloaded text) still appear
        val extra = installed.filter { it !in listed }.map { slug ->
            val w = textDb(slug).anagnosisQueries.selectWorkBySlug(slug).executeAsOneOrNull()
            CatalogEntry(slug, w?.title ?: slug, w?.author ?: "", w?.title ?: slug, w?.author ?: "", "", w?.edition ?: "", true)
        }
        return entries.map { it.copy(installed = it.slug in installed) }.distinctBy { it.slug } + extra
    }

    private fun CatalogEntry.copy(installed: Boolean) =
        CatalogEntry(slug, title, author, titleEn, authorEn, description, edition, installed, appId)

    private fun parseCatalog(json: String): List<CatalogEntry> {
        // the catalog is a flat JSON array of objects with string values; a small parser suffices
        val objects = Regex("\\{[^{}]*\\}").findAll(json).map { it.value }
        fun field(obj: String, name: String): String {
            val m = Regex("\"$name\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").find(obj) ?: return ""
            return m.groupValues[1].replace("\\n", "\n").replace("\\\"", "\"").replace("\\\\", "\\")
        }
        return objects.map { o ->
            CatalogEntry(field(o, "slug"), field(o, "title"), field(o, "author"), field(o, "title_en"),
                field(o, "author_en"), field(o, "description"), field(o, "edition"), false, field(o, "app_id"))
        }.filter { it.slug.isNotEmpty() }.toList()
    }

    fun loadWork(slug: String): WorkData {
        val q = textDb(slug).anagnosisQueries
        val work = q.selectWorkBySlug(slug).executeAsOne()
        val lines = q.selectLines(work.id).executeAsList()
        val tokens = q.selectTokensForWork(work.id).executeAsList().groupBy { it.line_id }
        val nodes = q.selectNodesForWork(work.id).executeAsList().groupBy { it.sentence }
        val sections = q.selectSections(work.id).executeAsList()
            .filter { it.first_line_id != null }
            .groupBy { it.first_line_id!! }
        val translations = q.selectTranslations(work.id).executeAsList().map {
            TranslationData(it, q.selectSegments(it.id).executeAsList())
        }
        val commentaries = q.selectCommentaries(work.id).executeAsList()
        val starts = q.selectNoteStarts().executeAsList()
        val withNotes = HashSet<Long>()
        var i = 0
        for (line in lines) {
            var mark = false
            while (i < starts.size && starts[i] <= line.n_int) { mark = true; i++ }
            if (mark) withNotes += line.id
        }
        val bookNumbered = q.selectMeta("line_numbers").executeAsOneOrNull() == "book.line"
        return WorkData(slug, work, lines, tokens, nodes, sections, translations, commentaries, withNotes, bookNumbered)
    }

    fun lookupWord(data: WorkData, tokenId: Long): WordInfo? {
        val q = textDb(data.slug).anagnosisQueries
        val token = data.tokensByLine.values.asSequence().flatten().firstOrNull { it.id == tokenId } ?: return null
        val lq = lexicon.lexiconQueries
        var rows = lq.selectEntriesByKey(token.lemma_key).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
        if (rows.isEmpty()) {
            rows = lq.selectEntriesByLooseKey(looseKey(token.lemma)).executeAsList()
                .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
        }
        val glossary = q.selectGlossaryByKey(token.lemma_key).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, it.html) }
        val short = q.selectShortDefinition(token.lemma_key).executeAsOneOrNull()?.definition
        val syntax = token.sentence?.let { Syntax.roleOf(sentenceTree(data, it), token) }
        return WordInfo(token.form, token.lemma, Morphology.describe(token.postag), short, glossary + rows, syntax)
    }

    /** The tokens of a sentence in text order; a sentence can run over several lines and share a line with another. */
    fun sentenceTokens(data: WorkData, sentence: String): List<Tokens> =
        data.lines.asSequence().flatMap { data.tokensByLine[it.id] ?: emptyList() }.filter { it.sentence == sentence }.toList()

    /** The dependency tree of a sentence, from its tokens and the treebank's extra nodes. */
    fun sentenceTree(data: WorkData, sentence: String): SyntaxTree =
        Syntax.build(sentence, sentenceTokens(data, sentence), data.nodesBySentence[sentence] ?: emptyList())

    /**
     * Notes of the given kind for a page: every note that starts on the page (or on a skipped
     * number just before it) or whose short range overlaps it, grouped by line or range.
     */
    fun notesForPage(data: WorkData, firstN: Long, lastN: Long, kind: NoteKind): List<NoteGroup> {
        val q = textDb(data.slug).anagnosisQueries
        val firstIdx = data.lines.indexOfFirst { it.n_int >= firstN }
        val prevN = if (firstIdx > 0) data.lines[firstIdx - 1].n_int else 0L
        val notes = data.commentaries.filter { it.kind() == kind }
            .flatMap { q.selectNotesForPage(it.id, prevN, lastN, firstN, OVERLAP_MAX_SPAN).executeAsList() }
            .sortedWith(compareBy({ it.from_n_int }, { -it.to_n_int }, { it.ord }))
        val groups = mutableListOf<NoteGroup>()
        for ((key, group) in notes.groupBy { it.n }) {
            val first = group.first()
            val heading = if (first.to_n_int > first.from_n_int) "Lines ${key.replace("-", "–")}" else "Line $key"
            val lineText = data.lines.firstOrNull { it.n_int >= first.from_n_int }?.text
            groups += NoteGroup(heading, lineText, group)
        }
        return groups
    }

    /** Titles of the work's free-standing documents (introduction, appendix, sigla ...). */
    fun documents(data: WorkData): List<Pair<String, String>> =
        textDb(data.slug).anagnosisQueries.selectDocuments(data.work.id).executeAsList().map { it.slug to it.title }

    /** A free-standing document of the work, e.g. "sigla" (manuscripts and symbols). */
    fun document(data: WorkData, slug: String): Documents? =
        textDb(data.slug).anagnosisQueries.selectDocument(data.work.id, slug).executeAsOneOrNull()

    /** Headwords starting with the given loose key (diacritics ignored), one per lemma. */
    fun searchHeadwords(looseKey: String, limit: Long = 80): List<HeadwordHit> {
        if (looseKey.isEmpty()) return emptyList()
        val q = lexicon.lexiconQueries
        val exactEnd = q.searchHeadwords(looseKey, looseKey + "\uFFFF", limit).executeAsList()
        // a key ending in ς is also the start of longer words, where the sigma is medial (σ)
        val longer = if (looseKey.endsWith('ς')) {
            val p = looseKey.dropLast(1) + 'σ'
            q.searchHeadwords(p, p + "\uFFFF", limit).executeAsList()
        } else emptyList()
        return (exactEnd + longer).distinctBy { it.lemma_key }
            .sortedWith(compareBy({ it.sort_key }, { it.lemma_key })).take(limit.toInt())
            .map { HeadwordHit(it.lemma_key, it.headword ?: it.lemma_key) }
    }

    /** The word sheet for a dictionary headword: gloss (when the lexicon has one) and full entries. */
    fun wordInfoForLemma(lemmaKey: String, headword: String): WordInfo {
        val lq = lexicon.lexiconQueries
        val entries = lq.selectEntriesByKey(lemmaKey).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
        val short = lq.selectShortDefinition(lemmaKey).executeAsOneOrNull()
        return WordInfo(headword, headword, "", short, entries)
    }

    /** Dictionary entries for a lemma, exact key first, then ignoring diacritics. */
    fun entriesForLemma(lemma: String): List<Entry> {
        val lq = lexicon.lexiconQueries
        val exact = lq.selectEntriesByKey(lemma.lowercase()).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
        if (exact.isNotEmpty()) return exact
        return lq.selectEntriesByLooseKey(looseKey(lemma)).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
    }

    /** The word sheet for an analysed form: the lemma's gloss and entries plus the parse. */
    fun wordInfoForAnalysis(a: FormAnalysis): WordInfo {
        val short = lexicon.lexiconQueries.selectShortDefinition(a.lemmaKey).executeAsOneOrNull()
        return WordInfo(a.form, a.lemma, Morphology.describe(a.postag), short, entriesForLemma(a.lemma))
    }

    /**
     * Analyses of an inflected form. Diacritics are ignored for the lookup; with [exact] the
     * result is narrowed to analyses whose form has the typed diacritics (when any were typed).
     */
    fun analyse(form: String, exact: Boolean = false): List<FormAnalysis> {
        val packed = lexicon.lexiconQueries.selectForms(looseKey(form)).executeAsOneOrNull() ?: return emptyList()
        val all = inflate(packed).lineSequence().mapNotNull { line ->
            val f = line.split('\t')
            if (f.size >= 4) FormAnalysis(f[0], f[1], f[1].lowercase(), f[2], f[3]) else null
        }.toList()
        if (!exact) return all
        val typed = no.anagnosis.greek.Polytonic.exactKey(form)
        if (typed == looseKey(form)) return all  // nothing beyond base letters was typed
        return all.filter { no.anagnosis.greek.Polytonic.exactKey(it.form) == typed }
    }

    /** Attribution for everything installed, for the About screen. */
    fun credits(): List<Credit> {
        val out = mutableListOf<Credit>()
        for (slug in driverFactory.installedTexts()) {
            val q = textDb(slug).anagnosisQueries
            for (w in q.selectWorks().executeAsList()) {
                out += Credit("Text", "${w.author ?: ""}, ${w.title}".trim(' ', ','), w.edition ?: w.source, w.license)
            }
            for (t in q.selectAllTranslations().executeAsList()) {
                out += Credit("Translation", listOfNotNull(t.translator, t.title).joinToString(", "), t.edition ?: t.source, t.license)
            }
            for (c in q.selectAllCommentaries().executeAsList()) {
                out += Credit("Commentary", listOfNotNull(c.author, c.title).joinToString(", "), c.source, c.license)
            }
            for (l in q.selectLexicons().executeAsList()) {
                out += Credit("Glossary", l.title, l.source, l.license)
            }
        }
        for (l in lexicon.lexiconQueries.selectLexicons().executeAsList()) {
            out += Credit("Dictionary", l.title, l.source, l.license)
        }
        out += Credit("Short definitions", "Logeion (Helma Dik, University of Chicago), based on the Perseus short definitions", "https://github.com/helmadik/shortdefs", "Used with credit to Perseus and Logeion")
        return out
    }

    companion object {
        /** Ranged notes shorter than this follow the reader across pages; longer ones stay on their first page. */
        const val OVERLAP_MAX_SPAN = 20L

        /** Mirrors greek.strip_diacritics in the pipeline: base letters only, lower case. */
        fun looseKey(s: String): String = no.anagnosis.greek.GreekNormalizer.looseKey(s)

    }
}
