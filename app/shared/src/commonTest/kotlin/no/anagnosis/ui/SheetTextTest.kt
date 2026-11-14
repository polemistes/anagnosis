package no.anagnosis.ui

import androidx.compose.material3.Typography
import androidx.compose.ui.unit.sp
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertSame

class SheetTextTest {
    private val base = Typography()

    @Test
    fun theDefaultSizeLeavesTheTypographyAsItIs() {
        assertSame(base, scaledTypography(base, 1f))
    }

    @Test
    fun theReadingStylesGrowWithTheFactor() {
        val t = scaledTypography(base, 20f / 14f)
        // the body text, in which entries and notes are set, is the chosen size
        assertEquals(20f, t.bodyMedium.fontSize.value, 0.01f)
        assertEquals(base.bodyMedium.lineHeight.value * 20f / 14f, t.bodyMedium.lineHeight.value, 0.01f)
        assertEquals(base.bodyLarge.fontSize.value * 20f / 14f, t.bodyLarge.fontSize.value, 0.01f)
        assertEquals(base.titleMedium.fontSize.value * 20f / 14f, t.titleMedium.fontSize.value, 0.01f)
        assertEquals(base.headlineSmall.fontSize.value * 20f / 14f, t.headlineSmall.fontSize.value, 0.01f)
    }

    @Test
    fun theLabelsOfButtonsKeepTheirSize() {
        val t = scaledTypography(base, 2f)
        assertEquals(base.labelLarge, t.labelLarge)
        assertEquals(base.labelMedium, t.labelMedium)
        assertEquals(14.sp, base.bodyMedium.fontSize)  // the default the setting starts from
    }
}
