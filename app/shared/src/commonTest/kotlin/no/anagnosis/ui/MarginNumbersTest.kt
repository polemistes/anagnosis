package no.anagnosis.ui

import no.anagnosis.prefs.LineNumberMode
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class MarginNumbersTest {
    private fun line(n: Long, sub: String = "", fits: Boolean = true, wordless: Boolean = false) = MarginNumbers.Line(n, sub, fits, wordless)
    private fun labels(lines: List<MarginNumbers.Line>, mode: LineNumberMode) =
        MarginNumbers.choose(lines, mode).mapValues { (_, m) -> "${m.nInt}${m.nSub}" + if (m.forced) "!" else "" }

    @Test
    fun aLineOfSignsIsWordless() {
        assertTrue(MarginNumbers.isWordless("⏑–́⏑–⏑–́⏑–⏑–́⏑–", 0))  // the Electra after 1264
        assertTrue(MarginNumbers.isWordless("* * * * *", 0))  // the Theogony after 1022
        assertFalse(MarginNumbers.isWordless("πῶς;", 1))
        assertFalse(MarginNumbers.isWordless("πῶς;", 0))  // letters: not a line of signs, even without tokens
    }

    @Test
    fun allModeNumbersEveryLineButAWordlessOne() {
        // Electra 1263, 1264, 1264a (signs), 1265; a shared verse 831a keeps its number
        val lines = listOf(line(1263), line(1264), line(1264, "a", wordless = true), line(1265), line(831, "a"))
        assertEquals(mapOf(0 to "1263", 1 to "1264", 3 to "1265", 4 to "831a"), labels(lines, LineNumberMode.ALL))
    }

    @Test
    fun everyFifthModeLeavesAWordlessLineOut() {
        // Theogony 1020-1022 and the asterisks
        val lines = listOf(line(1020), line(1021), line(1022), line(1022, "a", wordless = true))
        assertEquals(mapOf(0 to "1020"), labels(lines, LineNumberMode.FIFTH))
    }

    @Test
    fun aMovedNumberDoesNotGoToAWordlessLine() {
        // 1265 has no room for its number; the line after it is a line of signs (as if after
        // 1265), so the number goes to the line before, not to the signs
        val lines = listOf(line(1264), line(1265, fits = false), line(1265, "a", wordless = true), line(1266))
        assertEquals(mapOf(0 to "1264"), labels(lines, LineNumberMode.FIFTH))
        // and with no line before that has room: forced beside 1265 itself
        val alone = listOf(line(1265, fits = false), line(1265, "a", wordless = true))
        assertEquals(mapOf(0 to "1265!"), labels(alone, LineNumberMode.FIFTH))
    }

    @Test
    fun aWordlessLineDoesNotEndACoveredNumber() {
        // 1262 runs over 1263-1264; the next verse that counts is 1266 (the signs are skipped),
        // so 1262 carries the covered 1265
        val lines = listOf(line(1262), line(1262, "a", wordless = true), line(1266))
        assertEquals(mapOf(0 to "1265"), labels(lines, LineNumberMode.FIFTH))
        // a wordless line with a fifth number of its own (no letter) still carries none
        assertEquals(emptyMap(), labels(listOf(line(1270, wordless = true)), LineNumberMode.FIFTH))
    }

    @Test
    fun theRulesBeforeStand() {
        // a long verse covering 475 (Jebb's 473): the covered number beside it
        assertEquals(mapOf(0 to "475"), labels(listOf(line(473), line(476)), LineNumberMode.FIFTH))
        // 385 without room: the number moves to 386, which shows its own
        assertEquals(mapOf(1 to "386"), labels(listOf(line(385, fits = false), line(386)), LineNumberMode.FIFTH))
        // a lettered line has no number of its own in the every-fifth mode
        assertEquals(emptyMap(), labels(listOf(line(395, "a")), LineNumberMode.FIFTH))
        assertEquals(emptyMap(), labels(listOf(line(5)), LineNumberMode.NONE))
    }
}
