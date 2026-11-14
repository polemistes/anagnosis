package no.anagnosis.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.ParagraphStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextIndent
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** The visual lines of a long head paragraph that stay visible while it is folded. */
const val FORMS_SHOWN_LINES = 10

/**
 * A head paragraph is folded only if folding hides at least this many lines: a fold that puts away
 * a line or two saves nothing and costs a tap. On a phone some 370 of LSJ's forms sections fold.
 */
const val FORMS_MIN_HIDDEN_LINES = 5

/** How far the lines of a forms section are indented after their first line. */
private val FORMS_INDENT = 14.sp

/**
 * An entry cut into its head paragraph and the paragraphs after it. [hasLineBreaks] tells that the
 * head is a forms section of several lines.
 */
data class EntryParts(val head: String, val rest: String, val hasLineBreaks: Boolean)

private val HEAD_PARAGRAPH = Regex("""^\s*<p class="head">.*?</p>""", RegexOption.DOT_MATCHES_ALL)
private val LINE_BREAK = Regex("""<br\s*/?>""", RegexOption.IGNORE_CASE)
private val FORMS_LABEL = Regex("""class="[^"]*\b(?:tns|voice)\b""")

/**
 * Cuts an entry after its head paragraph, or returns null when the head has nothing the forms
 * treatment would change (no line break, no tense or voice label): such an entry is drawn whole by
 * [HtmlText], as every entry of the other dictionaries is.
 */
fun splitEntry(html: String): EntryParts? {
    val match = HEAD_PARAGRAPH.find(html) ?: return null
    val head = match.value.trim()
    val hasLineBreaks = LINE_BREAK.containsMatchIn(head)
    if (!hasLineBreaks && !FORMS_LABEL.containsMatchIn(head)) return null
    return EntryParts(head, html.substring(match.range.last + 1).trim(), hasLineBreaks)
}

/** Whether a head of [lines] visual lines is long enough to be folded. */
fun foldable(lines: Int): Boolean = lines - FORMS_SHOWN_LINES >= FORMS_MIN_HIDDEN_LINES

/**
 * The most lines to draw of a head of [lines] visual lines: [FORMS_SHOWN_LINES] while it is folded,
 * otherwise no limit at all, so that a line count that is off by one can never cut a line off.
 */
fun formsMaxLines(lines: Int, open: Boolean): Int =
    if (foldable(lines) && !open) FORMS_SHOWN_LINES else Int.MAX_VALUE

/**
 * The text with a hanging indent: each of its lines (between line breaks) starts at the margin and
 * the rows it wraps onto are indented, so the label that opens a line stands out.
 */
private fun withHangingIndent(text: AnnotatedString): AnnotatedString = buildAnnotatedString {
    withStyle(ParagraphStyle(textIndent = TextIndent(firstLine = 0.sp, restLine = FORMS_INDENT))) { append(text) }
}

/**
 * A dictionary entry. The forms section that opens a long entry (the tenses and dialect forms of a
 * verb, the cases of a noun) is set apart: its tense and voice labels stand out, each of its lines
 * hangs from the left margin, and when it is long only its first lines show, with a control to
 * show the rest. The senses after it are drawn as by [HtmlText]; so is the whole entry when it has
 * no forms section.
 */
@Composable
fun DictionaryEntry(
    html: String,
    modifier: Modifier = Modifier,
    onGreekWord: ((String) -> Unit)? = null,
) {
    val parts = remember(html) { splitEntry(html) }
    if (parts == null) {
        HtmlText(html, modifier, onGreekWord = onGreekWord)
        return
    }
    val linkColor = MaterialTheme.colorScheme.primary
    val muted = MaterialTheme.colorScheme.outline
    val formsColor = MaterialTheme.colorScheme.tertiary
    val greekWords = onGreekWord != null
    val head = remember(parts.head, linkColor, muted, formsColor, greekWords) {
        val text = htmlToAnnotated(
            parts.head, linkColor = linkColor, onNoteLink = null, mutedColor = muted,
            greekWords = greekWords, formsColor = formsColor,
        )
        if (parts.hasLineBreaks) withHangingIndent(text) else text
    }
    var open by remember(html) { mutableStateOf(false) }
    val style = MaterialTheme.typography.bodyMedium
    val measurer = rememberTextMeasurer()
    // the lines are counted at the width the head will be drawn at, before anything is drawn, so
    // that a long head never shows whole for a frame and then folds
    BoxWithConstraints(modifier) {
        val width = constraints.maxWidth
        val lines = remember(head, style, measurer, width) {
            measurer.measure(head, style, constraints = Constraints(maxWidth = width)).lineCount
        }
        val canFold = foldable(lines)
        Column {
            AnnotatedText(head, onGreekWord = onGreekWord, maxLines = formsMaxLines(lines, open))
            if (canFold) {
                FoldControl(open) { open = !open }
            } else if (parts.rest.isNotEmpty()) {
                // the blank line that separates two paragraphs of an entry drawn whole
                val line = style.lineHeight
                Spacer(Modifier.height(with(LocalDensity.current) { if (line.isSp) line.toDp() else 20.dp }))
            }
            if (parts.rest.isNotEmpty()) HtmlText(parts.rest, onGreekWord = onGreekWord)
        }
    }
}

/** The quiet text button under a folded head; it is as high as a finger needs, and says what it does. */
@Composable
private fun FoldControl(open: Boolean, onToggle: () -> Unit) {
    Box(
        Modifier.clickable(role = Role.Button, onClick = onToggle).heightIn(min = 48.dp).padding(end = 16.dp),
        contentAlignment = Alignment.CenterStart,
    ) {
        Text(
            if (open) "Show fewer forms" else "Show all forms",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
        )
    }
}
