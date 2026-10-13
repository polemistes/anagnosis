package no.anagnosis.data

import no.anagnosis.db.Lines
import no.anagnosis.db.Tokens

/**
 * Where a note's passage begins or ends: the line by its citation (n_int, n_sub) and the word's
 * 0-based place in that line (tokens.ord). Database ids change whenever a text is rebuilt; a
 * citation does not.
 */
data class WordAnchor(val nInt: Long, val nSub: String, val word: Long)

/** One of the reader's own notes on a passage of the Greek. */
class Note(
    val id: Long,
    val textSlug: String,
    val from: WordAnchor,
    val to: WordAnchor,
    /** The Greek of the passage when the note was made. */
    val quote: String,
    val body: String,
    val created: Long,
    val modified: Long,
)

/** A note's passage found in the current text: its first and last word with their lines. */
class Placement(val firstLine: Lines, val firstToken: Tokens, val lastLine: Lines, val lastToken: Tokens)

/** A note with its place in the text, or with null when its passage is not found (a renumbered edition). */
class PlacedNote(val note: Note, val placement: Placement?)

/** The stretch of a line's text (offsets into Lines.text) that a note covers. */
class NoteSpan(val start: Int, val end: Int, val noteId: Long)

/** A passage chosen for a new note, before it is saved. */
class NoteDraft(val from: WordAnchor, val to: WordAnchor, val quote: String, val heading: String)

/** Placing, quoting and naming the reader's notes, and writing them out as Markdown. */
object Notes {

    fun anchorOf(data: WorkData, token: Tokens): WordAnchor {
        val line = data.lineById.getValue(token.line_id)
        return WordAnchor(line.n_int, line.n_sub, token.ord)
    }

    private fun lineOf(data: WorkData, a: WordAnchor): Lines? = data.linesByCitation[a.nInt to a.nSub]

    private fun tokenOf(data: WorkData, line: Lines, a: WordAnchor): Tokens? =
        data.tokensByLine[line.id]?.firstOrNull { it.ord == a.word }

    /** Whether [a] comes before [b] in the text: by the lines' order, then the word's place. */
    fun isBefore(data: WorkData, a: WordAnchor, b: WordAnchor): Boolean {
        val la = lineOf(data, a)?.ord
        val lb = lineOf(data, b)?.ord
        if (la != null && lb != null && la != lb) return la < lb
        if (la == null || lb == null) {
            if (a.nInt != b.nInt) return a.nInt < b.nInt
            if (a.nSub != b.nSub) return a.nSub < b.nSub
        }
        return a.word < b.word
    }

    /** Finds the passage of each note in the current text; see [placementOf]. */
    fun place(notes: List<Note>, data: WorkData): List<PlacedNote> = notes.map { PlacedNote(it, placementOf(it, data)) }

    /**
     * A note is placed when both its words are found, the first is not after the last, and either
     * the passage reads as it did or its first and last words are the same ignoring diacritics
     * (a corrected accent elsewhere in it does not lose the note). Otherwise it is not placed.
     */
    fun placementOf(note: Note, data: WorkData): Placement? {
        val firstLine = lineOf(data, note.from) ?: return null
        val lastLine = lineOf(data, note.to) ?: return null
        val firstToken = tokenOf(data, firstLine, note.from) ?: return null
        val lastToken = tokenOf(data, lastLine, note.to) ?: return null
        if (firstLine.ord > lastLine.ord || (firstLine.ord == lastLine.ord && firstToken.ord > lastToken.ord)) return null
        val placement = Placement(firstLine, firstToken, lastLine, lastToken)
        if (quote(data, placement) == note.quote) return placement
        val words = note.quote.split(WHITESPACE).filter { it.isNotEmpty() }
        if (words.isEmpty()) return null
        val key = AnagnosisRepository::looseKey
        return if (key(words.first()) == key(firstToken.form) && key(words.last()) == key(lastToken.form)) placement else null
    }

    /** The Greek of a passage as one line of text, without verse marks or speaker braces. */
    fun quote(data: WorkData, p: Placement): String {
        val first = data.lineIndex[p.firstLine.id] ?: return ""
        val last = data.lineIndex[p.lastLine.id] ?: return ""
        val pieces = (first..last).map { i ->
            val line = data.lines[i]
            val text = line.text
            val start = if (i == first) p.firstToken.start.toInt() else 0
            val end = if (i == last) p.lastToken.end.toInt() else text.length
            displayText(text.substring(start.coerceIn(0, text.length), end.coerceIn(0, text.length))).trim()
        }
        return pieces.filter { it.isNotEmpty() }.joinToString(" ").replace(WHITESPACE, " ")
    }

    /** "Line 12", "Lines 12–14", "Lines 591–591a", "Lines 1.12–1.15", "Lines 172a1–172b3", "Matthew 5:3–7". */
    fun rangeLabel(data: WorkData, from: WordAnchor, to: WordAnchor): String = when {
        data.verses -> data.range(from.nInt, to.nInt)
        from.nInt == to.nInt && from.nSub == to.nSub -> "Line ${data.citation(from.nInt, from.nSub)}"
        else -> "Lines ${data.citation(from.nInt, from.nSub)}–${data.citation(to.nInt, to.nSub)}"
    }

    /** What each line carries of the placed notes, by line id: from a passage's first word to its last. */
    fun spansByLine(placed: List<PlacedNote>, data: WorkData): Map<Long, List<NoteSpan>> {
        val out = HashMap<Long, MutableList<NoteSpan>>()
        for (pn in placed) {
            val p = pn.placement ?: continue
            val first = data.lineIndex[p.firstLine.id] ?: continue
            val last = data.lineIndex[p.lastLine.id] ?: continue
            for (i in first..last) {
                val line = data.lines[i]
                val tokens = data.tokensByLine[line.id].orEmpty()
                if (tokens.isEmpty()) continue
                val start = if (i == first) p.firstToken.start else tokens.first().start
                val end = if (i == last) p.lastToken.end else tokens.last().end
                if (end > start) out.getOrPut(line.id) { mutableListOf() } += NoteSpan(start.toInt(), end.toInt(), pn.note.id)
            }
        }
        return out
    }

    /** The notes of a text as a Markdown file: placed ones in text order, then those whose passage is not found. */
    fun markdown(data: WorkData, title: String, author: String, edition: String, placed: List<PlacedNote>): String = buildString {
        append("# Notes on ").append(title).append("\n\n")
        append(listOf(author, title).filter { it.isNotBlank() }.joinToString(", ")).append('.')
        if (edition.isNotBlank()) append(" Edition: ").append(edition.trim().trimEnd('.')).append('.')
        append("\nExported from Anagnosis.\n")
        fun entry(n: Note, level: String) {
            append('\n').append(level).append(' ').append(rangeLabel(data, n.from, n.to)).append("\n\n")
            append("> ").append(n.quote).append("\n\n")
            append(n.body.trim()).append('\n')
        }
        placed.filter { it.placement != null }.forEach { entry(it.note, "##") }
        val lost = placed.filter { it.placement == null }
        if (lost.isNotEmpty()) {
            append("\n## Passages not found in the current text\n")
            lost.forEach { entry(it.note, "###") }
        }
    }

    private val WHITESPACE = Regex("\\s+")
}
