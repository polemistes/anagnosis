package no.anagnosis.data

import no.anagnosis.ui.plainText
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class LemmaIndexTest {
    private val odyssey = listOf(
        LemmaEntry("odyssey", "ἥλιος", "ἥλιος", 20),
        LemmaEntry("odyssey", "ἠέλιος", "ἠέλιος", 40),
        LemmaEntry("odyssey", "ἀποκρίνω", "ἀποκρίνω", 2),
        LemmaEntry("odyssey", "βίος", "βίος", 3),
        LemmaEntry("odyssey", "μοῦσα", "Μοῦσα", 5),
        LemmaEntry("odyssey", "λόγος", "λόγος", 4),
    )
    private val nt = listOf(
        LemmaEntry("nt", "ἀποκρίνομαι", "ἀποκρίνομαι", 230),
        LemmaEntry("nt", "βιός", "βιός", 1),
        LemmaEntry("nt", "λόγος", "λόγος", 330),
        LemmaEntry("nt", "λογίζομαι", "λογίζομαι", 40),
        LemmaEntry("nt", "λογικός", "λογικός", 2),
    )
    private val rows = LemmaIndex.merge(odyssey + nt, mapOf("odyssey" to mapOf("ἠέλιος" to "ἥλιος")))

    private fun row(key: String) = rows.single { it.contains(key) }

    @Test
    fun aliasesAndMiddlesAreJoined() {
        val sun = row("ἠέλιος")
        assertEquals(listOf("ἠέλιος", "ἥλιος"), sun.spellings)
        assertEquals(60, sun.total)
        val answer = row("ἀποκρίνω")
        assertEquals(listOf("ἀποκρίνομαι", "ἀποκρίνω"), answer.spellings)
        assertEquals(mapOf("odyssey" to 2, "nt" to 230), answer.countsBySlug)
        assertEquals(listOf("ἀποκρίνομαι"), answer.keysBySlug["nt"])
    }

    @Test
    fun accentsAloneDoNotJoin() {
        assertTrue(row("βίος") !== row("βιός"))
    }

    @Test
    fun countsAcrossTexts() {
        val word = row("λόγος")
        assertEquals(334, word.total)
        assertEquals(mapOf("odyssey" to 4, "nt" to 330), word.countsBySlug)
        assertEquals(listOf("Μοῦσα"), row("μοῦσα").spellings)
    }

    @Test
    fun suggestions() {
        assertEquals(listOf("λογίζομαι", "λογικός", "λόγος"), LemmaIndex.suggest(rows, "λογ").map { it.spellings.first() })
        // the word itself first, the longer words after it
        assertEquals("λόγος", LemmaIndex.suggest(rows, "λογος").first().spellings.first())
        assertEquals("λόγος", LemmaIndex.suggest(rows, "λογοσ").first().spellings.first())
        assertEquals(listOf("Μοῦσα"), LemmaIndex.suggest(rows, "μουσ").map { it.spellings.first() })
        assertTrue(LemmaIndex.suggest(rows, "").isEmpty())
    }

    @Test
    fun plainTextOfANote() {
        assertEquals(
            "κοινὸν] κλεινὸν Wecklein & Nauck. μοῦνον M. Schmidt.",
            plainText("<p><b>κοινὸν</b>] κλεινὸν Wecklein &amp; Nauck.</p><p>μοῦνον M. Schmidt.</p>"),
        )
    }
}
