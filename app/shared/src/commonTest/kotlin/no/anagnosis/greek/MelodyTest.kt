package no.anagnosis.greek

import kotlin.test.Test
import kotlin.test.assertEquals

class MelodyTest {
    @Test
    fun aSentenceStepsDownThroughFourLevelsAndFallsAtItsEnd() {
        val out = Melody.apply(listOf("a1", "a0", "a0", "a0"), listOf(Pause.NONE, Pause.NONE, Pause.NONE, Pause.LONG), listOf(false, false, false, false))
        assertEquals(listOf("a11", "a20", "a0", "a40"), out)
    }

    @Test
    fun aQuestionRisesAtItsEnd() {
        val out = Melody.apply(listOf("a1", "a0"), listOf(Pause.NONE, Pause.LONG), listOf(false, true))
        assertEquals(listOf("a11", "a41"), out)
    }

    @Test
    fun anAccentedLastSyllableKeepsItsAccentAtTheLowestLevel() {
        val out = Melody.apply(listOf("a0", "a0", "a0", "a3"), listOf(Pause.NONE, Pause.NONE, Pause.NONE, Pause.LONG), listOf(false, false, false, false))
        assertEquals(listOf("a10", "a20", "a0", "a33"), out)
    }

    @Test
    fun afterACommaTheNextStretchBeginsALevelLower() {
        val out = Melody.apply(listOf("a1", "a0", "a0", "a0"), listOf(Pause.NONE, Pause.SHORT, Pause.NONE, Pause.LONG), listOf(false, false, false, false))
        assertEquals(listOf("a11", "a0", "a20", "a40"), out)
    }

    @Test
    fun wordsWithSeveralSyllablesCountEachSyllable() {
        val out = Melody.apply(listOf("a1ndra0", "moI0", "e1nne0pe0 _:"), listOf(Pause.NONE, Pause.NONE, Pause.SHORT), listOf(false, false, false))
        // six syllables: levels 0 0 1 2 2 3 (the pause mark is not a tone)
        assertEquals(listOf("a11ndra10", "moI20", "e1nne0pe30 _:"), out)
    }

    @Test
    fun theUtteranceBuilderAppliesItForAtticOnly() {
        val line = "ἆρα σὺ ζῇς;"
        val words = listOf(SpeechWord(1, 1, "ἆρα", 0, 3), SpeechWord(2, 1, "σὺ", 4, 6), SpeechWord(3, 1, "ζῇς", 7, 10))
        val attic = Utterances.build(words, { line }, Pronunciation.ATTIC, verse = false, melody = true)
        assertEquals(listOf(Pause.NONE, Pause.NONE, Pause.LONG), attic.words.map { it.pause })
        // four syllables, one at each level: the first at the top, the last accented and so at the lowest level, not the rise
        assert(attic.words[0].phonemes.startsWith("a:13")) { attic.words[0].phonemes }
        assert(attic.words[2].phonemes.contains("33")) { attic.words[2].phonemes }
        val koine = Utterances.build(words, { line }, Pronunciation.KOINE, verse = false, melody = true)
        assertEquals(Utterances.build(words, { line }, Pronunciation.KOINE, verse = false).text, koine.text)
    }
}
