package no.anagnosis.data

import no.anagnosis.db.Lines

/**
 * Finding verses by number where the text prints some out of their numbers' order (the Theogony
 * prints 407 after 408, the Antigone and others transpose verses too): a number is looked for
 * where it is printed, never assumed to lie between its neighbours in the list.
 */
object LineOrder {
    /**
     * The line numbered [n] (the first so numbered, in printed order); for a number not printed,
     * the line with the next number above it; past the last number, the last line.
     */
    fun lineAtOrAfter(lines: List<Lines>, n: Long): Lines {
        lines.firstOrNull { it.n_int == n }?.let { return it }
        return lines.filter { it.n_int > n }.minByOrNull { it.n_int } ?: lines.last()
    }

    /**
     * The page (by index) that holds the verse [n]: the page where it is printed; for a number not
     * printed, the last page that starts at or before it. [pages] are each page's verse numbers in
     * printed order; -1 when there are none.
     */
    fun pageHolding(pages: List<List<Long>>, n: Long): Int {
        val exact = pages.indexOfFirst { n in it }
        if (exact >= 0) return exact
        return pages.indexOfLast { it.isNotEmpty() && it.first() <= n }
    }

    /**
     * Whether a note on [from]–[to] belongs to the page that prints [onPage]: it starts on a verse
     * printed there; or it starts on a number printed nowhere (a verse the edition leaves out)
     * between the number before the page and the page's last; or its short range (under
     * [maxSpan]) takes in a verse printed there.
     */
    fun noteOnPage(from: Long, to: Long, onPage: Set<Long>, printed: Set<Long>, prevN: Long, maxSpan: Long): Boolean {
        if (from in onPage) return true
        val last = onPage.maxOrNull() ?: return false
        if (from !in printed && from > prevN && from <= last) return true
        return to - from < maxSpan && onPage.any { it in from..to }
    }
}
