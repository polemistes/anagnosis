package no.anagnosis.data

import no.anagnosis.db.Lines
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Verses printed out of their numbers' order (the Theogony prints 407 after 408). */
class LineOrderTest {
    private fun line(id: Long, n: Long) = Lines(id, 1, id, n.toString(), n, "", null, null, 0, "verse $n")
    // as printed: 405 406 408 407 409, and 411 left out by the edition
    private val lines = listOf(line(1, 405), line(2, 406), line(3, 408), line(4, 407), line(5, 409), line(6, 410), line(7, 412))

    @Test
    fun aVerseIsFoundWhereItIsPrinted() {
        assertEquals(4L, LineOrder.lineAtOrAfter(lines, 407).id)   // a binary search over the list found 408 here
        assertEquals(3L, LineOrder.lineAtOrAfter(lines, 408).id)
        assertEquals(7L, LineOrder.lineAtOrAfter(lines, 411).id)   // not printed: the next number
        assertEquals(7L, LineOrder.lineAtOrAfter(lines, 999).id)   // past the end: the last line
        assertEquals(1L, LineOrder.lineAtOrAfter(lines, 1).id)
    }

    @Test
    fun thePageIsTheOneThatPrintsTheVerse() {
        // the page break falls between 408 and 407
        val pages = listOf(listOf(405L, 406L, 408L), listOf(407L, 409L, 410L, 412L))
        assertEquals(0, LineOrder.pageHolding(pages, 408))   // the first-number rule gave page 1
        assertEquals(1, LineOrder.pageHolding(pages, 407))
        assertEquals(1, LineOrder.pageHolding(pages, 411))
        assertEquals(0, LineOrder.pageHolding(pages, 1).coerceAtLeast(0))
    }

    @Test
    fun aNoteGoesWithThePageThatPrintsItsVerse() {
        val printed = lines.map { it.n_int }.toSet()
        val pageA = setOf(405L, 406L, 408L)
        val pageB = setOf(407L, 409L, 410L, 412L)
        // a note on 407: on page B only, although 407 lies between page A's first and last numbers
        assertFalse(LineOrder.noteOnPage(407, 407, pageA, printed, prevN = 404, maxSpan = 20))
        assertTrue(LineOrder.noteOnPage(407, 407, pageB, printed, prevN = 406, maxSpan = 20))
        // a note on 408: on page A only, although it lies between page B's first and last
        assertTrue(LineOrder.noteOnPage(408, 408, pageA, printed, prevN = 404, maxSpan = 20))
        assertFalse(LineOrder.noteOnPage(408, 408, pageB, printed, prevN = 406, maxSpan = 20))
        // a verse the edition leaves out (411) goes with the page that runs over its number
        assertTrue(LineOrder.noteOnPage(411, 411, pageB, printed, prevN = 406, maxSpan = 20))
        assertFalse(LineOrder.noteOnPage(411, 411, pageA, printed, prevN = 404, maxSpan = 20))
        // a short range goes with every page that prints a verse of it
        assertTrue(LineOrder.noteOnPage(407, 408, pageA, printed, prevN = 404, maxSpan = 20))
        assertTrue(LineOrder.noteOnPage(407, 408, pageB, printed, prevN = 406, maxSpan = 20))
    }
}
