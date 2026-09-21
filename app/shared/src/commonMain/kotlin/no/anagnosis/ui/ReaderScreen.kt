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
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextIndent
import androidx.compose.ui.text.withLink
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
    data class Segment(val segment: Translation_segments) : ReaderRow {
        override val nInt get() = segment.from_n_int
    }
}

/** A laid-out row: its rendering height and, for Greek lines, whether the line number fits on the right. */
private class Measured(val row: ReaderRow, val height: Int, val numberFits: Boolean = false)

class Page(val rows: List<ReaderRow>, val numbers: Map<ReaderRow, String>, val firstN: Long, val lastN: Long)

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
    var showAbout by remember { mutableStateOf(false) }
    var selectedTokenId by remember { mutableStateOf<Long?>(null) }
    var wordInfo by remember { mutableStateOf<WordInfo?>(null) }
    var notesLine by remember { mutableStateOf<Lines?>(null) }
    var notes by remember { mutableStateOf<List<NoteInfo>>(emptyList()) }
    var pageNotesKind by remember { mutableStateOf<NoteKind?>(null) }
    var pageNotes by remember { mutableStateOf<List<NoteGroup>>(emptyList()) }

    val translation = data.translations.firstOrNull()
    val rows = remember(data, mode) { buildRows(data, mode, translation?.segments ?: emptyList()) }

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
                title = { Text(data.work.title, maxLines = 1) },
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
            val computed = remember(rows, widthPx, heightPx, styles, settings.lineNumbers) {
                paginate(rows, measurer, styles, widthPx - numberColumnPx, heightPx, density, settings.lineNumbers)
            }
            LaunchedEffect(computed) {
                pages = computed
                val target = computed.indexOfLast { it.firstN <= anchorN }.coerceAtLeast(0)
                pagerState.scrollToPage(target)
            }
            if (pages.isNotEmpty()) {
                HorizontalPager(state = pagerState, modifier = Modifier.fillMaxSize(), beyondViewportPageCount = 1) { index ->
                    val page = pages.getOrNull(index) ?: return@HorizontalPager
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
                                    numberColumn = numberColumn,
                                    data = data,
                                    styles = styles,
                                    onWord = { selectedTokenId = it },
                                    onLine = { notesLine = row.line },
                                )
                                is ReaderRow.Segment -> SegmentRow(row.segment, styles)
                            }
                        }
                    }
                }
            }
        }
    }

    wordInfo?.let { WordSheet(it, onDismiss = { selectedTokenId = null }) }
    pageNotesKind?.let { kind -> PageNotesSheet(kind, pageNotes, onDismiss = { pageNotesKind = null }) }
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

private fun buildRows(data: WorkData, mode: ViewMode, segments: List<Translation_segments>): List<ReaderRow> {
    val rows = mutableListOf<ReaderRow>()
    if (mode == ViewMode.TRANSLATION) {
        for (s in segments) {
            if (s.speech_start == 1L && s.speaker != null) rows += ReaderRow.Speaker(s.speaker, s.from_n_int)
            rows += ReaderRow.Segment(s)
        }
        return rows
    }
    for (line in data.lines) {
        data.sectionsByFirstLine[line.id]?.forEach { rows += ReaderRow.Section(it, line.n_int) }
        if (line.speech_start == 1L && line.speaker != null) rows += ReaderRow.Speaker(line.speaker, line.n_int)
        rows += ReaderRow.GreekLine(line)
    }
    return rows
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
): List<Page> {
    if (widthPx <= 0 || heightPx <= 0) return emptyList()
    fun Dp.px() = with(density) { roundToPx() }
    val textWidth = widthPx
    val constraints = Constraints(maxWidth = textWidth)
    val numberWidth = measurer.measure("0000", styles.number).size.width + NUMBER_GAP.px()

    val measured = rows.map { row ->
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
            is ReaderRow.Segment -> {
                val style = if (row.segment.kind == "stage") styles.stage else styles.translation
                Measured(row, measurer.measure(row.segment.text, style, constraints = constraints).size.height + SEGMENT_GAP.px())
            }
        }
    }

    // Line numbers on the right, only where the first line of the verse leaves room. In the
    // every-fifth mode a number that does not fit moves to the next line with room.
    val numbers = HashMap<ReaderRow, String>()
    var pending = false
    for (m in measured) {
        val row = m.row as? ReaderRow.GreekLine ?: continue
        when (numbering) {
            LineNumberMode.NONE -> {}
            LineNumberMode.ALL -> if (m.numberFits) numbers[row] = row.line.n
            LineNumberMode.FIFTH -> {
                if (row.line.n_int % 5 == 0L || row.line.n_sub.isNotEmpty()) pending = true
                if (pending && m.numberFits) {
                    numbers[row] = row.line.n
                    pending = false
                }
            }
        }
    }

    val pages = mutableListOf<Page>()
    var current = mutableListOf<ReaderRow>()
    var used = 0
    fun flush() {
        if (current.isEmpty()) return
        pages += Page(current, numbers, current.first().nInt, current.last().nInt)
        current = mutableListOf()
        used = 0
    }
    var i = 0
    while (i < measured.size) {
        val m = measured[i]
        // keep a heading together with the row that follows it
        val isHeading = m.row is ReaderRow.Section || m.row is ReaderRow.Speaker
        val needed = if (isHeading && i + 1 < measured.size) m.height + measured[i + 1].height else m.height
        if (current.isNotEmpty() && used + needed > heightPx) {
            flush()
            continue
        }
        current += m.row
        used += m.height
        i++
    }
    flush()
    return pages
}

/** "Prologue" when the section has a name; otherwise the kind and number, e.g. "Strophe 1". */
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

@Composable
private fun SegmentRow(segment: Translation_segments, styles: Styles) {
    val isStage = segment.kind == "stage"
    Text(
        text = segment.text,
        style = if (isStage) styles.stage else styles.translation,
        color = if (isStage) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.onBackground,
        modifier = Modifier.padding(bottom = SEGMENT_GAP),
    )
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
