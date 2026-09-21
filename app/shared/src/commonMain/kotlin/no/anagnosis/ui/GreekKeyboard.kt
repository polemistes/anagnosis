package no.anagnosis.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import no.anagnosis.greek.Polytonic

/**
 * An on-screen polytonic keyboard. Letters follow the Greek keyboard layout; the top row holds
 * the marks, which apply to the last vowel typed, as dead keys do on the standard layout:
 * breathings and accents replace one another, subscript and diaeresis toggle.
 */
@Composable
fun GreekKeyboard(onKey: (String) -> Unit, onBackspace: () -> Unit, onDone: () -> Unit) {
    // the mark keys show their effect on an alpha (or iota), as a hint
    val marks = listOf(
        "ἀ" to Polytonic.SMOOTH, "ἁ" to Polytonic.ROUGH, "ά" to Polytonic.ACUTE, "ὰ" to Polytonic.GRAVE,
        "ᾶ" to Polytonic.CIRCUMFLEX, "ᾳ" to Polytonic.SUBSCRIPT, "ϊ" to Polytonic.DIAERESIS,
    )
    val rows = listOf("ςερτυθιοπ", "ασδφγηξκλ", "ζχψωβνμ")
    Column(Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surfaceVariant).padding(horizontal = 4.dp, vertical = 6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            for ((label, mark) in marks) {
                Key(label, Modifier.weight(1f), accent = true) { onKey(mark.toString()) }
            }
        }
        for (row in rows) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                if (row.length < 9) Box(Modifier.weight(1f))
                for (ch in row) Key(ch.toString(), Modifier.weight(1f)) { onKey(ch.toString()) }
                if (row.length < 9) Key("⌫", Modifier.weight(1f), accent = true, onClick = onBackspace)
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
            Key("ʼ", Modifier.weight(1f), accent = true) { onKey("ʼ") }
            Key("space", Modifier.weight(3f)) { onKey(" ") }
            Key("Done", Modifier.weight(1.5f), accent = true, onClick = onDone)
        }
    }
}

@Composable
private fun Key(label: String, modifier: Modifier, accent: Boolean = false, onClick: () -> Unit) {
    Box(
        modifier
            .height(42.dp)
            .clip(RoundedCornerShape(6.dp))
            .background(if (accent) MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.surface)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, fontSize = if (label.length > 1) 13.sp else 20.sp, color = MaterialTheme.colorScheme.onSurface)
    }
}
