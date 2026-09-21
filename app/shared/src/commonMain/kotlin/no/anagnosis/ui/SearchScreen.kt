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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.Entry
import no.anagnosis.data.FormAnalysis
import no.anagnosis.data.HeadwordHit
import no.anagnosis.data.Morphology
import no.anagnosis.greek.InputScheme
import no.anagnosis.greek.Transliteration
import no.anagnosis.prefs.ReaderSettings

/**
 * Dictionary lookup and morphological analysis. Type Greek, or Latin letters in the chosen
 * scheme; diacritics are ignored. Matching headwords appear as you type; if the typed word is
 * an inflected form known to the analyser, its analyses are shown first.
 */
@Composable
fun SearchScreen(
    repository: AnagnosisRepository,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    onBack: () -> Unit,
) {
    var query by remember { mutableStateOf("") }
    var hits by remember { mutableStateOf<List<HeadwordHit>>(emptyList()) }
    var analyses by remember { mutableStateOf<List<FormAnalysis>>(emptyList()) }
    var openEntries by remember { mutableStateOf<List<Entry>?>(null) }
    var openTitle by remember { mutableStateOf("") }
    val focus = remember { FocusRequester() }

    val greekQuery = Transliteration.toGreek(query, settings.inputScheme)
    val key = Transliteration.looseKey(greekQuery)

    LaunchedEffect(key) {
        if (key.isEmpty()) { hits = emptyList(); analyses = emptyList(); return@LaunchedEffect }
        delay(60)
        val (h, a) = withContext(Dispatchers.Default) { repository.searchHeadwords(key) to repository.analyse(key) }
        hits = h
        analyses = a
    }
    LaunchedEffect(Unit) { focus.requestFocus() }

    Column(Modifier.fillMaxSize().safeDrawingPadding().padding(horizontal = 16.dp)) {
        Row(Modifier.fillMaxWidth().padding(top = 4.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹ Back") }
            Spacer(Modifier.weight(1f))
            SingleChoiceSegmentedButtonRow {
                InputScheme.entries.forEachIndexed { i, s ->
                    SegmentedButton(
                        selected = settings.inputScheme == s,
                        onClick = { onSettingsChange(settings.copy(inputScheme = s)) },
                        shape = SegmentedButtonDefaults.itemShape(i, InputScheme.entries.size),
                        label = { Text(if (s == InputScheme.BETA) "q=θ w=ω" else "u=θ v=ω", fontSize = 12.sp) },
                    )
                }
            }
        }
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            modifier = Modifier.fillMaxWidth().focusRequester(focus),
            singleLine = true,
            label = { Text("Greek word or Latin letters") },
            supportingText = {
                Text(if (greekQuery != query && greekQuery.isNotEmpty()) greekQuery else settings.inputScheme.hint)
            },
            keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.None, autoCorrectEnabled = false, keyboardType = KeyboardType.Text),
        )
        LazyColumn(Modifier.fillMaxSize(), contentPadding = androidx.compose.foundation.layout.PaddingValues(vertical = 8.dp)) {
            if (analyses.isNotEmpty()) {
                item {
                    Text("Forms", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(top = 8.dp, bottom = 4.dp))
                }
                items(analyses) { a ->
                    Column(
                        Modifier.fillMaxWidth().clickable {
                            openTitle = a.lemma
                            openEntries = repository.entriesForLemma(a.lemma)
                        }.padding(vertical = 8.dp),
                    ) {
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text(a.form, style = MaterialTheme.typography.titleMedium)
                            Text("→ ${a.lemma}", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
                        }
                        Text(Morphology.describe(a.postag), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    HorizontalDivider()
                }
            }
            if (hits.isNotEmpty()) {
                item {
                    Text("Headwords", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(top = 12.dp, bottom = 4.dp))
                }
                items(hits) { hit ->
                    Row(
                        Modifier.fillMaxWidth().clickable {
                            openTitle = hit.headword
                            openEntries = listOfNotNull(repository.entry(hit.entryId))
                        }.padding(vertical = 10.dp),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text(hit.headword, style = MaterialTheme.typography.titleMedium)
                        if (hit.homograph > 0) Text(hit.homograph.toString(), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
                        Spacer(Modifier.weight(1f))
                        Text(if (hit.lexiconId == 1L) "LSJ" else "Middle Liddell", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
                    }
                    HorizontalDivider()
                }
            }
            if (key.isNotEmpty() && hits.isEmpty() && analyses.isEmpty()) {
                item { Text("No matches.", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 16.dp)) }
            }
            item { Spacer(Modifier.height(48.dp)) }
        }
    }
    openEntries?.let { entries ->
        EntrySheet(title = openTitle, entries = entries, onDismiss = { openEntries = null })
    }
}
