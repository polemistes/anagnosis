package no.anagnosis.data

import no.anagnosis.DriverFactory
import no.anagnosis.db.AnagnosisDatabase
import no.anagnosis.db.Documents
import no.anagnosis.db.Tokens
import no.anagnosis.inflate
import no.anagnosis.lexdb.LexiconDatabase
import no.anagnosis.notesdb.NotesDatabase
import no.anagnosis.ui.plainText
import no.anagnosis.nowMillis

class AnagnosisRepository(private val driverFactory: DriverFactory) {
    private val lexicon by lazy { LexiconDatabase(driverFactory.createDriver("lexicon")) }
    private val textDbs = HashMap<String, AnagnosisDatabase>()
    private val notesDb by lazy { NotesDatabase(driverFactory.createNotesDriver()) }

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
        CatalogEntry(slug, title, author, titleEn, authorEn, description, edition, installed, appId,
            editor, apparatus, translation, commentary, syntax, dictionaries, onGooglePlay,
            refEdition, refTranslation, refCommentary, syntaxSource, syntaxLicense)

    private fun parseCatalog(json: String): List<CatalogEntry> {
        // the catalog is a flat JSON array of objects with string values; a small parser suffices
        val objects = Regex("\\{[^{}]*\\}").findAll(json).map { it.value }
        fun field(obj: String, name: String): String {
            val m = Regex("\"$name\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").find(obj) ?: return ""
            return m.groupValues[1].replace("\\n", "\n").replace("\\\"", "\"").replace("\\\\", "\\")
        }
        return objects.map { o ->
            CatalogEntry(field(o, "slug"), field(o, "title"), field(o, "author"), field(o, "title_en"),
                field(o, "author_en"), field(o, "description"), field(o, "edition"), false, field(o, "app_id"),
                field(o, "editor"), field(o, "apparatus"), field(o, "translation"), field(o, "commentary"),
                field(o, "syntax"), field(o, "dictionaries"), field(o, "google_play") == "yes",
                field(o, "ref_edition"), field(o, "ref_translation"), field(o, "ref_commentary"),
                field(o, "syntax_source"), field(o, "syntax_license"))
        }.filter { it.slug.isNotEmpty() }.toList()
    }

    /**
     * Everything needed to read a text. A [light] work has its lines and sections only (no words,
     * translations or commentaries): enough for the search to cite and group its hits, without
     * the seconds the words of a long text take.
     */
    fun loadWork(slug: String, light: Boolean = false): WorkData {
        val q = textDb(slug).anagnosisQueries
        val work = q.selectWorkBySlug(slug).executeAsOne()
        val lines = q.selectLines(work.id).executeAsList()
        val tokens = if (light) emptyMap() else q.selectTokensForWork(work.id).executeAsList().groupBy { it.line_id }
        val nodes = if (light) emptyMap() else q.selectNodesForWork(work.id).executeAsList().groupBy { it.sentence }
        val sections = q.selectSections(work.id).executeAsList()
            .filter { it.first_line_id != null }
            .groupBy { it.first_line_id!! }
        val translations = if (light) emptyList() else q.selectTranslations(work.id).executeAsList().map {
            TranslationData(it, q.selectSegments(it.id).executeAsList())
        }
        val commentaries = if (light) emptyList() else q.selectCommentaries(work.id).executeAsList()
        val starts = if (light) emptyList() else q.selectNoteStarts().executeAsList()
        val withNotes = HashSet<Long>()
        var i = 0
        for (line in lines) {
            var mark = false
            while (i < starts.size && starts[i] <= line.n_int) { mark = true; i++ }
            if (mark) withNotes += line.id
        }
        val numbering = q.selectMeta("line_numbers").executeAsOneOrNull()
        return WorkData(
            slug, work, lines, tokens, nodes, sections, translations, commentaries, withNotes,
            bookNumbered = numbering == "book.line",
            verses = numbering == "verse",
            stephanus = numbering == "stephanus",
            prose = q.selectMeta("layout").executeAsOneOrNull() == "prose",
            automaticSyntax = q.selectMeta("syntax").executeAsOneOrNull() == "automatic",
            dictionaryOrder = q.selectMeta("dictionaries").executeAsOneOrNull()?.split(' ')?.filter { it.isNotBlank() } ?: emptyList(),
        )
    }

    fun lookupWord(data: WorkData, tokenId: Long): WordInfo? {
        val q = textDb(data.slug).anagnosisQueries
        val token = data.tokensByLine.values.asSequence().flatten().firstOrNull { it.id == tokenId } ?: return null
        val lq = lexicon.lexiconQueries
        // Each dictionary is looked up by itself: under the lemma, else under the headword it is
        // listed under (a Homeric ἠέλιος under ἥλιος, the New Testament's ἀποκρίνομαι under
        // ἀποκρίνω), so that one dictionary having the word does not hide another's entry.
        // Only when none has it are the diacritics ignored.
        val alias = q.selectAliasTarget(token.lemma_key).executeAsOneOrNull()
        val bySlug = LinkedHashMap<String, List<Entry>>()
        val tiers = listOfNotNull(token.lemma_key, alias)
        for (key in tiers) {
            val found = lq.selectEntriesByKey(key).executeAsList()
                .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
            for ((slug, es) in found.groupBy { it.lexiconSlug }) if (slug !in bySlug) bySlug[slug] = es
        }
        if (bySlug.isEmpty()) {
            lq.selectEntriesByLooseKey(looseKey(token.lemma)).executeAsList()
                .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
                .groupBy { it.lexiconSlug }.forEach { (slug, es) -> bySlug[slug] = es }
        }
        val rows = bySlug.values.flatten()
        // the text's own glossary and dictionaries (Dodson in the New Testament)
        val glossary = q.selectGlossaryByKey(token.lemma_key).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, it.html) }
        val short = q.selectShortDefinition(token.lemma_key).executeAsOneOrNull()?.definition
        val syntax = token.sentence?.let { Syntax.roleOf(sentenceTree(data, it), token) }
            ?.let { if (data.automaticSyntax) "$it (automatic)" else it }
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
            val heading = when {
                data.verses -> data.range(first.from_n_int, first.to_n_int)
                first.to_n_int > first.from_n_int -> "Lines ${key.replace("-", "–")}"
                else -> "Line $key"
            }
            val lineText = data.lines.firstOrNull { it.n_int >= first.from_n_int }?.text?.let(::displayText)
            groups += NoteGroup(heading, lineText, group)
        }
        return groups
    }

    /** The reader's notes on a text, in text order. */
    fun notes(textSlug: String): List<Note> =
        notesDb.notesQueries.selectForText(textSlug).executeAsList().map {
            Note(it.id, it.text_slug, WordAnchor(it.from_n_int, it.from_n_sub, it.from_word),
                WordAnchor(it.to_n_int, it.to_n_sub, it.to_word), it.quote, it.body, it.created, it.modified)
        }

    /** Saves a new note and returns its id. */
    fun addNote(textSlug: String, from: WordAnchor, to: WordAnchor, quote: String, body: String): Long {
        val q = notesDb.notesQueries
        val now = nowMillis()
        return q.transactionWithResult {
            q.insert(textSlug, from.nInt, from.nSub, from.word, to.nInt, to.nSub, to.word, quote, body, now, now)
            q.lastInsertId().executeAsOne()
        }
    }

    fun updateNote(id: Long, body: String) = notesDb.notesQueries.updateBody(body, nowMillis(), id)

    fun deleteNote(id: Long) = notesDb.notesQueries.delete(id)

    /** Titles of the work's free-standing documents (introduction, appendix, sigla ...). */
    fun documents(data: WorkData): List<Pair<String, String>> =
        textDb(data.slug).anagnosisQueries.selectDocuments(data.work.id).executeAsList().map { it.slug to it.title }

    /** A free-standing document of the work, e.g. "sigla" (manuscripts and symbols). */
    fun document(data: WorkData, slug: String): Documents? =
        textDb(data.slug).anagnosisQueries.selectDocument(data.work.id, slug).executeAsOneOrNull()

    /** The documents of a text by its slug, without loading the text itself (for its title page). */
    fun documents(textSlug: String): List<Pair<String, String>> {
        val q = textDb(textSlug).anagnosisQueries
        val work = q.selectWorkBySlug(textSlug).executeAsOneOrNull() ?: return emptyList()
        return q.selectDocuments(work.id).executeAsList().map { it.slug to it.title }
    }

    /** A document of a text by the text's slug, without loading the text itself. */
    fun document(textSlug: String, slug: String): Documents? {
        val q = textDb(textSlug).anagnosisQueries
        val work = q.selectWorkBySlug(textSlug).executeAsOneOrNull() ?: return null
        return q.selectDocument(work.id, slug).executeAsOneOrNull()
    }

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

    /**
     * The dictionaries the reader can turn on and off, as (slug, title): the shared ones and
     * those that come with an installed text (Dodson with the New Testament), not glossaries.
     */
    fun dictionaries(): List<Pair<String, String>> {
        val out = LinkedHashMap<String, String>()
        for (l in lexicon.lexiconQueries.selectLexicons().executeAsList()) out[l.slug] = l.title
        for (slug in driverFactory.installedTexts()) {
            for (l in textDb(slug).anagnosisQueries.selectLexicons().executeAsList()) {
                if (!l.slug.endsWith("-glossary")) out.getOrPut(l.slug) { l.title }
            }
        }
        return out.entries.sortedBy { Dictionaries.rank(it.key) }.map { it.key to it.value }
    }

    /** Attribution for the app itself (the shared dictionaries and short definitions), for the front page's About. */
    fun appCredits(): List<Credit> {
        val out = mutableListOf<Credit>()
        for (l in lexicon.lexiconQueries.selectLexicons().executeAsList()) {
            out += Credit("Dictionary", l.title, l.source, l.license)
        }
        out += Credit("Short definitions", "Logeion (Helma Dik, University of Chicago), based on the Perseus short definitions", "https://github.com/helmadik/shortdefs", "Used with credit to Perseus and Logeion")
        return out
    }

    /**
     * Attribution for one text, for its own About: the edition, translation and commentaries, the
     * dictionaries it brings or puts first (Dodson, Autenrieth ...), and its lemmas and syntax.
     */
    fun textCredits(entry: CatalogEntry): List<Credit> {
        val out = mutableListOf<Credit>()
        val q = textDb(entry.slug).anagnosisQueries
        for (w in q.selectWorks().executeAsList()) {
            out += Credit("Text", "${w.author ?: ""}, ${w.title}".trim(' ', ','), w.edition ?: w.source, w.license)
        }
        for (t in q.selectAllTranslations().executeAsList()) {
            out += Credit("Translation", listOfNotNull(t.translator, t.title).joinToString(", "), t.edition ?: t.source, t.license)
        }
        for (c in q.selectAllCommentaries().executeAsList()) {
            val kind = if (c.kind() == NoteKind.APPARATUS) "Critical apparatus" else "Commentary"
            out += Credit(kind, listOfNotNull(c.author, c.title).joinToString(", "), c.source, c.license)
        }
        for (l in q.selectLexicons().executeAsList()) {
            out += Credit(if (l.slug.endsWith("-glossary")) "Glossary" else "Dictionary", l.title, l.source, l.license)
        }
        // the shared dictionaries made for this text (not the Liddell-Scotts every text has)
        val own = q.selectMeta("dictionaries").executeAsOneOrNull()?.split(' ').orEmpty() - setOf("ml", "lsj", "")
        for (l in lexicon.lexiconQueries.selectLexicons().executeAsList()) {
            if (l.slug in own) out += Credit("Dictionary", l.title, l.source, l.license)
        }
        if (entry.syntaxSource.isNotEmpty()) {
            out += Credit("Lemmas, morphology and syntax", entry.syntaxSource, null, entry.syntaxLicense.ifEmpty { null })
        }
        return out
    }

    // --- search ---------------------------------------------------------------------------

    private val corpora = HashMap<String, TextCorpus>()
    private val lemmaEntryCache = HashMap<String, Pair<List<LemmaEntry>, Map<String, String>>>()
    private var lemmaRowCache: Pair<List<String>, List<LemmaRow>>? = null

    /**
     * A text made ready for the free-text search: its light work (for citations and books) and
     * one document for the Greek, one per translation and one per commentary. Built once.
     */
    fun corpus(slug: String): TextCorpus = corpora.getOrPut(slug) {
        val work = loadWork(slug, light = true)
        val q = textDb(slug).anagnosisQueries
        val docs = mutableListOf<SearchDoc>()
        docs += SearchDoc(slug, SearchSource.GREEK, "", work.lines.map { SearchUnit(it.n_int, it.n_sub, it.text) })
        for (t in q.selectTranslations(work.work.id).executeAsList()) {
            val units = q.selectSegments(t.id).executeAsList().map { SearchUnit(it.from_n_int, it.from_n_sub, it.text) }
            docs += SearchDoc(slug, SearchSource.TRANSLATION, SearchSource.TRANSLATION.label, units)
        }
        for (c in q.selectCommentaries(work.work.id).executeAsList()) {
            val units = q.selectAllNotes(c.id).executeAsList().map { SearchUnit(it.from_n_int, "", plainText(it.html), extra = c.id) }
            docs += SearchDoc(slug, SearchSource.COMMENTARY, c.kind().label, units)
        }
        TextCorpus(slug, work, docs)
    }

    /** The reader's notes on a text as a search document; made anew at every search, since notes change. */
    fun notesDoc(slug: String): SearchDoc =
        SearchDoc(slug, SearchSource.NOTES, "Note", notes(slug).map { SearchUnit(it.from.nInt, it.from.nSub, it.body, extra = it.id) })

    /** Searches the given sources of the given texts, in the order of [slugs]. */
    fun searchTexts(slugs: List<String>, query: String, options: SearchOptions, sources: Set<SearchSource>, isActive: () -> Boolean = { true }): SearchResult {
        val docs = mutableListOf<SearchDoc>()
        for (slug in slugs) {
            if (!isActive()) throw kotlin.coroutines.cancellation.CancellationException("search cancelled")
            docs += corpus(slug).docs.filter { it.source in sources }
            if (SearchSource.NOTES in sources) docs += notesDoc(slug)
        }
        return TextSearch.search(docs, query, options, isActive)
    }

    /** A text's lemmas with their counts, and its aliases (lemma key to the key the dictionaries use). */
    private fun lemmaEntries(slug: String): Pair<List<LemmaEntry>, Map<String, String>> = lemmaEntryCache.getOrPut(slug) {
        val q = textDb(slug).anagnosisQueries
        val entries = q.selectLemmaCounts().executeAsList().map { LemmaEntry(slug, it.lemma_key, it.lemma ?: it.lemma_key, it.n.toInt()) }
        val aliases = q.selectAliases().executeAsList().associate { it.lemma_key to it.target_key }
        entries to aliases
    }

    /** The lemmas of the given texts, joined across them (see [LemmaIndex.merge]). */
    fun lemmaRows(slugs: List<String>): List<LemmaRow> {
        lemmaRowCache?.let { if (it.first == slugs) return it.second }
        val parts = slugs.associateWith { lemmaEntries(it) }
        val rows = LemmaIndex.merge(parts.values.flatMap { it.first }, parts.mapValues { it.value.second })
        lemmaRowCache = slugs to rows
        return rows
    }

    /** The first short definition found for a row: in a text's own definitions, then the shared ones. */
    fun glossFor(row: LemmaRow): String? {
        for (key in row.keys) {
            for ((slug, keys) in row.keysBySlug) {
                if (key !in keys) continue
                textDb(slug).anagnosisQueries.selectShortDefinition(key).executeAsOneOrNull()?.let { return it.definition }
            }
            lexicon.lexiconQueries.selectShortDefinition(key).executeAsOneOrNull()?.let { return it }
        }
        return null
    }

    /** Every word of a row's lemma in the given texts, as Greek hits, in the order of [slugs] and then of each text. */
    fun occurrences(row: LemmaRow, slugs: List<String>): List<SearchHit> {
        val out = mutableListOf<SearchHit>()
        for (slug in slugs) {
            val keys = row.keysBySlug[slug] ?: continue
            val q = textDb(slug).anagnosisQueries
            out += keys.flatMap { q.selectOccurrences(it).executeAsList() }
                .sortedWith(compareBy({ it.line_ord }, { it.token_ord }))
                .map { SearchHit(slug, SearchSource.GREEK, "", it.n_int, it.n_sub, it.text, it.start.toInt(), it.end.toInt()) }
        }
        return out
    }

    companion object {
        /** Ranged notes shorter than this follow the reader across pages; longer ones stay on their first page. */
        const val OVERLAP_MAX_SPAN = 20L

        /** Mirrors greek.strip_diacritics in the pipeline: base letters only, lower case. */
        fun looseKey(s: String): String = no.anagnosis.greek.GreekNormalizer.looseKey(s)

    }
}

/** A line as a reader sees it: without the verse mark ("| ") or a speaker label's braces. */
fun displayText(text: String): String = text.removePrefix("| ").replace(Regex("\\{([^}]*)\\}"), "$1")
