package no.anagnosis.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.runtime.Composable
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.remember
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.unit.isSpecified
import no.anagnosis.prefs.ReaderSettings

/** The text size the reader chose for the sheets (Options), provided by [App] from the settings. */
val LocalSheetTextSize = compositionLocalOf { ReaderSettings.DEFAULT_SHEET_SIZE }

/**
 * The typography with the styles a sheet is read in, the body, title and headline styles, grown
 * or shrunk by [factor]. The label styles of buttons and small headings keep their size, so the
 * controls stay where the finger expects them.
 */
fun scaledTypography(t: Typography, factor: Float): Typography {
    if (factor == 1f) return t
    fun TextStyle.scaled() = copy(
        fontSize = if (fontSize.isSpecified) fontSize * factor else fontSize,
        lineHeight = if (lineHeight.isSpecified) lineHeight * factor else lineHeight,
    )
    return t.copy(
        headlineSmall = t.headlineSmall.scaled(),
        titleLarge = t.titleLarge.scaled(),
        titleMedium = t.titleMedium.scaled(),
        titleSmall = t.titleSmall.scaled(),
        bodyLarge = t.bodyLarge.scaled(),
        bodyMedium = t.bodyMedium.scaled(),
        bodySmall = t.bodySmall.scaled(),
    )
}

/**
 * The content of a sheet, with its text at the size chosen in Options: the body text (in which
 * dictionary entries and notes are set) is that size, and the other reading styles grow with it.
 */
@Composable
fun SheetText(content: @Composable () -> Unit) {
    val size = LocalSheetTextSize.current
    val base = MaterialTheme.typography
    val typography = remember(base, size) {
        val body = base.bodyMedium.fontSize.takeIf { it.isSpecified }?.value ?: ReaderSettings.DEFAULT_SHEET_SIZE.toFloat()
        scaledTypography(base, size / body)
    }
    MaterialTheme(colorScheme = MaterialTheme.colorScheme, shapes = MaterialTheme.shapes, typography = typography, content = content)
}
