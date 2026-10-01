package no.anagnosis.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.TextMeasurer
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import no.anagnosis.data.Morphology
import no.anagnosis.data.Syntax
import no.anagnosis.data.SyntaxNode
import no.anagnosis.data.SyntaxTree

/** One colour per syntactic role, legible on the light and on the dark backgrounds. */
@Composable
fun rememberRoleColors(): Map<Syntax.Role, Color> {
    val dark = MaterialTheme.colorScheme.background.luminance() < 0.5f
    return remember(dark) { roleColors(dark) }
}

private fun roleColors(dark: Boolean): Map<Syntax.Role, Color> = if (dark) mapOf(
    Syntax.Role.PREDICATE to Color(0xFFFF8A80),
    Syntax.Role.SUBJECT to Color(0xFF82B1FF),
    Syntax.Role.OBJECT to Color(0xFF9CCC65),
    Syntax.Role.ATTRIBUTE to Color(0xFFFFB74D),
    Syntax.Role.ADVERBIAL to Color(0xFFCE93D8),
    Syntax.Role.COMPLEMENT to Color(0xFF80CBC4),
) else mapOf(
    Syntax.Role.PREDICATE to Color(0xFFB3261E),
    Syntax.Role.SUBJECT to Color(0xFF1F5FBF),
    Syntax.Role.OBJECT to Color(0xFF2E7D32),
    Syntax.Role.ATTRIBUTE to Color(0xFFB26A00),
    Syntax.Role.ADVERBIAL to Color(0xFF7B1FA2),
    Syntax.Role.COMPLEMENT to Color(0xFF00796B),
)

private enum class SyntaxView(val label: String) { DIAGRAM("Diagram"), TREE("Tree") }

/**
 * The syntax of one sentence, as a page: the words in one row with their parts of speech,
 * coloured by role, and an arc from each word to the words that depend on it, on a canvas that
 * pans and zooms; or, with the toggle, the same as a tree. [label] names the sentence's lines.
 * Tapping a word opens its word sheet.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SyntaxScreen(tree: SyntaxTree, label: String, family: FontFamily, onWord: (Long) -> Unit, onBack: () -> Unit) {
    var view by remember { mutableStateOf(SyntaxView.DIAGRAM) }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(label.replaceFirstChar { it.uppercase() }, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back to the text") } },
                actions = {
                    SingleChoiceSegmentedButtonRow(Modifier.padding(end = 8.dp)) {
                        SyntaxView.entries.forEachIndexed { i, v ->
                            SegmentedButton(
                                selected = view == v,
                                onClick = { view = v },
                                shape = SegmentedButtonDefaults.itemShape(i, SyntaxView.entries.size),
                                label = { Text(v.label, fontSize = 13.sp) },
                            )
                        }
                    }
                },
            )
        },
    ) { padding ->
        Box(Modifier.padding(padding).fillMaxSize()) {
            when (view) {
                SyntaxView.DIAGRAM -> DependencyDiagram(tree, family, onWord, Modifier.fillMaxSize())
                SyntaxView.TREE -> Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 12.dp)) {
                    SyntaxTreeView(tree, family, onWord)
                    Spacer(Modifier.padding(bottom = 32.dp))
                }
            }
        }
    }
}

// ------------------------------------------------------------------ the diagram

private val SLOT_GAP = 12.dp
private val ARC_STEP = 16.dp
private val ARC_RADIUS = 7.dp
private val ARC_TIP = 3.dp      // the gap between an arc's foot and the word
private val ARROW = 5.dp
private val LABEL_PAD = 3.dp
private val CANVAS_MARGIN = 16.dp
private const val MIN_ZOOM = 0.4f
private const val MAX_ZOOM = 3f

private class DToken(val node: SyntaxNode, val form: TextLayoutResult, val pos: TextLayoutResult?, val left: Float, val width: Float) {
    val cx get() = left + width / 2
}

private class DArc(val x1: Float, val x2: Float, val level: Int, val arrowX: Float, val label: TextLayoutResult, val color: Color)

private class DRoot(val x: Float, val level: Int, val label: TextLayoutResult, val color: Color)

/** The whole sentence in one row: its tokens, arcs and roots, in the diagram's own coordinates. */
private class DiagramLayout(
    val tokens: List<DToken>, val arcs: List<DArc>, val roots: List<DRoot>,
    val wordTop: Float, val posTop: Float, val width: Float, val height: Float,
) {
    fun tokenAt(pos: Offset): DToken? {
        if (pos.y < wordTop || pos.y > height) return null
        return tokens.firstOrNull { pos.x >= it.left && pos.x < it.left + it.width }
    }
}

private class DiagramStyles(
    val word: TextStyle, val pos: TextStyle, val label: TextStyle,
    val roleColors: Map<Syntax.Role, Color>, val muted: Color, val text: Color, val arc: Color, val background: Color,
)

@Composable
private fun DependencyDiagram(tree: SyntaxTree, family: FontFamily, onWord: (Long) -> Unit, modifier: Modifier) {
    val measurer = rememberTextMeasurer()
    val density = LocalDensity.current
    val colors = MaterialTheme.colorScheme
    val roleColors = rememberRoleColors()
    val styles = remember(family, colors, roleColors) {
        DiagramStyles(
            word = TextStyle(fontFamily = family, fontSize = 16.sp),
            pos = TextStyle(fontSize = 10.sp),
            label = TextStyle(fontSize = 10.sp, fontWeight = FontWeight.Medium),
            roleColors = roleColors, muted = colors.onSurfaceVariant, text = colors.onSurface, arc = colors.outline, background = colors.background,
        )
    }
    val layout = remember(tree, styles) { layoutDiagram(tree, measurer, styles, with(density) { SLOT_GAP.toPx() }, with(density) { ARC_STEP.toPx() }) }
    BoxWithConstraints(modifier.background(colors.background).clipToBounds()) {
        val viewW = with(density) { maxWidth.toPx() }
        val viewH = with(density) { maxHeight.toPx() }
        val margin = with(density) { CANVAS_MARGIN.toPx() }
        // Opens at full size with the whole height in view and the start of the sentence at the left.
        fun initialZoom(): Float = minOf(1f, (viewH - 2 * margin) / layout.height).coerceIn(MIN_ZOOM, MAX_ZOOM)
        var zoom by remember(layout, viewW, viewH) { mutableStateOf(initialZoom()) }
        fun clampOffset(o: Offset, z: Float): Offset {
            val w = layout.width * z
            val h = layout.height * z
            // a diagram narrower than the view is centred; a wider one can be panned from end to end
            val x = if (w + 2 * margin <= viewW) (viewW - w) / 2 else o.x.coerceIn(viewW - w - margin, margin)
            val y = if (h + 2 * margin <= viewH) (viewH - h) / 2 else o.y.coerceIn(viewH - h - margin, margin)
            return Offset(x, y)
        }
        var offset by remember(layout, viewW, viewH) { mutableStateOf(clampOffset(Offset(margin, 0f), zoom)) }
        Canvas(
            Modifier.fillMaxSize()
                .pointerInput(layout) {
                    detectTransformGestures { centroid, pan, gestureZoom, _ ->
                        val newZoom = (zoom * gestureZoom).coerceIn(MIN_ZOOM, MAX_ZOOM)
                        // zoom about the fingers: the point under the centroid stays put
                        val scaled = (offset - centroid) * (newZoom / zoom) + centroid
                        zoom = newZoom
                        offset = clampOffset(scaled + pan, newZoom)
                    }
                }
                .pointerInput(layout) {
                    detectTapGestures(
                        onTap = { pos -> layout.tokenAt((pos - offset) / zoom)?.node?.token?.let { onWord(it.id) } },
                        onDoubleTap = { zoom = initialZoom(); offset = clampOffset(Offset(margin, 0f), zoom) },
                    )
                },
        ) {
            withTransform({ translate(offset.x, offset.y); scale(zoom, zoom, pivot = Offset.Zero) }) {
                drawDiagram(layout, styles)
            }
        }
    }
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawDiagram(layout: DiagramLayout, styles: DiagramStyles) {
    val step = ARC_STEP.toPx()
    val tip = ARC_TIP.toPx()
    val radius = ARC_RADIUS.toPx()
    val arrow = ARROW.toPx()
    val pad = LABEL_PAD.toPx()
    val stroke = Stroke(width = 1.dp.toPx())
    val foot = layout.wordTop - tip
    fun drawLabel(label: TextLayoutResult, cx: Float, cy: Float, color: Color) {
        val w = label.size.width + 2 * pad
        val h = label.size.height.toFloat()
        drawRect(styles.background, Offset(cx - w / 2, cy - h / 2), Size(w, h))
        drawText(label, color, Offset(cx - label.size.width / 2, cy - h / 2))
    }
    fun drawArrow(x: Float) {
        val head = Path().apply { moveTo(x, foot); lineTo(x - arrow / 2, foot - arrow); lineTo(x + arrow / 2, foot - arrow); close() }
        drawPath(head, styles.arc)
    }
    for (a in layout.arcs) {
        val y = layout.wordTop - a.level * step
        val r = minOf(radius, (a.x2 - a.x1) / 2)
        val path = Path().apply {
            moveTo(a.x1, foot); lineTo(a.x1, y + r); quadraticTo(a.x1, y, a.x1 + r, y)
            lineTo(a.x2 - r, y); quadraticTo(a.x2, y, a.x2, y + r); lineTo(a.x2, foot)
        }
        drawPath(path, styles.arc, style = stroke)
        drawArrow(a.arrowX)
        drawLabel(a.label, (a.x1 + a.x2) / 2, y, a.color)
    }
    for (root in layout.roots) {
        val y = layout.wordTop - root.level * step
        drawLine(styles.arc, Offset(root.x, y), Offset(root.x, foot), strokeWidth = stroke.width)
        drawArrow(root.x)
        drawLabel(root.label, root.x, y, root.color)
    }
    for (t in layout.tokens) {
        val color = if (t.node.artificial) styles.muted else Syntax.role(t.node.relation)?.let { styles.roleColors[it] } ?: styles.text
        drawText(t.form, color, Offset(t.cx - t.form.size.width / 2, layout.wordTop))
        t.pos?.let { drawText(it, styles.muted, Offset(t.cx - it.size.width / 2, layout.posTop)) }
    }
}

private fun layoutDiagram(tree: SyntaxTree, measurer: TextMeasurer, styles: DiagramStyles, gap: Float, step: Float): DiagramLayout {
    val nodes = diagramOrder(tree)
    // the words: each in a slot wide enough for the word and its part of speech
    val forms = nodes.map { n ->
        measurer.measure(Syntax.displayForm(n), if (n.artificial) styles.word.copy(fontStyle = FontStyle.Italic) else styles.word)
    }
    val poses = nodes.map { n -> Morphology.pos(n.postag).takeIf { it.isNotEmpty() }?.let { measurer.measure(it, styles.pos) } }
    val tokens = ArrayList<DToken>(nodes.size)
    var x = 0f
    for (i in nodes.indices) {
        val w = maxOf(forms[i].size.width, poses[i]?.size?.width ?: 0) + gap
        tokens += DToken(nodes[i], forms[i], poses[i], x, w)
        x += w
    }
    val width = x
    val index = nodes.withIndex().associate { (i, n) -> n.id to i }

    class Arc(val head: DToken, val dep: DToken, val label: TextLayoutResult, val color: Color)
    val arcs = mutableListOf<Arc>()
    val roots = mutableListOf<Triple<DToken, TextLayoutResult, Color>>()
    for (dep in tokens) {
        val color = Syntax.role(dep.node.relation)?.let { styles.roleColors[it] } ?: styles.muted
        val label = measurer.measure(Syntax.shortLabel(dep.node.relation), styles.label)
        val head = tree.headOf(dep.node)
        if (head == null) roots += Triple(dep, label, color) else arcs += Arc(tokens[index.getValue(head.id)], dep, label, color)
    }
    val levels = arcLevels(arcs.map { minOf(it.head.cx, it.dep.cx) to maxOf(it.head.cx, it.dep.cx) })
    val arcLevel = levels.maxOrNull() ?: 0
    val rootLevel = arcLevel + 1
    val top = if (roots.isNotEmpty()) rootLevel else arcLevel
    val labelHeight = measurer.measure("Xg", styles.label).size.height
    val wordTop = top * step + labelHeight / 2
    val posTop = wordTop + (forms.maxOfOrNull { it.size.height } ?: 0)
    val height = posTop + (poses.maxOfOrNull { it?.size?.height ?: 0 } ?: 0)
    return DiagramLayout(
        tokens,
        arcs.mapIndexed { i, a -> DArc(minOf(a.head.cx, a.dep.cx), maxOf(a.head.cx, a.dep.cx), levels[i], a.dep.cx, a.label, a.color) },
        roots.map { (t, label, color) -> DRoot(t.cx, rootLevel, label, color) },
        wordTop, posTop, width, height,
    )
}

/**
 * The nodes in the order they are drawn: the text's order, except that a node standing for an
 * omitted word goes just before its first dependent other than punctuation, where the word
 * would have been read, rather than at the end of the sentence where the treebank keeps it.
 */
private fun diagramOrder(tree: SyntaxTree): List<SyntaxNode> {
    val position = HashMap<SyntaxNode, Double>()
    for (n in tree.nodes) position[n] = n.id.toDouble()
    for (n in tree.nodes) {
        if (!n.artificial) continue
        val first = tree.children(n).filter { it.isWord || it.artificial }.minByOrNull { it.id } ?: continue
        position[n] = first.id - 0.5
    }
    return tree.nodes.sortedBy { position[it] }
}

// ------------------------------------------------------------------ the tree

private val TREE_INDENT = 14.dp

/** The sentence as an indented list: each word with its role spelt out and its full parse, under its head. */
@Composable
fun SyntaxTreeView(tree: SyntaxTree, family: FontFamily, onWord: (Long) -> Unit) {
    val roleColors = rememberRoleColors()
    val small = SpanStyle(fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    val wordStyle = TextStyle(fontFamily = family, fontSize = 15.sp, lineHeight = 21.sp)
    val guide = MaterialTheme.colorScheme.outlineVariant
    Column(Modifier.fillMaxWidth()) {
        for ((node, depth) in tree.flatten()) {
            val token = node.token
            val text = buildAnnotatedString {
                if (node.artificial) withStyle(SpanStyle(fontStyle = FontStyle.Italic)) { append(Syntax.displayForm(node)) }
                else append(Syntax.displayForm(node))
                val role = Syntax.describe(node.relation)
                if (role.isNotEmpty()) {
                    append("  ")
                    val colour = Syntax.role(node.relation)?.let { roleColors[it] }
                    withStyle(small.copy(fontWeight = FontWeight.SemiBold, color = colour ?: small.color)) { append(role) }
                }
                val morph = Morphology.short(node.postag)
                if (morph.isNotEmpty()) { append("  "); withStyle(small) { append(morph) } }
            }
            Row(
                Modifier.fillMaxWidth()
                    .then(if (token != null) Modifier.clickable { onWord(token.id) } else Modifier)
                    .drawBehind {
                        for (d in 0 until depth) {
                            val x = (TREE_INDENT * d).toPx() + 3.dp.toPx()
                            drawLine(guide, Offset(x, 0f), Offset(x, size.height), strokeWidth = 1.dp.toPx())
                        }
                    },
            ) {
                Spacer(Modifier.width(TREE_INDENT * depth))
                Text(text, style = wordStyle, color = MaterialTheme.colorScheme.onSurface, modifier = Modifier.padding(vertical = 1.dp))
            }
        }
    }
}
