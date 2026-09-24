package no.anagnosis.ui

import androidx.compose.foundation.clickable
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
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.CatalogEntry

/** The widest a page of the library, a text's page or the search is laid out; wider screens centre it. */
val CONTENT_MAX_WIDTH = 640.dp

/** The library: every text the app knows about, installed ones first. */
@Composable
fun LibraryScreen(
    catalog: List<CatalogEntry>,
    appVersion: String,
    repository: AnagnosisRepository,
    onOpen: (String) -> Unit,
    onSearch: () -> Unit,
) {
    var showHelp by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 24.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
    // on a tablet the page keeps a readable width in the middle of the screen
    Column(Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
        Spacer(Modifier.height(16.dp))
        Text("Anagnosis", style = MaterialTheme.typography.displaySmall, textAlign = TextAlign.Center)
        Text(
            "An ancient Greek text reader",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(20.dp))
        Text(
            "Anagnosis is for reading ancient Greek texts in the original. Tap any word to see its dictionary " +
                "form, its inflection and its meaning, with the full Liddell–Scott entries a tap further. Each text " +
                "comes with an English translation, a critical apparatus and a commentary, and everything works offline.",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(24.dp))
        androidx.compose.material3.OutlinedButton(onClick = onSearch, modifier = Modifier.fillMaxWidth()) { Text("Dictionary and Word Analysis") }
        Spacer(Modifier.height(24.dp))
        Text("Texts", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            for (entry in catalog.sortedByDescending { it.installed }) {
                Card(
                    modifier = Modifier.fillMaxWidth().clickable(enabled = entry.installed) { onOpen(entry.slug) },
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text(entry.titleEn.ifEmpty { entry.title }, style = MaterialTheme.typography.titleLarge)
                        Text(entry.authorEn.ifEmpty { entry.author }, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        if (entry.description.isNotEmpty()) {
                            Spacer(Modifier.height(8.dp))
                            Text(entry.description, style = MaterialTheme.typography.bodyMedium)
                        }
                        Spacer(Modifier.height(8.dp))
                        Text(
                            if (entry.installed) "Installed" else "Not yet available",
                            style = MaterialTheme.typography.labelMedium,
                            color = if (entry.installed) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline,
                        )
                    }
                }
            }
        }
        Spacer(Modifier.height(20.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = { showHelp = true }) { Text("How to use") }
            TextButton(onClick = { showAbout = true }) { Text("About and credits") }
        }
    }
    }
    if (showHelp) IntroDialog(onDismiss = { showHelp = false })
    if (showAbout) {
        val credits = remember { repository.credits() }
        AboutDialog(appVersion, credits, onDismiss = { showAbout = false })
    }
}
