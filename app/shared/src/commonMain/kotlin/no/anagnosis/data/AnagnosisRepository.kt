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
import no.anagnosis.todayIso

/**
 * @param today the device's local date (YYYY-MM-DD), asked each time: a text with a release date
 *   exists for the user only from that day ([ReleaseGate])
 * @param granted the texts this build gives without a purchase (the author's own build; empty
 *   in every other build): shown whatever their release date
 */
class AnagnosisRepository(
    private val driverFactory: DriverFactory,
    private val today: () -> String = ::todayIso,
    private val granted: Set<String> = emptySet(),
) {
    private val lexicon by lazy { LexiconDatabase(driverFactory.createDriver("lexicon")) }
    private val textDbs = HashMap<String, AnagnosisDatabase>()
    private val notesDb by lazy { NotesDatabase(driverFactory.createNotesDriver()) }

    private fun textDb(slug: String): AnagnosisDatabase =
        textDbs.getOrPut(slug) { AnagnosisDatabase(driverFactory.createDriver(slug)) }

    /**
     * The texts bought in the reader, as the store last said; set by the app before it reads the
     * catalog. A text downloaded from the store is shown only while it is among them.
     */
    var ownedTexts: Set<String> = emptySet()

    /** The note sets a text's meta `translation_notes` names as notes to the translation (slugs). */
    private fun translationNoteSlugs(q: no.anagnosis.db.AnagnosisQueries): Set<String> =
        q.selectMeta("translation_notes").executeAsOneOrNull()?.split(' ')?.filter { it.isNotBlank() }?.toSet() ?: emptySet()

    /** The texts this app knows about, installed ones marked. */
    fun catalog(): List<CatalogEntry> {
        val all = catalogEntries()
        val day = today()
        val hidden = ReleaseGate.hidden(all, day, granted)
        val installed = driverFactory.installedTexts(ownedTexts).toSet() - hidden
        val entries = all.filter { it.slug !in hidden }
        val listed = all.map { it.slug }.toSet()
        // installed texts missing from the catalog (e.g. a downloaded text) still appear
        val extra = installed.filter { it !in listed }.map { slug ->
            val w = textDb(slug).anagnosisQueries.selectWorkBySlug(slug).executeAsOneOrNull()
            CatalogEntry(slug, w?.title ?: slug, w?.author ?: "", w?.title ?: slug, w?.author ?: "", "", w?.edition ?: "", true)
        }
        return entries.map { it.copy(installed = it.slug in installed, offered = ReleaseGate.offered(it, day)) } + extra
    }

    /** The catalogue's entries, once each. */
    private fun catalogEntries(): List<CatalogEntry> =
        driverFactory.readCatalog()?.let(::parseCatalog).orEmpty().distinctBy { it.slug }

    /**
     * The texts on sale in the reader: those offered today ([ReleaseGate.offered]: marked for
     * sale, or past their release date), with a product id and a built database.
     */
    fun textsOnSale(): List<OnSale> {
        val day = today()
        return catalogEntries()
            .filter { !it.free && ReleaseGate.offered(it, day) && it.productId.isNotEmpty() && it.version.isNotEmpty() }
            .map { OnSale(it.slug, it.productId, it.version) }
    }

    /**
     * The free texts (catalogue `free`), released by their date and with a built database: offered
     * with Download, added without payment and fetched like a bought text; no product is needed.
     */
    fun textsFree(): List<OnSale> {
        val day = today()
        return catalogEntries()
            .filter { it.free && it.version.isNotEmpty() && ReleaseGate.released(it.release, day) }
            .map { OnSale(it.slug, it.productId, it.version) }
    }

    /**
     * The texts this build gives without a purchase (the author's own build, [slugs] from its
     * BuildConfig), as far as the catalogue has them with a built database. They carry no sale
     * mark and need no product in the store; their packs are fetched as for a bought text.
     */
    fun textsGranted(slugs: Collection<String>): List<OnSale> =
        if (slugs.isEmpty()) emptyList()
        else catalogEntries().filter { it.slug in slugs && it.version.isNotEmpty() }
            .map { OnSale(it.slug, it.productId, it.version) }

    private fun CatalogEntry.copy(installed: Boolean, offered: Boolean) =
        CatalogEntry(slug, title, author, titleEn, authorEn, description, edition, installed, appId,
            editor, apparatus, translation, commentary, syntax, dictionaries, offered, productId,
            refEdition, refTranslation, refCommentary, syntaxSource, syntaxLicense, version, release,
            translationNotes, refTranslationNotes, free, syntaxText)

    private fun parseCatalog(json: String): List<CatalogEntry> {
        // the catalog is a flat JSON array of objects with string values; a small parser suffices
        val objects = Regex("\\{[^{}]*\\}").findAll(json).map { it.value }
        fun flag(obj: String, name: String): Boolean = catalogFlag(obj, name)
        fun field(obj: String, name: String): String {
            val m = Regex("\"$name\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").find(obj) ?: return ""
            return m.groupValues[1].replace("\\n", "\n").replace("\\\"", "\"").replace("\\\\", "\\")
        }
        return objects.map { o ->
            CatalogEntry(field(o, "slug"), field(o, "title"), field(o, "author"), field(o, "title_en"),
                field(o, "author_en"), field(o, "description"), field(o, "edition"), false, field(o, "app_id"),
                field(o, "editor"), field(o, "apparatus"), field(o, "translation"), field(o, "commentary"),
                field(o, "syntax"), field(o, "dictionaries"), field(o, "google_play") == "yes", field(o, "product_id"),
                field(o, "ref_edition"), field(o, "ref_translation"), field(o, "ref_commentary"),
                field(o, "syntax_source"), field(o, "syntax_license"), field(o, "version"), field(o, "release"),
                field(o, "translation_notes"), field(o, "ref_translation_notes"), flag(o, "free"), field(o, "syntax_text"))
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
        // the trees made on another text: the rows only where the text says it has them
        val syntaxText = q.selectMeta("syntax_text").executeAsOneOrNull()?.takeIf { it.isNotBlank() }
        val textWords = if (light || q.selectMeta("syntax_text_words").executeAsOneOrNull() == null) emptyList()
            else q.selectSyntaxTextWords().executeAsList().map { SyntaxTextWord(it.kind, it.token_id, it.sentence, it.word_id?.toInt(), it.tree_form, it.tree_lemma, it.extent, it.same_construction, it.tree_postag, it.difference) }
        // where the notes on the Greek begin, for the book chooser's marks (only books are marked)
        val declaredTranslationNotes = q.selectMeta("translation_notes").executeAsOneOrNull()?.split(' ')?.filter { it.isNotBlank() }?.toSet() ?: emptySet()
        val onGreek = commentaries.filter { it.kind() == NoteKind.COMMENTARY && !BookContents.isTranslationNotes(it.slug, it.title, declaredTranslationNotes) }.map { it.id }.toSet()
        val commentaryStarts = if (light || onGreek.isEmpty() || numbering !in setOf("book.line", "verse")) emptyList()
            else q.selectNoteStartsByCommentary().executeAsList().filter { it.commentary_id in onGreek }.map { it.from_n_int }
        return WorkData(
            slug, work, lines, tokens, nodes, sections, translations, commentaries, withNotes,
            bookNumbered = numbering == "book.line",
            verses = numbering == "verse",
            dottedCitation = q.selectMeta("citation").executeAsOneOrNull() == "dotted",
            stephanus = numbering == "stephanus",
            prose = q.selectMeta("layout").executeAsOneOrNull() == "prose",
            closedDashes = q.selectMeta("dashes").executeAsOneOrNull() == "closed",
            automaticSyntax = q.selectMeta("syntax").executeAsOneOrNull() == "automatic",
            syntaxByBook = Book.parseSyntaxByBook(q.selectMeta("syntax_by_book").executeAsOneOrNull()),
            commentaryStarts = commentaryStarts,
            syntaxText = syntaxText,
            syntaxTextByToken = textWords.filter { it.tokenId != null }.associateBy { it.tokenId!! },
            syntaxTextByNode = textWords.filter { it.sentence != null && it.wordId != null && it.kind != "unit" }.associateBy { it.sentence!! to it.wordId!! },
            translationNoteIds = commentaries.filter { it.kind() == NoteKind.COMMENTARY && BookContents.isTranslationNotes(it.slug, it.title, declaredTranslationNotes) }.map { it.id }.toSet(),
            dictionaryOrder = q.selectMeta("dictionaries").executeAsOneOrNull()?.split(' ')?.filter { it.isNotBlank() } ?: emptyList(),
            pronunciation = defaultPronunciation(slug, work.author, q.selectMeta("pronunciation").executeAsOneOrNull()),
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
        // where the trees were made on another text, a role only where our word is the trees' own word
        val syntax = token.sentence?.takeIf { SyntaxText.showsRole(data.syntaxTextByToken[token.id], token.form) }
            ?.let { Syntax.roleLine(sentenceTree(data, it), token) }
            ?.let { if (data.automaticSyntaxAt(data.lineById[token.line_id]?.n_int ?: 0L)) "$it (automatic)" else it }
        val (lemma, homograph) = splitHomograph(token.lemma)
        return WordInfo(token.form, lemma, Morphology.describe(token.postag), short, glossary + rows, syntax, markedForm(token), homograph,
        )
    }

    /** The token's form with the long vowels its spelling does not show marked, or null (see [VowelLength]). */
    fun markedForm(token: Tokens): String? {
        val analyses = analyse(token.form, exact = true).ifEmpty { analyse(token.form) }
        return VowelLength.choose(token.form, token.lemma_key, token.postag, analyses)
    }

    /** A word outside the text (a speaker's name) with its long vowels marked when the analyses agree, or null. */
    fun markedWord(form: String): String? = VowelLength.ofForm(form, analyse(form, exact = true).ifEmpty { analyse(form) })

    /** The tokens of a sentence in text order; a sentence can run over several lines and share a line with another. */
    fun sentenceTokens(data: WorkData, sentence: String): List<Tokens> =
        data.lines.asSequence().flatMap { data.tokensByLine[it.id] ?: emptyList() }.filter { it.sentence == sentence }.toList()

    /** The dependency tree of a sentence, from its tokens and the treebank's extra nodes. */
    fun sentenceTree(data: WorkData, sentence: String): SyntaxTree =
        Syntax.asTreesText(Syntax.build(sentence, sentenceTokens(data, sentence), data.nodesBySentence[sentence] ?: emptyList()),
            data.syntaxTextByToken, data.syntaxTextByNode)

    /**
     * Notes of the given kind for a page: every note that starts on the page (or on a skipped
     * number just before it) or whose short range overlaps it, grouped by line or range.
     */
    fun notesForPage(data: WorkData, firstN: Long, lastN: Long, kind: NoteKind): List<NoteGroup> {
        val q = textDb(data.slug).anagnosisQueries
        val firstIdx = data.lines.indexOfFirst { it.n_int >= firstN }
        val prevN = if (firstIdx > 0) data.lines[firstIdx - 1].n_int else 0L
        val commentaries = data.commentaries.filter { it.kind() == kind }
        val order = commentaries.withIndex().associate { (i, c) -> c.id to i }
        val notes = commentaries
            .flatMap { q.selectNotesForPage(it.id, prevN, lastN, firstN, OVERLAP_MAX_SPAN).executeAsList() }
            .sortedWith(compareBy({ it.from_n_int }, { -it.to_n_int }, { order[it.commentary_id] ?: 0 }, { it.ord }))
        // where the text has two or more sets of notes of this kind (Jerram's and the Dickinson
        // College Commentaries' on Lucian; Lysias's four, Gillies's notes to his translation among
        // them), each group names whose notes they are, also on a page where only one set speaks
        val mixed = NoteGroups.nameEachGroup(commentaries.size)
        val names = commentaries.associate { c ->
            c.id to (c.title?.let { Regex("\\(([^)]+)\\)").find(it)?.groupValues?.get(1) } ?: c.author ?: c.slug)
        }
        val groups = mutableListOf<NoteGroup>()
        for ((key, group) in notes.groupBy { it.n to (if (mixed) it.commentary_id else 0L) }) {
            val first = group.first()
            val byWhom = if (mixed) " · " + NoteLabels.groupName(names[first.commentary_id].orEmpty(),
                first.commentary_id in data.translationNoteIds, data.onlyTranslationNotes) else ""
            val heading = when {
                data.verses -> data.range(first.from_n_int, first.to_n_int)
                data.sectioned && first.to_n_int > first.from_n_int -> "§§ ${key.first.replace("-", "–")}"
                data.sectioned -> "§ ${key.first}"
                first.to_n_int > first.from_n_int -> "Lines ${key.first.replace("-", "–")}"
                else -> "Line ${key.first}"
            } + byWhom
            // the line's text once, above the first commentator's notes on it
            val lineText = if (mixed && groups.isNotEmpty() && groups.last().key == key.first) null
                else data.lines.firstOrNull { it.n_int >= first.from_n_int }?.text?.let(::displayText)
            groups += NoteGroup(heading, lineText, group, key.first)
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

    /** The reader's bookmarks in a text, in text order. */
    fun bookmarks(textSlug: String): List<Bookmark> =
        notesDb.bookmarksQueries.selectForText(textSlug).executeAsList().map {
            Bookmark(it.id, it.text_slug, WordAnchor(it.n_int, it.n_sub, it.word), it.name, it.quote, it.created)
        }

    /** Saves a new bookmark and returns its id. */
    fun addBookmark(textSlug: String, at: WordAnchor, name: String, quote: String): Long {
        val q = notesDb.bookmarksQueries
        return q.transactionWithResult {
            q.insert(textSlug, at.nInt, at.nSub, at.word, name, quote, nowMillis())
            q.lastInsertId().executeAsOne()
        }
    }

    fun renameBookmark(id: Long, name: String) = notesDb.bookmarksQueries.rename(name, id)

    fun deleteBookmark(id: Long) = notesDb.bookmarksQueries.delete(id)

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

    /** Whether the shared lexicon holds the dictionary (Woodhouse comes with lexicons built since 2026-10). */
    fun hasLexicon(slug: String): Boolean = lexicon.lexiconQueries.selectLexicons().executeAsList().any { it.slug == slug }

    /** Woodhouse's English headwords starting with the given key (Dictionaries.englishKey). */
    fun searchEnglish(key: String, limit: Long = 80): List<HeadwordHit> {
        if (key.isEmpty()) return emptyList()
        return lexicon.lexiconQueries.searchLexiconHeadwords(Dictionaries.WOODHOUSE, key, key + "\uFFFF", limit).executeAsList()
            .map { HeadwordHit(it.lemma_key, it.headword ?: it.lemma_key) }
    }

    /** The sheet of an English headword: Woodhouse's entries for it (Late, adj., and Late, adv.). */
    fun wordInfoForEnglish(key: String, headword: String): WordInfo {
        val entries = lexicon.lexiconQueries.selectEntriesByKeyIn(Dictionaries.WOODHOUSE, key).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, inflate(it.html)) }
        return WordInfo(headword, headword, "", null, entries)
    }

    /**
     * The sheet of a Greek word tapped in a dictionary entry: the word as a headword, or else as an
     * inflected form, its lemma's (with the marks typed, when they narrow it). Woodhouse's marks
     * of vowel length are left out.
     */
    fun wordInfoForForm(word: String): WordInfo {
        val form = no.anagnosis.greek.Polytonic.withoutLength(word.trimEnd('ʼ', '’'))
        val lq = lexicon.lexiconQueries
        if (lq.selectEntriesByKey(form.lowercase()).executeAsList().isNotEmpty()) {
            return wordInfoForLemma(form.lowercase(), form)
        }
        val analyses = analyse(form, exact = true).ifEmpty { analyse(form) }
        val a = analyses.firstOrNull { entriesForLemma(it.lemma).isNotEmpty() } ?: analyses.firstOrNull()
        return if (a != null) wordInfoForAnalysis(a) else WordInfo(form, form, "", null, entriesForLemma(form))
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
        return WordInfo(a.form, a.lemma, Morphology.describe(a.postag), short, entriesForLemma(a.lemma),
            marked = a.marked?.let { no.anagnosis.greek.Phonology.transferLength(a.form, it) })
    }

    /**
     * Analyses of an inflected form. Diacritics are ignored for the lookup; with [exact] the
     * result is narrowed to analyses whose form has the typed diacritics (when any were typed).
     */
    fun analyse(form: String, exact: Boolean = false): List<FormAnalysis> {
        val packed = lexicon.lexiconQueries.selectForms(looseKey(form)).executeAsOneOrNull() ?: return emptyList()
        val all = inflate(packed).lineSequence().mapNotNull { line ->
            val f = line.split('\t')
            if (f.size >= 4) FormAnalysis(f[0], f[1], f[1].lowercase(), f[2], f[3], f.getOrNull(4)?.takeIf { it.isNotEmpty() }) else null
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
        val hidden = ReleaseGate.hidden(catalogEntries(), today(), granted)
        for (slug in driverFactory.installedTexts(ownedTexts).filter { it !in hidden }) {
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
        val declared = translationNoteSlugs(q)
        for (c in q.selectAllCommentaries().executeAsList()) {
            val kind = NoteLabels.creditKind(c.kind() == NoteKind.APPARATUS, BookContents.isTranslationNotes(c.slug, c.title, declared))
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
        if (entry.syntaxText.isNotEmpty()) {
            out += Credit(SyntaxText.CREDIT_KIND, entry.syntaxText, null, null)
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
        val declared = translationNoteSlugs(q)
        for (c in q.selectCommentaries(work.work.id).executeAsList()) {
            val units = q.selectAllNotes(c.id).executeAsList().map { SearchUnit(it.from_n_int, "", plainText(it.html), extra = c.id) }
            docs += SearchDoc(slug, SearchSource.COMMENTARY, NoteLabels.searchLabel(c.kind(), BookContents.isTranslationNotes(c.slug, c.title, declared)), units)
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
                textDb(slug).anagnosisQueries.selectShortDefinition(key).executeAsOneOrNull()?.let { return it.definition.replace("\n", "  ") }
            }
            lexicon.lexiconQueries.selectShortDefinition(key).executeAsOneOrNull()?.let { return it.replace("\n", "  ") }
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

/** A catalogue entry's yes/no key ("free": true, a JSON boolean; also the string "yes"), in one entry's JSON object. */
internal fun catalogFlag(obj: String, name: String): Boolean =
    Regex("\"$name\"\\s*:\\s*(true|\"yes\")").containsMatchIn(obj)
