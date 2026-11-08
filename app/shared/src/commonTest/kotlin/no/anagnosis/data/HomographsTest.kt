package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals

class HomographsTest {
    @Test
    fun lemmaWithoutItsNumber() {
        assertEquals("μήν" to 2, splitHomograph("μήν2"))
        assertEquals("μήν" to null, splitHomograph("μήν"))
    }

    @Test
    fun sensesOfAList() {
        assertEquals(listOf(1 to "now verily, full surely", 2 to "[month > μείς, μηνός]"),
            homographSenses("1. now verily, full surely\n2. [month > μείς, μηνός]"))
        // an ordinary definition is one part, even if it holds a number
        assertEquals(listOf(0 to "1. a guess"), homographSenses("1. a guess"))
        assertEquals(listOf(0 to "the head"), homographSenses("the head"))
    }
}
