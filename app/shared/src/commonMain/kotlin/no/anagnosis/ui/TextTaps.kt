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
