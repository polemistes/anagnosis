package no.anagnosis.data

import kotlin.coroutines.cancellation.CancellationException

/** Where the text search looks. */
enum class SearchSource(val label: String) {
    GREEK("Greek"), TRANSLATION("Translation"), COMMENTARY("Commentary"), NOTES("My notes"),
}

/** How the text search matches; all off by default (accents and case ignored, any part of a word). */
data class SearchOptions(
    val exactAccents: Boolean = false,
    val exactCase: Boolean = false,
    val wholeWords: Boolean = false,
    val regex: Boolean = false,
)

/**
 * One searchable unit: a Greek line, a translation paragraph, a commentary note or one of the
 * reader's notes, with the citation it belongs to. [extra] is the note's id for the reader's
 * notes and the commentary's id for a commentary note.
 */
class SearchUnit(val nInt: Long, val nSub: String, val text: String, val extra: Long = 0)

/** The units of one source of one text, joined by newlines into one string. */
class SearchDoc(val slug: String, val source: SearchSource, val label: String, val units: List<SearchUnit>) {
    /** Where each unit starts in [text]. */
    val starts: IntArray = IntArray(units.size)
    val text: String = buildString {
        units.forEachIndexed { i, u ->
            if (i > 0) append('\n')
            starts[i] = length
            append(u.text)
        }
    }

    // the folding last asked for: a text is usually searched again and again with the same options
    private var cache: Pair<Int, String>? = null

    fun folded(options: SearchOptions): String {
        val key = (if (options.exactAccents) 1 else 0) + (if (options.exactCase) 2 else 0)
        cache?.let { if (it.first == key) return it.second }
        val f = TextFold.fold(text, !options.exactAccents, !options.exactCase)
        cache = key to f
        return f
    }

    /** The index of the unit holding the offset (a separating newline belongs to the unit before it). */
    fun unitAt(offset: Int): Int {
        var lo = 0
        var hi = starts.size - 1
        while (lo < hi) {
            val mid = (lo + hi + 1) / 2
            if (starts[mid] <= offset) lo = mid else hi = mid - 1
        }
        return lo
    }
}

/** A match: its text and source, the unit it lies in, and its place in that unit's text. */
class SearchHit(
    val slug: String,
    val source: SearchSource,
    val label: String,
    val nInt: Long,
    val nSub: String,
    val unitText: String,
    val start: Int,
    val end: Int,
    val extra: Long = 0,
)

/** What a search found; [error] is set when the pattern is not a valid regular expression. */
class SearchResult(val hits: List<SearchHit>, val truncated: Boolean = false, val error: String? = null) {
    companion object {
        val EMPTY = SearchResult(emptyList())
    }
}

/** A stretch of text to show for a hit, with the match's place in it. */
class Excerpt(val text: String, val start: Int, val end: Int)

/**
 * Where a hit opens the reader: the line, the match in the Greek or in the translation, the
 * commentary sheet to open (by its kind) or the reader's note to open (by id).
 */
class SearchTarget(
    val slug: String,
    val source: SearchSource,
    val nInt: Long,
    val nSub: String,
    val start: Int,
    val end: Int,
    val noteKind: NoteKind? = null,
    val noteId: Long? = null,
)

/**
 * A text that asks [isActive] every few thousand characters read and stops with a
 * [CancellationException] once it is false: the regular-expression engine never checks for
 * cancellation itself, and a pattern that backtracks badly could otherwise run on for minutes.
 */
class CancellableText(private val text: String, private val isActive: () -> Boolean) : CharSequence {
    private var reads = 0
    override val length: Int get() = text.length
    override fun get(index: Int): Char {
        if ((++reads and 4095) == 0 && !isActive()) throw CancellationException("search cancelled")
        return text[index]
    }
    override fun subSequence(startIndex: Int, endIndex: Int): CharSequence = text.subSequence(startIndex, endIndex)
    override fun toString(): String = text
}

object TextSearch {
    const val MAX_HITS = 2000
    private const val BEFORE = 60
    private const val AFTER = 80

    /**
     * Searches the documents in the order given. An empty query finds nothing. Stops with a
     * [CancellationException] when [isActive] turns false, and after [MAX_HITS] hits.
     */
    fun search(docs: List<SearchDoc>, query: String, options: SearchOptions, isActive: () -> Boolean = { true }): SearchResult {
        val q = query.trim()
        if (q.isEmpty()) return SearchResult.EMPTY
        val ignoreAccents = !options.exactAccents
        val ignoreCase = !options.exactCase
        val pattern = if (options.regex) {
            try {
                Regex(TextFold.foldPattern(q, ignoreAccents, ignoreCase))
            } catch (e: IllegalArgumentException) {  // java's PatternSyntaxException is one
                return SearchResult(emptyList(), error = "Not a valid pattern")
            }
        } else null
        val needle = TextFold.fold(q, ignoreAccents, ignoreCase)
        val hits = ArrayList<SearchHit>()
        for (doc in docs) {
            if (!isActive()) throw CancellationException("search cancelled")
            val folded = doc.folded(options)
            val matches: Sequence<IntRange> = if (pattern != null) {
                pattern.findAll(CancellableText(folded, isActive)).map { it.range }.filter { !it.isEmpty() }
            } else {
                generateSequence(folded.indexOf(needle).takeIf { it >= 0 }) { prev ->
                    folded.indexOf(needle, prev + needle.length).takeIf { it >= 0 }
                }.map { it until it + needle.length }
            }
            for (m in matches) {
                val start = m.first
                val end = m.last + 1
                if (options.wholeWords && !isWholeWord(folded, start, end)) continue
                val i = doc.unitAt(start)
                val unit = doc.units[i]
                val base = doc.starts[i]
                hits += SearchHit(
                    doc.slug, doc.source, doc.label, unit.nInt, unit.nSub, unit.text,
                    start - base, minOf(end - base, unit.text.length), unit.extra,
                )
                if (hits.size >= MAX_HITS) return SearchResult(hits, truncated = true)
            }
        }
        return SearchResult(hits)
    }

    private fun isWholeWord(text: String, start: Int, end: Int): Boolean =
        (start == 0 || !text[start - 1].isLetter()) && (end >= text.length || !text[end].isLetter())

    /**
     * What a hit shows: a Greek line whole (without the mark of a verse quoted in prose); the
     * other sources a stretch around the match, cut at word boundaries, with … where cut.
     */
    fun excerpt(hit: SearchHit): Excerpt {
        val t = hit.unitText
        if (hit.source == SearchSource.GREEK) {
            if (t.startsWith("| ")) return Excerpt(t.substring(2), maxOf(0, hit.start - 2), maxOf(0, hit.end - 2))
            return Excerpt(t, hit.start, hit.end)
        }
        var from = maxOf(0, hit.start - BEFORE)
        var to = minOf(t.length, hit.end + AFTER)
        // cut at a word boundary: the stretch begins after a space and ends before one
        if (from > 0) {
            val space = t.indexOf(' ', from)
            if (space in 0 until hit.start) from = space + 1
        }
        if (to < t.length) {
            val space = t.lastIndexOf(' ', to)
            if (space >= hit.end) to = space
        }
        val prefix = if (from > 0) "…" else ""
        val suffix = if (to < t.length) "…" else ""
        val text = prefix + t.substring(from, to) + suffix
        return Excerpt(text, hit.start - from + prefix.length, hit.end - from + prefix.length)
    }
}
