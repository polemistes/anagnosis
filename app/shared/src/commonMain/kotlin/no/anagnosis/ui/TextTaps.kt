package no.anagnosis.ui

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.text.TextLayoutResult

/**
 * The offset of the character under a tap. getOffsetForPosition gives the nearest gap between
 * characters, which is the gap after a letter when its right half is tapped: on the last letter
 * of a word that gap lies outside the word, and the tap found no word. The letter whose box
 * holds the tap is taken instead.
 */
internal fun TextLayoutResult.charAt(pos: Offset): Int {
    val offset = getOffsetForPosition(pos)
    if (offset > 0 && getLineForOffset(offset - 1) == getLineForVerticalPosition(pos.y)) {
        val box = getBoundingBox(offset - 1)
        if (pos.x >= box.left && pos.x < box.right) return offset - 1
    }
    return offset
}

/**
 * Whether a tap at [x] falls on a row of text that is drawn from [left] to [right], with [slop]
 * allowed on either side. A tap in the blank space before a row (the indent of a staggered
 * part, the hanging indent of a wrapped verse's second row, a paragraph's first-line indent)
 * or after it is no tap on a word.
 */
internal fun withinRow(x: Float, left: Float, right: Float, slop: Float): Boolean =
    x >= left - slop && x <= right + slop

/**
 * The character under a tap on a word, or null when the tap is beside the row's text.
 * getOffsetForPosition clamps a tap left of a row to the row's first character, so without the
 * left bound a tap in an indent opened the first word of the row. The row's left edge is the
 * drawn position of its first character (getLineLeft gives the layout's edge, not the indent).
 */
internal fun TextLayoutResult.wordCharAt(pos: Offset, slop: Float): Int? {
    val line = getLineForVerticalPosition(pos.y)
    val left = getHorizontalPosition(getLineStart(line), usePrimaryDirection = true)
    if (!withinRow(pos.x, left, getLineRight(line), slop)) return null
    return charAt(pos)
}
