package no.anagnosis.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import no.anagnosis.speech.ReadAloud

/**
 * The play bar of reading aloud, above the progress bar: previous sentence, play or pause, next
 * sentence, the pronunciation, and a close button that stops the reading.
 */
@Composable
fun ReadAloudBar(readAloud: ReadAloud, label: String, onPlay: () -> Unit) {
    Surface(tonalElevation = 3.dp) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = { readAloud.previous() }, modifier = Modifier.semantics { contentDescription = "Previous sentence" }) {
                SkipIcon(forward = false, color = LocalContentColor.current)
            }
            if (readAloud.playing) {
                IconButton(onClick = { readAloud.pause() }, modifier = Modifier.semantics { contentDescription = "Pause" }) {
                    PauseIcon(LocalContentColor.current)
                }
            } else {
                IconButton(onClick = onPlay) { Icon(Icons.Filled.PlayArrow, contentDescription = "Read aloud") }
            }
            IconButton(onClick = { readAloud.next() }, modifier = Modifier.semantics { contentDescription = "Next sentence" }) {
                SkipIcon(forward = true, color = LocalContentColor.current)
            }
            Text(
                label,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f).padding(start = 8.dp),
            )
            IconButton(onClick = { readAloud.close() }) { Icon(Icons.Filled.Close, contentDescription = "Stop reading aloud") }
        }
    }
}

/** Two upright bars. */
@Composable
fun PauseIcon(color: Color) {
    Canvas(Modifier.size(24.dp)) {
        val w = size.width * 0.2f
        val top = size.height * 0.2f
        val bottom = size.height * 0.8f
        for (x in listOf(size.width * 0.32f, size.width * 0.68f)) {
            drawLine(color, Offset(x, top), Offset(x, bottom), strokeWidth = w)
        }
    }
}

/** A triangle against a bar: skip to the next (or previous) sentence. */
@Composable
fun SkipIcon(forward: Boolean, color: Color) {
    Canvas(Modifier.size(24.dp)) {
        val l = size.width * 0.25f
        val r = size.width * 0.72f
        val top = size.height * 0.25f
        val bottom = size.height * 0.75f
        val path = Path().apply {
            if (forward) { moveTo(l, top); lineTo(r, size.height / 2); lineTo(l, bottom) }
            else { moveTo(r, top); lineTo(l, size.height / 2); lineTo(r, bottom) }
            close()
        }
        drawPath(path, color)
        val barX = if (forward) size.width * 0.78f else size.width * 0.22f
        drawLine(color, Offset(barX, top), Offset(barX, bottom), strokeWidth = size.width * 0.09f)
    }
}

/** A loudspeaker with two sound waves. */
@Composable
fun SpeakerIcon(color: Color) {
    Canvas(Modifier.size(24.dp)) {
        val w = size.width
        val h = size.height
        val body = Path().apply {
            moveTo(w * 0.12f, h * 0.38f); lineTo(w * 0.3f, h * 0.38f); lineTo(w * 0.5f, h * 0.2f)
            lineTo(w * 0.5f, h * 0.8f); lineTo(w * 0.3f, h * 0.62f); lineTo(w * 0.12f, h * 0.62f); close()
        }
        drawPath(body, color)
        val stroke = Stroke(width = w * 0.07f, cap = StrokeCap.Round)
        for (r in listOf(0.16f, 0.3f)) {
            drawArc(color, startAngle = -50f, sweepAngle = 100f, useCenter = false,
                topLeft = Offset(w * 0.5f - w * r, h * 0.5f - h * r), size = androidx.compose.ui.geometry.Size(w * r * 2, h * r * 2), style = stroke)
        }
    }
}
