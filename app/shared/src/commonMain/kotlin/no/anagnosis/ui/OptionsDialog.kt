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
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import no.anagnosis.data.Credit
import no.anagnosis.data.Dictionaries
import no.anagnosis.greek.InputScheme
import no.anagnosis.greek.Pronunciation
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import kotlin.math.roundToInt
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
    /** A screen reader runs: offer the two ways the text is given to it. */
    screenReader: Boolean = false,
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
                Text("Text size in dictionaries and notes  ·  ${settings.sheetFontSize}", style = MaterialTheme.typography.labelLarge)
                Text(
                    "Dictionary entries, commentary, critical apparatus, introductions and your own notes.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Slider(
                    value = settings.sheetFontSize.toFloat(),
                    onValueChange = { onChange(settings.copy(sheetFontSize = it.roundToInt())) },
                    valueRange = ReaderSettings.MIN_SHEET_SIZE.toFloat()..ReaderSettings.MAX_SHEET_SIZE.toFloat(),
                    steps = ReaderSettings.MAX_SHEET_SIZE - ReaderSettings.MIN_SHEET_SIZE - 1,
                )
                // a sample at the chosen size: the sheets are not in sight behind the dialog
                Text(
                    buildAnnotatedString {
                        withStyle(SpanStyle(fontWeight = FontWeight.Bold)) { append("λόγος") }
                        append(", ὁ, ")
                        withStyle(SpanStyle(fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.primary)) { append("computation, reckoning") }
                    },
                    fontSize = settings.sheetFontSize.sp,
                    lineHeight = (settings.sheetFontSize * 20f / 14f).sp,
                    modifier = Modifier.padding(bottom = 4.dp),
                )
                Spacer(Modifier.height(8.dp))
                Text("Line length  ·  ${settings.lineLength} characters", style = MaterialTheme.typography.labelLarge)
                Text(
                    "The widest the text is set, in characters of Greek at the chosen size; a phone's screen is mostly narrower. Lines of 50 to 75 characters read well, 60 to 66 best.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Slider(
                    value = settings.lineLength.toFloat(),
                    onValueChange = { onChange(settings.copy(lineLength = (it / ReaderSettings.LINE_LENGTH_STEP).roundToInt() * ReaderSettings.LINE_LENGTH_STEP)) },
                    valueRange = ReaderSettings.MIN_LINE_LENGTH.toFloat()..ReaderSettings.MAX_LINE_LENGTH.toFloat(),
                    steps = (ReaderSettings.MAX_LINE_LENGTH - ReaderSettings.MIN_LINE_LENGTH) / ReaderSettings.LINE_LENGTH_STEP - 1,
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
                Text("Notes and bookmarks", style = MaterialTheme.typography.labelLarge)
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(noteMarks = !settings.noteMarks)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Underline passages that have a note", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.noteMarks, onCheckedChange = { onChange(settings.copy(noteMarks = it)) })
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(noteTicks = !settings.noteTicks)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Mark pages with notes on the progress bar", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.noteTicks, onCheckedChange = { onChange(settings.copy(noteTicks = it)) })
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(bookmarkTicks = !settings.bookmarkTicks)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Mark bookmarked pages on the progress bar", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.bookmarkTicks, onCheckedChange = { onChange(settings.copy(bookmarkTicks = it)) })
                }
                Spacer(Modifier.height(8.dp))
                Text("Reading aloud", style = MaterialTheme.typography.labelLarge)
                // the text's own pronunciation (null) or one for every text
                val choices = listOf<Pronunciation?>(null) + Pronunciation.entries
                for (p in choices) {
                    Row(
                        Modifier.fillMaxWidth().clickable { onChange(settings.copy(pronunciation = p)) },
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = settings.pronunciation == p, onClick = { onChange(settings.copy(pronunciation = p)) })
                        Column(Modifier.padding(vertical = 4.dp)) {
                            Text(p?.label ?: "The text's own", style = MaterialTheme.typography.bodyMedium)
                            Text(
                                p?.description ?: "Homeric for Homer, Koine for the New Testament, Attic for the rest",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(sentenceMelody = !settings.sentenceMelody)) }, verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f).padding(vertical = 4.dp)) {
                        Text("Sentence melody", style = MaterialTheme.typography.bodyMedium)
                        Text(
                            "The voice sinks over each sentence, falls at its end and rises before a question mark; the accents keep their shapes. Homeric and Attic only.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Switch(checked = settings.sentenceMelody, onCheckedChange = { onChange(settings.copy(sentenceMelody = it)) })
                }
                Text("Voice", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 8.dp))
                SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth().padding(top = 6.dp, bottom = 4.dp)) {
                    listOf(false to "Man", true to "Woman").forEachIndexed { i, (female, label) ->
                        SegmentedButton(
                            selected = settings.femaleVoice == female,
                            onClick = { onChange(settings.copy(femaleVoice = female)) },
                            shape = SegmentedButtonDefaults.itemShape(i, 2),
                            label = { Text(label, fontSize = 13.sp) },
                        )
                    }
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(speakSpeakers = !settings.speakSpeakers)) }, verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f).padding(vertical = 4.dp)) {
                        Text("Say the speakers' names", style = MaterialTheme.typography.bodyMedium)
                        Text(
                            "In a play or a dialogue, the speaker's name before each speech, at another pitch.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Switch(checked = settings.speakSpeakers, onCheckedChange = { onChange(settings.copy(speakSpeakers = it)) })
                }
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(klattVoice = !settings.klattVoice)) }, verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f).padding(vertical = 4.dp)) {
                        Text("Klatt voice", style = MaterialTheme.typography.bodyMedium)
                        Text(
                            "A darker, softer sound from eSpeak's other synthesiser, a little less distinct. Worth trying with the man's voice; the woman's and the Koine are clearer without it.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    Switch(checked = settings.klattVoice, onCheckedChange = { onChange(settings.copy(klattVoice = it)) })
                }
                val speedLabel = if (settings.speechSpeed == 100) "standard" else "${settings.speechSpeed} % of standard"
                Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("Speed  ·  $speedLabel", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    if (settings.speechSpeed != 100) {
                        TextButton(onClick = { onChange(settings.copy(speechSpeed = 100)) }) { Text("Standard") }
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Slower", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Slider(
                        value = settings.speechSpeed.toFloat(),
                        onValueChange = { onChange(settings.copy(speechSpeed = (it / 10).roundToInt() * 10)) },
                        valueRange = ReaderSettings.MIN_SPEED.toFloat()..ReaderSettings.MAX_SPEED.toFloat(),
                        steps = (ReaderSettings.MAX_SPEED - ReaderSettings.MIN_SPEED) / 10 - 1,
                        modifier = Modifier.weight(1f).padding(horizontal = 8.dp).semantics { contentDescription = "Reading speed" },
                    )
                    Text("Faster", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                if (screenReader) {
                    Spacer(Modifier.height(8.dp))
                    Text("Screen reader", style = MaterialTheme.typography.labelLarge)
                    for ((lines, label, hint) in listOf(
                        Triple(false, "Word by word", "Each word of the text is a button that looks it up"),
                        Triple(true, "Whole lines", "Each line is read whole, with an action to look up each word; for braille displays"),
                    )) {
                        Row(
                            Modifier.fillMaxWidth().clickable { onChange(settings.copy(screenReaderLines = lines)) },
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            RadioButton(selected = settings.screenReaderLines == lines, onClick = { onChange(settings.copy(screenReaderLines = lines)) })
                            Column(Modifier.padding(vertical = 4.dp)) {
                                Text(label, style = MaterialTheme.typography.bodyMedium)
                                Text(hint, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
                Spacer(Modifier.height(8.dp))
                Text("Front page", style = MaterialTheme.typography.labelLarge)
                Row(Modifier.fillMaxWidth().clickable { onChange(settings.copy(showDescription = !settings.showDescription)) }, verticalAlignment = Alignment.CenterVertically) {
                    Text("Show the description of the app", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(checked = settings.showDescription, onCheckedChange = { onChange(settings.copy(showDescription = it)) })
                }
                Spacer(Modifier.height(8.dp))
                Text("Typing Greek with Latin letters", style = MaterialTheme.typography.labelLarge)
                for (scheme in InputScheme.entries) {
                    Row(
                        Modifier.fillMaxWidth().clickable { onChange(settings.copy(inputScheme = scheme)) },
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = settings.inputScheme == scheme, onClick = { onChange(settings.copy(inputScheme = scheme)) })
                        Column(Modifier.padding(vertical = 4.dp)) {
                            Text(scheme.label, style = MaterialTheme.typography.bodyMedium)
                            Text(scheme.hint, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
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
                        "The app is free; each text, with its translation and commentary, is bought in the app. " +
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
                Spacer(Modifier.height(6.dp))
                Text(
                    "The voice that reads the Greek aloud is eSpeak NG (github.com/espeak-ng/espeak-ng, GNU General Public " +
                        "License, version 3 or later), with an Ancient Greek phoneme table and pronunciation rules written for this app.",
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
                        "in the dictionaries, or type an inflected form to see what it can be. Each text is bought in the app, " +
                        "under Available texts, and comes with an English translation, a critical apparatus and, for most, a " +
                        "commentary, all available offline.",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(12.dp))
                HelpItem("Tap a word", "to see its dictionary form, its inflection and a short definition. The buttons below open the full entries of each dictionary that has the word: Middle Liddell and LSJ for every text, Abbott-Smith for New Testament words, Dodson with the New Testament, the text's own dictionary first. Dictionaries can be turned off in the options. A Greek word in an entry can be tapped to look it up in turn; back returns to the entry. Occurrences lists every place in the text where the word occurs, in any of its forms.")
                HelpItem("Search", "is on the front page, and in a text under the three-dot menu at the top right on a phone, the magnifying glass on a wider screen. Dictionary finds headwords. Analysis tells what a typed form can be. Text searches the texts themselves. Lemma finds every form of a word: type its dictionary form, choose it from the suggestions, and each place it occurs is listed. Tap a result to go there; the match is marked until you turn the page, and back returns to the results.")
                HelpItem("Typing Greek", "Latin letters type Greek by the scheme chosen in Options (q = θ, w = ω, c = ξ, y = ψ, h = η; or u = θ, v = ω, j = ξ, c = ψ); the line under the field shows the Greek they make. Breathings and accents need not be typed. The app's own Greek keyboard, the first choice under the sliders at the left of the field, has them: type a vowel, then its breathing and accent.")
                HelpItem("The sliders", "at the left of the field open the options of the search, which differ by mode. Dictionary: Greek → English, or English → Greek, which finds English words in Woodhouse's English-Greek Dictionary (P. marks a word used in prose, V. in verse, Ar. in Aristophanes; Woodhouse can be turned off under Dictionaries in Options). Analysis: Diacritics makes it heed the accents and breathings typed. Text: Latin letters type Greek, or search the English for what you type; Diacritics and Case make the search heed accents, breathings and capitals, which it otherwise ignores; Whole words matches only whole words; Regex takes a regular expression; Search in chooses the Greek, the translation, the commentaries and your own notes, and, when the search is opened from a text, that text or all your texts. The line under the field shows the Greek that Latin letters make and the choices that are on; in Text mode it always names what is searched (All sources when all four are).")
                HelpItem("Press and hold a word", "to see the syntax of its sentence on a page of its own. Simple shows the sentence as an outline, one phrase per line in the order of the text, with its role after it (main verb, subject, object · dat., adverbial ...) and the verb in bold. Each clause is named (main clause, ὅτι clause, relative clause, infinitive, participle ...) with a note on what it belongs to, and has a bar down its left; a clause inside a clause is indented one step where it occurs, and the outer clause goes on below it. Drag and pinch to move and zoom, double tap to reset. Diagram shows every word with a line to each word that depends on it; drag and pinch to move and zoom, double tap to reset. Tree lists the same under one another with the full forms; […] stands for a word that is understood. Tap a word for its dictionary entry. In Plato the syntax is a parser's and not checked by hand, so it can be wrong.")
                HelpItem("Read aloud", "reads the Greek from a word you choose: on a phone under the three-dot menu at the top right, on a wider screen the play button; then tap the word to begin at. The word being spoken is marked and the pages turn by themselves. In a play or a dialogue the speaker's name is said before each speech, at another pitch; this can be turned off in the options. The bar above the bottom one goes back or on a sentence, pauses and closes; play goes on where the reading was paused, or asks again where to begin. A change to the voice, the speed or the pronunciation in the options is heard at once. The word sheet's loudspeaker says the word alone, and the sheet shows the word in phonetic letters. The voice is a synthetic one and sounds mechanical, but every sound is distinct.")
                HelpItem("Three pronunciations", "can be chosen in the options, or each text read in its own: Homeric for Homer, the Ionic Greek of the epics as it is usually reconstructed; Attic for the rest, the Greek of Athens about 400 BC, with long and short vowels and a musical pitch accent (the voice rises on an acute, falls on a circumflex); Koine, the Hellenistic Greek of the New Testament about AD 100, with a stress accent and the vowels and fricatives that had changed by then. Vowel length of α, ι and υ, which the spelling does not show, comes from the Morpheus analyser where it knows the form; elsewhere they are read short. In the options you can also choose a man's or a woman's voice, the Klatt voice (eSpeak's other synthesiser: darker and softer, a little less distinct) and the speed: standard, or slower or faster than it. Sentence melody, off at first, lays a sentence tune over the pitch accent of Homeric and Attic: the voice sinks over each sentence, falls at a full stop and rises before a question mark.")
                HelpItem("With a screen reader", "such as TalkBack, every word of the text is a button: double tap to look it up, and the actions menu reads the sentence aloud, reads on from the word, shows the syntax, adds a note or bookmarks the sentence. For a braille display, choose Whole lines under Screen reader in the options: each line is then read whole, with an action to look up each of its words. The syntax page opens on the Tree view, which is text. The Greek is marked as Greek, so a screen reader with a Greek voice uses it; for the ancient pronunciation, use Read aloud.")
                HelpItem("Apparatus and Commentary", "at the bottom open the editor's critical apparatus or the commentary for all the lines on the page. On a phone, when Notes and Bookmarks stand beside them, they are shortened to App. and Comm. Where a text's only notes are a translator's notes to his translation, the button reads Translation notes (Tr. notes); where a text has both, a translator's notes are marked \"notes to the translation\".")
                HelpItem("The pencil", "at the top starts a note of your own: tap the first and the last word of the passage, then write the note. The passage is underlined, and the page gets a mark on the bar at the bottom. Tapping a word of the passage shows a Note button beside the dictionaries, which opens the note. Notes at the bottom opens the notes on the page and the list of all your notes in the text, from which you can go to a note or export them all to a file. The underline and the marks can be hidden in the options.")
                HelpItem("The bookmark", "beside the pencil bookmarks a sentence: tap it, then tap any word of the sentence, and give the bookmark a name if you like. The bookmark is filled when a bookmarked sentence starts on the page, and the page gets a small triangle on the bar at the bottom. Bookmarks at the bottom lists all your bookmarks in the text, those on the page highlighted; tap one to go to the page where its sentence starts, or its pencil to rename or delete it. Exporting your notes includes the bookmarks.")
                HelpItem("Swipe left or right", "to turn the page.")
                HelpItem("Press or slide on the bar at the bottom", "to go to any part of the text.")
                HelpItem("Greek / English", "at the top switches between the text and the translation; on a phone it is a single button that names the other: English on a Greek page, Greek on an English one. On a wide screen, or a phone held sideways, a third choice, Both, puts them side by side.")
                HelpItem("The title", "of an epic such as the Odyssey, or of the New Testament, shows the book being read; tap it to choose another book. Swiping past the last page of a book goes on to the next. In the New Testament the chapter's number stands in bold before its first verse and the verse numbers are raised; Line numbers None hides them.")
                HelpItem("Plato", "is cited by the pages of Stephanus's edition (1578) and their sections a–e, which the margin shows (172, b, c ...). Line numbers count the editor's lines within each section: 172a1 is the first line of 172a.")
                HelpItem("About this edition", "opens the edition's introduction, appendix or preface, where the text has them: on a phone under the three-dot menu at the top right, on a wider screen the i button. The manuscripts and sigla are under Manuscripts in the Apparatus view.")
                HelpItem("Options", "font, text size, line length (the widest the text is set, in characters, on a tablet), line numbers, notes and bookmarks, reading aloud, the Latin letters that type Greek in the search (q = θ or u = θ), dictionaries and colours: on the front page, and in a text on a phone under the three-dot menu, on a wider screen the gear. You can reopen this help there.")
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
