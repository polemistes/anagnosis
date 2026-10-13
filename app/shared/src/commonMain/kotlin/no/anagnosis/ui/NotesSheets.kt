package no.anagnosis.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import no.anagnosis.data.Note
import no.anagnosis.data.PlacedNote

/**
 * Writing or changing one of the reader's notes: the passage's citation and Greek, then the note.
 * Closing the sheet by swiping it away or with back keeps what was written, so that no writing
 * is lost; Cancel throws a change away. [onDelete] is null for a note not yet saved.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NoteEditorSheet(
    heading: String,
    quote: String,
    initialBody: String,
    isNew: Boolean,
    onSave: (String) -> Unit,
    onDelete: (() -> Unit)?,
    onDismiss: () -> Unit,
) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var body by remember { mutableStateOf(initialBody) }
    var confirmDelete by remember { mutableStateOf(false) }
    val focus = remember { FocusRequester() }
    val current = rememberUpdatedState(body)
    fun keep() {
        val text = current.value
        if (text.isNotBlank() && text != initialBody) onSave(text) else onDismiss()
    }
    ModalBottomSheet(onDismissRequest = { keep() }, sheetState = state, modifier = sheetModifier()) {
        Column(Modifier.fillMaxWidth().imePadding().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
            Text(heading, style = MaterialTheme.typography.titleMedium)
            if (quote.isNotEmpty()) {
                // a reminder of the passage, not the passage: a long one is cut short
                Text(quote, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 4, overflow = TextOverflow.Ellipsis)
            }
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = body,
                onValueChange = { body = it },
                placeholder = { Text("Your note") },
                minLines = 4,
                modifier = Modifier.fillMaxWidth().focusRequester(focus),
            )
            Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                if (onDelete != null) {
                    TextButton(onClick = { confirmDelete = true }) { Text("Delete", color = MaterialTheme.colorScheme.error) }
                }
                Spacer(Modifier.weight(1f))
                TextButton(onClick = onDismiss) { Text("Cancel") }
                Button(onClick = { onSave(body) }, enabled = body.isNotBlank(), modifier = Modifier.padding(start = 8.dp)) { Text("Save") }
            }
            Spacer(Modifier.height(16.dp))
        }
    }
    if (isNew) LaunchedEffect(Unit) { focus.requestFocus() }
    if (confirmDelete && onDelete != null) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Delete this note?") },
            confirmButton = { TextButton(onClick = { confirmDelete = false; onDelete() }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirmDelete = false }) { Text("Cancel") } },
        )
    }
}

/** One note in a list: its citation, the Greek, and the note, shortened where [short]. */
@Composable
private fun NoteEntry(heading: String, note: Note, short: Boolean, onClick: () -> Unit) {
    Column(Modifier.fillMaxWidth().clickable(onClick = onClick).padding(vertical = 4.dp)) {
        Text(heading, style = MaterialTheme.typography.titleMedium)
        Text(
            note.quote, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
            maxLines = if (short) 1 else Int.MAX_VALUE, overflow = TextOverflow.Ellipsis,
        )
        Spacer(Modifier.height(4.dp))
        Text(note.body, style = MaterialTheme.typography.bodyMedium, maxLines = if (short) 3 else Int.MAX_VALUE, overflow = TextOverflow.Ellipsis)
    }
}

/** The reader's notes on the current page; a note opens in the editor. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PageNotesListSheet(
    notes: List<PlacedNote>,
    label: (Note) -> String,
    onOpen: (PlacedNote) -> Unit,
    onAll: () -> Unit,
    onDismiss: () -> Unit,
) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state, modifier = sheetModifier()) {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
            Text("Notes", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
            if (notes.isEmpty()) {
                Spacer(Modifier.height(12.dp))
                Text("No notes on this page.", style = MaterialTheme.typography.bodyMedium)
            }
            notes.forEachIndexed { i, pn ->
                if (i > 0) HorizontalDivider(Modifier.padding(vertical = 10.dp)) else Spacer(Modifier.height(12.dp))
                NoteEntry(label(pn.note), pn.note, short = false) { onOpen(pn) }
            }
            Spacer(Modifier.height(16.dp))
            TextButton(onClick = onAll, modifier = Modifier.align(Alignment.CenterHorizontally)) { Text("All notes in this text") }
            Spacer(Modifier.height(16.dp))
        }
    }
}

/**
 * Every note on the text in text order; a tap goes to the note's page. Notes whose passage is
 * not found in the current text come last and open in the editor instead.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AllNotesSheet(
    title: String,
    notes: List<PlacedNote>,
    label: (Note) -> String,
    onGo: (PlacedNote) -> Unit,
    onOpen: (PlacedNote) -> Unit,
    onExport: (() -> Unit)?,
    onDismiss: () -> Unit,
) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val placed = notes.filter { it.placement != null }
    val lost = notes.filter { it.placement == null }
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state, modifier = sheetModifier()) {
        LazyColumn(Modifier.fillMaxWidth().heightIn(min = 120.dp), contentPadding = PaddingValues(horizontal = 20.dp, vertical = 8.dp)) {
            item {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text("Notes on $title", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary, modifier = Modifier.weight(1f))
                    if (onExport != null && notes.isNotEmpty()) TextButton(onClick = onExport) { Text("Export") }
                }
                if (notes.isEmpty()) {
                    Spacer(Modifier.height(12.dp))
                    Text("No notes yet.", style = MaterialTheme.typography.bodyMedium)
                }
            }
            items(placed, key = { it.note.id }) { pn ->
                Column {
                    if (pn !== placed.first()) HorizontalDivider(Modifier.padding(vertical = 10.dp)) else Spacer(Modifier.height(8.dp))
                    NoteEntry(label(pn.note), pn.note, short = true) { onGo(pn) }
                }
            }
            if (lost.isNotEmpty()) {
                item {
                    Text(
                        "Passages not found in the current text",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(top = 24.dp, bottom = 4.dp),
                    )
                }
                items(lost, key = { it.note.id }) { pn ->
                    Column(verticalArrangement = Arrangement.spacedBy(0.dp)) {
                        if (pn !== lost.first()) HorizontalDivider(Modifier.padding(vertical = 10.dp)) else Spacer(Modifier.height(8.dp))
                        NoteEntry(label(pn.note), pn.note, short = true) { onOpen(pn) }
                    }
                }
            }
            item { Spacer(Modifier.height(32.dp)) }
        }
    }
}
