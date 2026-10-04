package no.anagnosis.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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
import no.anagnosis.data.CatalogEntry

/** A text's own page: title, description, the way into the text and the edition's documents. */
@Composable
fun TextHomeScreen(
    repository: AnagnosisRepository,
    entry: CatalogEntry,
    appVersion: String,
    onRead: () -> Unit,
    onBack: () -> Unit,
    onSearch: () -> Unit,
) {
    var showHelp by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    var openDocument by remember { mutableStateOf<String?>(null) }
    val data = remember(entry.slug) { repository.loadWork(entry.slug) }
    val documents = remember(entry.slug) { repository.documents(data) }
    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 28.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
    Column(Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
        TextButton(onClick = onBack, modifier = Modifier.align(Alignment.Start)) { Text("‹ Library") }
        Spacer(Modifier.height(8.dp))
        Text(entry.titleEn.ifEmpty { entry.title }, style = MaterialTheme.typography.displaySmall, textAlign = TextAlign.Center)
        // a text without an author (the New Testament) is named in Greek instead
        val author = entry.authorEn.ifEmpty { entry.author }
        Text(if (author.isNotBlank()) "by $author" else entry.title, style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
        Spacer(Modifier.height(28.dp))
        Text(entry.description, style = MaterialTheme.typography.bodyLarge, textAlign = TextAlign.Center)
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
                OutlinedButton(onClick = { openDocument = slug }, modifier = Modifier.fillMaxWidth()) { Text(title) }
            }
        }
        Spacer(Modifier.height(12.dp))
        OutlinedButton(onClick = onSearch, modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp)) { Text("Dictionary and word analysis") }
        Spacer(Modifier.height(28.dp))
        androidx.compose.foundation.layout.Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TextButton(onClick = { showHelp = true }) { Text("How to use") }
            TextButton(onClick = { showAbout = true }) { Text("About and credits") }
        }
    }
    }
    openDocument?.let { slug ->
        val doc = remember(slug) { repository.document(data, slug) }
        if (doc != null) DocumentSheet(doc, onDismiss = { openDocument = null }) else openDocument = null
    }
    if (showHelp) IntroDialog(onDismiss = { showHelp = false })
    if (showAbout) {
        val credits = remember { repository.credits() }
        AboutDialog(appVersion, credits, onDismiss = { showAbout = false })
    }
}
