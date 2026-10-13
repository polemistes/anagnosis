package no.anagnosis.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import no.anagnosis.data.Credit
import no.anagnosis.data.Dictionaries
import no.anagnosis.prefs.ColorTheme
import no.anagnosis.prefs.FontChoice
import no.anagnosis.prefs.LineNumberMode
import no.anagnosis.prefs.ReaderSettings

@Composable
fun OptionsDialog(
    settings: ReaderSettings,
    onChange: (ReaderSettings) -> Unit,
    onHelp: () -> Unit,
    onAbout: () -> Unit,
    onDismiss: () -> Unit,
    dictionaries: List<Pair<String, String>> = emptyList(),
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Options") },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        dismissButton = {
            Row {
                TextButton(onClick = onHelp) { Text("Help") }
                TextButton(onClick = onAbout) { Text("About") }
            }
        },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text("Font", style = MaterialTheme.typography.labelLarge)
                for (font in FontChoice.entries) {
                    Row(
                        Modifier.fillMaxWidth().clickable { onChange(settings.copy(font = font)) },
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = settings.font == font, onClick = { onChange(settings.copy(font = font)) })
                        Text("${font.label}  ·  ἀλλ᾽ εἰ μὲν οὖν", fontFamily = font.family(), fontSize = 16.sp)
                    }
                }
                Spacer(Modifier.height(12.dp))
                Text("Text size  ·  ${settings.fontSize}", style = MaterialTheme.typography.labelLarge)
                Slider(
                    value = settings.fontSize.toFloat(),
                    onValueChange = { onChange(settings.copy(fontSize = it.toInt())) },
                    valueRange = ReaderSettings.MIN_SIZE.toFloat()..ReaderSettings.MAX_SIZE.toFloat(),
                    steps = ReaderSettings.MAX_SIZE - ReaderSettings.MIN_SIZE - 1,
                )
                Spacer(Modifier.height(8.dp))
                Text("Line numbers", style = MaterialTheme.typography.labelLarge)
                SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth().padding(top = 6.dp, bottom = 12.dp)) {
                    LineNumberMode.entries.forEachIndexed { i, m ->
                        SegmentedButton(
                            selected = settings.lineNumbers == m,
                            onClick = { onChange(settings.copy(lineNumbers = m)) },
                            shape = SegmentedButtonDefaults.itemShape(i, LineNumberMode.entries.size),
                            label = { Text(m.label, fontSize = 13.sp) },
                        )
                    }
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(fitTranslation = !settings.fitTranslation)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Shorten Greek pages, so the translation fits on one page", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.fitTranslation, onCheckedChange = { onChange(settings.copy(fitTranslation = it)) })
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(wordFunction = !settings.wordFunction)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Name a word's function in its sentence when tapped", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.wordFunction, onCheckedChange = { onChange(settings.copy(wordFunction = it)) })
                }
                Spacer(Modifier.height(8.dp))
                Text("Notes", style = MaterialTheme.typography.labelLarge)
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(noteMarks = !settings.noteMarks)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Underline passages that have a note", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.noteMarks, onCheckedChange = { onChange(settings.copy(noteMarks = it)) })
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(noteTicks = !settings.noteTicks)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Mark pages with notes on the progress bar", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.noteTicks, onCheckedChange = { onChange(settings.copy(noteTicks = it)) })
                }
                if (dictionaries.isNotEmpty()) {
                    Spacer(Modifier.height(8.dp))
                    Text("Dictionaries", style = MaterialTheme.typography.labelLarge)
                    for ((slug, title) in dictionaries) {
                        val on = slug !in settings.disabledDictionaries
                        fun toggle(enable: Boolean) = onChange(settings.copy(
                            disabledDictionaries = if (enable) settings.disabledDictionaries - slug else settings.disabledDictionaries + slug,
                        ))
                        Row(Modifier.fillMaxWidth().clickable { toggle(!on) }, verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f).padding(vertical = 4.dp)) {
                                Text(Dictionaries.label(slug, title), style = MaterialTheme.typography.bodyMedium)
                                Text(title, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            Switch(checked = on, onCheckedChange = { toggle(it) })
                        }
                    }
                }
                Spacer(Modifier.height(8.dp))
                Text("Colours", style = MaterialTheme.typography.labelLarge)
                Row(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    for (theme in ColorTheme.entries) {
                        val bg = if (theme == ColorTheme.SYSTEM) MaterialTheme.colorScheme.background else Color(theme.background)
                        val fg = if (theme == ColorTheme.SYSTEM) MaterialTheme.colorScheme.onBackground else Color(theme.text)
                        val selected = settings.theme == theme
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Box(
                                Modifier
                                    .size(40.dp)
                                    .clip(CircleShape)
                                    .background(bg)
                                    .border(if (selected) 3.dp else 1.dp, if (selected) MaterialTheme.colorScheme.primary else fg, CircleShape)
                                    .clickable { onChange(settings.copy(theme = theme)) },
                                contentAlignment = Alignment.Center,
                            ) {
                                Text("α", color = fg, fontSize = 18.sp)
                            }
                            Text(theme.label, style = MaterialTheme.typography.labelSmall, modifier = Modifier.padding(top = 4.dp))
                        }
                    }
                }
            }
        },
    )
}

/** About the app as a whole: its licence, the shared dictionaries and the analyser, fonts and software. */
@Composable
fun AboutDialog(appVersion: String, credits: List<Credit>, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Anagnosis") },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text("Version $appVersion", style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(8.dp))
                Text(
                    "An app for reading ancient Greek texts, with dictionaries and morphological analysis, working offline. " +
                        "The app is free; each text, with its translation and commentary, is bought as an app of its own. " +
                        "The credits for a text are on its own page.",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(12.dp))
                Text("Licence", style = MaterialTheme.typography.labelLarge)
                Text(
                    "Copyright © 2026 Robert Emil Berge. The app is free software under the GNU General Public License, " +
                        "version 3 or later: you may use, study, share and modify it. The source code, the texts and the data " +
                        "are published at github.com/polemistes/anagnosis. It comes without any warranty. The name Anagnosis " +
                        "and the app icon are not covered by that licence.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(12.dp))
                Text("Dictionaries and data", style = MaterialTheme.typography.labelLarge)
                Text(
                    "The dictionaries in this app are derived from open data and are themselves published under the " +
                        "Creative Commons Attribution-ShareAlike 4.0 licence. They come from:",
                    style = MaterialTheme.typography.bodySmall,
                )
                CreditList(credits)
                Spacer(Modifier.height(6.dp))
                Text(
                    "The word analyser uses the Perseus treebanks and the Morpheus morphological analyser (Perseus Digital " +
                        "Library, Mozilla Public License 2.0), run over the Perseus Greek corpus. Perseus Digital Library " +
                        "materials are copyright Tufts University and are used under their Creative Commons Attribution-ShareAlike " +
                        "licences; the data has been reformatted and in places corrected for this app.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(12.dp))
                Text("Fonts", style = MaterialTheme.typography.labelLarge)
                Text(
                    "Gentium Plus (SIL International), Cardo (David J. Perry), GFS Didot and GFS Neohellenic (Greek Font " +
                        "Society), all under the SIL Open Font License 1.1.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(12.dp))
                Text("Software", style = MaterialTheme.typography.labelLarge)
                Text(
                    "Built with Kotlin Multiplatform, Jetpack Compose and Compose Multiplatform (JetBrains, Google) and " +
                        "SQLDelight (Cash App), all under the Apache License 2.0. Icons from Material Icons (Google, Apache License 2.0).",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        },
    )
}

/** About one text: where its edition, translation, commentary, dictionaries and syntax come from. */
@Composable
fun TextAboutDialog(title: String, credits: List<Credit>, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text(
                    "The text, translation, commentary and annotation are derived from open data and are themselves " +
                        "published under the Creative Commons Attribution-ShareAlike 4.0 licence; they have been reformatted " +
                        "and in places corrected for this app. They come from:",
                    style = MaterialTheme.typography.bodySmall,
                )
                CreditList(credits)
                Spacer(Modifier.height(12.dp))
                Text(
                    "The app itself, its dictionaries and the word analyser are credited under About and credits on the front page.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        },
    )
}

@Composable
private fun CreditList(credits: List<Credit>) {
    for (c in credits) {
        Spacer(Modifier.height(6.dp))
        Text(c.kind, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
        Text(c.title, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Medium)
        c.detail?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
        c.license?.let { Text("Licence: $it", style = MaterialTheme.typography.bodySmall) }
    }
}

/** Shown on the first launch and from Options > Help. */
@Composable
fun IntroDialog(onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Welcome to Anagnosis") },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text(
                    "Anagnosis is an app for reading ancient Greek texts. On its front page you can look up a headword " +
                        "in the dictionaries, or type an inflected form to see what it can be. Each text is bought as an app " +
                        "of its own and comes with an English translation, critical notes and, for most, a commentary, all " +
                        "available offline.",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(12.dp))
                HelpItem("Tap a word", "to see its dictionary form, its inflection and a short definition. The buttons below open the full entries of each dictionary that has the word: Middle Liddell and LSJ for every text, Abbott-Smith for New Testament words, Dodson with the New Testament, the text's own dictionary first. Dictionaries can be turned off in the options.")
                HelpItem("Press and hold a word", "to see the syntax of its sentence on a page of its own. Simple shows the sentence as an outline, one phrase per line in the order of the text, with its role after it (main verb, subject, object · dat., adverbial ...) and the verb in bold. Each clause is named (main clause, ὅτι clause, relative clause, infinitive, participle ...) with a note on what it belongs to, and has a bar down its left; a clause inside a clause is indented one step where it occurs, and the outer clause goes on below it. Drag and pinch to move and zoom, double tap to reset. Diagram shows every word with a line to each word that depends on it; drag and pinch to move and zoom, double tap to reset. Tree lists the same under one another with the full forms; […] stands for a word that is understood. Tap a word for its dictionary entry. In Plato the syntax is a parser's and not checked by hand, so it can be wrong.")
                HelpItem("Apparatus and Commentary", "at the bottom open the editor's critical notes or the commentary for all the lines on the page.")
                HelpItem("The pencil", "at the top starts a note of your own: tap the first and the last word of the passage, then write the note. The passage is underlined, and the page gets a mark on the bar at the bottom. Notes at the bottom opens the notes on the page and the list of all your notes in the text, from which you can go to a note or export them all to a file. The underline and the marks can be hidden in the options.")
                HelpItem("Swipe left or right", "to turn the page.")
                HelpItem("Press or slide on the bar at the bottom", "to go to any part of the text.")
                HelpItem("Greek / English", "at the top switches between the text and the translation.")
                HelpItem("Book", "at the top of an epic such as the Odyssey, or of the New Testament, chooses the book to read. Swiping past the last page of a book goes on to the next. In the New Testament the chapter's number stands in bold before its first verse and the verse numbers are raised; Line numbers None hides them.")
                HelpItem("Plato", "is cited by the pages of Stephanus's edition (1578) and their sections a–e, which the margin shows (172, b, c ...). Line numbers count the editor's lines within each section: 172a1 is the first line of 172a.")
                HelpItem("The i button", "at the top opens the edition's introduction, appendix or preface, where the text has them. The manuscripts and sigla are under Manuscripts in the Apparatus view.")
                HelpItem("The gear", "opens the options: font, text size, line numbers and colours. You can reopen this help there.")
            }
        },
    )
}

@Composable
private fun HelpItem(title: String, body: String) {
    Column(Modifier.padding(bottom = 10.dp)) {
        Text(title, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold)
        Text(body, style = MaterialTheme.typography.bodyMedium)
    }
}
