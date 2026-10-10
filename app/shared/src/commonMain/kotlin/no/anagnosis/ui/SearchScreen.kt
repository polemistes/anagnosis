package no.anagnosis.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.foundation.lazy.LazyListScope
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
 * one per word; in the analyser, the typed form's analyses are listed. Shared by the search
 * page and the front page.
 */
class SearchState {
    var mode by mutableStateOf(SearchMode.DICTIONARY)
    var query by mutableStateOf(TextFieldValue(""))
    var hits by mutableStateOf<List<HeadwordHit>>(emptyList())
    var analyses by mutableStateOf<List<FormAnalysis>>(emptyList())
    var word by mutableStateOf<WordInfo?>(null)

    /** Whether the results are those of something typed (and not of an empty field). */
    var searched by mutableStateOf(false)

    /** A key of the on-screen Greek keyboard: a letter, or a mark applied to the last vowel. */
    fun typeGreek(s: String) {
        val text = query.text
        val newText = if (s.length == 1 && s[0].code in 0x300..0x345) Polytonic.apply(text, s[0]) else text + s
        query = TextFieldValue(newText, TextRange(newText.length))
    }

    fun backspace() {
        val t = query.text
        if (t.isNotEmpty()) query = TextFieldValue(t.dropLast(1), TextRange(t.length - 1))
    }
}

/** A search whose results follow what is typed. */
@Composable
fun rememberSearchState(repository: AnagnosisRepository, settings: ReaderSettings): SearchState {
    val state = remember { SearchState() }
    val greekQuery = Transliteration.toGreek(state.query.text, settings.inputScheme)
    val key = Transliteration.looseKey(greekQuery)
    val exact = settings.exactDiacritics && state.mode == SearchMode.ANALYSER
    LaunchedEffect(key, state.mode, greekQuery, exact) {
        if (key.isEmpty()) { state.hits = emptyList(); state.analyses = emptyList(); state.searched = false; return@LaunchedEffect }
        delay(60)
        when (state.mode) {
            SearchMode.DICTIONARY -> { state.hits = withContext(Dispatchers.Default) { repository.searchHeadwords(key) }; state.analyses = emptyList() }
            SearchMode.ANALYSER -> { state.analyses = withContext(Dispatchers.Default) { repository.analyse(greekQuery, exact) }; state.hits = emptyList() }
        }
        state.searched = true
    }
    return state
}

/**
 * The mode switch, the search field and its options. `navigation` is put before the mode
 * switch (the search page's way back); `fieldModifier` lets the page follow the field's focus.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SearchControls(
    state: SearchState,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    fieldModifier: Modifier = Modifier,
    navigation: (@Composable () -> Unit)? = null,
) {
    val greekQuery = Transliteration.toGreek(state.query.text, settings.inputScheme)
    Column(Modifier.fillMaxWidth()) {
        Row(Modifier.fillMaxWidth().padding(top = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            if (navigation != null) {
                navigation()
                Spacer(Modifier.weight(1f))
            }
            SingleChoiceSegmentedButtonRow(if (navigation == null) Modifier.fillMaxWidth() else Modifier) {
                SearchMode.entries.forEachIndexed { i, m ->
                    SegmentedButton(
                        selected = state.mode == m,
                        onClick = { state.mode = m },
                        shape = SegmentedButtonDefaults.itemShape(i, SearchMode.entries.size),
                        label = { Text(m.label, fontSize = 12.sp) },
                    )
                }
            }
        }
        OutlinedTextField(
            value = state.query,
            onValueChange = { state.query = it },
            modifier = fieldModifier.fillMaxWidth().padding(top = 4.dp),
            singleLine = true,
            readOnly = settings.greekKeyboard,
            label = { Text(if (state.mode == SearchMode.DICTIONARY) "Headword" else "Inflected form") },
            supportingText = {
                Text(if (greekQuery != state.query.text && greekQuery.isNotEmpty()) greekQuery else if (settings.greekKeyboard) "Type a vowel, then its breathing and accent" else settings.inputScheme.hint)
            },
            keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.None, autoCorrectEnabled = false, keyboardType = KeyboardType.Text),
        )
        // the scheme switch moves to a line of its own when the row has no room for it (word analysis on a phone)
        FlowRow(
            Modifier.fillMaxWidth().padding(top = 2.dp, bottom = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            itemVerticalAlignment = Alignment.CenterVertically,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                TextButton(onClick = { onSettingsChange(settings.copy(greekKeyboard = !settings.greekKeyboard)) }) {
                    Text(if (settings.greekKeyboard) "Phone keyboard" else "Greek keyboard", fontSize = 12.sp)
                }
                if (state.mode == SearchMode.ANALYSER) {
                    TextButton(onClick = { onSettingsChange(settings.copy(exactDiacritics = !settings.exactDiacritics)) }) {
                        Text(if (settings.exactDiacritics) "Accents: exact" else "Accents: ignored", fontSize = 12.sp)
                    }
                }
            }
            if (!settings.greekKeyboard) {
                // wide enough for the labels beside the check mark
                SingleChoiceSegmentedButtonRow(Modifier.widthIn(min = 240.dp)) {
                    InputScheme.entries.forEachIndexed { i, s ->
                        SegmentedButton(
                            selected = settings.inputScheme == s,
                            onClick = { onSettingsChange(settings.copy(inputScheme = s)) },
                            shape = SegmentedButtonDefaults.itemShape(i, InputScheme.entries.size),
                            label = { Text(if (s == InputScheme.BETA) "q=θ w=ω" else "u=θ v=ω", fontSize = 12.sp, maxLines = 1) },
                        )
                    }
                }
            }
        }
    }
}

/** The analyses or headwords found, each opening its word sheet; `itemModifier` sets their width. */
fun LazyListScope.searchResults(state: SearchState, repository: AnagnosisRepository, itemModifier: Modifier = Modifier) {
    items(state.analyses) { a ->
        Column(itemModifier) {
            Column(
                Modifier.fillMaxWidth().clickable { state.word = repository.wordInfoForAnalysis(a) }.padding(vertical = 8.dp),
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
    items(state.hits) { hit ->
        Column(itemModifier) {
            Text(
                hit.headword,
                style = MaterialTheme.typography.titleMedium,
                modifier = Modifier.fillMaxWidth().clickable { state.word = repository.wordInfoForLemma(hit.lemmaKey, hit.headword) }.padding(vertical = 10.dp),
            )
            HorizontalDivider()
        }
    }
    if (state.searched && state.hits.isEmpty() && state.analyses.isEmpty()) {
        item { Text("No matches.", style = MaterialTheme.typography.bodyMedium, modifier = itemModifier.padding(top = 16.dp)) }
    }
}

/** The search as a page of its own, reached from a text. */
@Composable
fun SearchScreen(
    repository: AnagnosisRepository,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    onBack: () -> Unit,
) {
    val state = rememberSearchState(repository, settings)
    val focus = remember { FocusRequester() }
    LaunchedEffect(settings.greekKeyboard) { if (!settings.greekKeyboard) focus.requestFocus() }

    Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
    Column(Modifier.weight(1f).widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth().padding(horizontal = 16.dp)) {
        SearchControls(state, settings, onSettingsChange, fieldModifier = Modifier.focusRequester(focus)) {
            TextButton(onClick = onBack) { Text("‹ Back") }
        }
        LazyColumn(Modifier.weight(1f).fillMaxWidth(), contentPadding = PaddingValues(vertical = 4.dp)) {
            searchResults(state, repository)
            item { Spacer(Modifier.height(48.dp)) }
        }
    }
        if (settings.greekKeyboard) {
            GreekKeyboard(
                onKey = { state.typeGreek(it) },
                onBackspace = { state.backspace() },
                onDone = { onSettingsChange(settings.copy(greekKeyboard = false)) },
            )
        }
    }
    state.word?.let { WordSheet(it, onDismiss = { state.word = null }, disabled = settings.disabledDictionaries) }
}
