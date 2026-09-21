package no.anagnosis.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.drag
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.TextMeasurer
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.BaselineShift
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextIndent
import androidx.compose.ui.text.withLink
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.NoteGroup
import no.anagnosis.data.NoteInfo
import no.anagnosis.data.NoteKind
import no.anagnosis.data.kind
import no.anagnosis.data.WordInfo
import no.anagnosis.data.WorkData
import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
import no.anagnosis.db.Translation_segments
import no.anagnosis.prefs.LineNumberMode
import no.anagnosis.prefs.ReaderSettings

enum class ViewMode(val label: String) { GREEK("Greek"), TRANSLATION("English") }

/** One row of the reader. `nInt` is the Greek line number the row belongs to, for the progress bar. */
sealed interface ReaderRow {
    val nInt: Long

    data class Section(val section: Sections, override val nInt: Long) : ReaderRow
    data class Speaker(val name: String, override val nInt: Long) : ReaderRow
    data class GreekLine(val line: Lines) : ReaderRow {
        override val nInt get() = line.n_int
    }
}

/** A laid-out row: its rendering height and, for Greek lines, whether the line number fits on the right. */
private class Measured(val row: ReaderRow, val height: Int, val numberFits: Boolean = false)

class Page(val rows: List<ReaderRow>, val numbers: Map<ReaderRow, String>, val forced: Set<ReaderRow>, val firstN: Long, val lastN: Long)

private class Styles(
    val section: TextStyle,
    val subsection: TextStyle,
    val speaker: TextStyle,
    val greek: TextStyle,
    val translation: TextStyle,
    val stage: TextStyle,
    val number: TextStyle,
)

private val SECTION_TOP = 16.dp
private val SUBSECTION_TOP = 8.dp
private val SPEAKER_TOP = 10.dp
private val ROW_GAP = 2.dp
private val SEGMENT_GAP = 6.dp
private val NUMBER_GAP = 12.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReaderScreen(
    repository: AnagnosisRepository,
    data: WorkData,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    onHelp: () -> Unit,
    appVersion: String,
) {
    var mode by remember { mutableStateOf(ViewMode.GREEK) }
    var showOptions by remember { mutableStateOf(false) }
    var showDocuments by remember { mutableStateOf(false) }
    var openDocument by remember { mutableStateOf<String?>(null) }
    var showAbout by remember { mutableStateOf(false) }
    var selectedTokenId by remember { mutableStateOf<Long?>(null) }
    var wordInfo by remember { mutableStateOf<WordInfo?>(null) }
    var notesLine by remember { mutableStateOf<Lines?>(null) }
    var notes by remember { mutableStateOf<List<NoteInfo>>(emptyList()) }
    var pageNotesKind by remember { mutableStateOf<NoteKind?>(null) }
    var pageNotes by remember { mutableStateOf<List<NoteGroup>>(emptyList()) }

    val translation = data.translations.firstOrNull()
    val rows = remember(data) { buildRows(data) }

    LaunchedEffect(selectedTokenId) {
        val id = selectedTokenId
        wordInfo = if (id == null) null else withContext(Dispatchers.Default) { repository.lookupWord(data, id) }
    }
    LaunchedEffect(notesLine) {
        val line = notesLine
        notes = if (line == null) emptyList() else withContext(Dispatchers.Default) { repository.notesForLine(data, line) }
        if (line != null && notes.isEmpty()) notesLine = null
    }

    val typography = MaterialTheme.typography
    val base = LocalTextStyle.current
    val family = settings.font.family()
    val size = settings.fontSize
    val styles = remember(typography, base, family, size) {
        Styles(
            section = base.merge(typography.titleLarge.copy(fontFamily = family, fontSize = (size + 5).sp, lineHeight = (size + 9).sp)),
            subsection = base.merge(typography.titleSmall.copy(fontFamily = family, fontSize = (size - 1).sp, lineHeight = (size + 3).sp)),
            speaker = base.merge(typography.titleMedium.copy(fontFamily = family, fontSize = size.sp, lineHeight = (size + 4).sp, fontWeight = FontWeight.SemiBold)),
            greek = base.merge(TextStyle(fontFamily = family, fontSize = size.sp, lineHeight = (size * 1.5f).sp, textIndent = TextIndent(restLine = 20.sp))),
            translation = base.merge(TextStyle(fontFamily = family, fontSize = (size - 1).sp, lineHeight = ((size - 1) * 1.5f).sp)),
            stage = base.merge(TextStyle(fontFamily = family, fontSize = (size - 2).sp, lineHeight = ((size - 2) * 1.4f).sp, fontStyle = FontStyle.Italic)),
            number = base.merge(typography.labelSmall),
        )
    }

    // Position to keep across re-pagination (rotation, mode change): the first Greek line on screen.
    var anchorN by remember { mutableStateOf(1L) }
    var pages by remember { mutableStateOf<List<Page>>(emptyList()) }
    val pagerState = rememberPagerState { pages.size }
    val scope = rememberCoroutineScope()

    // Scrubbing state for the progress bar
    var scrubPage by remember { mutableStateOf<Int?>(null) }
    var scrubOrigin by remember { mutableStateOf(0) }
    var scrubPopup by remember { mutableStateOf(false) }

    LaunchedEffect(pagerState, pages) {
        snapshotCurrentPage(pagerState.currentPage, pages)?.let { if (scrubPage == null) anchorN = it }
    }
    LaunchedEffect(pagerState.currentPage) {
        if (scrubPage == null) pages.getOrNull(pagerState.currentPage)?.let { anchorN = it.firstN }
    }
    LaunchedEffect(pageNotesKind, pagerState.currentPage) {
        val kind = pageNotesKind
        val page = pages.getOrNull(pagerState.currentPage)
        pageNotes = if (kind == null || page == null) emptyList() else withContext(Dispatchers.Default) {
            repository.notesForPage(data, page.firstN, page.lastN, kind)
        }
    }
    // Swiping while the Go here / Go back choice is showing counts as "Go here".
    LaunchedEffect(pagerState.isScrollInProgress, scrubPopup) {
        if (scrubPopup && pagerState.isScrollInProgress) {
            scrubPopup = false
            scrubPage = null
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(data.work.title, maxLines = 1, modifier = Modifier.clickable { showDocuments = true }) },
                actions = {
                    if (translation != null) {
                        SingleChoiceSegmentedButtonRow(Modifier.padding(end = 4.dp)) {
                            ViewMode.entries.forEachIndexed { i, m ->
                                SegmentedButton(
                                    selected = mode == m,
                                    onClick = { mode = m },
                                    shape = SegmentedButtonDefaults.itemShape(i, ViewMode.entries.size),
                                    label = { Text(m.label, fontSize = 13.sp) },
                                )
                            }
                        }
                    }
                    IconButton(onClick = { showOptions = true }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Options")
                    }
                },
            )
        },
        bottomBar = {
            ProgressScrubber(
                pages = pages,
                currentPage = scrubPage ?: pagerState.currentPage,
                scrubbing = scrubPage != null,
                popup = scrubPopup,
                noteKinds = data.commentaries.map { it.kind() }.distinct(),
                onNotes = { pageNotesKind = it },
                onScrub = { page ->
                    if (scrubPage == null) scrubOrigin = pagerState.currentPage
                    scrubPopup = false
                    scrubPage = page
                    scope.launch { pagerState.scrollToPage(page) }
                },
                onRelease = { scrubPopup = true },
                onGoHere = { scrubPopup = false; scrubPage = null },
                onGoBack = {
                    scrubPopup = false
                    scrubPage = null
                    scope.launch { pagerState.scrollToPage(scrubOrigin) }
                },
            )
        },
    ) { padding ->
        BoxWithConstraints(Modifier.padding(padding).fillMaxSize()) {
            val measurer = rememberTextMeasurer()
            val density = LocalDensity.current
            val horizontal = 20.dp
            val vertical = 12.dp
            val widthPx = with(density) { (maxWidth - horizontal * 2).roundToPx() }
            val heightPx = with(density) { (maxHeight - vertical * 2).roundToPx() }
            // With numbers on every line, reserve a column for them so the text wraps around it.
            val numberColumnPx = if (settings.lineNumbers == LineNumberMode.ALL) {
                measurer.measure("0000", styles.number).size.width + with(density) { NUMBER_GAP.roundToPx() }
            } else 0
            val numberColumn = with(density) { numberColumnPx.toDp() }
            val forcedColumn = with(density) { (measurer.measure("0000", styles.number).size.width + NUMBER_GAP.roundToPx()).toDp() }
            val computed = remember(rows, widthPx, heightPx, styles, settings.lineNumbers, settings.fitTranslation) {
                val enHeights = if (settings.fitTranslation && translation != null) {
                    translationHeights(translation.segments, data.lines, measurer, styles, widthPx, density)
                } else emptyMap()
                paginate(rows, measurer, styles, widthPx - numberColumnPx, heightPx, density, settings.lineNumbers, enHeights)
            }
            LaunchedEffect(computed) {
                pages = computed
                val target = computed.indexOfLast { it.firstN <= anchorN }.coerceAtLeast(0)
                pagerState.scrollToPage(target)
            }
            if (pages.isNotEmpty()) {
                val pageSegments = remember(pages, translation) { segmentsByPage(pages, translation?.segments ?: emptyList(), data.lines) }
                HorizontalPager(state = pagerState, modifier = Modifier.fillMaxSize(), beyondViewportPageCount = 1) { index ->
                    val page = pages.getOrNull(index) ?: return@HorizontalPager
                    if (mode == ViewMode.TRANSLATION) {
                        TranslationPage(pageSegments.getOrNull(index) ?: emptyList(), styles, Modifier.fillMaxSize().padding(horizontal = horizontal, vertical = vertical))
                        return@HorizontalPager
                    }
                    Column(Modifier.fillMaxSize().padding(horizontal = horizontal, vertical = vertical)) {
                        for (row in page.rows) {
                            when (row) {
                                is ReaderRow.Section -> SectionHeader(row.section, styles)
                                is ReaderRow.Speaker -> Text(
                                    row.name,
                                    style = styles.speaker,
                                    color = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.padding(top = SPEAKER_TOP, bottom = ROW_GAP),
                                )
                                is ReaderRow.GreekLine -> GreekLineRow(
                                    line = row.line,
                                    number = page.numbers[row],
                                    numberColumn = if (row in page.forced) forcedColumn else numberColumn,
                                    data = data,
                                    styles = styles,
                                    onWord = { selectedTokenId = it },
                                    onLine = { notesLine = row.line },
                                )
                            }
                        }
                    }
                }
            }
        }
    }

    wordInfo?.let { WordSheet(it, onDismiss = { selectedTokenId = null }) }
    pageNotesKind?.let { kind ->
        val sigla = remember(kind) { if (kind == NoteKind.APPARATUS) repository.document(data, "sigla") else null }
        PageNotesSheet(kind, pageNotes, sigla, onDismiss = { pageNotesKind = null })
    }
    if (showDocuments) {
        val docs = remember { repository.documents(data) }
        DocumentsSheet(docs, onOpen = { showDocuments = false; openDocument = it }, onDismiss = { showDocuments = false })
    }
    openDocument?.let { slug ->
        val doc = remember(slug) { repository.document(data, slug) }
        if (doc != null) DocumentSheet(doc, onDismiss = { openDocument = null }) else openDocument = null
    }
    if (showOptions) {
        OptionsDialog(
            settings, onSettingsChange,
            onHelp = { showOptions = false; onHelp() },
            onAbout = { showOptions = false; showAbout = true },
            onDismiss = { showOptions = false },
        )
    }
    if (showAbout) {
        val credits = remember { repository.credits() }
        AboutDialog(appVersion, credits, onDismiss = { showAbout = false })
    }
    val line = notesLine
    if (line != null && notes.isNotEmpty()) {
        NotesSheet(line, notes, onDismiss = { notesLine = null })
    }
}

private fun snapshotCurrentPage(index: Int, pages: List<Page>): Long? = pages.getOrNull(index)?.firstN

private fun buildRows(data: WorkData): List<ReaderRow> {
    val rows = mutableListOf<ReaderRow>()
    for (line in data.lines) {
        data.sectionsByFirstLine[line.id]?.forEach { rows += ReaderRow.Section(it, line.n_int) }
        if (line.speech_start == 1L && line.speaker != null) rows += ReaderRow.Speaker(line.speaker, line.n_int)
        rows += ReaderRow.GreekLine(line)
    }
    return rows
}

/**
 * The translation segments belonging to each Greek page: a segment goes with the page that
 * holds the first line at or after its anchor. English page N is thus the prose for Greek page N.
 */
private fun segmentsByPage(pages: List<Page>, segments: List<Translation_segments>, lines: List<Lines>): List<List<Translation_segments>> {
    val pageOfLine = HashMap<Long, Int>()
    pages.forEachIndexed { i, page -> page.rows.forEach { if (it is ReaderRow.GreekLine) pageOfLine[it.line.id] = i } }
    val out = List(pages.size) { mutableListOf<Translation_segments>() }
    if (pages.isEmpty()) return out
    for (seg in segments) {
        val line = lines.firstOrNull { it.n_int >= seg.from_n_int } ?: lines.last()
        out[pageOfLine[line.id] ?: (pages.size - 1)] += seg
    }
    return out
}

/** Measure every row at the given width, assign line numbers, and cut the list into pages. */
private fun paginate(
    rows: List<ReaderRow>,
    measurer: TextMeasurer,
    styles: Styles,
    widthPx: Int,
    heightPx: Int,
    density: androidx.compose.ui.unit.Density,
    numbering: LineNumberMode,
    translationHeights: Map<Long, Int> = emptyMap(),
): List<Page> {
    if (widthPx <= 0 || heightPx <= 0) return emptyList()
    fun Dp.px() = with(density) { roundToPx() }
    val textWidth = widthPx
    val constraints = Constraints(maxWidth = textWidth)
    val numberWidth = measurer.measure("0000", styles.number).size.width + NUMBER_GAP.px()

    val measured: MutableList<Measured> = rows.map { row ->
        when (row) {
            is ReaderRow.Section -> {
                val top = if (row.section.level <= 1L) SECTION_TOP else SUBSECTION_TOP
                val style = if (row.section.level <= 1L) styles.section else styles.subsection
                Measured(row, measurer.measure(sectionLabel(row.section), style, constraints = constraints).size.height + top.px() + ROW_GAP.px())
            }
            is ReaderRow.Speaker ->
                Measured(row, measurer.measure(row.name, styles.speaker, constraints = constraints).size.height + SPEAKER_TOP.px() + ROW_GAP.px())
            is ReaderRow.GreekLine -> {
                val layout = measurer.measure(row.line.text, styles.greek, constraints = constraints)
                // In the all-lines mode the caller has already reserved a column for the numbers.
                val fits = numbering == LineNumberMode.ALL || textWidth - layout.getLineRight(0) >= numberWidth
                Measured(row, layout.size.height, fits)
            }
        }
    }.toMutableList()

    // Line numbers on the right. Every-fifth mode: the number goes on its own line if the first
    // line of the verse leaves room, else on the following line, else on the preceding one
    // (each showing its own number), else on its own line, which is re-wrapped around it.
    val numbers = HashMap<ReaderRow, String>()
    val forced = HashSet<ReaderRow>()
    val greekIdx = measured.withIndex().filter { it.value.row is ReaderRow.GreekLine }.map { it.index }
    fun lineAt(k: Int) = measured[greekIdx[k]].row as ReaderRow.GreekLine
    fun fitsAt(k: Int) = measured[greekIdx[k]].numberFits
    for ((k, i) in greekIdx.withIndex()) {
        val row = lineAt(k)
        when (numbering) {
            LineNumberMode.NONE -> {}
            LineNumberMode.ALL -> if (measured[i].numberFits) numbers[row] = row.line.n
            LineNumberMode.FIFTH -> {
                val isTarget = row.line.n_int % 5 == 0L || row.line.n_sub.isNotEmpty()
                if (!isTarget) continue
                when {
                    fitsAt(k) -> numbers[row] = row.line.n
                    k + 1 < greekIdx.size && fitsAt(k + 1) && lineAt(k + 1) !in numbers -> numbers[lineAt(k + 1)] = lineAt(k + 1).line.n
                    k > 0 && fitsAt(k - 1) && lineAt(k - 1) !in numbers -> numbers[lineAt(k - 1)] = lineAt(k - 1).line.n
                    else -> { numbers[row] = row.line.n; forced += row }
                }
            }
        }
    }
    // Lines that must make room for a forced number are laid out narrower.
    for (i in greekIdx) {
        val row = measured[i].row
        if (row in forced) {
            val layout = measurer.measure((row as ReaderRow.GreekLine).line.text, styles.greek, constraints = Constraints(maxWidth = textWidth - numberWidth))
            measured[i] = Measured(row, layout.size.height, true)
        }
    }

    val pages = mutableListOf<Page>()
    var current = mutableListOf<ReaderRow>()
    var used = 0
    fun flush() {
        if (current.isEmpty()) return
        pages += Page(current, numbers, forced, current.first().nInt, current.last().nInt)
        current = mutableListOf()
        used = 0
    }
    var usedEn = 0  // height of the translation anchored to the lines on the page so far
    fun enHeight(row: ReaderRow) = (row as? ReaderRow.GreekLine)?.let { translationHeights[it.line.id] } ?: 0
    fun flushAll() { flush(); usedEn = 0 }
    var i = 0
    while (i < measured.size) {
        val m = measured[i]
        // keep a heading together with the row that follows it
        val isHeading = m.row is ReaderRow.Section || m.row is ReaderRow.Speaker
        val needed = if (isHeading && i + 1 < measured.size) m.height + measured[i + 1].height else m.height
        val neededEn = enHeight(m.row) + (if (isHeading && i + 1 < measured.size) enHeight(measured[i + 1].row) else 0)
        if (current.isNotEmpty() && (used + needed > heightPx || usedEn + neededEn > heightPx)) {
            flushAll()
            continue
        }
        current += m.row
        used += m.height
        usedEn += enHeight(m.row)
        i++
    }
    flush()
    return pages
}

/** "Prologue" when the section has a name; otherwise the kind and number, e.g. "Strophe 1". */
/**
 * Height of the translation attached to each line (by line id). Speeches are measured as the
 * joined paragraphs they are displayed as, and the height is shared out among the speech's
 * segments in proportion to their length.
 */
private fun translationHeights(
    segments: List<Translation_segments>,
    lines: List<Lines>,
    measurer: TextMeasurer,
    styles: Styles,
    widthPx: Int,
    density: androidx.compose.ui.unit.Density,
): Map<Long, Int> {
    if (widthPx <= 0) return emptyMap()
    val constraints = Constraints(maxWidth = widthPx)
    val gap = with(density) { SEGMENT_GAP.roundToPx() }
    val speakerTop = with(density) { (SPEAKER_TOP + ROW_GAP).roundToPx() }
    val out = HashMap<Long, Int>()
    fun lineOf(seg: Translation_segments) = lines.firstOrNull { it.n_int >= seg.from_n_int } ?: lines.last()
    fun add(seg: Translation_segments, h: Int) {
        val id = lineOf(seg).id
        out[id] = (out[id] ?: 0) + h
    }
    var i = 0
    while (i < segments.size) {
        val seg = segments[i]
        if (seg.kind == "stage") {
            add(seg, measurer.measure(seg.text, styles.stage, constraints = constraints).size.height + gap)
            i++
            continue
        }
        var j = i + 1
        while (j < segments.size && segments[j].kind == "speech" && segments[j].speech_start == 0L) j++
        val group = segments.subList(i, j)
        // Each segment's height is the growth of the paragraph when the segment is appended.
        var previous = 0
        val prefix = StringBuilder()
        for ((k, g) in group.withIndex()) {
            if (k > 0) prefix.append(' ')
            prefix.append(g.from_n_int).append('\u2009').append(g.text)
            val h = measurer.measure(prefix.toString(), styles.translation, constraints = constraints).size.height
            add(g, h - previous + if (k == group.lastIndex) gap else 0)
            previous = h
        }
        if (seg.speech_start == 1L && seg.speaker != null) {
            add(seg, measurer.measure(seg.speaker, styles.speaker, constraints = constraints).size.height + speakerTop)
        }
        i = j
    }
    return out
}

private fun sectionLabel(section: Sections): String {
    val label = section.label
    if (!label.isNullOrBlank() && label.first().isLetter()) return label
    val kind = section.kind.replaceFirstChar { it.uppercase() }
    return listOfNotNull(kind, label?.takeIf { it.isNotBlank() }).joinToString(" ")
}

@Composable
private fun SectionHeader(section: Sections, styles: Styles) {
    val top = if (section.level <= 1L) SECTION_TOP else SUBSECTION_TOP
    Text(
        sectionLabel(section),
        style = if (section.level <= 1L) styles.section else styles.subsection,
        color = if (section.level <= 1L) MaterialTheme.colorScheme.onBackground else MaterialTheme.colorScheme.secondary,
        modifier = Modifier.padding(top = top, bottom = ROW_GAP),
    )
}

@Composable
private fun GreekLineRow(line: Lines, number: String?, numberColumn: Dp, data: WorkData, styles: Styles, onWord: (Long) -> Unit, onLine: () -> Unit) {
    val tokens = data.tokensByLine[line.id] ?: emptyList()
    val textColor = MaterialTheme.colorScheme.onBackground
    val annotated = remember(line.id, textColor) {
        buildAnnotatedString {
            var pos = 0
            for (t in tokens) {
                val start = t.start.toInt()
                val end = t.end.toInt()
                if (start > pos) append(line.text.substring(pos, start))
                withLink(
                    LinkAnnotation.Clickable(tag = "t:${t.id}", styles = TextLinkStyles(style = SpanStyle(color = textColor))) { onWord(t.id) }
                ) { append(line.text.substring(start, end)) }
                pos = end
            }
            if (pos < line.text.length) append(line.text.substring(pos))
        }
    }
    Box(Modifier.fillMaxWidth().clickable(onClick = onLine)) {
        Text(text = annotated, style = styles.greek, modifier = Modifier.fillMaxWidth().padding(end = numberColumn))
        if (number != null) {
            Text(
                number,
                style = styles.number,
                color = MaterialTheme.colorScheme.outline,
                modifier = Modifier.align(Alignment.TopEnd).padding(top = 5.dp),
            )
        }
    }
}

/**
 * Jebb's prose for one Greek page. Consecutive segments of the same speech are joined into
 * one paragraph; each segment's anchor line number is shown as a small raised figure.
 */
@Composable
private fun TranslationPage(segments: List<Translation_segments>, styles: Styles, modifier: Modifier) {
    val anchorStyle = SpanStyle(
        fontSize = 10.sp,
        color = MaterialTheme.colorScheme.outline,
        baselineShift = BaselineShift.Superscript,
    )
    Column(modifier.verticalScroll(rememberScrollState())) {
        var i = 0
        while (i < segments.size) {
            val seg = segments[i]
            if (seg.kind == "stage") {
                Text(seg.text, style = styles.stage, color = MaterialTheme.colorScheme.secondary, modifier = Modifier.padding(vertical = 6.dp))
                i++
                continue
            }
            // gather the rest of this speech
            var j = i + 1
            while (j < segments.size && segments[j].kind == "speech" && segments[j].speech_start == 0L) j++
            val group = segments.subList(i, j)
            if (seg.speech_start == 1L && seg.speaker != null) {
                Text(seg.speaker, style = styles.speaker, color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(top = SPEAKER_TOP, bottom = ROW_GAP))
            }
            val paragraph = buildAnnotatedString {
                group.forEachIndexed { k, g ->
                    if (k > 0) append(" ")
                    withStyle(anchorStyle) { append(g.from_n_int.toString()) }
                    append("\u2009")
                    append(g.text)
                }
            }
            Text(paragraph, style = styles.translation, color = MaterialTheme.colorScheme.onBackground, modifier = Modifier.padding(bottom = SEGMENT_GAP))
            i = j
        }
    }
}

/**
 * Bottom progress bar. Press or slide anywhere on it to preview that page (the reader follows);
 * on release a small popup offers to stay ("Go here") or return to the original page ("Go back").
 */
@Composable
private fun ProgressScrubber(
    pages: List<Page>,
    currentPage: Int,
    scrubbing: Boolean,
    popup: Boolean,
    noteKinds: List<NoteKind>,
    onNotes: (NoteKind) -> Unit,
    onScrub: (Int) -> Unit,
    onRelease: () -> Unit,
    onGoHere: () -> Unit,
    onGoBack: () -> Unit,
) {
    val count = pages.size
    val primary = MaterialTheme.colorScheme.primary
    val track = MaterialTheme.colorScheme.surfaceVariant
    Surface(color = MaterialTheme.colorScheme.surface) {
        Column(Modifier.fillMaxWidth().navigationBarsPadding().padding(bottom = 8.dp)) {
            Row(
                Modifier.fillMaxWidth().height(40.dp).padding(horizontal = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                val page = pages.getOrNull(currentPage)
                if (page != null && count > 0) {
                    val span = if (page.firstN == page.lastN) "Line ${page.firstN}" else "Lines ${page.firstN}–${page.lastN}"
                    Text(
                        span,
                        style = MaterialTheme.typography.labelMedium,
                        color = if (scrubbing || popup) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.outline,
                        modifier = Modifier.weight(1f),
                    )
                } else {
                    Spacer(Modifier.weight(1f))
                }
                if (popup) {
                    TextButton(onClick = onGoBack) { Text("Go back") }
                    TextButton(onClick = onGoHere) { Text("Go here") }
                } else {
                    for (kind in noteKinds) {
                        TextButton(onClick = { onNotes(kind) }) { Text(kind.label) }
                    }
                }
            }
            Canvas(
                Modifier.fillMaxWidth().height(28.dp).padding(horizontal = 16.dp).pointerInput(count) {
                    if (count == 0) return@pointerInput
                    fun pageAt(x: Float) = ((x / size.width) * count).toInt().coerceIn(0, count - 1)
                    awaitEachGesture {
                        val down = awaitFirstDown()
                        onScrub(pageAt(down.position.x))
                        drag(down.id) { change ->
                            onScrub(pageAt(change.position.x))
                            change.consume()
                        }
                        onRelease()
                    }
                },
            ) {
                val y = size.height / 2
                val stroke = 4.dp.toPx()
                drawLine(track, Offset(0f, y), Offset(size.width, y), strokeWidth = stroke)
                if (count > 0) {
                    val x = size.width * (currentPage + 1) / count
                    drawLine(primary, Offset(0f, y), Offset(x, y), strokeWidth = stroke)
                    drawCircle(primary, radius = if (scrubbing) 9.dp.toPx() else 6.dp.toPx(), center = Offset(x, y))
                }
            }
        }
    }
}
