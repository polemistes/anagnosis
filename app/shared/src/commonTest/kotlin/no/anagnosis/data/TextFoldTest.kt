package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals

class TextFoldTest {
    private val greek = "ἀλλά μοι ἀμφʼ Ὀδυσῆϊ δαΐφρονι δαίεται ἦτορ, ᾤμωξεν Ῥόδος"
    private val english = "Tell me, O Muse, of the man’s “many devices” — café\nand more"

    @Test
    fun foldKeepsTheLength() {
        for (ia in listOf(true, false)) for (ic in listOf(true, false)) {
            assertEquals(greek.length, TextFold.fold(greek, ia, ic).length)
            assertEquals(english.length, TextFold.fold(english, ia, ic).length)
        }
    }

    @Test
    fun accentsAndCase() {
        assertEquals("ανδρα", TextFold.fold("Ἄνδρα", ignoreAccents = true, ignoreCase = true))
        assertEquals("Ανδρα", TextFold.fold("Ἄνδρα", ignoreAccents = true, ignoreCase = false))
        assertEquals("ἄνδρα", TextFold.fold("Ἄνδρα", ignoreAccents = false, ignoreCase = true))
        assertEquals("Ἄνδρα", TextFold.fold("Ἄνδρα", ignoreAccents = false, ignoreCase = false))
        assertEquals("ωμωξεν ροδοσ", TextFold.fold("ᾤμωξεν Ῥόδος", ignoreAccents = true, ignoreCase = true))
        assertEquals("οδυσηι", TextFold.fold("Ὀδυσῆϊ", ignoreAccents = true, ignoreCase = true))
    }

    @Test
    fun finalSigmaIsAlwaysMedial() {
        assertEquals("λόγοσ", TextFold.fold("λόγος", ignoreAccents = false, ignoreCase = false))
    }

    @Test
    fun marksAndLatin() {
        assertEquals("αμφ'", TextFold.fold("ἀμφʼ", ignoreAccents = true, ignoreCase = true))
        assertEquals("man's", TextFold.fold("man’s", ignoreAccents = true, ignoreCase = true))
        assertEquals("\"many\"", TextFold.fold("“many”", ignoreAccents = true, ignoreCase = true))
        assertEquals("cafe", TextFold.fold("café", ignoreAccents = true, ignoreCase = true))
        assertEquals("Cafe", TextFold.fold("Café", ignoreAccents = true, ignoreCase = false))
        assertEquals("café", TextFold.fold("Café", ignoreAccents = false, ignoreCase = true))
        assertEquals("a b", TextFold.fold("a\nb", ignoreAccents = true, ignoreCase = true))
    }

    @Test
    fun patternKeepsEscapes() {
        assertEquals("\\bλογ\\S*", TextFold.foldPattern("\\bλόγ\\S*", ignoreAccents = true, ignoreCase = true))
        assertEquals("[α-ω]", TextFold.foldPattern("[Ἀ-Ὠ]", ignoreAccents = true, ignoreCase = true))
        assertEquals("\\p{Lu}σ", TextFold.foldPattern("\\p{Lu}Σ", ignoreAccents = true, ignoreCase = true))
    }
}
