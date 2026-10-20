package no.anagnosis.data

import no.anagnosis.greek.Pronunciation
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class VowelLengthTest {
    private fun a(form: String, lemma: String, postag: String, marked: String?) = FormAnalysis(form, lemma, lemma, postag, "morpheus", marked)

    @Test
    fun theParseDecides() {
        val analyses = listOf(
            a("πολλά", "πολύς", "a-s---fn-", "πολλᾱ́"),
            a("πολλά", "πολύς", "a-p---nn-", null),
        )
        assertNull(VowelLength.choose("πολλά", "πολύς", "a-p---nn-", analyses))
        assertEquals("πολλᾱ́", VowelLength.choose("πολλά", "πολύς", "a-s---fn-", analyses))
        // a parse the analyser does not have: the lemma's analyses disagree, so nothing is known
        assertNull(VowelLength.choose("πολλά", "πολύς", "a-d---fn-", analyses))
    }

    @Test
    fun theLemmaDecidesWhenItsAnalysesAgree() {
        val analyses = listOf(
            a("ψυχή", "ψυχή", "n-s---fn-", "ψῡχή"),
            a("ψυχή", "ψυχή", "n-s---fv-", "ψῡχή"),
        )
        // the treebank's parse is not among Morpheus's, but every analysis of the lemma agrees
        assertEquals("ψῡχή", VowelLength.choose("ψυχή", "ψυχή", "n-s---f--", analyses))
        assertNull(VowelLength.choose("ψυχή", "ἄλλο", "n-s---fn-", analyses))
    }

    @Test
    fun theTokensOwnSpellingIsKept() {
        val analyses = listOf(a("τιμή", "τιμή", "n-s---fn-", "τῑμή"))
        // a capital and a grave in the text stay as they are
        assertEquals("Τι\u0304μη\u0300", VowelLength.choose("Τιμὴ", "τιμή", "n-s---fn-", analyses))
    }

    @Test
    fun defaults() {
        assertEquals(Pronunciation.HOMERIC, defaultPronunciation("odyssey", "Ὅμηρος", null))
        assertEquals(Pronunciation.KOINE, defaultPronunciation("newtestament", null, null))
        assertEquals(Pronunciation.ATTIC, defaultPronunciation("antigone", "Σοφοκλῆς", null))
        assertEquals(Pronunciation.KOINE, defaultPronunciation("antigone", "Σοφοκλῆς", "koine"))
    }
}
