package no.anagnosis.speech

import no.anagnosis.db.Lines
import no.anagnosis.db.Tokens
import kotlin.test.Test
import kotlin.test.assertEquals

class SpeakersTest {
    private var nextToken = 1L

    /** A line with its words as tokens (every run of letters a word, labels in braces skipped). */
    private fun line(id: Long, text: String, speaker: String? = null, start: Boolean = false): Pair<Lines, List<Tokens>> {
        val tokens = Regex("\\{[^}]*\\}|[\\p{L}ʼ]+").findAll(text).filter { !it.value.startsWith("{") }.mapIndexed { i, m ->
            Tokens(nextToken++, id, i.toLong(), m.range.first.toLong(), m.range.last + 1L, m.value, m.value, m.value, "", null, null, "s", null)
        }.toList()
        return Lines(id, 1, id, "$id", id, "", null, speaker, if (start) 1 else 0, text) to tokens
    }

    @Test
    fun aPlayNamesTheSpeakerOfEachSpeech() {
        val rows = listOf(
            line(1, "ὦ κοινὸν αὐτάδελφον", "Ἀντιγόνη", start = true),
            line(2, "Ἰσμήνης κάρα", "Ἀντιγόνη"),
            line(3, "ἐμοὶ μὲν οὐδεὶς", "Ἡμιχόριον 1", start = true),
        )
        val cues = Speakers.cues(rows.map { it.first }, rows.associate { it.first.id to it.second })
        assertEquals(mapOf(rows[0].second[0].id to "Ἀντιγόνη", rows[2].second[0].id to "Ἡμιχόριον πρῶτον"), cues)
    }

    @Test
    fun aDialogueNamesTheSpeakerOfEachLabelInFull() {
        val rows = listOf(
            line(1, "{ΚΑΛ.} Πολέμου καὶ μάχης", start = true),
            line(2, "ἦ γάρ;—{ΓΟΡ.} Ναί.—{ΣΩ.}"),
            line(3, "Οὐκοῦν καὶ"),
        )
        val cues = Speakers.cues(rows.map { it.first }, rows.associate { it.first.id to it.second })
        assertEquals(
            mapOf(
                rows[0].second[0].id to "Καλλικλῆς",
                rows[1].second[2].id to "Γοργίας",
                rows[2].second[0].id to "Σωκράτης",
            ),
            cues,
        )
    }

    @Test
    fun anUnknownAbbreviationIsSaidAsPrinted() {
        assertEquals("ΑΓΑ", Speakers.fullSpeakerName("ΑΓΑ."))
    }
}
