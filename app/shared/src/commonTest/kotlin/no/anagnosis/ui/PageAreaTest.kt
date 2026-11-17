package no.anagnosis.ui

import kotlin.math.roundToInt
import kotlin.test.Test
import kotlin.test.assertEquals

class PageAreaTest {
    // The phone measured on the emulator (1080 px wide, density 2.625): the page box is 1080 x 1841;
    // 20 dp a side is 52.5 px, drawn as 53, and 12 dp top and bottom is 31.5, drawn as 32. The
    // column was drawn from x 53 to 1027 (974 px) and from y 328 to 2105 (1777 px), while the
    // pages were cut for 975 x 1778 (the dp sizes less the paddings, rounded once), so a page of
    // the Theogony (486-502) held a verse that wraps at 974 px but not at 975, and was too long.
    private val density = 2.625f
    // as Compose's roundToPx: half up (52.5 -> 53)
    private fun px(dp: Float) = (dp * density).roundToInt()

    @Test
    fun portraitColumnIsTheBoxLessTheRoundedPaddings() {
        val chosen = px(1080 / density - 40)  // the readable width in dp, rounded as a whole: 975
        assertEquals(975, chosen)
        assertEquals(974, PageArea.columnWidth(boxWidthPx = 1080, paddingPx = px(20f), columnPx = chosen))
    }

    @Test
    fun pageHeightIsTheBoxLessTheRoundedPaddings() {
        assertEquals(1777, PageArea.height(boxHeightPx = 1841, paddingPx = px(12f)))
    }

    @Test
    fun aNarrowerReadableColumnIsKept() {
        // a line length shorter than the screen: the chosen width stands
        assertEquals(700, PageArea.columnWidth(boxWidthPx = 1080, paddingPx = 53, columnPx = 700))
    }

    @Test
    fun sideBySideColumnsFitWithTheGap() {
        // landscape, two columns and a 40 dp gap (105 px): each column no wider than half what is left
        val each = PageArea.columnWidth(boxWidthPx = 2400, paddingPx = 53, columnPx = 1095, columns = 2, gapPx = px(40f))
        assertEquals(1094, each)
        assertEquals(true, 2 * each + px(40f) <= 2400 - 2 * 53)
    }
}
