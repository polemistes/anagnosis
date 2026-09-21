package no.anagnosis.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import no.anagnosis.data.WorkData

/** The first screen: what this app is, and the way into the text and the edition's documents. */
@Composable
fun HomeScreen(
    repository: AnagnosisRepository,
    data: WorkData,
    appVersion: String,
    onRead: () -> Unit,
    onOpenDocument: (String) -> Unit,
) {
    var showHelp by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    val documents = remember { repository.documents(data) }
    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 28.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(24.dp))
        Text("Antigone", style = MaterialTheme.typography.displaySmall, textAlign = TextAlign.Center)
        Text("by Sophocles", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
        Spacer(Modifier.height(28.dp))
        Text(
            "The Greek text of Sir Richard Jebb's edition, with his translation, critical notes and commentary, " +
                "and the Liddell–Scott dictionaries. Tap any word for its meaning and form.",
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(12.dp))
        Text(
            "Provided by Anagnosis, an ancient Greek text reader for Android.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(36.dp))
        Button(onClick = onRead, modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp)) {
            Text("Read the text", modifier = Modifier.padding(vertical = 6.dp))
        }
        Spacer(Modifier.height(20.dp))
        Column(Modifier.fillMaxWidth().padding(horizontal = 24.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            for ((slug, title) in documents) {
                OutlinedButton(onClick = { onOpenDocument(slug) }, modifier = Modifier.fillMaxWidth()) { Text(title) }
            }
        }
        Spacer(Modifier.height(28.dp))
        androidx.compose.foundation.layout.Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = { showHelp = true }) { Text("How to use") }
            TextButton(onClick = { showAbout = true }) { Text("About and credits") }
        }
    }
    if (showHelp) IntroDialog(onDismiss = { showHelp = false })
    if (showAbout) {
        val credits = remember { repository.credits() }
        AboutDialog(appVersion, credits, onDismiss = { showAbout = false })
    }
}
