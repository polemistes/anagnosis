package no.anagnosis.speech

import no.anagnosis.greek.Pronunciation
import no.anagnosis.greek.SpeechWord
import no.anagnosis.greek.Utterances
import kotlin.test.Test
import kotlin.test.assertEquals

class SpeechTest {
    @Test
    fun wordEventsGiveTheWordStarts() {
        val line = "ἄνδρα μοι ἔννεπε, Μοῦσα,"
        val words = listOf(
            SpeechWord(1, 1, "ἄνδρα", 0, 5), SpeechWord(2, 1, "μοι", 6, 9),
            SpeechWord(3, 1, "ἔννεπε", 10, 16), SpeechWord(4, 1, "Μοῦσα", 18, 23),
        )
        val u = Utterances.build(words, { line }, Pronunciation.ATTIC, verse = true)
        assertEquals("[[a1ndra0]] [[moI0]] [[e1nne0pe0 _:]] [[mu:3sa0 _:]]", u.text)
        // as eSpeak reported them for this text (1-based positions less one): the pauses are words too
        val events = listOf(2 to 0, 14 to 5527, 23 to 9495, 33 to 17868, 40 to 19080, 48 to 25822)
        val starts = wordStarts(u, events)
        assertEquals(listOf(0, 5527, 9495, 19080), starts.toList())
        val speech = Speech(ShortArray(0), 22050, starts)
        assertEquals(0, speech.wordAt(100))
        assertEquals(1, speech.wordAt(5527))
        assertEquals(2, speech.wordAt(18000))
        assertEquals(3, speech.wordAt(30000))
    }

    @Test
    fun aWordWithoutAnEventStartsWithTheOneBefore() {
        val line = "ἀλλʼ οὐδʼ ὣς"
        val words = listOf(SpeechWord(1, 1, "ἀλλʼ", 0, 4), SpeechWord(2, 1, "οὐδʼ", 5, 9), SpeechWord(3, 1, "ὣς", 10, 12))
        val u = Utterances.build(words, { line }, Pronunciation.ATTIC, verse = false)
        val starts = wordStarts(u, listOf(2 to 0, u.offsets[2] + 2 to 9000))
        assertEquals(listOf(0, 0, 9000), starts.toList())
    }

    @Test
    fun aKoineWordBeginningWithAStressMarkIsFoundWhereESpeakReportsIt() {
        // ἐν ἀρχῇ ἦν ὁ λόγος: Koine words may begin with ' or %; eSpeak reports them past the mark
        val line = "ἐν ἀρχῇ ἦν ὁ λόγος"
        val words = listOf(SpeechWord(1, 1, "ἐν", 0, 2), SpeechWord(2, 1, "ἀρχῇ", 3, 7), SpeechWord(3, 1, "ἦν", 8, 10),
            SpeechWord(4, 1, "ὁ", 11, 12), SpeechWord(5, 1, "λόγος", 13, 18))
        val u = Utterances.build(words, { line }, Pronunciation.KOINE, verse = false)
        val events = u.words.mapIndexed { i, w ->
            val past = if (w.phonemes.first() == '\'' || w.phonemes.first() == '%') 3 else 2
            (u.offsets[i] + past) to (i + 1) * 1000
        }
        assertEquals(true, u.words.any { it.phonemes.first() == '\'' || it.phonemes.first() == '%' })
        assertEquals(listOf(1000, 2000, 3000, 4000, 5000), wordStarts(u, events).toList())
    }

    @Test
    fun voices() {
        assertEquals("grc", voiceOf(Pronunciation.ATTIC))
        assertEquals("grc", voiceOf(Pronunciation.HOMERIC))
        assertEquals("grc-koine", voiceOf(Pronunciation.KOINE))
        assertEquals("grc-f", voiceOf(Pronunciation.ATTIC, female = true))
        assertEquals("grc-koine-f", voiceOf(Pronunciation.KOINE, female = true))
        assertEquals("grc-klatt", voiceOf(Pronunciation.HOMERIC, klatt = true))
        assertEquals("grc-f-klatt", voiceOf(Pronunciation.ATTIC, female = true, klatt = true))
        assertEquals("grc-koine-f-klatt", voiceOf(Pronunciation.KOINE, female = true, klatt = true))
    }

    @Test
    fun slowSpeedsAreStretchedInPlayback() {
        assertEquals(100 to 1f, engineRate(100))
        assertEquals(200 to 1f, engineRate(200))
        assertEquals(80 to 1f, engineRate(80))
        assertEquals(80 to 0.625f, engineRate(50))
    }
}
