package no.anagnosis.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalViewConfiguration
import androidx.compose.ui.platform.ViewConfiguration
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.onClick
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.text
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.intl.LocaleList
import androidx.compose.ui.unit.IntOffset
import no.anagnosis.db.Tokens
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/** Whether a screen reader (TalkBack) is running: explore by touch is on. */
@Composable
expect fun rememberScreenReaderActive(): Boolean

/** What a screen reader can do with a word of the text besides looking it up. */
enum class WordAction(val label: String) {
    READ_SENTENCE("Read the sentence aloud"),
    READ_FROM_HERE("Read aloud from here"),
    SYNTAX("Syntax of the sentence"),
    NOTE("Add a note on this word"),
    BOOKMARK("Bookmark this sentence"),
}

/**
 * The words of the text for a screen reader. Given by the reader while a screen reader runs, and
 * absent otherwise, so that sighted reading does no extra work: [lines] keeps each line one node
 * with an action per word (for braille displays); otherwise every word is a node of its own.
 */
class WordAccess(
    val lines: Boolean,
    val actions: List<WordAction>,
    val onWord: (Long) -> Unit,
    val onAction: (Tokens, WordAction) -> Unit,
)

val LocalWordAccess = compositionLocalOf<WordAccess?> { null }

/** Greek is marked as Greek (el) for the screen reader, which then picks a Greek voice when it has one. */
val GREEK_LOCALE = LocaleList("el")

fun greekText(s: String): AnnotatedString = AnnotatedString(s, spanStyle = SpanStyle(localeList = GREEK_LOCALE))

fun greekText(s: AnnotatedString): AnnotatedString =
    AnnotatedString.Builder(s).apply { addStyle(SpanStyle(localeList = GREEK_LOCALE), 0, s.length) }.toAnnotatedString()

private fun actionsFor(token: Tokens, access: WordAccess): List<CustomAccessibilityAction> =
    access.actions.map { a -> CustomAccessibilityAction(a.label) { access.onAction(token, a); true } }

/**
 * One node per word over a laid-out text: [words] are (start, end, token) offsets in it. A word
 * broken over two lines gets the node of its first part. Place it over the text, with the same origin.
 */
@Composable
fun WordNodes(layout: TextLayoutResult?, words: List<Triple<Int, Int, Tokens>>, access: WordAccess, modifier: Modifier = Modifier) {
    val l = layout ?: return
    val density = LocalDensity.current
    val length = l.layoutInput.text.length
    // A word is smaller than the usual minimum touch target, which would stretch its bounds over
    // the line below: the words keep their own bounds, so that exploring by touch finds the right one.
    val base = LocalViewConfiguration.current
    val exact = remember(base) { object : ViewConfiguration by base { override val minimumTouchTargetSize: DpSize get() = DpSize.Zero } }
    CompositionLocalProvider(LocalViewConfiguration provides exact) {
    Box(modifier) {
        for ((start, end, token) in words) {
            if (start < 0 || end <= start || end > length) continue
            val line = l.getLineForOffset(start)
            val left = l.getBoundingBox(start).left
            val right = if (l.getLineForOffset(end - 1) == line) l.getBoundingBox(end - 1).right else l.getLineRight(line)
            val x = min(left, right)
            val top = l.getLineTop(line)
            val w = max(1f, max(left, right) - x)
            val h = l.getLineBottom(line) - top
            with(density) {
                Box(
                    Modifier
                        .offset { IntOffset(x.roundToInt(), top.roundToInt()) }
                        .size(w.toDp(), h.toDp())
                        .semantics {
                            text = greekText(token.form)
                            role = Role.Button
                            onClick(label = "Look up") { access.onWord(token.id); true }
                            customActions = actionsFor(token, access)
                        },
                )
            }
        }
    }
    }
}

/** A line (or paragraph) as one node: a look-up action for each of its words, then the actions of its first word. */
fun Modifier.lineActions(tokens: List<Tokens>, access: WordAccess): Modifier = semantics {
    customActions = tokens.map { t -> CustomAccessibilityAction("Look up ${t.form}") { access.onWord(t.id); true } } +
        (tokens.firstOrNull()?.let { actionsFor(it, access) } ?: emptyList())
}
