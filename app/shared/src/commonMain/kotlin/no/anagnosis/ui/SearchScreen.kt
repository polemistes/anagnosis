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
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.FilterChip
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.ui.draw.rotate
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.InterceptPlatformTextInput
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.Dictionaries
import no.anagnosis.data.CatalogEntry
import no.anagnosis.data.LemmaIndex
import no.anagnosis.data.LemmaRow
import no.anagnosis.data.SearchHit
import no.anagnosis.data.SearchOptions
import no.anagnosis.data.SearchResult
import no.anagnosis.data.SearchSource
import no.anagnosis.data.TextSearch
import no.anagnosis.data.WorkData
import no.anagnosis.data.FormAnalysis
import no.anagnosis.data.HeadwordHit
import no.anagnosis.data.Morphology
import no.anagnosis.data.WordInfo
import no.anagnosis.greek.InputScheme
import no.anagnosis.greek.Polytonic
import no.anagnosis.greek.Transliteration
import no.anagnosis.prefs.ReaderSettings

enum class SearchMode(val label: String) {
    DICTIONARY("Dictionary"), ANALYSER("Analysis"), TEXT("Text"), LEMMA("Lemma"),
}

/** A line of the results of a search in the texts: a text's heading, a book's, or a hit with its citation. */
sealed interface ResultRow {
    /** A text's heading; with a [title] (a search of several texts) it folds the text's hits away. */
    class TextHeader(val slug: String, val title: String?, val counts: String) : ResultRow
    class BookHeader(val slug: String, val title: String) : ResultRow
    class Hit(val hit: SearchHit, val cite: String) : ResultRow
}

/**
 * The search: dictionary lookup, morphological analysis, free text in the texts, and lemmas.
 * Type Greek, or Latin letters in the chosen scheme. In the dictionary, matching headwords appear
 * as you type, one per word; in the analyser, the typed form's analyses are listed; in the texts,
 * Latin letters search the English until the reader asks for the Greek. Made once for the
 * session (in [App]), so that leaving the search for a hit and coming back finds it as it was.
 */
class SearchState {
    var mode by mutableStateOf(SearchMode.DICTIONARY)
    var query by mutableStateOf(TextFieldValue(""))
    var hits by mutableStateOf<List<HeadwordHit>>(emptyList())

    /** Whether [hits] are Woodhouse's English headwords (and not Greek ones). */
    var hitsEnglish by mutableStateOf(false)

    /** Dictionary mode: English to Greek (Woodhouse) instead of Greek to English. */
    var english by mutableStateOf(false)

    /** Whether the lexicon has Woodhouse, so that English to Greek can be offered (set by [SearchEffects]). */
    var englishOffered by mutableStateOf(false)

    /** Greek words tapped in a dictionary entry, each looked up on a sheet of its own; the last is shown. */
    var lookedUp by mutableStateOf<List<WordInfo>>(emptyList())
    var analyses by mutableStateOf<List<FormAnalysis>>(emptyList())
    var word by mutableStateOf<WordInfo?>(null)

    /** Whether the results are those of something typed (and not of an empty field). */
    var searched by mutableStateOf(false)

    /** The scope of a search opened from a text: that text only, or every installed text. */
    var thisText by mutableStateOf(true)

    /** Text mode: Latin letters are made Greek (by the scheme) instead of searching the English. */
    var asGreek by mutableStateOf(false)
    var options by mutableStateOf(SearchOptions())
    var sources by mutableStateOf(SearchSource.entries.toSet())
    var textResult by mutableStateOf<SearchResult?>(null)
    var textRows by mutableStateOf<List<ResultRow>>(emptyList())

    /** The texts opened out in the results of a search of several texts (all folded at first, unless only one has hits). */
    var openTexts by mutableStateOf<Set<String>>(emptySet())
    var openOccurrenceTexts by mutableStateOf<Set<String>>(emptySet())

    /** While the texts are made ready for searching (the first search in each takes a moment). */
    var busy by mutableStateOf(false)

    /** Lemma mode: the suggestions for what is typed, each with its gloss filled in. */
    var lemmaRows by mutableStateOf<List<LemmaRow>>(emptyList())

    /** Lemma mode: when no lemma begins with what is typed, the analyser's readings of it as a form. */
    var analysedLemmas by mutableStateOf<List<FormAnalysis>>(emptyList())
    var lemmaSearched by mutableStateOf(false)

    /** Lemma mode: the lemma whose occurrences are listed, its row as found in the texts searched, and the list. */
    var chosen by mutableStateOf<LemmaRow?>(null)
    var chosenShown by mutableStateOf<LemmaRow?>(null)
    var occurrenceRows by mutableStateOf<List<ResultRow>>(emptyList())
    var occurrenceCount by mutableStateOf(0)
    var occurrenceTexts by mutableStateOf(0)

    /** A lemma to choose once the texts' lemmas are at hand: (lemma key, lemma). */
    var pendingLemma by mutableStateOf<Pair<String, String>?>(null)

    /** The lemma key of the word whose sheet is open from the dictionary or the analyser. */
    var wordKey by mutableStateOf<String?>(null)

    /** The results list, kept so that coming back from a hit finds it scrolled where it was. */
    val listState = LazyListState()

    /** The texts searched: the text the search was opened from, or all installed texts. */
    fun slugs(textSlug: String?, installed: List<CatalogEntry>): List<String> =
        if (textSlug != null && thisText) listOf(textSlug) else installed.map { it.slug }

    fun setText(value: TextFieldValue) {
        if (value.text != query.text) {
            if (value.text.isEmpty()) asGreek = false
            chosen = null
        }
        query = value
    }

    /** Lemma mode with the given lemma chosen: the occurrences of a word, asked for from its sheet. */
    fun openLemma(lemmaKey: String, lemma: String) {
        mode = SearchMode.LEMMA
        word = null
        query = TextFieldValue(lemma, TextRange(lemma.length))
        chosen = null
        pendingLemma = lemmaKey to lemma
    }

    /** The search key of the keyboard: in Lemma mode it takes the first suggestion. */
    fun submit() {
        if (mode == SearchMode.LEMMA && chosen == null) lemmaRows.firstOrNull()?.let { chosen = it }
    }

    /**
     * A key of the on-screen Greek keyboard, typed at the cursor: a letter, or a mark applied to
     * the last vowel before it. A selection is replaced.
     */
    fun typeGreek(s: String) {
        val text = query.text
        val before = text.substring(0, query.selection.min)
        val after = text.substring(query.selection.max)
        val newBefore = if (s.length == 1 && s[0].code in 0x300..0x345) Polytonic.apply(before, s[0]) else before + s
        query = TextFieldValue(newBefore + after, TextRange(newBefore.length))
    }

    /** Deletes the selection, or the character before the cursor. */
    fun backspace() {
        val text = query.text
        val sel = query.selection
        val start = if (sel.collapsed) maxOf(sel.min - 1, 0) else sel.min
        if (start == sel.max) return
        setText(TextFieldValue(text.substring(0, start) + text.substring(sel.max), TextRange(start)))
    }
}

/** Whether English to Greek can be chosen: Woodhouse is there and turned on. */
fun SearchState.englishChoice(settings: ReaderSettings): Boolean =
    englishOffered && Dictionaries.WOODHOUSE !in settings.disabledDictionaries

/** Whether the dictionary looks up English now. */
fun SearchState.lookingUpEnglish(settings: ReaderSettings): Boolean =
    mode == SearchMode.DICTIONARY && english && englishChoice(settings)

/** Whether the app's Greek keyboard is in use: chosen, and not while English is typed. */
fun SearchState.greekKeys(settings: ReaderSettings): Boolean = settings.greekKeyboard && !lookingUpEnglish(settings)

/** Whether the text holds a Latin letter, and whether it holds a Greek one. */
private fun hasLatin(s: String) = s.any { it in 'a'..'z' || it in 'A'..'Z' }
private fun hasGreek(s: String) = s.any { it in '\u0370'..'\u03FF' || it in '\u1F00'..'\u1FFF' }

/** A pattern made Greek by the scheme, leaving what follows a backslash (\b, \s) as typed. */
private fun toGreekPattern(s: String, scheme: InputScheme): String {
    val sb = StringBuilder(s.length)
    var i = 0
    while (i < s.length) {
        if (s[i] == '\\' && i + 1 < s.length) { sb.append(s, i, i + 2); i += 2; continue }
        sb.append(Transliteration.toGreek(s[i].toString(), scheme))
        i++
    }
    return sb.toString()
}

/** What Text mode searches for: the field as typed, or made Greek when the reader asked for that. */
fun SearchState.textQuery(scheme: InputScheme): String = when {
    !asGreek -> query.text
    options.regex -> toGreekPattern(query.text, scheme)
    else -> Transliteration.toGreek(query.text, scheme)
}

/** The texts are searched one job at a time, so that two searches never build the same text at once. */
private val searchDispatcher = Dispatchers.Default.limitedParallelism(1)

/**
 * The lines of the results: under each text (named when [showTitles]) its counts by source, then
 * its hits in the order of the text, under the books of an epic or the New Testament.
 */
fun resultRows(
    hits: List<SearchHit>,
    slugs: List<String>,
    work: (String) -> WorkData,
    titles: Map<String, String>,
    showTitles: Boolean,
    counts: (List<SearchHit>, WorkData) -> String,
): List<ResultRow> {
    val out = mutableListOf<ResultRow>()
    val bySlug = hits.groupBy { it.slug }
    for (slug in slugs) {
        val textHits = bySlug[slug] ?: continue
        val w = work(slug)
        out += ResultRow.TextHeader(slug, if (showTitles) titles[slug] ?: slug else null, counts(textHits, w))
        val sorted = textHits.sortedWith(compareBy({ it.nInt }, { it.nSub }, { it.source.ordinal }))
        var book: Int? = null
        for (h in sorted) {
            if (w.byBook) {
                val b = w.bookOf(h.nInt)
                if (b != book) {
                    book = b
                    w.books.firstOrNull { it.number == b }?.let { out += ResultRow.BookHeader(slug, it.title) }
                }
            }
            out += ResultRow.Hit(h, if (w.byBook) w.lineLabel(h.nInt, h.nSub) else w.citation(h.nInt, h.nSub))
        }
    }
    return out
}

/** The text to open out at once: the only one with hits, when there is only one. */
private fun soleText(rows: List<ResultRow>): Set<String> =
    rows.filterIsInstance<ResultRow.TextHeader>().singleOrNull()?.let { setOf(it.slug) } ?: emptySet()

/** "214 matches in 3 texts": the total of a search, above its texts. */
private fun totalLine(count: Int, texts: Int, one: String, many: String, truncated: Boolean = false): String {
    val n = if (truncated) "More than $count $many; the first $count are listed" else if (count == 1) "1 $one" else "$count $many"
    return if (texts > 1) "$n, in $texts texts" else n
}

/** "Greek 214 · Translation 12 · Apparatus 3": the hits of a text by source. */
fun countsBySource(hits: List<SearchHit>, @Suppress("UNUSED_PARAMETER") work: WorkData): String =
    hits.groupBy { if (it.source == SearchSource.GREEK) SearchSource.GREEK.label else it.label }
        .entries.joinToString(" · ") { "${it.key} ${it.value.size}" }

/**
 * Runs the search whose results follow what is typed. `textSlug` is the text the search was
 * opened from (null on the front page); `installed` the texts there are, in the catalog's order.
 */
@Composable
fun SearchEffects(state: SearchState, repository: AnagnosisRepository, settings: ReaderSettings, textSlug: String?, installed: List<CatalogEntry>) {
    // A word looked up takes the focus from the field, so that the keyboard (the phone's or the
    // app's) stays hidden when its sheet is closed, until the field is tapped again.
    val focusManager = LocalFocusManager.current
    LaunchedEffect(state.word) { if (state.word != null) focusManager.clearFocus() }
    LaunchedEffect(Unit) { state.englishOffered = withContext(Dispatchers.Default) { repository.hasLexicon(Dictionaries.WOODHOUSE) } }
    val english = state.lookingUpEnglish(settings)
    val greekQuery = Transliteration.toGreek(state.query.text, settings.inputScheme)
    val key = if (english) Dictionaries.englishKey(state.query.text) else Transliteration.looseKey(greekQuery)
    val exact = settings.exactDiacritics && state.mode == SearchMode.ANALYSER
    LaunchedEffect(key, state.mode, greekQuery, exact, english) {
        if (key.isEmpty() || state.mode == SearchMode.TEXT || state.mode == SearchMode.LEMMA) {
            state.hits = emptyList(); state.analyses = emptyList(); state.searched = false; return@LaunchedEffect
        }
        delay(60)
        when (state.mode) {
            SearchMode.DICTIONARY -> {
                state.hits = withContext(Dispatchers.Default) { if (english) repository.searchEnglish(key) else repository.searchHeadwords(key) }
                state.hitsEnglish = english
                state.analyses = emptyList()
            }
            SearchMode.ANALYSER -> { state.analyses = withContext(Dispatchers.Default) { repository.analyse(greekQuery, exact) }; state.hits = emptyList() }
            else -> {}
        }
        state.searched = true
    }
    val slugs = state.slugs(textSlug, installed)
    val textQuery = state.textQuery(settings.inputScheme)
    LaunchedEffect(state.mode, textQuery, state.options, state.sources, slugs) {
        if (state.mode != SearchMode.TEXT) return@LaunchedEffect
        if (textQuery.isBlank() || slugs.isEmpty()) { state.textResult = null; state.textRows = emptyList(); return@LaunchedEffect }
        delay(120)
        state.busy = true
        try {
            val titles = installed.associate { it.slug to it.titleEn.ifEmpty { it.title } }
            val (result, rows) = withContext(searchDispatcher) {
                val job = coroutineContext
                val r = repository.searchTexts(slugs, textQuery, state.options, state.sources) { job.isActive }
                r to resultRows(r.hits, slugs, { repository.corpus(it).work }, titles, slugs.size > 1 || textSlug == null, ::countsBySource)
            }
            state.textResult = result
            state.textRows = rows
            state.openTexts = soleText(rows)
        } finally {
            state.busy = false
        }
    }
    LaunchedEffect(state.mode, greekQuery, slugs, state.chosen, state.pendingLemma) {
        if (state.mode != SearchMode.LEMMA || slugs.isEmpty()) return@LaunchedEffect
        val pending = state.pendingLemma
        if (pending != null) {
            // a word from a sheet: its row among the texts' lemmas, or a row of its own when none has it
            val row = withContext(searchDispatcher) {
                repository.lemmaRows(slugs).firstOrNull { it.contains(pending.first) } ?: LemmaIndex.lonely(pending.first, pending.second)
            }
            state.pendingLemma = null
            state.chosen = row
            return@LaunchedEffect
        }
        val chosen = state.chosen
        if (chosen != null) {
            state.busy = true
            try {
                val titles = installed.associate { it.slug to it.titleEn.ifEmpty { it.title } }
                val (row, hits, rows) = withContext(searchDispatcher) {
                    // the row as the texts now searched have it (the scope may have changed)
                    val row = repository.lemmaRows(slugs).firstOrNull { r -> chosen.keys.any { r.contains(it) } } ?: chosen
                    if (row.gloss == null) row.gloss = repository.glossFor(row)
                    val hits = repository.occurrences(row, slugs)
                    Triple(row, hits, resultRows(hits, slugs, { repository.corpus(it).work }, titles, slugs.size > 1 || textSlug == null) { h, w ->
                        (if (h.size == 1) "1 occurrence" else "${h.size} occurrences") +
                            (if (w.automaticSyntax) " · lemmas by a parser, not checked by hand" else "")
                    })
                }
                state.chosenShown = row
                state.occurrenceCount = hits.size
                state.occurrenceTexts = hits.distinctBy { it.slug }.size
                state.occurrenceRows = rows
                state.openOccurrenceTexts = soleText(rows)
            } finally {
                state.busy = false
            }
            return@LaunchedEffect
        }
        if (key.isEmpty()) { state.lemmaRows = emptyList(); state.analysedLemmas = emptyList(); state.lemmaSearched = false; return@LaunchedEffect }
        delay(60)
        val (rows, analysed) = withContext(searchDispatcher) {
            val rows = LemmaIndex.suggest(repository.lemmaRows(slugs), greekQuery)
            rows.forEach { if (it.gloss == null) it.gloss = repository.glossFor(it) }
            rows to (if (rows.isEmpty()) repository.analyse(greekQuery).distinctBy { it.lemmaKey } else emptyList())
        }
        state.lemmaRows = rows
        state.analysedLemmas = analysed
        state.lemmaSearched = true
    }
}

/**
 * The mode switch, the search field and its options. `navigation` stands in a row of its own
 * above the mode switch (the search page's way back); `fieldModifier` lets the page follow the
 * field's focus; `textSlug` is the text the search was opened from, which offers the choice
 * between that text and all texts. With the app's Greek keyboard the field stays editable, so
 * that it shows its cursor, but the phone's keyboard is kept from opening.
 */
@OptIn(ExperimentalLayoutApi::class, ExperimentalComposeUiApi::class)
@Composable
fun SearchControls(
    state: SearchState,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    textSlug: String? = null,
    fieldModifier: Modifier = Modifier,
    onSubmit: () -> Unit = {},
    /** Whether Text mode's chips stand here; the search page puts them at the top of its list instead. */
    chips: Boolean = true,
    /** Whether any text is installed: without one there is nothing for Text and Lemma to search, and they are not offered. */
    textsAvailable: Boolean = true,
    navigation: (@Composable () -> Unit)? = null,
) {
    val greekQuery = Transliteration.toGreek(state.query.text, settings.inputScheme)
    val english = state.lookingUpEnglish(settings)
    val greekKeys = state.greekKeys(settings)
    val fieldFocus = remember { FocusRequester() }
    var focused by remember { mutableStateOf(false) }
    // switching keyboards makes the field anew (the phone's keyboard is let in or kept out when
    // the field takes the focus); a field in use gets the focus back
    var refocus by remember { mutableStateOf(false) }
    LaunchedEffect(greekKeys) {
        if (refocus) { fieldFocus.requestFocus(); refocus = false }
    }
    val focusManager = LocalFocusManager.current
    val inTexts = state.mode == SearchMode.TEXT || state.mode == SearchMode.LEMMA
    val modes = if (textsAvailable) SearchMode.entries else listOf(SearchMode.DICTIONARY, SearchMode.ANALYSER)
    // the last text gone while Text or Lemma was chosen: back to the dictionary
    LaunchedEffect(textsAvailable) { if (!textsAvailable && inTexts) state.mode = SearchMode.DICTIONARY }
    Column(Modifier.fillMaxWidth()) {
        if (navigation != null) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { navigation() }
        }
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth().padding(top = 4.dp)) {
            modes.forEachIndexed { i, m ->
                SegmentedButton(
                    selected = state.mode == m,
                    onClick = { state.mode = m },
                    shape = SegmentedButtonDefaults.itemShape(i, modes.size),
                    // no check mark: four labels share a phone's width
                    icon = {},
                    label = { Text(m.label, fontSize = 12.sp, maxLines = 1, softWrap = false) },
                )
            }
        }
        key(greekKeys) {
            InterceptPlatformTextInput(
                interceptor = { request, nextHandler ->
                    if (greekKeys) awaitCancellation() else nextHandler.startInputMethod(request)
                },
            ) {
                OutlinedTextField(
                    value = state.query,
                    onValueChange = { state.setText(it) },
                    modifier = fieldModifier.focusRequester(fieldFocus).onFocusChanged { focused = it.isFocused }
                        .fillMaxWidth().padding(top = 4.dp),
                    singleLine = true,
                    // the keyboard in use, which a tap changes: the app's Greek one or the phone's
                    leadingIcon = if (english) null else {
                        {
                            val label = if (settings.greekKeyboard) "The app's Greek keyboard; tap for the phone's" else "The phone's keyboard; tap for the app's Greek keyboard"
                            IconButton(
                                onClick = { refocus = focused; onSettingsChange(settings.copy(greekKeyboard = !settings.greekKeyboard)) },
                                modifier = Modifier.semantics { contentDescription = label },
                            ) {
                                Text(
                                    if (settings.greekKeyboard) "αβγ" else "abc",
                                    fontSize = 14.sp,
                                    color = if (settings.greekKeyboard) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    },
                    label = {
                        Text(when (state.mode) {
                            SearchMode.DICTIONARY -> if (english) "English word" else "Headword"
                            SearchMode.ANALYSER -> "Inflected form"
                            SearchMode.TEXT -> "Word or phrase"
                            SearchMode.LEMMA -> "Lemma"
                        })
                    },
                    trailingIcon = if (state.query.text.isEmpty()) null else {
                        { IconButton(onClick = { state.setText(TextFieldValue("")) }) { Icon(Icons.Filled.Clear, contentDescription = "Clear") } }
                    },
                    supportingText = {
                        val text = state.query.text
                        when {
                            state.mode == SearchMode.TEXT && !state.asGreek && hasLatin(text) && !hasGreek(text) -> Text(
                                "English · Search the Greek for ${withFinalSigma(state.textQueryAsGreek(settings.inputScheme))}",
                                color = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.clickable { state.asGreek = true },
                                maxLines = 1, overflow = TextOverflow.Ellipsis,
                            )
                            state.mode == SearchMode.TEXT && state.asGreek -> Text(
                                "Greek: ${withFinalSigma(state.textQuery(settings.inputScheme))} · Search the English",
                                color = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.clickable { state.asGreek = false },
                                maxLines = 1, overflow = TextOverflow.Ellipsis,
                            )
                            state.mode == SearchMode.TEXT -> Text(
                                if (settings.greekKeyboard) "Type a vowel, then its breathing and accent" else "Greek searches the Greek; Latin letters the English",
                                maxLines = 1, overflow = TextOverflow.Ellipsis,
                            )
                            english -> Text("Woodhouse, English-Greek Dictionary", maxLines = 1, overflow = TextOverflow.Ellipsis)
                            greekQuery != text && greekQuery.isNotEmpty() -> Text(greekQuery)
                            settings.greekKeyboard -> Text("Type a vowel, then its breathing and accent")
                            else -> Text(settings.inputScheme.hint)
                        }
                    },
                    keyboardOptions = KeyboardOptions(
                        capitalization = KeyboardCapitalization.None, autoCorrectEnabled = false, keyboardType = KeyboardType.Text,
                        imeAction = if (state.mode == SearchMode.LEMMA) ImeAction.Search else ImeAction.Done,
                    ),
                    keyboardActions = KeyboardActions(
                        onDone = { focusManager.clearFocus() },
                        onSearch = { onSubmit(); focusManager.clearFocus() },
                    ),
                )
            }
        }
        // the mode's own options under the field: the dictionary's direction, the analyser's
        // diacritics, the texts' scope (Text mode's chips follow); nothing for a mode without any
        val direction = state.mode == SearchMode.DICTIONARY && state.englishChoice(settings)
        val diacritics = state.mode == SearchMode.ANALYSER
        val scope = inTexts && textSlug != null
        if (direction || diacritics || scope) {
            FlowRow(
                Modifier.fillMaxWidth().padding(bottom = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                itemVerticalAlignment = Alignment.CenterVertically,
            ) {
                if (direction) {
                    // the whole width: the two labels are long for a phone
                    SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                        listOf(false to "Greek → English", true to "English → Greek").forEachIndexed { i, (toGreek, label) ->
                            SegmentedButton(
                                selected = state.english == toGreek,
                                onClick = { if (state.english != toGreek) { refocus = focused; state.english = toGreek } },
                                shape = SegmentedButtonDefaults.itemShape(i, 2),
                                icon = {},
                                label = { Text(label, fontSize = 12.sp, maxLines = 1, softWrap = false) },
                            )
                        }
                    }
                }
                if (diacritics) {
                    FilterChip(
                        selected = settings.exactDiacritics,
                        onClick = { onSettingsChange(settings.copy(exactDiacritics = !settings.exactDiacritics)) },
                        label = { Text("Diacritics", fontSize = 12.sp) },
                    )
                }
                if (scope) {
                    SingleChoiceSegmentedButtonRow {
                        listOf(true to "This text", false to "All texts").forEachIndexed { i, (mine, label) ->
                            SegmentedButton(
                                selected = state.thisText == mine,
                                onClick = { state.thisText = mine },
                                shape = SegmentedButtonDefaults.itemShape(i, 2),
                                icon = {},
                                label = { Text(label, fontSize = 12.sp, maxLines = 1, softWrap = false) },
                            )
                        }
                    }
                }
            }
        }
        if (chips && state.mode == SearchMode.TEXT) TextChips(state)
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth().padding(vertical = 2.dp))
    }
}

/** Text mode's options and its sources, as two rows of chips. Diacritics and Case, when on, make the match exact in them. */
@Composable
fun TextChips(state: SearchState) {
    Column(Modifier.fillMaxWidth()) {
        val o = state.options
        ChipRow(
            listOf(
                Triple("Diacritics", o.exactAccents) { state.options = o.copy(exactAccents = !o.exactAccents) },
                Triple("Case", o.exactCase) { state.options = o.copy(exactCase = !o.exactCase) },
                Triple("Whole words", o.wholeWords) { state.options = o.copy(wholeWords = !o.wholeWords) },
                Triple("Regex", o.regex) { state.options = o.copy(regex = !o.regex) },
            ),
        )
        ChipRow(
            SearchSource.entries.map { src ->
                Triple(src.label, src in state.sources) {
                    state.sources = if (src in state.sources) state.sources - src else state.sources + src
                }
            },
        )
    }
}

/** The Greek a Latin query would search for. */
private fun SearchState.textQueryAsGreek(scheme: InputScheme): String =
    if (options.regex) toGreekPattern(query.text, scheme) else Transliteration.toGreek(query.text, scheme)

/** Greek as shown to the reader: a sigma at the end of a word written ς. */
private fun withFinalSigma(s: String): String = FINAL_SIGMA.replace(s, "ς")
private val FINAL_SIGMA = Regex("σ(?![\\p{L}])")

/** A row of filter chips that scrolls sideways when the screen is too narrow for it. */
@Composable
private fun ChipRow(chips: List<Triple<String, Boolean, () -> Unit>>) {
    Row(
        Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        for ((label, on, toggle) in chips) {
            FilterChip(selected = on, onClick = toggle, label = { Text(label, fontSize = 12.sp) })
        }
    }
}

/**
 * The results: the analyses or headwords found, each opening its word sheet, or the hits in the
 * texts, each opening the reader there (`onOpen`). `itemModifier` sets their width.
 */
fun LazyListScope.searchResults(
    state: SearchState,
    repository: AnagnosisRepository,
    installed: List<CatalogEntry>,
    onOpen: (SearchHit) -> Unit,
    itemModifier: Modifier = Modifier,
) {
    when (state.mode) {
        SearchMode.TEXT -> textResults(state, installed, onOpen, itemModifier)
        SearchMode.LEMMA -> lemmaResults(state, installed, onOpen, itemModifier)
        else -> dictionaryResults(state, repository, itemModifier)
    }
}

private fun LazyListScope.dictionaryResults(state: SearchState, repository: AnagnosisRepository, itemModifier: Modifier) {
    items(state.analyses) { a ->
        Column(itemModifier) {
            Column(
                Modifier.fillMaxWidth().clickable { state.word = repository.wordInfoForAnalysis(a); state.wordKey = a.lemmaKey }.padding(vertical = 8.dp),
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
                modifier = Modifier.fillMaxWidth().clickable {
                    if (state.hitsEnglish) {
                        state.word = repository.wordInfoForEnglish(hit.lemmaKey, hit.headword); state.wordKey = null
                    } else {
                        state.word = repository.wordInfoForLemma(hit.lemmaKey, hit.headword); state.wordKey = hit.lemmaKey
                    }
                }.padding(vertical = 10.dp),
            )
            HorizontalDivider()
        }
    }
    if (state.searched && state.hits.isEmpty() && state.analyses.isEmpty()) {
        item { Text("No matches.", style = MaterialTheme.typography.bodyMedium, modifier = itemModifier.padding(top = 16.dp)) }
    }
}

private fun LazyListScope.textResults(state: SearchState, installed: List<CatalogEntry>, onOpen: (SearchHit) -> Unit, itemModifier: Modifier) {
    if (installed.isEmpty()) {
        item { Text("No text is installed yet. The texts are bought as apps of their own.", style = MaterialTheme.typography.bodyMedium, modifier = itemModifier.padding(top = 16.dp)) }
        return
    }
    val result = state.textResult ?: return
    result.error?.let { err ->
        item { Text(err, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.error, modifier = itemModifier.padding(top = 16.dp)) }
        return
    }
    if (result.hits.isNotEmpty()) {
        item {
            Text(
                totalLine(result.hits.size, result.hits.distinctBy { it.slug }.size, "match", "matches", result.truncated),
                style = MaterialTheme.typography.titleSmall,
                modifier = itemModifier.padding(top = 8.dp),
            )
        }
    }
    resultRowItems(state.textRows, state.openTexts, { slug -> state.openTexts = state.openTexts.toggle(slug) }, onOpen, itemModifier)
    if (result.hits.isEmpty()) {
        item { Text("No matches.", style = MaterialTheme.typography.bodyMedium, modifier = itemModifier.padding(top = 16.dp)) }
    }
}

private fun LazyListScope.lemmaResults(state: SearchState, installed: List<CatalogEntry>, onOpen: (SearchHit) -> Unit, itemModifier: Modifier) {
    if (installed.isEmpty()) {
        item { Text("No text is installed yet. The texts are bought as apps of their own.", style = MaterialTheme.typography.bodyMedium, modifier = itemModifier.padding(top = 16.dp)) }
        return
    }
    if (state.chosen != null) {
        val row = state.chosenShown ?: state.chosen ?: return
        item {
            Column(itemModifier.padding(top = 8.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(row.spellings.joinToString(" / "), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    TextButton(onClick = { state.chosen = null }) { Text("Suggestions") }
                }
                row.gloss?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                if (state.occurrenceCount > 0) {
                    Text(
                        totalLine(state.occurrenceCount, state.occurrenceTexts, "occurrence", "occurrences"),
                        style = MaterialTheme.typography.titleSmall,
                        modifier = Modifier.padding(top = 4.dp),
                    )
                }
                if (!state.busy && state.occurrenceCount == 0) {
                    Text("No occurrences in the texts searched.", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 12.dp))
                }
                HorizontalDivider(Modifier.padding(top = 8.dp))
            }
        }
        resultRowItems(state.occurrenceRows, state.openOccurrenceTexts, { slug -> state.openOccurrenceTexts = state.openOccurrenceTexts.toggle(slug) }, onOpen, itemModifier)
        return
    }
    items(state.lemmaRows) { row ->
        Column(itemModifier) {
            Row(
                Modifier.fillMaxWidth().clickable { state.chosen = row }.padding(vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(Modifier.weight(1f)) {
                    Text(row.spellings.joinToString(" / "), style = MaterialTheme.typography.titleMedium)
                    row.gloss?.let {
                        Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
                Text(row.total.toString(), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(start = 12.dp))
            }
            HorizontalDivider()
        }
    }
    if (state.lemmaRows.isEmpty() && state.analysedLemmas.isNotEmpty()) {
        item {
            Text("No lemma begins so; the form can be:", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = itemModifier.padding(top = 12.dp, bottom = 4.dp))
        }
        items(state.analysedLemmas) { a ->
            Column(itemModifier) {
                Column(
                    Modifier.fillMaxWidth().clickable { state.pendingLemma = a.lemmaKey.trimEnd { it.isDigit() } to a.lemma.trimEnd { it.isDigit() } }.padding(vertical = 8.dp),
                ) {
                    // one line per lemma: the form's several parses belong to the analyser
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(a.form, style = MaterialTheme.typography.titleMedium)
                        Text("→ ${a.lemma}", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
                    }
                }
                HorizontalDivider()
            }
        }
    }
    if (state.lemmaSearched && state.lemmaRows.isEmpty() && state.analysedLemmas.isEmpty()) {
        item { Text("No lemma begins so.", style = MaterialTheme.typography.bodyMedium, modifier = itemModifier.padding(top = 16.dp)) }
    }
}

/**
 * The word sheet of a headword or an analysis, with Occurrences when there are texts to look in.
 * A Greek word tapped in an entry opens a sheet of its own; closing it goes back to the one before.
 */
@Composable
fun SearchWordSheet(state: SearchState, settings: ReaderSettings, installed: List<CatalogEntry>, repository: AnagnosisRepository) {
    val lookUp: (String) -> Unit = { w -> state.lookedUp = state.lookedUp + repository.wordInfoForForm(w) }
    state.lookedUp.lastOrNull()?.let { looked ->
        WordSheet(looked, onDismiss = { state.lookedUp = state.lookedUp.dropLast(1) }, disabled = settings.disabledDictionaries, onGreekWord = lookUp)
        return
    }
    val info = state.word ?: return
    val key = state.wordKey
    WordSheet(
        info,
        onDismiss = { state.word = null },
        disabled = settings.disabledDictionaries,
        onOccurrences = if (key == null || installed.isEmpty()) null else { { state.openLemma(key.trimEnd { it.isDigit() }, info.lemma.trimEnd { it.isDigit() }) } },
        onGreekWord = lookUp,
    )
}

private fun Set<String>.toggle(slug: String): Set<String> = if (slug in this) this - slug else this + slug

/**
 * Headings and hits as list items; a hit shows its citation, its excerpt with the match in bold,
 * and its source. In a search of several texts each text's heading folds its hits: only the texts
 * in [open] show them, and a tap on a heading calls [onToggle].
 */
fun LazyListScope.resultRowItems(
    rows: List<ResultRow>,
    open: Set<String>,
    onToggle: (String) -> Unit,
    onOpen: (SearchHit) -> Unit,
    itemModifier: Modifier,
) {
    val folding = rows.any { it is ResultRow.TextHeader && it.title != null }
    val shown = if (!folding) rows else rows.filter {
        when (it) {
            is ResultRow.TextHeader -> true
            is ResultRow.BookHeader -> it.slug in open
            is ResultRow.Hit -> it.hit.slug in open
        }
    }
    items(shown) { row ->
        when (row) {
            is ResultRow.TextHeader -> if (row.title == null) {
                Column(itemModifier.padding(top = 14.dp, bottom = 4.dp)) {
                    Text(row.counts, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            } else {
                val isOpen = row.slug in open
                Column(itemModifier.padding(top = 6.dp)) {
                    Row(
                        Modifier.fillMaxWidth().clickable { onToggle(row.slug) }.padding(vertical = 8.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(row.title, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
                            Text(row.counts, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Icon(
                            Icons.Filled.KeyboardArrowDown,
                            contentDescription = if (isOpen) "Fold" else "Show the matches",
                            modifier = Modifier.rotate(if (isOpen) 180f else 0f),
                        )
                    }
                    if (!isOpen) HorizontalDivider()
                }
            }
            is ResultRow.BookHeader -> Text(
                row.title, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = itemModifier.padding(top = 10.dp, bottom = 2.dp),
            )
            is ResultRow.Hit -> {
                val bold = FontWeight.Bold
                val excerpt = remember(row) { TextSearch.excerpt(row.hit) }
                val text = remember(excerpt) {
                    buildAnnotatedString {
                        append(excerpt.text)
                        if (excerpt.end > excerpt.start) addStyle(SpanStyle(fontWeight = bold), excerpt.start, excerpt.end)
                    }
                }
                Row(itemModifier.clickable { onOpen(row.hit) }.padding(vertical = 6.dp)) {
                    Text(
                        row.cite, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline,
                        modifier = Modifier.widthIn(min = 56.dp).padding(top = 2.dp, end = 8.dp),
                    )
                    Column(Modifier.weight(1f)) {
                        Text(text, style = MaterialTheme.typography.bodyMedium)
                        if (row.hit.source != SearchSource.GREEK) {
                            Text(row.hit.label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
                        }
                    }
                }
            }
        }
    }
}

/** The search as a page of its own, reached from a text (`textSlug`). */
@Composable
fun SearchScreen(
    repository: AnagnosisRepository,
    state: SearchState,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    textSlug: String?,
    installed: List<CatalogEntry>,
    onOpen: (SearchHit) -> Unit,
    onBack: () -> Unit,
) {
    SearchEffects(state, repository, settings, textSlug, installed)
    val focus = remember { FocusRequester() }
    // the Greek keyboard shows while the field is in use
    var fieldFocused by remember { mutableStateOf(false) }
    val focusManager = LocalFocusManager.current
    // the field is ready for typing when the page opens empty; coming back to results, it is not
    LaunchedEffect(Unit) { if (state.query.text.isEmpty()) focus.requestFocus() }

    Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
    Column(Modifier.weight(1f).widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth().padding(horizontal = 16.dp)) {
        SearchControls(
            state, settings, onSettingsChange, textSlug,
            fieldModifier = Modifier.focusRequester(focus).onFocusChanged { fieldFocused = it.isFocused },
            chips = false,
            onSubmit = { state.submit() },
            textsAvailable = installed.isNotEmpty(),
        ) {
            TextButton(onClick = onBack) { Text("‹ Back") }
        }
        LazyColumn(Modifier.weight(1f).fillMaxWidth(), state = state.listState, contentPadding = PaddingValues(vertical = 4.dp)) {
            // the chips scroll away with the results, which leaves them room under the keyboard
            if (state.mode == SearchMode.TEXT) item { TextChips(state) }
            searchResults(state, repository, installed, onOpen)
            item { Spacer(Modifier.height(48.dp)) }
        }
    }
        if (state.greekKeys(settings) && fieldFocused) {
            GreekKeyboard(
                onKey = { state.typeGreek(it) },
                onBackspace = { state.backspace() },
                onDone = { focusManager.clearFocus() },
            )
        }
    }
    SearchWordSheet(state, settings, installed, repository)
}
