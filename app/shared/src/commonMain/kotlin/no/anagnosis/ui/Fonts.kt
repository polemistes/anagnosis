package no.anagnosis.ui

import androidx.compose.runtime.Composable
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import no.anagnosis.prefs.FontChoice
import no.anagnosis.resources.Res
import no.anagnosis.resources.cardo_bold
import no.anagnosis.resources.cardo_italic
import no.anagnosis.resources.cardo_regular
import no.anagnosis.resources.gentiumplus_bold
import no.anagnosis.resources.gentiumplus_italic
import no.anagnosis.resources.gentiumplus_regular
import no.anagnosis.resources.gfsdidot_regular
import no.anagnosis.resources.gfsneohellenic_bold
import no.anagnosis.resources.gfsneohellenic_regular
import org.jetbrains.compose.resources.Font

/** The bundled fonts (all under the SIL Open Font License) as Compose font families. */
@Composable
fun FontChoice.family(): FontFamily = when (this) {
    FontChoice.SYSTEM -> FontFamily.Default
    FontChoice.GENTIUM -> FontFamily(
        Font(Res.font.gentiumplus_regular),
        Font(Res.font.gentiumplus_bold, FontWeight.Bold),
        Font(Res.font.gentiumplus_italic, style = FontStyle.Italic),
    )
    FontChoice.CARDO -> FontFamily(
        Font(Res.font.cardo_regular),
        Font(Res.font.cardo_bold, FontWeight.Bold),
        Font(Res.font.cardo_italic, style = FontStyle.Italic),
    )
    FontChoice.DIDOT -> FontFamily(Font(Res.font.gfsdidot_regular))
    FontChoice.NEOHELLENIC -> FontFamily(
        Font(Res.font.gfsneohellenic_regular),
        Font(Res.font.gfsneohellenic_bold, FontWeight.Bold),
    )
}
