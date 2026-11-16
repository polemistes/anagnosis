package no.anagnosis.ui

import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class TextTapsTest {
    // a wrapped verse's second row drawn from x 108 to 257 (its hanging indent before it), slop 10
    @Test
    fun tapInTheIndentBeforeARowIsNoWord() {
        assertFalse(withinRow(60f, 108f, 257f, 10f))
        assertFalse(withinRow(97f, 108f, 257f, 10f))
    }

    @Test
    fun tapOnTheRowOrWithinTheSlopIsAWord() {
        assertTrue(withinRow(98f, 108f, 257f, 10f))
        assertTrue(withinRow(108f, 108f, 257f, 10f))
        assertTrue(withinRow(200f, 108f, 257f, 10f))
        assertTrue(withinRow(267f, 108f, 257f, 10f))
    }

    @Test
    fun tapAfterTheRowIsNoWord() {
        assertFalse(withinRow(268f, 108f, 257f, 10f))
    }

    @Test
    fun anUnindentedRowStartsAtZero() {
        // the first row of a verse: the text starts at the left of its layout; a tap left of the
        // layout (negative, in the indent of a staggered part) is no word
        assertTrue(withinRow(0f, 0f, 764f, 10f))
        assertFalse(withinRow(-40f, 0f, 764f, 10f))
    }
}
