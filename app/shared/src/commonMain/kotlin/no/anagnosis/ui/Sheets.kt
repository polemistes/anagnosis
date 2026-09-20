package no.anagnosis.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import no.anagnosis.data.NoteInfo
import no.anagnosis.data.WordInfo
import no.anagnosis.db.Lines

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WordSheet(info: WordInfo, onDismiss: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var open by remember { mutableStateOf<String?>(null) }
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state) {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
            Text(info.token.form, style = MaterialTheme.typography.headlineSmall)
            Text(
                text = buildString {
                    append(info.token.lemma)
                    if (info.morphology.isNotEmpty()) append("  ·  ").append(info.morphology)
                },
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(12.dp))
            val glossary = info.entries.filter { it.lexiconSlug.endsWith("-glossary") }
            when {
                info.shortDefinition != null -> Text(info.shortDefinition, style = MaterialTheme.typography.bodyLarge)
                glossary.isNotEmpty() -> glossary.forEach { HtmlText(it.html) }
                info.entries.isEmpty() -> Text("No dictionary entry found.", style = MaterialTheme.typography.bodyMedium)
            }
            val buttons = listOf("lsj" to "LSJ", "ml" to "Middle Liddell")
                .filter { (slug, _) -> info.entries.any { it.lexiconSlug == slug } }
            if (buttons.isNotEmpty()) {
                Spacer(Modifier.height(16.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    for ((slug, label) in buttons) {
                        val toggle = { open = if (open == slug) null else slug }
                        if (open == slug) {
                            FilledTonalButton(onClick = toggle) { Text(label) }
                        } else {
                            OutlinedButton(onClick = toggle) { Text(label) }
                        }
                    }
                }
            }
            val shown = open
            if (shown != null) {
                Spacer(Modifier.height(8.dp))
                info.entries.filter { it.lexiconSlug == shown }.forEachIndexed { i, e ->
                    if (i > 0) HorizontalDivider(Modifier.padding(vertical = 10.dp))
                    HtmlText(e.html)
                }
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NotesSheet(line: Lines, notes: List<NoteInfo>, onDismiss: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = false)
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state) {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
            Text("Line ${line.n}", style = MaterialTheme.typography.headlineSmall)
            Text(line.text, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            for (info in notes) {
                Spacer(Modifier.height(12.dp))
                Text(
                    listOfNotNull(info.commentary.author, info.commentary.title).joinToString(", "),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                )
                for (note in info.notes) {
                    Spacer(Modifier.height(6.dp))
                    Text("§ ${note.n}", style = MaterialTheme.typography.labelMedium)
                    HtmlText(note.html)
                }
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}
