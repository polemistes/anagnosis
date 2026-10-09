package no.anagnosis.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import no.anagnosis.data.CatalogEntry

/**
 * The texts on sale, each an app of its own on Google Play: what each comes with, its price and
 * the way to its page there. Only texts marked as on Google Play in the catalog are listed.
 */
@Composable
fun AvailableTextsScreen(catalog: List<CatalogEntry>, onOpen: (String) -> Unit, onBack: () -> Unit) {
    val uriHandler = LocalUriHandler.current
    val offered = catalog.filter { it.onGooglePlay && it.appId.isNotEmpty() }.sortedBy { it.titleEn.ifEmpty { it.title } }
    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 24.dp, vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
    Column(Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth()) {
        TextButton(onClick = onBack) { Text("‹ Back") }
        Spacer(Modifier.height(8.dp))
        Text("Available texts", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Each text is an app of its own on Google Play. Once it is installed, the text appears on the front page of Anagnosis.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(16.dp))
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            for (entry in offered) {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text(titleByAuthor(entry), style = MaterialTheme.typography.titleLarge)
                        Spacer(Modifier.height(8.dp))
                        Detail("Editor", entry.editor)
                        Detail("Critical apparatus", entry.apparatus)
                        Detail("Translation", entry.translation)
                        Detail("Commentary", entry.commentary)
                        Detail("Syntax", entry.syntax)
                        Detail("Extra dictionaries", entry.dictionaries)
                        Spacer(Modifier.height(8.dp))
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                            if (entry.installed) {
                                Text("Installed", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                                Spacer(Modifier.weight(1f))
                                OutlinedButton(onClick = { onOpen(entry.slug) }) { Text("Open") }
                            } else {
                                Text(entry.price, style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.weight(1f))
                                Button(onClick = { uriHandler.openUri(entry.storeUrl) }) { Text("Google Play") }
                            }
                        }
                    }
                }
            }
        }
        Spacer(Modifier.height(24.dp))
    }
    }
}

/** One thing a text comes with, as "Label: what"; nothing when it does not have it. */
@Composable
private fun Detail(label: String, value: String) {
    if (value.isEmpty()) return
    Text(
        buildAnnotatedString {
            withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) { append("$label: ") }
            append(value)
        },
        style = MaterialTheme.typography.bodyMedium,
        modifier = Modifier.padding(vertical = 2.dp),
    )
}
