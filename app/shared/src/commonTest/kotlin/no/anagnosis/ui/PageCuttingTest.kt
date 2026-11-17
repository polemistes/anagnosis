package no.anagnosis.ui

import kotlin.test.Test
import kotlin.test.assertEquals

class PageCuttingTest {
    private fun cut(rows: List<Pair<Int, Boolean>>, page: Int, en: List<Int>? = null, enPage: Int = Int.MAX_VALUE) =
        PageCutting.forward(
            IntArray(rows.size) { rows[it].first }, IntArray(rows.size) { en?.get(it) ?: 0 }, BooleanArray(rows.size) { rows[it].second },
            0, rows.size, page, enPage,
        )

    private val verse = 67 to false
    private val strophe = 79 to true
    private val speaker = 61 to true

    @Test
    fun aHeadingFollowedByASpeakerGoesWithTheFirstVerse() {
        // Ajax 220–221: three verses, then "Strophe 1", the speaker Χορός and verse 221; the page
        // has room for the heading and the speaker but not for the verse as well
        val rows = listOf(verse, verse, verse, strophe, speaker, verse, verse)
        val page = 3 * 67 + 79 + 61 + 30
        assertEquals(listOf(0..2, 3..6), cut(rows, page))
    }

    @Test
    fun aHeadingWithItsVerseStaysWhereBothFit() {
        val rows = listOf(verse, verse, strophe, speaker, verse, verse)
        assertEquals(listOf(0..4, 5..5), cut(rows, 2 * 67 + 79 + 61 + 67))
    }

    @Test
    fun aHeadingFollowedByAVerseIsKeptWithIt() {
        // the rule before: a heading and the row after it
        val rows = listOf(verse, verse, verse, strophe, verse)
        assertEquals(listOf(0..2, 3..4), cut(rows, 3 * 67 + 79 + 30))
    }

    @Test
    fun rowsFillThePageAndALongerRowStillGetsAPage() {
        assertEquals(listOf(0..1, 2..3), cut(listOf(verse, verse, verse, verse), 2 * 67))
        assertEquals(listOf(0..0, 1..1), cut(listOf(500 to false, verse), 100))
    }

    @Test
    fun theTranslationBesideTheGreekCutsTooAndKeepsTheHeadingWithItsVerse() {
        val rows = listOf(verse, strophe, speaker, verse)
        assertEquals(listOf(0..0, 1..3), cut(rows, 1000, en = listOf(100, 0, 0, 100), enPage = 150))
    }
}
