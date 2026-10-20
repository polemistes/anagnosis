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
    fun voices() {
        assertEquals("grc", voiceOf(Pronunciation.ATTIC))
        assertEquals("grc", voiceOf(Pronunciation.HOMERIC))
        assertEquals("grc-koine", voiceOf(Pronunciation.KOINE))
    }
}
