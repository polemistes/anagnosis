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
import androidx.compose.material3.Card
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.CatalogEntry
import no.anagnosis.prefs.ReaderSettings

/** The widest a page of the front page, a text's page or the search is laid out; wider screens centre it. */
val CONTENT_MAX_WIDTH = 640.dp

/**
 * The front page: what the app is, the dictionary and word analysis, the texts installed, and
 * the way to the texts on sale. Without a text the app is a dictionary and analyser.
 */
@Composable
fun HomeScreen(
    catalog: List<CatalogEntry>,
    appVersion: String,
    repository: AnagnosisRepository,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    onOpen: (String) -> Unit,
    onAvailable: () -> Unit,
) {
    var showHelp by remember { mutableStateOf(false) }
    var showAbout by remember { mutableStateOf(false) }
    val search = rememberSearchState(repository, settings)
    // the Greek keyboard shows only while the field is in use, so that it does not cover the page
    var fieldFocused by remember { mutableStateOf(false) }
    val focusManager = LocalFocusManager.current
    val installed = catalog.filter { it.installed }.sortedBy { it.titleEn.ifEmpty { it.title } }
    // on a tablet the page keeps a readable width in the middle of the screen
    val width = Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth()
    Column(Modifier.fillMaxSize().safeDrawingPadding(), horizontalAlignment = Alignment.CenterHorizontally) {
        LazyColumn(
            Modifier.weight(1f).fillMaxWidth(),
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
                    Text(
                        "Anagnosis is an app for reading ancient Greek texts. It provides dictionaries and a tool for " +
                            "morphological analysis. The reading app itself is free, but it is possible to buy texts that " +
                            "can be read in the app. While reading, you can look up words, see the syntax of sentences and " +
                            "look at the critical apparatus, a commentary or an English translation of the current page.",
                        style = MaterialTheme.typography.bodyMedium,
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
            searchResults(search, repository, width)
            if (installed.isNotEmpty()) {
                item {
                    Text(
                        "Your texts",
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = width.padding(top = 24.dp, bottom = 8.dp),
                    )
                }
                items(installed, key = { it.slug }) { entry ->
                    Card(width.padding(bottom = 8.dp).clickable { onOpen(entry.slug) }) {
                        Text(titleByAuthor(entry), style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(16.dp))
                    }
                }
            }
            item {
                OutlinedButton(onClick = onAvailable, modifier = width.padding(top = 24.dp)) { Text("Available texts") }
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
        val credits = remember { repository.credits() }
        AboutDialog(appVersion, credits, onDismiss = { showAbout = false })
    }
}

/** "Antigone by Sophocles"; a text without an author (the New Testament) by its title alone. */
@Composable
fun titleByAuthor(entry: CatalogEntry) = buildAnnotatedString {
    append(entry.titleEn.ifEmpty { entry.title })
    val author = entry.authorEn.ifEmpty { entry.author }
    if (author.isNotBlank()) {
        withStyle(SpanStyle(color = MaterialTheme.colorScheme.onSurfaceVariant)) { append(" by $author") }
    }
}
