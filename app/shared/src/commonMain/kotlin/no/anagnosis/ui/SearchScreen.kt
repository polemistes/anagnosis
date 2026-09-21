package no.anagnosis.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.FormAnalysis
import no.anagnosis.data.HeadwordHit
import no.anagnosis.data.Morphology
import no.anagnosis.data.WordInfo
import no.anagnosis.greek.InputScheme
import no.anagnosis.greek.Polytonic
import no.anagnosis.greek.Transliteration
import no.anagnosis.prefs.ReaderSettings

enum class SearchMode(val label: String) { DICTIONARY("Dictionary"), ANALYSER("Word analysis") }

/**
 * Dictionary lookup or morphological analysis. Type Greek, or Latin letters in the chosen
 * scheme; diacritics are ignored. In the dictionary, matching headwords appear as you type,
 * one per word; in the analyser, the typed form's analyses are listed.
 */
@Composable
fun SearchScreen(
    repository: AnagnosisRepository,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    onBack: () -> Unit,
) {
    var mode by remember { mutableStateOf(SearchMode.DICTIONARY) }
    var query by remember { mutableStateOf(TextFieldValue("")) }
    var hits by remember { mutableStateOf<List<HeadwordHit>>(emptyList()) }
    var analyses by remember { mutableStateOf<List<FormAnalysis>>(emptyList()) }
    var word by remember { mutableStateOf<WordInfo?>(null) }
    val focus = remember { FocusRequester() }

    val greekQuery = Transliteration.toGreek(query.text, settings.inputScheme)
    val key = Transliteration.looseKey(greekQuery)
    val exact = settings.exactDiacritics && mode == SearchMode.ANALYSER

    LaunchedEffect(key, mode, greekQuery, exact) {
        if (key.isEmpty()) { hits = emptyList(); analyses = emptyList(); return@LaunchedEffect }
        delay(60)
        when (mode) {
            SearchMode.DICTIONARY -> { hits = withContext(Dispatchers.Default) { repository.searchHeadwords(key) }; analyses = emptyList() }
            SearchMode.ANALYSER -> { analyses = withContext(Dispatchers.Default) { repository.analyse(greekQuery, exact) }; hits = emptyList() }
        }
    }
    LaunchedEffect(settings.greekKeyboard) { if (!settings.greekKeyboard) focus.requestFocus() }

    fun typeGreek(s: String) {
        val text = query.text
        val newText = if (s.length == 1 && s[0].code in 0x300..0x345) Polytonic.apply(text, s[0]) else text + s
        query = TextFieldValue(newText, TextRange(newText.length))
    }

    Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
    Column(Modifier.weight(1f).widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth().padding(horizontal = 16.dp)) {
        Row(Modifier.fillMaxWidth().padding(top = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹ Back") }
            Spacer(Modifier.weight(1f))
            SingleChoiceSegmentedButtonRow {
                SearchMode.entries.forEachIndexed { i, m ->
                    SegmentedButton(
                        selected = mode == m,
                        onClick = { mode = m },
                        shape = SegmentedButtonDefaults.itemShape(i, SearchMode.entries.size),
                        label = { Text(m.label, fontSize = 12.sp) },
                    )
                }
            }
        }
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            modifier = Modifier.fillMaxWidth().padding(top = 4.dp).focusRequester(focus),
            singleLine = true,
            readOnly = settings.greekKeyboard,
            label = { Text(if (mode == SearchMode.DICTIONARY) "Headword" else "Inflected form") },
            supportingText = {
                Text(if (greekQuery != query.text && greekQuery.isNotEmpty()) greekQuery else if (settings.greekKeyboard) "Type a vowel, then its breathing and accent" else settings.inputScheme.hint)
            },
            keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.None, autoCorrectEnabled = false, keyboardType = KeyboardType.Text),
        )
        Row(Modifier.fillMaxWidth().padding(top = 2.dp, bottom = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = { onSettingsChange(settings.copy(greekKeyboard = !settings.greekKeyboard)) }) {
                Text(if (settings.greekKeyboard) "Phone keyboard" else "Greek keyboard", fontSize = 12.sp)
            }
            if (mode == SearchMode.ANALYSER) {
                TextButton(onClick = { onSettingsChange(settings.copy(exactDiacritics = !settings.exactDiacritics)) }) {
                    Text(if (settings.exactDiacritics) "Accents: exact" else "Accents: ignored", fontSize = 12.sp)
                }
            }
            Spacer(Modifier.weight(1f))
            if (!settings.greekKeyboard) {
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
        }
        LazyColumn(Modifier.weight(1f).fillMaxWidth(), contentPadding = PaddingValues(vertical = 4.dp)) {
            items(analyses) { a ->
                Column(
                    Modifier.fillMaxWidth().clickable { word = repository.wordInfoForAnalysis(a) }.padding(vertical = 8.dp),
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(a.form, style = MaterialTheme.typography.titleMedium)
                        Text("→ ${a.lemma}", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
                    }
                    Text(Morphology.describe(a.postag), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                HorizontalDivider()
            }
            items(hits) { hit ->
                Text(
                    hit.headword,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.fillMaxWidth().clickable { word = repository.wordInfoForLemma(hit.lemmaKey, hit.headword) }.padding(vertical = 10.dp),
                )
                HorizontalDivider()
            }
            if (key.isNotEmpty() && hits.isEmpty() && analyses.isEmpty()) {
                item { Text("No matches.", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 16.dp)) }
            }
            item { Spacer(Modifier.height(48.dp)) }
        }
    }
        if (settings.greekKeyboard) {
            GreekKeyboard(
                onKey = { typeGreek(it) },
                onBackspace = { val t = query.text; if (t.isNotEmpty()) query = TextFieldValue(t.dropLast(1), TextRange(t.length - 1)) },
                onDone = { onSettingsChange(settings.copy(greekKeyboard = false)) },
            )
        }
    }
    word?.let { WordSheet(it, onDismiss = { word = null }) }
}
