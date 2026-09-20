package no.anagnosis.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration

/**
 * Renders the small HTML subset produced by the pipeline: p, br, b, i, span, a.
 * Links of the form href="note:123" call [onNoteLink] with the line number.
 */
@Composable
fun HtmlText(html: String, modifier: Modifier = Modifier, onNoteLink: ((String) -> Unit)? = null) {
    val linkColor = MaterialTheme.colorScheme.primary
    Text(
        text = htmlToAnnotated(html, linkColor = linkColor, onNoteLink = onNoteLink),
        modifier = modifier,
        style = MaterialTheme.typography.bodyMedium,
    )
}

private val TAG = Regex("<(/?)([a-zA-Z0-9]+)([^>]*)>")
private val HREF = Regex("href=\"([^\"]*)\"")
private val CLASS = Regex("class=\"([^\"]*)\"")

fun htmlToAnnotated(
    html: String,
    linkColor: Color,
    onNoteLink: ((String) -> Unit)?,
): AnnotatedString = buildAnnotatedString {
    var pos = 0
    var paragraphs = 0
    val styleStack = ArrayDeque<Int>() // number of pushed styles per open tag
    var pendingParagraphBreak = false

    fun appendText(raw: String) {
        if (raw.isEmpty()) return
        if (pendingParagraphBreak) {
            append("\n\n")
            pendingParagraphBreak = false
        }
        append(unescape(raw))
    }

    for (m in TAG.findAll(html)) {
        appendText(html.substring(pos, m.range.first))
        pos = m.range.last + 1
        val closing = m.groupValues[1] == "/"
        val tag = m.groupValues[2].lowercase()
        val attrs = m.groupValues[3]
        if (!closing) {
            var pushed = 0
            when (tag) {
                "p" -> {
                    if (paragraphs > 0) pendingParagraphBreak = true
                    paragraphs++
                }
                "br" -> append("\n")
                "b" -> { pushStyle(SpanStyle(fontWeight = FontWeight.Bold)); pushed++ }
                "i" -> { pushStyle(SpanStyle(fontStyle = FontStyle.Italic)); pushed++ }
                "span" -> {
                    val cls = CLASS.find(attrs)?.groupValues?.get(1) ?: ""
                    when {
                        "orth" in cls -> { pushStyle(SpanStyle(fontWeight = FontWeight.Bold)); pushed++ }
                        "tr" in cls -> { pushStyle(SpanStyle(fontStyle = FontStyle.Italic)); pushed++ }
                        "bibl" in cls || "usg" in cls -> {
                            pushStyle(SpanStyle(color = linkColor.copy(alpha = 0.75f))); pushed++
                        }
                    }
                }
                "a" -> {
                    val href = HREF.find(attrs)?.groupValues?.get(1) ?: ""
                    if (href.startsWith("note:") && onNoteLink != null) {
                        val target = href.removePrefix("note:")
                        pushLink(
                            LinkAnnotation.Clickable(
                                tag = href,
                                styles = TextLinkStyles(SpanStyle(color = linkColor, textDecoration = TextDecoration.Underline)),
                            ) { onNoteLink(target) }
                        )
                        pushed++
                    }
                }
            }
            if (tag != "br") styleStack.addLast(pushed)
        } else {
            val pushed = styleStack.removeLastOrNull() ?: 0
            repeat(pushed) { pop() }
        }
    }
    appendText(html.substring(pos))
}

private fun unescape(s: String): String = s
    .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"")
    .replace("&#39;", "'").replace("&apos;", "'").replace("&nbsp;", " ")
    .replace("&amp;", "&")
