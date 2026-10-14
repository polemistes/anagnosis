package no.anagnosis.ui

import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.CatalogEntry
import no.anagnosis.data.SearchHit
import no.anagnosis.prefs.ReaderSettings

/** The widest the front page or the search is laid out; wider screens centre it. */
val CONTENT_MAX_WIDTH = 640.dp

/**
 * The front page: what the app is (a box that can be put away), the dictionary and word
 * analysis, the texts installed, and the way to the texts on sale. Without a text the app is a
 * dictionary and analyser. A text's title opens out to the books it comes from and the way into
 * it (`expanded` is its slug). While something is typed in the search field, the page holds the
 * search and its results alone, with a Close button that empties the field.
 */
@Composable
fun HomeScreen(
    catalog: List<CatalogEntry>,
    appVersion: String,
    repository: AnagnosisRepository,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    expanded: String?,
    onExpand: (String?) -> Unit,
    onRead: (String) -> Unit,
    onAvailable: () -> Unit,
    /** The search, kept by the app for the session. */
    search: SearchState,
    /** A hit of a search in the texts, to be opened in the reader. */
    onOpenHit: (SearchHit) -> Unit,
    /** The page's scroll position, kept by the app, so that coming back from a hit finds the results. */
    listState: LazyListState,
    /** The description was put away for this session. */
    descriptionDismissed: Boolean = false,
    /** Puts the description away; `true` also for good (the settings can bring it back). */
    onDismissDescription: (Boolean) -> Unit = {},
) {
    var aboutText by remember { mutableStateOf<CatalogEntry?>(null) }
    var showHelp by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    var showOptions by remember { mutableStateOf(false) }
    val installedTexts = catalog.filter { it.installed }
    SearchEffects(search, repository, settings, textSlug = null, installed = installedTexts)
    // the Greek keyboard shows only while the field is in use, so that it does not cover the page
    var fieldFocused by remember { mutableStateOf(false) }
    val focusManager = LocalFocusManager.current
    val installed = catalog.filter { it.installed }
    // only texts marked as on sale are offered; until there are some, the button says so
    val anyOffered = catalog.any { it.onGooglePlay }
    // on a tablet the page keeps a readable width in the middle of the screen
    val width = Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth()
    // something typed in the search field: the page holds the search alone
    val searching = search.query.text.isNotEmpty()
    // while searching, back does what Close does
    if (searching) PlatformBackHandler { search.setText(TextFieldValue("")); focusManager.clearFocus() }
    Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
        LazyColumn(
            Modifier.weight(1f).fillMaxWidth(),
            state = listState,
            contentPadding = PaddingValues(horizontal = 24.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            item {
                Column(width, horizontalAlignment = Alignment.CenterHorizontally) {
                    Spacer(Modifier.height(16.dp))
                    Text("Anagnosis", style = MaterialTheme.typography.displaySmall, textAlign = TextAlign.Center)
                    Text(
                        "An Ancient Greek Reading App",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center,
                    )
                    Spacer(Modifier.height(20.dp))
                }
            }
            if (!searching && settings.showDescription && !descriptionDismissed) {
                item { Description(onDismiss = onDismissDescription, modifier = width.padding(bottom = 20.dp)) }
            }
            item {
                Column(width) {
                    SearchControls(search, settings, onSettingsChange, fieldModifier = Modifier.onFocusChanged { fieldFocused = it.isFocused }, onSubmit = { search.submit() }, textsAvailable = installedTexts.isNotEmpty())
                }
            }
            searchResults(search, repository, installedTexts, onOpenHit, width)
            if (searching) {
                item {
                    OutlinedButton(
                        onClick = { search.setText(TextFieldValue("")); focusManager.clearFocus() },
                        modifier = width.padding(top = 24.dp),
                    ) { Text("Close") }
                }
            } else {
                if (installed.isNotEmpty()) {
                    item {
                        Text(
                            "Your texts",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = width.padding(top = 24.dp, bottom = 8.dp),
                        )
                    }
                    // in the order of their authors, each named in its title ("Antigone by Sophocles")
                    items(byAuthor(installed).flatMap { it.second }, key = { it.slug }) { entry ->
                        TextCard(
                            entry,
                            open = entry.slug == expanded,
                            onToggle = { onExpand(if (entry.slug == expanded) null else entry.slug) },
                            onRead = { onRead(entry.slug) },
                            onAbout = { aboutText = entry },
                            modifier = width.padding(bottom = 8.dp),
                        )
                    }
                }
                item {
                    OutlinedButton(onClick = onAvailable, enabled = anyOffered, modifier = width.padding(top = 24.dp)) {
                        Text(if (anyOffered) "Available texts" else "Texts will be available soon")
                    }
                }
                item {
                    Row(Modifier.padding(top = 20.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        TextButton(onClick = { showHelp = true }) { Text("How to use") }
                        TextButton(onClick = { showOptions = true }) { Text("Options") }
                        TextButton(onClick = { showAbout = true }) { Text("About and credits") }
                    }
                }
            }
        }
        if (search.greekKeys(settings) && fieldFocused) {
            GreekKeyboard(
                onKey = { search.typeGreek(it) },
                onBackspace = { search.backspace() },
                onDone = { focusManager.clearFocus() },
            )
        }
    }
    SearchWordSheet(search, settings, installedTexts, repository)
    if (showHelp) IntroDialog(onDismiss = { showHelp = false })
    if (showOptions) {
        OptionsDialog(
            settings, onSettingsChange,
            onHelp = { showOptions = false; showHelp = true },
            onAbout = { showOptions = false; showAbout = true },
            onDismiss = { showOptions = false },
            dictionaries = remember { repository.dictionaries() },
        )
    }
    if (showAbout) {
        val credits = remember { repository.appCredits() }
        AboutDialog(appVersion, credits, onDismiss = { showAbout = false })
    }
    aboutText?.let { entry ->
        val credits = remember(entry.slug) { repository.textCredits(entry) }
        TextAboutDialog(entry.titleEn.ifEmpty { entry.title }, credits, onDismiss = { aboutText = null })
    }
}

/**
 * What the app is, in a box at the top of the front page: Dismiss puts it away for the session,
 * or for good with "Do not show again" ticked.
 */
@Composable
private fun Description(onDismiss: (Boolean) -> Unit, modifier: Modifier = Modifier) {
    var forGood by remember { mutableStateOf(false) }
    OutlinedCard(modifier) {
        Column(Modifier.padding(start = 16.dp, end = 8.dp, top = 16.dp, bottom = 4.dp)) {
            Text(
                "An app for reading ancient Greek texts, with dictionaries and morphological analysis, working offline. " +
                    "The app is free; each text, with its translation and commentary, is bought in the app.",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(end = 8.dp),
            )
            Row(Modifier.fillMaxWidth().padding(top = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                // the checkbox's touch area reaches past its box: moved left, the box lines up with the text
                Row(
                    Modifier.weight(1f).offset(x = (-13).dp).clickable { forGood = !forGood },
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Checkbox(checked = forGood, onCheckedChange = { forGood = it })
                    Text("Do not show again", style = MaterialTheme.typography.bodyMedium)
                }
                TextButton(onClick = { onDismiss(forGood) }) { Text("Dismiss") }
            }
        }
    }
}

/** A text's title with its author, "Antigone by Sophocles"; a text without an author by its title alone. */
internal fun fullTitle(entry: CatalogEntry): String {
    val title = entry.titleEn.ifEmpty { entry.title }
    val author = entry.authorEn.ifEmpty { entry.author }.trim()
    return if (author.isEmpty()) title else "$title by $author"
}

/** An installed text: its title, which opens out to the books it comes from and the way into it. */
@Composable
private fun TextCard(
    entry: CatalogEntry,
    open: Boolean,
    onToggle: () -> Unit,
    onRead: () -> Unit,
    onAbout: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(modifier.animateContentSize()) {
        Row(Modifier.fillMaxWidth().clickable(onClick = onToggle).padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(fullTitle(entry), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            Icon(
                if (open) Icons.Filled.KeyboardArrowUp else Icons.Filled.KeyboardArrowDown,
                contentDescription = if (open) "Less" else "More",
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (open) {
            Column(Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, bottom = 12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                for ((label, reference) in references(entry)) {
                    Text(
                        buildAnnotatedString {
                            withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) { append("$label: ") }
                            append(reference)
                        },
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                Button(onClick = onRead, modifier = Modifier.fillMaxWidth().padding(top = 10.dp)) {
                    Text("Read this text", modifier = Modifier.padding(vertical = 4.dp))
                }
                TextButton(onClick = onAbout, modifier = Modifier.align(Alignment.CenterHorizontally)) { Text("About and credits") }
            }
        }
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

/**
 * Texts grouped by author, the authors in alphabetical order and each one's texts by title; a text
 * without an author (the New Testament) comes first, under no heading.
 */
internal fun byAuthor(entries: List<CatalogEntry>): List<Pair<String, List<CatalogEntry>>> =
    entries.groupBy { it.authorEn.ifEmpty { it.author }.trim() }
        .toList()
        .sortedBy { it.first }
        .map { (author, texts) -> author to texts.sortedBy { it.titleEn.ifEmpty { it.title } } }
