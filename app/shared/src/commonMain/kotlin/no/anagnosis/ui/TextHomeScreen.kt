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
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.CatalogEntry

/**
 * A text's own page: title and author, the books its edition, translation and commentary come
 * from, how to use the reader, and the way into the text. The edition's introduction and
 * appendix are reached from the reader.
 */
@Composable
fun TextHomeScreen(
    repository: AnagnosisRepository,
    entry: CatalogEntry,
    appVersion: String,
    onRead: () -> Unit,
    onBack: () -> Unit,
) {
    var showHelp by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 28.dp, vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
    Column(Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
        TextButton(onClick = onBack, modifier = Modifier.align(Alignment.Start)) { Text("‹ Home") }
        Spacer(Modifier.height(8.dp))
        Text(entry.titleEn.ifEmpty { entry.title }, style = MaterialTheme.typography.displaySmall, textAlign = TextAlign.Center)
        // a text without an author (the New Testament) is named in Greek instead
        val author = entry.authorEn.ifEmpty { entry.author }
        Text(if (author.isNotBlank()) "by $author" else entry.title, style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
        Spacer(Modifier.height(28.dp))
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            for ((label, reference) in references(entry)) {
                Text(
                    buildAnnotatedString {
                        withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) { append("$label: ") }
                        append(reference)
                    },
                    style = MaterialTheme.typography.bodyLarge,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }
        Spacer(Modifier.height(28.dp))
        for (hint in listOf("Tap a word to see its meaning and form.", "Long press a word to see the syntax of its sentence.")) {
            Text(
                hint,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(vertical = 2.dp),
            )
        }
        Spacer(Modifier.height(28.dp))
        Button(onClick = onRead, modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp)) {
            Text("Read the text", modifier = Modifier.padding(vertical = 6.dp))
        }
        Spacer(Modifier.height(28.dp))
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

/**
 * The edition, translation and commentary with the book each comes from; parts from the same
 * book share one line ("Edition and translation", "Edition, translation and commentary").
 */
internal fun references(entry: CatalogEntry): List<Pair<String, String>> {
    val parts = listOf("edition" to entry.refEdition, "translation" to entry.refTranslation, "commentary" to entry.refCommentary)
        .filter { it.second.isNotBlank() }
    return parts.groupBy({ it.second }, { it.first }).map { (reference, names) ->
        val label = if (names.size == 1) names[0] else names.dropLast(1).joinToString(", ") + " and " + names.last()
        label.replaceFirstChar { it.uppercase() } to reference
    }
}
