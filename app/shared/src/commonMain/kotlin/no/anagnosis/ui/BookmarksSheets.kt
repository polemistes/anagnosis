package no.anagnosis.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import no.anagnosis.data.Bookmark
import no.anagnosis.data.PlacedBookmark

/**
 * Saving or changing a bookmark: the sentence's citation and first words, then a name, which may
 * be left empty. Closing the sheet by swiping it away or with back keeps the bookmark (a new one
 * is saved, a changed name kept); Cancel throws it away. [onDelete] is null for a new bookmark.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BookmarkEditorSheet(
    heading: String,
    quote: String,
    initialName: String,
    isNew: Boolean,
    onSave: (String) -> Unit,
    onDelete: (() -> Unit)?,
    onDismiss: () -> Unit,
) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var name by remember { mutableStateOf(initialName) }
    var confirmDelete by remember { mutableStateOf(false) }
    val focus = remember { FocusRequester() }
    val current = rememberUpdatedState(name)
    fun keep() {
        val text = current.value.trim()
        if (isNew || text != initialName) onSave(text) else onDismiss()
    }
    ModalBottomSheet(onDismissRequest = { keep() }, sheetState = state, modifier = sheetModifier()) {
        Column(Modifier.fillMaxWidth().imePadding().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
            Text(heading, style = MaterialTheme.typography.titleMedium)
            Text(quote, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 2, overflow = TextOverflow.Ellipsis)
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                placeholder = { Text("Name (optional)") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                modifier = Modifier.fillMaxWidth().focusRequester(focus),
            )
            Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                if (onDelete != null) {
                    TextButton(onClick = { confirmDelete = true }) { Text("Delete", color = MaterialTheme.colorScheme.error) }
                }
                Spacer(Modifier.weight(1f))
                TextButton(onClick = onDismiss) { Text("Cancel") }
                Button(onClick = { onSave(name.trim()) }, modifier = Modifier.padding(start = 8.dp)) { Text("Save") }
            }
            Spacer(Modifier.height(16.dp))
        }
    }
    if (isNew) LaunchedEffect(Unit) { focus.requestFocus() }
    if (confirmDelete && onDelete != null) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Delete this bookmark?") },
            confirmButton = { TextButton(onClick = { confirmDelete = false; onDelete() }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirmDelete = false }) { Text("Cancel") } },
        )
    }
}

/** One bookmark in the list: citation and name, the first words under them; highlighted when [here]. */
@Composable
private fun BookmarkRow(heading: String, bookmark: Bookmark, here: Boolean, onClick: () -> Unit, onEdit: () -> Unit) {
    val background = if (here) Modifier.background(MaterialTheme.colorScheme.primaryContainer, MaterialTheme.shapes.small) else Modifier
    Row(
        Modifier.fillMaxWidth().padding(vertical = 2.dp).then(background).clickable(onClick = onClick).padding(start = 8.dp, top = 6.dp, bottom = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.Bottom) {
                Text(heading, style = MaterialTheme.typography.titleMedium, maxLines = 1)
                if (bookmark.name.isNotEmpty()) {
                    Text(
                        "  " + bookmark.name, style = MaterialTheme.typography.bodyMedium,
                        maxLines = 1, overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            Text(
                bookmark.quote, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1, overflow = TextOverflow.Ellipsis,
            )
        }
        IconButton(onClick = onEdit) { Icon(Icons.Outlined.Edit, contentDescription = "Edit the bookmark") }
    }
}

/**
 * Every bookmark in the text, in text order; those whose sentence starts on the present page
 * ([here], by bookmark id) are highlighted. A tap goes to the bookmark's page, the pencil opens
 * it in the editor. Bookmarks not found in the current text come last; a tap opens them in the editor.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BookmarksSheet(
    bookmarks: List<PlacedBookmark>,
    label: (Bookmark) -> String,
    here: Set<Long>,
    onGo: (PlacedBookmark) -> Unit,
    onOpen: (PlacedBookmark) -> Unit,
    onDismiss: () -> Unit,
) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val placed = bookmarks.filter { it.token != null }
    val lost = bookmarks.filter { it.token == null }
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state, modifier = sheetModifier()) {
        LazyColumn(Modifier.fillMaxWidth().heightIn(min = 120.dp), contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp)) {
            item {
                Text(
                    "Bookmarks", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(start = 8.dp, bottom = 8.dp),
                )
            }
            items(placed, key = { it.bookmark.id }) { pb ->
                BookmarkRow(label(pb.bookmark), pb.bookmark, pb.bookmark.id in here, onClick = { onGo(pb) }, onEdit = { onOpen(pb) })
            }
            if (lost.isNotEmpty()) {
                item {
                    Text(
                        "Not found in the current text",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(start = 8.dp, top = 24.dp, bottom = 4.dp),
                    )
                }
                items(lost, key = { it.bookmark.id }) { pb ->
                    BookmarkRow(label(pb.bookmark), pb.bookmark, false, onClick = { onOpen(pb) }, onEdit = { onOpen(pb) })
                }
            }
            item { Spacer(Modifier.height(32.dp)) }
        }
    }
}
