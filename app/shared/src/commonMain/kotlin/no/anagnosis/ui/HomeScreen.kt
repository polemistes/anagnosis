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
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
 * The front page: what the app is, the dictionary and word analysis, the texts installed, and
 * the way to the texts on sale. Without a text the app is a dictionary and analyser. A text's
 * title opens out to the books it comes from and the way into it (`expanded` is its slug).
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
) {
    var aboutText by remember { mutableStateOf<CatalogEntry?>(null) }
    var showHelp by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    val installedTexts = catalog.filter { it.installed }
    SearchEffects(search, repository, settings, textSlug = null, installed = installedTexts)
    // the Greek keyboard shows only while the field is in use, so that it does not cover the page
    var fieldFocused by remember { mutableStateOf(false) }
    val focusManager = LocalFocusManager.current
    val installed = catalog.filter { it.installed }
    // only texts whose app is on Google Play are offered; until there are some, the button says so
    val anyOffered = catalog.any { it.onGooglePlay && it.appId.isNotEmpty() }
    // on a tablet the page keeps a readable width in the middle of the screen
    val width = Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth()
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
            item {
                Column(width) {
                    SearchControls(search, settings, onSettingsChange, fieldModifier = Modifier.onFocusChanged { fieldFocused = it.isFocused })
                }
            }
            searchResults(search, repository, installedTexts, onOpenHit, width)
            item {
                Text(
                    "Anagnosis is an app for reading ancient Greek texts. It provides dictionaries and a tool for " +
                        "morphological analysis. The reading app itself is free, but it is possible to buy texts that " +
                        "can be read in the app. While reading, you can look up words, see the syntax of sentences and " +
                        "look at the critical apparatus, a commentary or an English translation of the current page.",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = width.padding(top = 20.dp),
                )
            }
            if (installed.isNotEmpty()) {
                item {
                    Text(
                        "Your texts",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = width.padding(top = 24.dp),
                    )
                }
                for ((author, texts) in byAuthor(installed)) {
                    if (author.isNotEmpty()) {
                        item(key = "author:$author") {
                            Text(
                                author,
                                style = MaterialTheme.typography.titleSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = width.padding(top = 12.dp, bottom = 6.dp),
                            )
                        }
                    }
                    items(texts, key = { it.slug }) { entry ->
                        TextCard(
                            entry,
                            open = entry.slug == expanded,
                            onToggle = { onExpand(if (entry.slug == expanded) null else entry.slug) },
                            onRead = { onRead(entry.slug) },
                            onAbout = { aboutText = entry },
                            modifier = width.padding(top = if (author.isEmpty()) 8.dp else 0.dp, bottom = 8.dp),
                        )
                    }
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
                    TextButton(onClick = { showAbout = true }) { Text("About and credits") }
                }
            }
        }
        if (settings.greekKeyboard && fieldFocused) {
            GreekKeyboard(
                onKey = { search.typeGreek(it) },
                onBackspace = { search.backspace() },
                onDone = { focusManager.clearFocus() },
            )
        }
    }
    search.word?.let { WordSheet(it, onDismiss = { search.word = null }, disabled = settings.disabledDictionaries) }
    if (showHelp) IntroDialog(onDismiss = { showHelp = false })
    if (showAbout) {
        val credits = remember { repository.appCredits() }
        AboutDialog(appVersion, credits, onDismiss = { showAbout = false })
    }
    aboutText?.let { entry ->
        val credits = remember(entry.slug) { repository.textCredits(entry) }
        TextAboutDialog(entry.titleEn.ifEmpty { entry.title }, credits, onDismiss = { aboutText = null })
    }
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
            Text(entry.titleEn.ifEmpty { entry.title }, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
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
