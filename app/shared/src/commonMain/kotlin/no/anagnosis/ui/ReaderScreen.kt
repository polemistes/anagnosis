package no.anagnosis.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.foundation.gestures.drag
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.platform.LocalFontFamilyResolver
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.TextMeasurer
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.BaselineShift
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.TextIndent
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.Morphology
import no.anagnosis.data.NoteGroup
import no.anagnosis.data.Syntax
import no.anagnosis.data.SyntaxNode
import no.anagnosis.data.NoteKind
import no.anagnosis.data.kind
import no.anagnosis.data.WordInfo
import no.anagnosis.data.WorkData
import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
import no.anagnosis.db.Tokens
import no.anagnosis.db.Translation_segments
import no.anagnosis.prefs.LineNumberMode
import no.anagnosis.prefs.ReaderSettings

/** What the page shows. `BOTH` (Greek and translation side by side) is offered on wide screens only. */
enum class ViewMode(val label: String) { GREEK("Greek"), TRANSLATION("English"), BOTH("Both") }

/** A text column is never wider than this: about 80 characters of prose, or the longest verse at the largest size. */
private val MAX_COLUMN = 580.dp
/** The space between the Greek and the translation when they are shown side by side. */
private val COLUMN_GAP = 40.dp
/** Windows at least this wide can show the two columns next to each other. */
private val WIDE = 840.dp

/** One row of the reader. `nInt` is the Greek line number the row belongs to, for the progress bar. */
sealed interface ReaderRow {
    val nInt: Long

    data class Section(val section: Sections, override val nInt: Long) : ReaderRow
    data class Speaker(val name: String, override val nInt: Long) : ReaderRow
    data class GreekLine(val line: Lines) : ReaderRow {
        override val nInt get() = line.n_int
    }
    /** Heads the syntax of a sentence, shown after the sentence's last line; `label` names its lines. */
    class SyntaxHeader(val sentence: String, val label: String, override val nInt: Long) : ReaderRow
    /** One node of a sentence's syntax tree, indented by its depth; `last` closes the tree. */
    class SyntaxLine(val sentence: String, val node: SyntaxNode, val depth: Int, val last: Boolean, override val nInt: Long) : ReaderRow
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
    /** A row of the syntax tree: the word in the text's font, a little smaller. */
    val syntaxWord: TextStyle,
    /** The role and the parse after the word, smaller and muted. */
    val syntaxSmall: SpanStyle,
    val syntaxHeader: TextStyle,
    /** The colour of each syntactic role, in the text and in the tree. */
    val roleColors: Map<Syntax.Role, Color>,
)

private val SECTION_TOP = 16.dp
private val SUBSECTION_TOP = 8.dp
private val SPEAKER_TOP = 10.dp
private val ROW_GAP = 2.dp
private val SEGMENT_GAP = 6.dp
private val NUMBER_GAP = 12.dp
private val SYNTAX_INDENT = 14.dp
private val SYNTAX_HEADER_TOP = 8.dp
private val SYNTAX_HEADER_HEIGHT = 28.dp
private val SYNTAX_BOTTOM = 8.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReaderScreen(
    repository: AnagnosisRepository,
    data: WorkData,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    onHelp: () -> Unit,
    onBack: () -> Unit,
    onHome: () -> Unit,
    onSearch: () -> Unit,
    startLine: Long,
    onPositionChange: (Long) -> Unit,
    appVersion: String,
) {
    // The reader's choice of view, or null for the default: both columns on a wide screen, else the Greek.
    var chosenMode by remember { mutableStateOf<ViewMode?>(null) }
    var showOptions by remember { mutableStateOf(false) }
    var showDocuments by remember { mutableStateOf(false) }
    var openDocument by remember { mutableStateOf<String?>(null) }
    var showAbout by remember { mutableStateOf(false) }
    var selectedTokenId by remember { mutableStateOf<Long?>(null) }
    var wordInfo by remember { mutableStateOf<WordInfo?>(null) }
    var pageNotesKind by remember { mutableStateOf<NoteKind?>(null) }
    var pageNotes by remember { mutableStateOf<List<NoteGroup>>(emptyList()) }

    val translation = data.translations.firstOrNull()
    val baseRows = remember(data) { buildRows(data) }
    // The sentences whose syntax is shown in the text, by treebank sentence id. The tree of a
    // sentence goes after its last line; its rows are built once and kept.
    var openSentences by remember(data) { mutableStateOf<Set<String>>(emptySet()) }
    val syntaxRowsCache = remember(data) { HashMap<String, List<ReaderRow>>() }
    val lastLineOfSentence = remember(data) { lastLines(data) }
    val rows = remember(baseRows, openSentences) {
        if (openSentences.isEmpty()) baseRows
        else withSyntax(baseRows, openSentences, lastLineOfSentence) { s -> syntaxRowsCache.getOrPut(s) { syntaxRows(data, repository, s) } }
    }
    fun toggleSentence(sentence: String) {
        openSentences = if (sentence in openSentences) openSentences - sentence else openSentences + sentence
    }
    val selectedToken = remember(selectedTokenId, data) {
        selectedTokenId?.let { id -> data.tokensByLine.values.asSequence().flatten().firstOrNull { it.id == id } }
    }

    LaunchedEffect(selectedTokenId) {
        val id = selectedTokenId
        wordInfo = if (id == null) null else withContext(Dispatchers.Default) { repository.lookupWord(data, id) }
    }

    val typography = MaterialTheme.typography
    val base = LocalTextStyle.current
    val colors = MaterialTheme.colorScheme
    val family = settings.font.family()
    val size = settings.fontSize
    val styles = remember(typography, base, colors, family, size) { stylesFor(typography, base, family, size, colors) }

    // Position to keep across re-pagination (rotation, mode change): the first Greek line on screen.
    var anchorN by remember { mutableStateOf(startLine) }
    // Pinch-to-zoom: the size being previewed while the fingers are down, or null.
    var pinchSize by remember { mutableStateOf<Float?>(null) }
    var pinchAnchorRow by remember { mutableStateOf<ReaderRow?>(null) }
    var pages by remember { mutableStateOf<List<Page>>(emptyList()) }
    val pagerState = rememberPagerState { pages.size }
    val scope = rememberCoroutineScope()

    // The page being previewed while a finger slides on the progress bar, or null.
    var scrubPage by remember { mutableStateOf<Int?>(null) }

    LaunchedEffect(pagerState.currentPage, pages) {  // also once the pages exist, so opening a text counts as reading it
        if (scrubPage == null) pages.getOrNull(pagerState.currentPage)?.let { anchorN = it.firstN; onPositionChange(it.firstN) }
    }
    LaunchedEffect(pageNotesKind, pagerState.currentPage) {
        val kind = pageNotesKind
        val page = pages.getOrNull(pagerState.currentPage)
        pageNotes = if (kind == null || page == null) emptyList() else withContext(Dispatchers.Default) {
            repository.notesForPage(data, page.firstN, page.lastN, kind)
        }
    }

    BoxWithConstraints(Modifier.fillMaxSize()) {
    val wide = translation != null && maxWidth >= WIDE
    val modes = if (wide) ViewMode.entries else ViewMode.entries.filter { it != ViewMode.BOTH }
    val mode = chosenMode?.takeIf { it in modes } ?: if (wide) ViewMode.BOTH else ViewMode.GREEK
    Scaffold(
        topBar = {
            // Two rows: the title with the way back and the way home, then the controls, so that
            // the title is never squeezed by the buttons on a narrow screen.
            Column(Modifier.background(MaterialTheme.colorScheme.surface)) {
                TopAppBar(
                    title = { Text(data.work.title, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.clickable { onBack() }) },
                    navigationIcon = {
                        IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back to the text's page") }
                    },
                    actions = {
                        IconButton(onClick = onHome) { Icon(Icons.Filled.Home, contentDescription = "Front page") }
                    },
                    windowInsets = TopAppBarDefaults.windowInsets,
                )
                Row(
                    Modifier.fillMaxWidth().padding(start = 12.dp, end = 4.dp, bottom = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    if (translation != null) {
                        SingleChoiceSegmentedButtonRow {
                            modes.forEachIndexed { i, m ->
                                SegmentedButton(
                                    selected = mode == m,
                                    onClick = { chosenMode = m },
                                    shape = SegmentedButtonDefaults.itemShape(i, modes.size),
                                    label = { Text(m.label, fontSize = 13.sp) },
                                )
                            }
                        }
                    }
                    Spacer(Modifier.weight(1f))
                    IconButton(onClick = onSearch) {
                        Icon(Icons.Filled.Search, contentDescription = "Dictionary")
                    }
                    IconButton(onClick = { showOptions = true }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Options")
                    }
                }
            }
        },
        bottomBar = {
            ProgressScrubber(
                pages = pages,
                currentPage = scrubPage ?: pagerState.currentPage,
                scrubbing = scrubPage != null,
                noteKinds = data.commentaries.map { it.kind() }.distinct(),
                onNotes = { pageNotesKind = it },
                onScrub = { page ->
                    scrubPage = page
                    scope.launch { pagerState.scrollToPage(page) }
                },
                onRelease = { scrubPage = null },
            )
        },
    ) { padding ->
        BoxWithConstraints(Modifier.padding(padding).fillMaxSize()) {
            val measurer = rememberTextMeasurer()
            val density = LocalDensity.current
            val horizontal = 20.dp
            val vertical = 12.dp
            // The text sits in a column of readable width, centred; side by side, each column gets half.
            val available = maxWidth - horizontal * 2
            val sideBySide = mode == ViewMode.BOTH
            val columnWidth = (if (sideBySide) (available - COLUMN_GAP) / 2 else available).coerceAtMost(MAX_COLUMN)
            val widthPx = with(density) { columnWidth.roundToPx() }
            val heightPx = with(density) { (maxHeight - vertical * 2).roundToPx() }
            // With numbers on every line, reserve a column for them so the text wraps around it.
            val numberColumnPx = if (settings.lineNumbers == LineNumberMode.ALL) {
                measurer.measure("0000", styles.number).size.width + with(density) { NUMBER_GAP.roundToPx() }
            } else 0
            val numberColumn = with(density) { numberColumnPx.toDp() }
            val forcedColumn = with(density) { (measurer.measure("0000", styles.number).size.width + NUMBER_GAP.roundToPx()).toDp() }
            // Pagination measures every line of the text, which takes seconds on a slow tablet, so it
            // runs off the main thread with its own measurer. Row heights are kept between runs that
            // share a width and style, so a rotation only has to cut the pages again.
            val fontResolver = LocalFontFamilyResolver.current
            val layoutDirection = LocalLayoutDirection.current
            val backgroundMeasurer = remember(fontResolver, density, layoutDirection) { TextMeasurer(fontResolver, density, layoutDirection, cacheSize = 0) }
            val measureCache = remember(data, styles, widthPx, numberColumnPx, settings.lineNumbers) { HashMap<ReaderRow, Measured>() }
            LaunchedEffect(rows, widthPx, heightPx, styles, settings.lineNumbers, settings.fitTranslation, numberColumnPx) {
                // after a pinch, the page the reader was previewing keeps its first row
                val anchorRow = pinchAnchorRow
                val anchorIndex = if (anchorRow != null) rows.indexOfFirst { it === anchorRow }.takeIf { it >= 0 } else null
                // the job works on its own copy of the cache: the shared one is touched on this thread only
                val cache = HashMap(measureCache)
                val computed = withContext(Dispatchers.Default) {
                    val enHeights = if (settings.fitTranslation && translation != null) {
                        translationHeights(translation.segments, data.lines, backgroundMeasurer, styles, widthPx, density)
                    } else emptyMap()
                    paginate(rows, backgroundMeasurer, styles, widthPx - numberColumnPx, heightPx, density, settings.lineNumbers, enHeights, anchorIndex, cache) { ensureActive() }
                }
                measureCache.putAll(cache)
                pages = computed
                pinchAnchorRow = null
                pinchSize = null  // a committed pinch keeps its preview on screen until here
                val byRow = if (anchorRow != null) computed.indexOfFirst { page -> page.rows.any { it === anchorRow } } else -1
                val target = if (byRow >= 0) byRow else computed.indexOfLast { it.firstN <= anchorN }.coerceAtLeast(0)
                pagerState.scrollToPage(target)
            }
            // Live preview during a pinch: only the current page, re-laid out at the previewed size.
            val previewStyles = pinchSize?.let { size -> stylesFor(typography, base, family, (size + 0.5f).toInt(), colors) }
            val previewPage = if (previewStyles != null && pages.isNotEmpty()) {
                val page = pages.getOrNull(pagerState.currentPage)
                val first = page?.rows?.firstOrNull()
                val startIdx = if (first != null) rows.indexOfFirst { it === first } else -1
                if (startIdx >= 0) {
                    val enHeights = if (settings.fitTranslation && translation != null) {
                        translationHeights(translation.segments, data.lines, measurer, previewStyles, widthPx, density)
                    } else emptyMap()
                    // only as many rows as could possibly fit on one page, so the preview stays cheap
                    val endIdx = minOf(rows.size, startIdx + 120)
                    paginate(rows.subList(startIdx, endIdx), measurer, previewStyles, widthPx - numberColumnPx, heightPx, density, settings.lineNumbers, enHeights).firstOrNull()
                } else null
            } else null
            // Two-finger pinch changes the text size; one finger is left to the pager. The page
            // content is a child of the pager, so it sees the pointers first and can claim them.
            val currentSize = rememberUpdatedState(settings.fontSize)
            val currentSettings = rememberUpdatedState(settings)
            val currentPages = rememberUpdatedState(pages)
            // The handler lives on a parent that stays in composition throughout the gesture and
            // watches the Initial pass, so two-finger events are taken before the pager sees them.
            val pinchModifier = Modifier.pointerInput(Unit) {
                awaitEachGesture {
                    awaitFirstDown(requireUnconsumed = false, pass = PointerEventPass.Initial)
                    var size = currentSize.value.toFloat()
                    var lastDistance = -1f
                    var pinched = false
                    while (true) {
                        val event = awaitPointerEvent(PointerEventPass.Initial)
                        val pressed = event.changes.filter { it.pressed }
                        if (pressed.isEmpty()) break
                        if (pressed.size >= 2) {
                            val distance = (pressed[0].position - pressed[1].position).getDistance()
                            if (lastDistance > 0f && distance > 0f) {
                                size = (size * distance / lastDistance).coerceIn(ReaderSettings.MIN_SIZE.toFloat(), ReaderSettings.MAX_SIZE.toFloat())
                                pinchSize = size
                                pinched = true
                            }
                            lastDistance = distance
                            event.changes.forEach { it.consume() }
                        } else if (pinched) {
                            event.changes.forEach { it.consume() }  // one finger lifted: keep the gesture until all are up
                        }
                    }
                    if (pinched) {
                        // commit: the previewed page keeps its first row after the full re-pagination
                        val page = currentPages.value.getOrNull(pagerState.currentPage)
                        pinchAnchorRow = page?.rows?.firstOrNull()
                        val rounded = (size + 0.5f).toInt()
                        val current = currentSettings.value
                        // the preview stays up while the pages are cut again at the new size
                        if (rounded != current.fontSize) onSettingsChange(current.copy(fontSize = rounded)) else pinchSize = null
                    }
                }
            }
            val showAnchors = settings.lineNumbers != LineNumberMode.NONE
            /** The page area: one centred column, or the Greek and the translation next to each other. */
            @Composable
            fun PageFrame(greek: @Composable () -> Unit, english: (@Composable () -> Unit)?, modifier: Modifier = Modifier) {
                Box(modifier.fillMaxSize().padding(horizontal = horizontal, vertical = vertical), contentAlignment = Alignment.TopCenter) {
                    if (sideBySide && english != null) {
                        Row(Modifier.fillMaxHeight()) {
                            Column(Modifier.width(columnWidth).fillMaxHeight()) { greek() }
                            Spacer(Modifier.width(COLUMN_GAP))
                            Column(Modifier.width(columnWidth).fillMaxHeight()) { english() }
                        }
                    } else {
                        Column(Modifier.width(columnWidth).fillMaxHeight()) { if (english != null && mode == ViewMode.TRANSLATION) english() else greek() }
                    }
                }
            }
            Box(Modifier.fillMaxSize().then(pinchModifier)) {
                if (pages.isEmpty()) {
                    CircularProgressIndicator(Modifier.align(Alignment.Center))
                }
                if (pages.isNotEmpty()) {
                    val pageSegments = remember(pages, translation) { segmentsByPage(pages, translation?.segments ?: emptyList(), data.lines) }
                    HorizontalPager(state = pagerState, modifier = Modifier.fillMaxSize(), beyondViewportPageCount = 1) { index ->
                        val page = pages.getOrNull(index) ?: return@HorizontalPager
                        PageFrame(
                            greek = {
                                PageContent(
                                    page, styles, data, numberColumn, forcedColumn, openSentences,
                                    onWord = { selectedTokenId = it },
                                    onSentence = { token -> token.sentence?.let { toggleSentence(it) } },
                                    onCloseSyntax = { toggleSentence(it) },
                                )
                            },
                            english = if (translation == null) null else {
                                { TranslationPage(pageSegments.getOrNull(index) ?: emptyList(), styles, showAnchors, Modifier.fillMaxSize()) }
                            },
                        )
                    }
                }
                if (previewPage != null && previewStyles != null) {
                    val previewSegments = if (sideBySide && translation != null) {
                        segmentsByPage(listOf(previewPage), translation.segments, data.lines).first()
                    } else emptyList()
                    PageFrame(
                        greek = { PageContent(previewPage, previewStyles, data, numberColumn, forcedColumn, openSentences, onWord = {}, onSentence = {}, onCloseSyntax = {}) },
                        english = if (translation == null) null else {
                            { TranslationPage(previewSegments, previewStyles, showAnchors, Modifier.fillMaxSize()) }
                        },
                        modifier = Modifier.background(MaterialTheme.colorScheme.background),
                    )
                }
            }
        }
    }
    }

    wordInfo?.let { info ->
        val sentence = selectedToken?.sentence
        WordSheet(
            info,
            onDismiss = { selectedTokenId = null },
            syntaxLabel = if (sentence in openSentences) "Hide syntax" else "Show syntax",
            onSyntax = if (sentence == null) null else { { toggleSentence(sentence); selectedTokenId = null } },
        )
    }
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
}

private fun buildRows(data: WorkData): List<ReaderRow> {
    val rows = mutableListOf<ReaderRow>()
    for (line in data.lines) {
        data.sectionsByFirstLine[line.id]?.forEach { rows += ReaderRow.Section(it, line.n_int) }
        if (line.speech_start == 1L && line.speaker != null) rows += ReaderRow.Speaker(line.speaker, line.n_int)
        rows += ReaderRow.GreekLine(line)
    }
    return rows
}

/** The id of the line each sentence ends on. */
private fun lastLines(data: WorkData): Map<String, Long> {
    val out = HashMap<String, Long>()
    for (line in data.lines) {
        for (t in data.tokensByLine[line.id] ?: emptyList()) t.sentence?.let { out[it] = line.id }
    }
    return out
}

/** The rows with the syntax of the open sentences inserted after each sentence's last line. */
private fun withSyntax(base: List<ReaderRow>, open: Set<String>, lastLine: Map<String, Long>, rowsFor: (String) -> List<ReaderRow>): List<ReaderRow> {
    val out = ArrayList<ReaderRow>(base.size + open.size * 24)
    for (row in base) {
        out += row
        if (row is ReaderRow.GreekLine) {
            // sentence ids number the sentences in order, so sorting them keeps the text's order
            for (s in open.filter { lastLine[it] == row.line.id }.sorted()) out += rowsFor(s)
        }
    }
    return out
}

/** The syntax rows of a sentence: a header naming its lines, then its tree, each head before its dependents. */
private fun syntaxRows(data: WorkData, repository: AnagnosisRepository, sentence: String): List<ReaderRow> {
    val tree = repository.sentenceTree(data, sentence)
    val linesById = data.lines.associateBy { it.id }
    val lines = tree.nodes.mapNotNull { it.token }.mapNotNull { linesById[it.line_id] }
    val first = lines.minByOrNull { it.ord } ?: return emptyList()
    val last = lines.maxBy { it.ord }
    val label = if (first.id == last.id) "line ${first.n}" else "lines ${first.n}–${last.n}"
    val flat = tree.flatten()
    val rows = ArrayList<ReaderRow>(flat.size + 1)
    rows += ReaderRow.SyntaxHeader(sentence, label, last.n_int)
    flat.forEachIndexed { i, (node, depth) -> rows += ReaderRow.SyntaxLine(sentence, node, depth, i == flat.lastIndex, last.n_int) }
    return rows
}

/** What a row of the tree says: the word, its role in colour, its parse in small muted type. */
private fun syntaxLineText(row: ReaderRow.SyntaxLine, styles: Styles): AnnotatedString = buildAnnotatedString {
    val node = row.node
    if (node.artificial) withStyle(SpanStyle(fontStyle = FontStyle.Italic)) { append(Syntax.displayForm(node)) }
    else append(Syntax.displayForm(node))
    val role = Syntax.describe(node.relation)
    if (role.isNotEmpty()) {
        append("  ")
        val colour = Syntax.role(node.relation)?.let { styles.roleColors[it] }
        withStyle(styles.syntaxSmall.copy(fontWeight = FontWeight.SemiBold, color = colour ?: styles.syntaxSmall.color)) { append(role) }
    }
    val morph = Morphology.short(node.postag)
    if (morph.isNotEmpty()) {
        append("  ")
        withStyle(styles.syntaxSmall) { append(morph) }
    }
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
    anchorIndex: Int? = null,
    cache: MutableMap<ReaderRow, Measured>? = null,
    checkActive: () -> Unit = {},
): List<Page> {
    if (widthPx <= 0 || heightPx <= 0) return emptyList()
    fun Dp.px() = with(density) { roundToPx() }
    val textWidth = widthPx
    val constraints = Constraints(maxWidth = textWidth)
    val numberWidth = measurer.measure("0000", styles.number).size.width + NUMBER_GAP.px()

    val measured: MutableList<Measured> = rows.map { row ->
        cache?.get(row) ?: run {
        checkActive()
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
            is ReaderRow.SyntaxHeader -> Measured(row, (SYNTAX_HEADER_TOP + SYNTAX_HEADER_HEIGHT).px())
            is ReaderRow.SyntaxLine -> {
                val indent = (SYNTAX_INDENT * row.depth).px()
                val layout = measurer.measure(syntaxLineText(row, styles), styles.syntaxWord, constraints = Constraints(maxWidth = (textWidth - indent).coerceAtLeast(1)))
                Measured(row, layout.size.height + if (row.last) SYNTAX_BOTTOM.px() else 0)
            }
        }.also { cache?.put(row, it) }
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

    fun enHeight(row: ReaderRow) = (row as? ReaderRow.GreekLine)?.let { translationHeights[it.line.id] } ?: 0
    fun isHeading(row: ReaderRow) = row is ReaderRow.Section || row is ReaderRow.Speaker || row is ReaderRow.SyntaxHeader

    /** Cuts rows[from until to) into pages from the front. */
    fun forward(from: Int, to: Int): List<List<ReaderRow>> {
        val pages = mutableListOf<List<ReaderRow>>()
        var current = mutableListOf<ReaderRow>()
        var used = 0
        var usedEn = 0
        var i = from
        while (i < to) {
            val m = measured[i]
            val heading = isHeading(m.row) && i + 1 < to
            val needed = if (heading) m.height + measured[i + 1].height else m.height
            val neededEn = enHeight(m.row) + (if (heading) enHeight(measured[i + 1].row) else 0)
            if (current.isNotEmpty() && (used + needed > heightPx || usedEn + neededEn > heightPx)) {
                pages += current; current = mutableListOf(); used = 0; usedEn = 0
                continue
            }
            current += m.row; used += m.height; usedEn += enHeight(m.row); i++
        }
        if (current.isNotEmpty()) pages += current
        return pages
    }

    /** Cuts rows[0 until to) into pages from the back, so that a page ends just before `to`. */
    fun backward(to: Int): List<List<ReaderRow>> {
        val pages = mutableListOf<List<ReaderRow>>()
        var current = ArrayDeque<ReaderRow>()
        var used = 0
        var usedEn = 0
        var i = to - 1
        while (i >= 0) {
            val m = measured[i]
            if (current.isNotEmpty() && (used + m.height > heightPx || usedEn + enHeight(m.row) > heightPx)) {
                pages += current.toList(); current = ArrayDeque(); used = 0; usedEn = 0
                continue
            }
            current.addFirst(m.row); used += m.height; usedEn += enHeight(m.row); i--
        }
        if (current.isNotEmpty()) pages += current.toList()
        pages.reverse()
        // a heading that ended up last on a page moves to the start of the following page
        for (k in 0 until pages.size - 1) {
            val page = pages[k].toMutableList()
            while (page.isNotEmpty() && isHeading(page.last())) {
                pages[k + 1] = listOf(page.removeAt(page.size - 1)) + pages[k + 1]
            }
            pages[k] = page
        }
        return pages.filter { it.isNotEmpty() }
    }

    val minFirst = heightPx / 3
    fun heightOf(rows: List<ReaderRow>) = rows.sumOf { r -> measured.first { it.row === r }.height }
    val chunks: List<List<ReaderRow>> = if (anchorIndex == null || anchorIndex <= 0 || anchorIndex >= measured.size) {
        forward(0, measured.size)
    } else {
        // pages after the anchor from the front, pages before it from the back
        var before = backward(anchorIndex)
        var after = forward(anchorIndex, measured.size)
        if (before.isNotEmpty() && heightOf(before.first()) < minFirst) {
            // a stub at the beginning looks wrong: cut the pages before the anchor from the front
            // instead and let the anchored page start a little earlier
            val fwd = forward(0, anchorIndex)
            val tail = fwd.last()
            before = fwd.dropLast(1)
            after = forward(anchorIndex - tail.size, measured.size)
        }
        before + after
    }
    return chunks.map { Page(it, numbers, forced, it.first().nInt, it.last().nInt) }
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

private fun stylesFor(typography: androidx.compose.material3.Typography, base: TextStyle, family: androidx.compose.ui.text.font.FontFamily, size: Int, colors: androidx.compose.material3.ColorScheme) = Styles(
    section = base.merge(typography.titleLarge.copy(fontFamily = family, fontSize = (size + 5).sp, lineHeight = (size + 9).sp)),
    subsection = base.merge(typography.titleSmall.copy(fontFamily = family, fontSize = (size - 1).sp, lineHeight = (size + 3).sp)),
    speaker = base.merge(typography.titleMedium.copy(fontFamily = family, fontSize = size.sp, lineHeight = (size + 4).sp, fontWeight = FontWeight.SemiBold)),
    greek = base.merge(TextStyle(fontFamily = family, fontSize = size.sp, lineHeight = (size * 1.5f).sp, textIndent = TextIndent(restLine = 20.sp))),
    translation = base.merge(TextStyle(fontFamily = family, fontSize = (size - 1).sp, lineHeight = ((size - 1) * 1.5f).sp)),
    stage = base.merge(TextStyle(fontFamily = family, fontSize = (size - 2).sp, lineHeight = ((size - 2) * 1.4f).sp, fontStyle = FontStyle.Italic)),
    number = base.merge(typography.labelSmall),
    syntaxWord = base.merge(TextStyle(fontFamily = family, fontSize = (size - 1).sp, lineHeight = ((size - 1) * 1.4f).sp)),
    syntaxSmall = SpanStyle(fontSize = (size - 4).sp, color = colors.onSurfaceVariant),
    syntaxHeader = base.merge(typography.labelMedium),
    roleColors = roleColors(dark = colors.background.luminance() < 0.5f),
)

/** One colour per syntactic role, legible on the light and on the dark backgrounds. */
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

@Composable
private fun PageContent(
    page: Page,
    styles: Styles,
    data: WorkData,
    numberColumn: Dp,
    forcedColumn: Dp,
    openSentences: Set<String>,
    onWord: (Long) -> Unit,
    onSentence: (Tokens) -> Unit,
    onCloseSyntax: (String) -> Unit,
) {
    for (row in page.rows) {
        when (row) {
            is ReaderRow.SyntaxHeader -> Row(
                Modifier.fillMaxWidth().padding(top = SYNTAX_HEADER_TOP, end = numberColumn).height(SYNTAX_HEADER_HEIGHT),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Syntax, ${row.label}", style = styles.syntaxHeader, color = MaterialTheme.colorScheme.primary, modifier = Modifier.weight(1f))
                Box(Modifier.size(SYNTAX_HEADER_HEIGHT).clickable { onCloseSyntax(row.sentence) }, contentAlignment = Alignment.Center) {
                    Icon(Icons.Filled.Close, contentDescription = "Hide the syntax", tint = MaterialTheme.colorScheme.outline, modifier = Modifier.size(18.dp))
                }
            }
            is ReaderRow.SyntaxLine -> {
                val token = row.node.token
                val guide = MaterialTheme.colorScheme.outlineVariant
                Row(
                    Modifier.fillMaxWidth().padding(end = numberColumn)
                        .then(if (token != null) Modifier.clickable { onWord(token.id) } else Modifier)
                        .padding(bottom = if (row.last) SYNTAX_BOTTOM else 0.dp)
                        .drawBehind {
                            // a rule down from each ancestor, so that the depth can be followed
                            for (d in 0 until row.depth) {
                                val x = (SYNTAX_INDENT * d).toPx() + 3.dp.toPx()
                                drawLine(guide, Offset(x, 0f), Offset(x, size.height), strokeWidth = 1.dp.toPx())
                            }
                        },
                ) {
                    Spacer(Modifier.width(SYNTAX_INDENT * row.depth))
                    Text(syntaxLineText(row, styles), style = styles.syntaxWord, color = MaterialTheme.colorScheme.onBackground, modifier = Modifier.weight(1f))
                }
            }
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
                openSentences = openSentences,
                onWord = onWord,
                onSentence = onSentence,
            )
        }
    }
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
private fun GreekLineRow(
    line: Lines,
    number: String?,
    numberColumn: Dp,
    data: WorkData,
    styles: Styles,
    openSentences: Set<String>,
    onWord: (Long) -> Unit,
    onSentence: (Tokens) -> Unit,
) {
    val tokens = data.tokensByLine[line.id] ?: emptyList()
    // One tap handler per line, which finds the word from the tap position, is far cheaper than
    // a clickable link per word: a page holds a few hundred words, and slow tablets feel it.
    var layout by remember { mutableStateOf<TextLayoutResult?>(null) }
    val currentOnWord = rememberUpdatedState(onWord)
    val currentOnSentence = rememberUpdatedState(onSentence)
    val haptic = LocalHapticFeedback.current
    // The words of a sentence whose syntax is shown take the colour of their role.
    val text = remember(line, tokens, openSentences, styles) {
        if (tokens.none { it.sentence in openSentences }) AnnotatedString(line.text) else buildAnnotatedString {
            append(line.text)
            for (t in tokens) {
                if (t.sentence !in openSentences) continue
                val colour = Syntax.role(t.relation)?.let { styles.roleColors[it] } ?: continue
                addStyle(SpanStyle(color = colour), t.start.toInt(), t.end.toInt())
            }
        }
    }
    Box(
        Modifier.fillMaxWidth().pointerInput(tokens) {
            fun tokenAt(pos: Offset): Tokens? {
                val result = layout ?: return null
                val lineIndex = result.getLineForVerticalPosition(pos.y)
                // a tap in the blank space to the right of the words is not a tap on a word
                if (pos.x > result.getLineRight(lineIndex) + 4.dp.toPx()) return null
                val offset = result.getOffsetForPosition(pos)
                return tokens.firstOrNull { offset >= it.start && offset < it.end }
            }
            detectTapGestures(
                onLongPress = { pos ->
                    tokenAt(pos)?.let {
                        haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                        currentOnSentence.value(it)
                    }
                },
                onTap = { pos -> tokenAt(pos)?.let { currentOnWord.value(it.id) } },
            )
        },
    ) {
        Text(text = text, style = styles.greek, onTextLayout = { layout = it }, modifier = Modifier.fillMaxWidth().padding(end = numberColumn))
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
private fun TranslationPage(segments: List<Translation_segments>, styles: Styles, showAnchors: Boolean, modifier: Modifier) {
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
                    if (showAnchors) {
                        withStyle(anchorStyle) { append(g.from_n_int.toString()) }
                        append("\u2009")
                    }
                    append(g.text)
                }
            }
            Text(paragraph, style = styles.translation, color = MaterialTheme.colorScheme.onBackground, modifier = Modifier.padding(bottom = SEGMENT_GAP))
            i = j
        }
    }
}

/** Bottom progress bar. Press or slide anywhere on it to go to that page; the reader follows the finger. */
@Composable
private fun ProgressScrubber(
    pages: List<Page>,
    currentPage: Int,
    scrubbing: Boolean,
    noteKinds: List<NoteKind>,
    onNotes: (NoteKind) -> Unit,
    onScrub: (Int) -> Unit,
    onRelease: () -> Unit,
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
                        color = if (scrubbing) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.outline,
                        modifier = Modifier.weight(1f),
                    )
                } else {
                    Spacer(Modifier.weight(1f))
                }
                for (kind in noteKinds) {
                    TextButton(onClick = { onNotes(kind) }) { Text(kind.label) }
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
