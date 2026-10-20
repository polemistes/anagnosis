package no.anagnosis.greek

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class PhonologyTest {
    /** NFD-like normalisation of the expected strings: precomposed IPA letters with an accent split. */
    private fun norm(s: String): String = buildString {
        for (c in s) {
            when (c) {
                'á' -> append("á"); 'é' -> append("é"); 'í' -> append("í"); 'ó' -> append("ó")
                'ú' -> append("ú"); 'ý' -> append("ý")
                'ǎ' -> append("ǎ"); 'ě' -> append("ě"); 'ǐ' -> append("ǐ"); 'ǒ' -> append("ǒ"); 'ǔ' -> append("ǔ")
                'â' -> append("â"); 'ê' -> append("ê"); 'î' -> append("î"); 'ô' -> append("ô"); 'û' -> append("û")
                'ŷ' -> append("ŷ")
                else -> append(c)
            }
        }
    }

    private fun check(variant: Pronunciation, form: String, marked: String?, expected: String) {
        assertEquals(norm(expected), norm(Phonology.ipa(form, marked, variant)), "$variant $form")
    }

    @Test
    fun attic() {
        val rows = listOf(
            Triple("ἄνδρα", null, "ándra"),
            Triple("ἀνήρ", null, "anɛ̌ːr"),
            Triple("Μοῦσα", null, "mûːsa"),
            Triple("πολύτροπον", null, "polýtropon"),
            Triple("ὅς", null, "hós"),
            Triple("πολλά", null, "pollá"),
            Triple("θάλασσα", null, "tʰálassa"),
            Triple("ψυχή", "ψῡχή", "psyːkʰɛ̌ː"),
            Triple("ἀγγέλλω", null, "aŋgéllɔː"),
            Triple("Ζεύς", null, "zděus"),
            Triple("οὐδείς", null, "uːděːs"),
            Triple("ᾠδή", null, "ɔːidɛ̌ː"),
            Triple("εἰμί", null, "eːmí"),
            Triple("ῥήτωρ", null, "hrɛ̌ːtɔːr"),
            Triple("ἄνθρωπος", null, "ántʰrɔːpos"),
            Triple("γιγνώσκω", null, "gignɔ̌ːskɔː"),
            Triple("ἐσβάλλω", null, "ezbállɔː"),
            Triple("τιμή", "τῑμή", "tiːmɛ̌ː"),
            Triple("νεανίας", "νεᾱνίᾱς", "neaːníaːs"),
            Triple("ἀΐσσω", null, "aíssɔː"),
            Triple("Ἀθηναῖος", null, "atʰɛːnâios"),
            Triple("δέ", null, "dé"),
            Triple("δὲ", null, "de"),
            Triple("λῦσαι", null, "lŷːsai"),
            Triple("ἀλλ᾽", null, "all"),
        )
        for ((form, marked, expected) in rows) check(Pronunciation.ATTIC, form, marked, expected)
    }

    @Test
    fun koine() {
        val rows = listOf(
            "ἀνήρ" to "aˈner",
            "φωνή" to "foˈne",
            "εἰρήνη" to "iˈrene",
            "Χριστός" to "xriˈstos",
            "αὐτός" to "afˈtos",
            "εὐαγγέλιον" to "evaŋˈgɛlion",
            "υἱός" to "yˈos",
            "βασιλεία" to "vasiˈlia",
            "οἶκος" to "ˈykos",
            "ἡμέρα" to "eˈmɛra",
            "καί" to "ˈkɛ",
            "ἐγώ" to "ɛˈɣo",
            "θεός" to "θɛˈos",
            "ἄνθρωπος" to "ˈanθropos",
            "Ἰησοῦς" to "ieˈsus",
            "δόξα" to "ˈðoksa",
            "Ζεύς" to "ˈzefs",
            "πνεῦμα" to "ˈpnevma",
            "ἄλλος" to "ˈalos",
        )
        for ((form, expected) in rows) check(Pronunciation.KOINE, form, null, expected)
    }

    @Test
    fun homeric() {
        val rows = listOf(
            Triple("Μοῦσα", null, "môːsa"),
            Triple("πολύτροπον", null, "polútropon"),
            Triple("θυμός", "θῡμός", "tʰuːmós"),
            Triple("Ζεύς", null, "zděus"),
            Triple("οὐ", null, "oː"),
            Triple("Ὀδυσσεύς", null, "odussěus"),
            Triple("ἠώς", null, "ɛːɔ̌ːs"),
        )
        for ((form, marked, expected) in rows) check(Pronunciation.HOMERIC, form, marked, expected)
    }

    @Test
    fun capitalsAndOddTokens() {
        assertEquals(Phonology.ipa("ἄνδρα", null, Pronunciation.ATTIC), Phonology.ipa("Ἄνδρα", null, Pronunciation.ATTIC))
        assertTrue(Phonology.segments("123", null, Pronunciation.ATTIC).isEmpty())
        assertTrue(Phonology.segments("", null, Pronunciation.KOINE).isEmpty())
        // decomposed input reads as the precomposed
        assertEquals(Phonology.ipa("ἀνήρ", null, Pronunciation.ATTIC), Phonology.ipa("ἀνήρ", null, Pronunciation.ATTIC))
        // the tonos of modern keyboards is an acute
        assertEquals(Phonology.ipa("δέ", null, Pronunciation.ATTIC), Phonology.ipa("δέ", null, Pronunciation.ATTIC))
    }

    @Test
    fun transfersLength() {
        assertEquals("τι\u0304μη\u0301", Phonology.transferLength("τιμή", "τῑμή"))
        // the form keeps its capital and its own accents
        assertEquals("Νεα\u0304νι\u0301α\u0304ς", Phonology.transferLength("Νεανίας", "νεᾱνίᾱς"))
        assertEquals(null, Phonology.transferLength("τιμή", "ψῡχή"))
        val marked = Phonology.transferLength("ψυχή", "ψῡχή")
        assertEquals(norm("psyːkʰɛ̌ː"), norm(Phonology.ipa("ψυχή", marked, Pronunciation.ATTIC)))
    }

    @Test
    fun espeakAttic() {
        assertEquals("a1ndra0", Phonology.espeak(Phonology.segments("ἄνδρα", null, Pronunciation.ATTIC), Pronunciation.ATTIC))
        assertEquals("a0nE:2r", Phonology.espeak(Phonology.segments("ἀνήρ", null, Pronunciation.ATTIC), Pronunciation.ATTIC))
        assertEquals("mu:3sa0", Phonology.espeak(Phonology.segments("Μοῦσα", null, Pronunciation.ATTIC), Pronunciation.ATTIC))
        assertEquals("tHa1la0ssa0", Phonology.espeak(Phonology.segments("θάλασσα", null, Pronunciation.ATTIC), Pronunciation.ATTIC))
        assertEquals("zdeU2s", Phonology.espeak(Phonology.segments("Ζεύς", null, Pronunciation.ATTIC), Pronunciation.ATTIC))
    }

    @Test
    fun espeakKoine() {
        assertEquals("xri'stos", Phonology.espeak(Phonology.segments("Χριστός", null, Pronunciation.KOINE), Pronunciation.KOINE))
        assertEquals("af'tos", Phonology.espeak(Phonology.segments("αὐτός", null, Pronunciation.KOINE), Pronunciation.KOINE))
        assertEquals("'pnevma", Phonology.espeak(Phonology.segments("πνεῦμα", null, Pronunciation.KOINE), Pronunciation.KOINE))
        // a word without an accent is marked unstressed, so that eSpeak does not stress it
        assertEquals("%o", Phonology.espeak(Phonology.segments("ὁ", null, Pronunciation.KOINE), Pronunciation.KOINE))
        assertEquals("%En", Phonology.espeak(Phonology.segments("ἐν", null, Pronunciation.KOINE), Pronunciation.KOINE))
    }
}
