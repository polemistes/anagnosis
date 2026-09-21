package no.anagnosis.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
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
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import no.anagnosis.data.Entry
import no.anagnosis.data.NoteGroup
import no.anagnosis.data.NoteInfo
import no.anagnosis.data.NoteKind
import no.anagnosis.data.kind
import no.anagnosis.data.WordInfo
import kotlinx.coroutines.launch
import no.anagnosis.db.Documents
import no.anagnosis.db.Lines

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WordSheet(info: WordInfo, onDismiss: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val glossary = info.entries.filter { it.lexiconSlug.endsWith("-glossary") }
    val buttons = listOf("ml" to "Middle Liddell", "lsj" to "LSJ")
        .filter { (slug, _) -> info.entries.any { it.lexiconSlug == slug } }
    // Without a gloss there is nothing to read on the sheet itself: open the only or the shorter dictionary at once.
    val initial = if (info.shortDefinition == null && glossary.isEmpty()) buttons.firstOrNull()?.first else null
    var open by remember { mutableStateOf(initial) }
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state) {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
            Text(info.form, style = MaterialTheme.typography.headlineSmall)
            val subtitle = buildString {
                if (info.lemma != info.form) append(info.lemma)
                if (info.morphology.isNotEmpty()) { if (isNotEmpty()) append("  ·  "); append(info.morphology) }
            }
            if (subtitle.isNotEmpty()) {
                Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Spacer(Modifier.height(12.dp))
            when {
                info.shortDefinition != null -> Text(info.shortDefinition, style = MaterialTheme.typography.bodyLarge)
                glossary.isNotEmpty() -> glossary.forEach { HtmlText(it.html) }
                info.entries.isEmpty() -> Text("No dictionary entry found.", style = MaterialTheme.typography.bodyMedium)
            }
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
            LineHeading(line)
            for (info in notes) {
                Spacer(Modifier.height(12.dp))
                Text(info.commentary.kind().label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                for (note in info.notes) {
                    Spacer(Modifier.height(6.dp))
                    HtmlText(note.html)
                }
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}

/** Apparatus or commentary for all the lines of the current page. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PageNotesSheet(kind: NoteKind, entries: List<NoteGroup>, sigla: Documents?, onDismiss: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var showSigla by remember { mutableStateOf(false) }
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state) {
        Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(kind.label, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary, modifier = Modifier.weight(1f))
                if (sigla != null) {
                    TextButton(onClick = { showSigla = true }) { Text("Manuscripts") }
                }
            }
            if (entries.isEmpty()) {
                Spacer(Modifier.height(12.dp))
                Text("Nothing on this page.", style = MaterialTheme.typography.bodyMedium)
            }
            entries.forEachIndexed { i, entry ->
                if (i > 0) HorizontalDivider(Modifier.padding(vertical = 14.dp)) else Spacer(Modifier.height(12.dp))
                Text(entry.heading, style = MaterialTheme.typography.titleMedium)
                entry.lineText?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                for (note in entry.notes) {
                    Spacer(Modifier.height(6.dp))
                    HtmlText(note.html)
                }
            }
            Spacer(Modifier.height(32.dp))
        }
    }
    if (showSigla && sigla != null) {
        DocumentSheet(sigla, onDismiss = { showSigla = false })
    }
}

/** A section of a document: the text between two <h1>/<h2> headings. */
private class DocSection(val level: Int, val title: String?, val html: String)

private fun splitSections(html: String): List<DocSection> {
    val out = mutableListOf<DocSection>()
    val re = Regex("<h([12])>(.*?)</h[12]>")
    var pos = 0
    var level = 0
    var title: String? = null
    for (m in re.findAll(html)) {
        val body = html.substring(pos, m.range.first)
        if (body.isNotBlank() || title != null) out += DocSection(level, title, body)
        level = m.groupValues[1].toInt()
        title = m.groupValues[2]
        pos = m.range.last + 1
    }
    out += DocSection(level, title, html.substring(pos))
    return out
}

/** A free-standing document (introduction, appendix, sigla), section by section with a contents list. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DocumentSheet(document: Documents, onDismiss: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val sections = remember(document.id) { splitSections(document.html) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state) {
        LazyColumn(state = listState, modifier = Modifier.fillMaxWidth(), contentPadding = PaddingValues(horizontal = 20.dp, vertical = 8.dp)) {
            item { Text(document.title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(bottom = 8.dp)) }
            if (sections.count { it.title != null } > 3) {
                item {
                    Column(Modifier.padding(bottom = 12.dp)) {
                        sections.forEachIndexed { i, sec ->
                            if (sec.title != null) {
                                Text(
                                    sec.title,
                                    style = if (sec.level == 1) MaterialTheme.typography.labelLarge else MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clickable { scope.launch { listState.animateScrollToItem(i + 2) } }
                                        .padding(start = if (sec.level == 1) 0.dp else 12.dp, top = if (sec.level == 1) 8.dp else 2.dp),
                                )
                            }
                        }
                    }
                    HorizontalDivider()
                }
            }
            itemsIndexed(sections) { _, sec ->
                if (sec.title != null) {
                    Text(
                        sec.title,
                        style = if (sec.level == 1) MaterialTheme.typography.titleLarge else MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(top = if (sec.level == 1) 24.dp else 16.dp, bottom = 6.dp),
                    )
                }
                if (sec.html.isNotBlank()) HtmlText(sec.html)
            }
            item { Spacer(Modifier.height(32.dp)) }
        }
    }
}

/** The list of documents, opened from the title. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DocumentsSheet(documents: List<Pair<String, String>>, onOpen: (String) -> Unit, onDismiss: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = false)
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 8.dp)) {
            Text("About this edition", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
            Spacer(Modifier.height(8.dp))
            for ((slug, title) in documents) {
                Text(
                    title,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.fillMaxWidth().clickable { onOpen(slug) }.padding(vertical = 12.dp),
                )
                HorizontalDivider()
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}

@Composable
private fun LineHeading(line: Lines) {
    Text("Line ${line.n}", style = MaterialTheme.typography.titleMedium)
    Text(line.text, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
}
