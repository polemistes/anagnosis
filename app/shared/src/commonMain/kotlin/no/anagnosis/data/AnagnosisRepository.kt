package no.anagnosis.data

import no.anagnosis.DriverFactory
import no.anagnosis.db.AnagnosisDatabase
import no.anagnosis.db.Documents
import no.anagnosis.db.Lines

class AnagnosisRepository(driverFactory: DriverFactory) {
    private val db = AnagnosisDatabase(driverFactory.createDriver())
    private val q get() = db.anagnosisQueries

    fun loadWork(slug: String): WorkData {
        val work = q.selectWorkBySlug(slug).executeAsOne()
        val lines = q.selectLines(work.id).executeAsList()
        val tokens = q.selectTokensForWork(work.id).executeAsList().groupBy { it.line_id }
        val sections = q.selectSections(work.id).executeAsList()
            .filter { it.first_line_id != null }
            .groupBy { it.first_line_id!! }
        val translations = q.selectTranslations(work.id).executeAsList().map {
            TranslationData(it, q.selectSegments(it.id).executeAsList())
        }
        val commentaries = q.selectCommentaries(work.id).executeAsList()
        // A note on line n attaches to the first existing line with n_int >= n (numbering has gaps).
        val starts = q.selectNoteStarts().executeAsList()
        val withNotes = HashSet<Long>()
        var i = 0
        for (line in lines) {
            var mark = false
            while (i < starts.size && starts[i] <= line.n_int) { mark = true; i++ }
            if (mark) withNotes += line.id
        }
        return WorkData(work, lines, tokens, sections, translations, commentaries, withNotes)
    }

    fun lookupWord(data: WorkData, tokenId: Long): WordInfo? {
        val token = data.tokensByLine.values.asSequence().flatten().firstOrNull { it.id == tokenId } ?: return null
        var rows = q.selectEntriesByKey(token.lemma_key).executeAsList()
            .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, it.html) }
        if (rows.isEmpty()) {
            rows = q.selectEntriesByLooseKey(looseKey(token.lemma)).executeAsList()
                .map { Entry(it.lexicon_slug, it.lexicon_title, it.headword, it.homograph, it.html) }
        }
        val short = q.selectShortDefinition(token.lemma_key).executeAsOneOrNull()?.definition
        return WordInfo(token, Morphology.describe(token.postag), short, rows)
    }

    /** Notes for a line: those on the line itself plus those on absent line numbers just before it. */
    fun notesForLine(data: WorkData, line: Lines): List<NoteInfo> {
        val idx = data.lines.indexOf(line)
        val prevN = if (idx > 0) data.lines[idx - 1].n_int else 0L
        return data.commentaries.map { c ->
            NoteInfo(c, q.selectNotesForLine(c.id, prevN, line.n_int).executeAsList())
        }.filter { it.notes.isNotEmpty() }
    }

    /**
     * Notes of the given kind for a page: every note that starts on the page (or on a skipped
     * number just before it) or whose range overlaps it, grouped by line or range.
     */
    fun notesForPage(data: WorkData, firstN: Long, lastN: Long, kind: NoteKind): List<NoteGroup> {
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
        q.selectDocuments(data.work.id).executeAsList().map { it.slug to it.title }

    /** A free-standing document of the work, e.g. "sigla" (manuscripts and symbols). */
    fun document(data: WorkData, slug: String): Documents? = q.selectDocument(data.work.id, slug).executeAsOneOrNull()

    /** Attribution for everything in the bundle, for the About screen. */
    fun credits(): List<Credit> {
        val out = mutableListOf<Credit>()
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
            out += Credit("Dictionary", l.title, l.source, l.license)
        }
        val short = q.selectShortDefinition("ὁ").executeAsOneOrNull()
        if (short != null) {
            out += Credit("Short definitions", "Logeion (Helma Dik, University of Chicago), based on the Perseus short definitions", "https://github.com/helmadik/shortdefs", "Used with credit to Perseus and Logeion")
        }
        return out
    }

    companion object {
        /** Ranged notes shorter than this follow the reader across pages; longer ones stay on their first page. */
        const val OVERLAP_MAX_SPAN = 20L

        /** Mirrors greek.strip_diacritics in the pipeline: base letters only, lower case. */
        fun looseKey(s: String): String {
            val sb = StringBuilder()
            for (ch in s.lowercase()) {
                val base = STRIP[ch] ?: ch
                if (base in 'α'..'ω' || base == 'ϝ' || base == 'ς') sb.append(base)
            }
            return sb.toString()
        }

        private val STRIP: Map<Char, Char> = buildMap {
            fun add(base: Char, variants: String) = variants.forEach { put(it, base) }
            add('α', "ἀἁἂἃἄἅἆἇὰάᾀᾁᾂᾃᾄᾅᾆᾇᾰᾱᾲᾳᾴᾶᾷά")
            add('ε', "ἐἑἒἓἔἕὲέέ")
            add('η', "ἠἡἢἣἤἥἦἧὴήᾐᾑᾒᾓᾔᾕᾖᾗῂῃῄῆῇή")
            add('ι', "ἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗίϊΐ")
            add('ο', "ὀὁὂὃὄὅὸόό")
            add('υ', "ὐὑὒὓὔὕὖὗὺύῠῡῢΰῦῧύϋΰ")
            add('ω', "ὠὡὢὣὤὥὦὧὼώᾠᾡᾢᾣᾤᾥᾦᾧῲῳῴῶῷώ")
            add('ρ', "ῤῥ")
        }
    }
}
