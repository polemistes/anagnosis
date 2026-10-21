package no.anagnosis.data

import no.anagnosis.db.Lines
import no.anagnosis.db.Tokens

/** One of the reader's bookmarks: a sentence to come back to, anchored by its first word, with a name if one was given. */
class Bookmark(
    val id: Long,
    val textSlug: String,
    val at: WordAnchor,
    val name: String,
    /** The text's first words from the sentence's start when the bookmark was set. */
    val quote: String,
    val created: Long,
)

/** A bookmark with its first word in the current text, or with nulls when it is not found (a renumbered edition). */
class PlacedBookmark(val bookmark: Bookmark, val line: Lines?, val token: Tokens?)

/** Quoting, placing and naming the reader's bookmarks. */
object Bookmarks {

    /** How many words a quote holds. */
    const val QUOTE_WORDS = 8

    /**
     * The first [QUOTE_WORDS] words of the text from [token] on, running past the end of a short
     * sentence into the next and stopping only at the end of the text; "…" follows when more
     * words come after. Punctuation between the words is kept, verse marks and speaker braces are not.
     */
    fun quote(data: WorkData, token: Tokens): String {
        val firstLine = data.lineById[token.line_id] ?: return ""
        val start = data.lineIndex[firstLine.id] ?: return ""
        var taken = 0
        var last: Tokens? = null
        var more = false
        loop@ for (i in start until data.lines.size) {
            val tokens = data.tokensByLine[data.lines[i].id].orEmpty()
            for (t in tokens) {
                if (i == start && t.ord < token.ord) continue
                if (taken == QUOTE_WORDS) { more = true; break@loop }
                last = t
                taken++
            }
        }
        val lastToken = last ?: return ""
        val lastLine = data.lineById[lastToken.line_id] ?: return ""
        val text = Notes.quote(data, Placement(firstLine, token, lastLine, lastToken))
        return if (more) "$text…" else text
    }

    /** Finds the first word of each bookmark in the current text; see [placementOf]. */
    fun place(bookmarks: List<Bookmark>, data: WorkData): List<PlacedBookmark> =
        bookmarks.map { b -> placementOf(b, data)?.let { (line, token) -> PlacedBookmark(b, line, token) } ?: PlacedBookmark(b, null, null) }

    /**
     * The bookmark's line and first word, when both are found by the citation and either the
     * text still reads as it did or begins with the same word ignoring diacritics (a corrected
     * accent does not lose the bookmark).
     */
    fun placementOf(bookmark: Bookmark, data: WorkData): Pair<Lines, Tokens>? {
        val line = data.linesByCitation[bookmark.at.nInt to bookmark.at.nSub] ?: return null
        val token = data.tokensByLine[line.id]?.firstOrNull { it.ord == bookmark.at.word } ?: return null
        if (quote(data, token) == bookmark.quote) return line to token
        val was = bookmark.quote.split(WHITESPACE).firstOrNull { it.isNotEmpty() } ?: return null
        val key = AnagnosisRepository::looseKey
        return if (key(was) == key(token.form)) line to token else null
    }

    /** "Line 12", "Line 591a", "Line 1.12", "Line 172a1", "Matthew 5:3". */
    fun label(data: WorkData, at: WordAnchor): String = Notes.rangeLabel(data, at, at)

    private val WHITESPACE = Regex("\\s+")
}
