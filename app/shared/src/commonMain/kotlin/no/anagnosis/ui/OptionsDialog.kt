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

@Composable
fun AboutDialog(appVersion: String, credits: List<Credit>, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Anagnosis: Antigone") },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text("Version $appVersion", style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(8.dp))
                Text(
                    "A reader for Sophocles' Antigone in ancient Greek, with translation, commentary and dictionaries, working offline.",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(12.dp))
                Text("Licence", style = MaterialTheme.typography.labelLarge)
                Text(
                    "Copyright © 2026 Robert Emil Berge. The app is free software under the GNU General Public License, " +
                        "version 3 or later: you may use, study, share and modify it, and its source code is published at " +
                        "the project's repository. It comes without any warranty. The name Anagnosis and the app icon are " +
                        "not covered by that licence.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(12.dp))
                Text("Texts and data", style = MaterialTheme.typography.labelLarge)
                Text(
                    "The texts, translations, commentaries and dictionaries in this app are derived from open data and are " +
                        "themselves published under the Creative Commons Attribution-ShareAlike 4.0 licence. They come from:",
                    style = MaterialTheme.typography.bodySmall,
                )
                for (c in credits) {
                    Spacer(Modifier.height(6.dp))
                    Text(c.kind, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                    Text(c.title, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Medium)
                    c.detail?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                    c.license?.let { Text("Licence: $it", style = MaterialTheme.typography.bodySmall) }
                }
                Spacer(Modifier.height(6.dp))
                Text(
                    "Lemmas and morphology come from the Ancient Greek Dependency Treebank (Perseus Digital Library, " +
                        "CC BY-SA 3.0 US). Perseus Digital Library materials are copyright Tufts University and are used " +
                        "under their Creative Commons Attribution-ShareAlike licences; the data has been reformatted and in " +
                        "places corrected for this app.",
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
                        "SQLDelight (Cash App), all under the Apache License 2.0.",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        },
    )
}

/** Shown on the first launch and from Options > Help. */
@Composable
fun IntroDialog(onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Welcome to Anagnosis") },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Start reading") } },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text(
                    "Anagnosis is a reader for ancient Greek texts. This app contains Sophocles' Antigone " +
                        "with an English translation, a commentary and two dictionaries, all available offline.",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(12.dp))
                HelpItem("Tap a word", "to see its dictionary form, its inflection and a short definition. The LSJ and Middle Liddell buttons open the full dictionary entries.")
                HelpItem("Apparatus and Commentary", "at the bottom open Jebb's critical notes or his commentary for all the lines on the page. Tapping a line outside the words shows the notes for that line alone.")
                HelpItem("Swipe left or right", "to turn the page.")
                HelpItem("Press or slide on the bar at the bottom", "to look at any part of the text, then choose Go here or Go back.")
                HelpItem("Greek / English", "at the top switches between the text and the translation.")
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
