package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class LemmaSpellingTest {
    // the short definitions of a text keyed by spelling (Gorgias, Antigone as built on 2026-11-17)
    private val gorgias = mapOf("Πῶλος" to "Polus", "πῶλος" to "Polus", "ἄνθρωπος" to "man, person, human")
    private val antigone = mapOf("ἔρως" to "love")

    private fun shortDefinition(defs: Map<String, String>, lemma: String, lemmaKey: String, bySpelling: Boolean = true) =
        defs[LemmaSpelling.shortDefinitionKey(lemma, lemmaKey, bySpelling)]

    @Test
    fun aNameIsLookedUpByItsOwnSpelling() {
        assertEquals("Πῶλος", LemmaSpelling.shortDefinitionKey("Πῶλος", "πῶλος", bySpelling = true))
        assertEquals("Polus", shortDefinition(gorgias, "Πῶλος", "πῶλος"))
    }

    @Test
    fun aNameWithoutItsOwnRowHasNoShortDefinitionNotTheCommonWords() {
        // Ἔρως must not show ἔρως "love"
        assertEquals(null, shortDefinition(antigone, "Ἔρως", "ἔρως"))
        assertEquals(null, shortDefinition(gorgias, "Ἄνθρωπος", "ἄνθρωπος"))
    }

    @Test
    fun aLemmaWrittenSmallKeepsTheLowerCaseKey() {
        assertEquals("love", shortDefinition(antigone, "ἔρως", "ἔρως"))
        assertEquals("man, person, human", shortDefinition(gorgias, "ἄνθρωπος", "ἄνθρωπος"))
    }

    @Test
    fun theHomographDigitIsTakenOff() {
        assertEquals("Ζεύς", LemmaSpelling.shortDefinitionKey("Ζεύς1", "ζεύς", bySpelling = true))
        assertEquals("ζεύς", LemmaSpelling.shortDefinitionKey("ζεύς1", "ζεύς", bySpelling = true))
    }

    @Test
    fun aPackWithoutTheFlagKeepsTheLowerCaseKey() {
        // packs already on phones: one row under the lower-case key for both spellings
        assertEquals("πῶλος", LemmaSpelling.shortDefinitionKey("Πῶλος", "πῶλος", bySpelling = false))
    }

    @Test
    fun capitalsWithBreathingAndIotaAdscriptCount() {
        assertTrue(LemmaSpelling.isCapitalised("Ἔρως"))
        assertTrue(LemmaSpelling.isCapitalised("Ἰωνία"))
        assertTrue(LemmaSpelling.isCapitalised("ᾍδης"))
        assertTrue(LemmaSpelling.isCapitalised("ᾼ"))  // a titlecase letter
        assertFalse(LemmaSpelling.isCapitalised("ἰωνιά"))
        assertFalse(LemmaSpelling.isCapitalised("*ʼρᾶρος"))  // the first letter decides, not a mark before it
        assertFalse(LemmaSpelling.isCapitalised(""))
    }

    private data class Found(val lexicon: String, val headword: String)

    @Test
    fun aNameFindsByTheLooseKeyOnlyHeadwordsWithACapital() {
        // Ἰωνίας: the loose key finds only LSJ's ἰωνιά "violet-bed": no dictionary entry
        assertEquals(emptyList(), LemmaSpelling.looseMatches("Ἰωνία", listOf(Found("lsj", "ἰωνιά"))) { it.headword })
        assertEquals(emptyList(), LemmaSpelling.looseMatches("Ἄνδρων", listOf(Found("lsj", "ἀνδρών"), Found("ml", "ἀνδρών"))) { it.headword })
        assertEquals(emptyList(), LemmaSpelling.looseMatches("Σαώ", listOf(Found("lsj", "σάω"))) { it.headword })
        // a capitalised headword spelt otherwise is kept, the common word beside it left out
        val zeus = listOf(Found("autenrieth", "Ζεῦς"), Found("lsj", "ζεῦς"))
        assertEquals(listOf(Found("autenrieth", "Ζεῦς")), LemmaSpelling.looseMatches("Ζεύς", zeus) { it.headword })
    }

    @Test
    fun aLemmaWrittenSmallKeepsTheWholeLooseFallback() {
        val found = listOf(Found("lsj", "μιμνήσκω"), Found("ml", "μιμνήσκω"), Found("lsj", "Μιμνήσκω"))
        assertEquals(found, LemmaSpelling.looseMatches("μιμνῄσκω", found) { it.headword })
    }
}
