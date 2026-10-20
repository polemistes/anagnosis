package no.anagnosis.greek

import kotlin.test.Test
import kotlin.test.assertEquals

class UtteranceTest {
    /** The words of [text] (one line, id 1) as speech words, token ids from 1. */
    private fun words(text: String, lineId: Long = 1, firstId: Long = 1): List<SpeechWord> {
        val out = ArrayList<SpeechWord>()
        val re = Regex("[^\\s,.·;:!?—]+")
        for ((i, m) in re.findAll(text).withIndex()) {
            out += SpeechWord(firstId + i, lineId, m.value, m.range.first, m.range.last + 1)
        }
        return out
    }

    @Test
    fun pausesFromPunctuation() {
        val line = "ἄνδρα μοι ἔννεπε, Μοῦσα, πολύτροπον, ὃς μάλα πολλὰ"
        val u = Utterances.build(words(line), { line }, Pronunciation.ATTIC, verse = true)
        assertEquals(listOf(Pause.NONE, Pause.NONE, Pause.SHORT, Pause.SHORT, Pause.SHORT, Pause.NONE, Pause.NONE, Pause.SHORT), u.words.map { it.pause })
        assertEquals("[[a1ndra0]] [[moI0]] [[e1nne0pe0 _:]]", u.text.substring(0, u.offsets[3]).trimEnd())
    }

    @Test
    fun longPauseAndElision() {
        val line = "ἀλλʼ οὐδʼ ὣς ἑτάρους ἐρρύσατο, ἱέμενός περ·"
        val u = Utterances.build(words(line), { line }, Pronunciation.HOMERIC, verse = true)
        assertEquals(Pause.JOIN, u.words[0].pause)
        assertEquals(Pause.JOIN, u.words[1].pause)
        assertEquals(Pause.LONG, u.words.last().pause)
        // joined words run together without a space
        assertEquals("[[a0ll]][[o:0d]][[hO:0s]]", u.text.substring(0, u.offsets[3]).trimEnd())
    }

    @Test
    fun lineEndsAndOffsets() {
        val l1 = "ἄνδρα μοι"
        val l2 = "Μοῦσα"
        val ws = words(l1, 1, 1) + words(l2, 2, 3)
        val verse = Utterances.build(ws, { if (it == 1L) l1 else l2 }, Pronunciation.ATTIC, verse = true)
        assertEquals(Pause.SHORT, verse.words[1].pause)
        val prose = Utterances.build(ws, { if (it == 1L) l1 else l2 }, Pronunciation.ATTIC, verse = false)
        assertEquals(Pause.NONE, prose.words[1].pause)
        for ((i, o) in prose.offsets.withIndex()) {
            assertEquals("[[", prose.text.substring(o, o + 2))
            assertEquals(i, prose.wordAt(o))
            assertEquals(i, prose.wordAt(o + 3))
        }
        assertEquals(3L, prose.words[2].tokenId)
    }

    @Test
    fun tokensWithoutGreekAreSkipped() {
        val line = "ἄνδρα 12 μοι"
        val u = Utterances.build(words(line), { line }, Pronunciation.KOINE, verse = false)
        assertEquals(listOf(1L, 3L), u.words.map { it.tokenId })
    }
}
