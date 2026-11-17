package no.anagnosis.ui

/**
 * The page's text area in whole pixels, as the layout gives it. The layout rounds each padding
 * to whole pixels on its own (20 dp at density 2.625 is 52.5, so 53 px a side), so the area is
 * the box less those rounded paddings; the box's size in dp less the paddings, rounded once,
 * can come out a pixel larger than what is drawn, and a page then holds a line that does not
 * fit (a verse that just fits at 975 px wraps at the 974 px drawn: Theogony 486–502 in portrait).
 */
internal object PageArea {
    /**
     * The width a column of text is measured and drawn at: the readable width [columnPx] (the
     * column's chosen width, rounded), no wider than the box leaves to each of [columns] columns
     * after the side paddings and the gaps between the columns.
     */
    fun columnWidth(boxWidthPx: Int, paddingPx: Int, columnPx: Int, columns: Int = 1, gapPx: Int = 0): Int =
        minOf(columnPx, (boxWidthPx - 2 * paddingPx - (columns - 1) * gapPx) / columns)

    /** The height a page is cut to: the box less its top and bottom paddings, each rounded. */
    fun height(boxHeightPx: Int, paddingPx: Int): Int = boxHeightPx - 2 * paddingPx
}
