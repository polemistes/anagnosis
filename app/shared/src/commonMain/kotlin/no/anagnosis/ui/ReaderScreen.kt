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
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
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
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.platform.LocalFontFamilyResolver
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.ParagraphStyle
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
import androidx.compose.foundation.layout.offset
import androidx.compose.ui.unit.em
import androidx.compose.ui.text.AnnotatedString
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.Book
import no.anagnosis.data.CatalogEntry
import no.anagnosis.data.NoteGroup
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
import no.anagnosis.resources.Res
import no.anagnosis.resources.dictionary
import org.jetbrains.compose.resources.painterResource

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
    /** `after`: for the later part of a verse shared between speakers, the verse's earlier parts,
     *  after whose width this part is set, as printed editions set it. */
    data class GreekLine(val line: Lines, val after: String? = null) : ReaderRow {
        override val nInt get() = line.n_int
    }
}

/** A laid-out row: its rendering height and, for Greek lines, whether the line number fits on the right. */
private class Measured(val row: ReaderRow, val height: Int, val numberFits: Boolean = false, val indent: Int = 0)

class Page(val rows: List<ReaderRow>, val numbers: Map<ReaderRow, String>, val forced: Set<ReaderRow>, val firstN: Long, val lastN: Long,
           val indents: Map<ReaderRow, Int> = emptyMap())

private class Styles(
    val section: TextStyle,
    val subsection: TextStyle,
    val speaker: TextStyle,
    val greek: TextStyle,
    val translation: TextStyle,
    val stage: TextStyle,
    val number: TextStyle,
    /** Prose: a paragraph's first line is indented; a paragraph continued from the page before is not. */
    val prose: TextStyle,
    val proseContinued: TextStyle,
)

private val SECTION_TOP = 16.dp
private val SUBSECTION_TOP = 8.dp
private val SPEAKER_TOP = 10.dp
private val ROW_GAP = 2.dp
private val SEGMENT_GAP = 6.dp
private val NUMBER_GAP = 12.dp
/** The space above a paragraph of prose. */
private val PARAGRAPH_GAP = 6.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReaderScreen(
    repository: AnagnosisRepository,
    data: WorkData,
    settings: ReaderSettings,
    onSettingsChange: (ReaderSettings) -> Unit,
    onHelp: () -> Unit,
    onBack: () -> Unit,
    onSearch: () -> Unit,
    startLine: Long,
    onPositionChange: (Long) -> Unit,
    /** The text's catalog entry, for its credits. */
    entry: CatalogEntry,
) {
    // The reader's choice of view, or null for the default: both columns on a wide screen, else the Greek.
    var chosenMode by remember { mutableStateOf<ViewMode?>(null) }
    var showOptions by remember { mutableStateOf(false) }
    var showDocuments by remember { mutableStateOf(false) }
    // the edition's introduction, appendix, preface ...; the sigla are reached from the apparatus
    val documents = remember(data) { repository.documents(data).filter { it.first != "sigla" } }
    var openDocument by remember { mutableStateOf<String?>(null) }
    var showAbout by remember { mutableStateOf(false) }
    var selectedTokenId by remember { mutableStateOf<Long?>(null) }
    var wordInfo by remember { mutableStateOf<WordInfo?>(null) }
    var pageNotesKind by remember { mutableStateOf<NoteKind?>(null) }
    var pageNotes by remember { mutableStateOf<List<NoteGroup>>(emptyList()) }

    val translation = data.translations.firstOrNull()
    val allRows = remember(data) { buildRows(data) }
    // An epic is read one book at a time: pagination stays quick, and a page before and after
    // each book leads to the neighbouring one. For a play `book` is null and all rows are paged.
    var book by remember(data) { mutableStateOf(if (data.byBook) data.bookOf(startLine).coerceIn(data.books.first().number, data.books.last().number) else null) }
    val currentBook = book?.let { b -> data.books.firstOrNull { it.number == b } }
    val rows = remember(allRows, book) { if (book == null) allRows else allRows.filter { data.bookOf(it.nInt) == book } }
    val bookLines = remember(data, book) { if (currentBook == null) data.lines else data.lines.filter { it.n_int in currentBook.firstN..currentBook.lastN } }
    val bookSegments = remember(translation, book) {
        val segs = translation?.segments ?: emptyList()
        if (currentBook == null) segs else segs.filter { it.from_n_int in currentBook.firstN..currentBook.lastN }
    }
    val prevBook = currentBook?.let { b -> data.books.lastOrNull { it.number < b.number } }
    val nextBook = currentBook?.let { b -> data.books.firstOrNull { it.number > b.number } }
    var showBooks by remember { mutableStateOf(false) }
    // The sentence whose syntax sheet is open, by treebank sentence id.
    var syntaxSentence by remember { mutableStateOf<String?>(null) }
    val selectedToken = remember(selectedTokenId, data) {
        selectedTokenId?.let { id -> data.tokensByLine.values.asSequence().flatten().firstOrNull { it.id == id } }
    }

    LaunchedEffect(selectedTokenId) {
        val id = selectedTokenId
        wordInfo = if (id == null) null else withContext(Dispatchers.Default) { repository.lookupWord(data, id) }
    }

    val typography = MaterialTheme.typography
    val base = LocalTextStyle.current
    val family = settings.font.family()
    val size = settings.fontSize
    val styles = remember(typography, base, family, size) { stylesFor(typography, base, family, size) }

    // Position to keep across re-pagination (rotation, mode change): the first Greek line on screen.
    var anchorN by remember { mutableStateOf(startLine) }
    // Pinch-to-zoom: the size being previewed while the fingers are down, or null.
    var pinchSize by remember { mutableStateOf<Float?>(null) }
    var pinchAnchorRow by remember { mutableStateOf<ReaderRow?>(null) }
    var pages by remember { mutableStateOf<List<Page>>(emptyList()) }
    // False from a change of book until the new pages are cut and scrolled to the anchor: until
    // then the pager's index belongs to the old pages and must not move the reader.
    var positioned by remember { mutableStateOf(false) }
    // pager index = page index + offset: the first pager page leads back to the previous book
    val offset = if (prevBook != null && pages.isNotEmpty()) 1 else 0
    val stubs = if (pages.isEmpty()) 0 else offset + (if (nextBook != null) 1 else 0)
    val pagerState = rememberPagerState { pages.size + stubs }
    fun pageAt(pagerIndex: Int): Page? = pages.getOrNull(pagerIndex - offset)
    /** Opens another book at its first line, or at its last page when going back. */
    fun goToBook(target: Book, atEnd: Boolean = false) {
        positioned = false
        pages = emptyList()
        anchorN = if (atEnd) target.lastN else target.firstN
        book = target.number
    }
    val scope = rememberCoroutineScope()

    // The page being previewed while a finger slides on the progress bar, or null.
    var scrubPage by remember { mutableStateOf<Int?>(null) }

    LaunchedEffect(pagerState.currentPage, pages) {  // also once the pages exist, so opening a text counts as reading it
        if (scrubPage == null && positioned) pageAt(pagerState.currentPage)?.let { anchorN = it.firstN; onPositionChange(it.firstN) }
    }
    // Settling on the page before or after a book opens the neighbouring book.
    LaunchedEffect(pagerState.settledPage, pages, positioned) {
        if (pages.isEmpty() || !positioned) return@LaunchedEffect
        val i = pagerState.settledPage
        if (i < offset) prevBook?.let { goToBook(it, atEnd = true) }
        else if (i >= offset + pages.size) nextBook?.let { goToBook(it) }
    }
    LaunchedEffect(pageNotesKind, pagerState.currentPage) {
        val kind = pageNotesKind
        val page = pageAt(pagerState.currentPage)
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
            // Two rows: the title with the way back to the front page, then the controls, so that
            // the title is never squeezed by the buttons on a narrow screen.
            Column(Modifier.background(MaterialTheme.colorScheme.surface)) {
                TopAppBar(
                    title = { Text(data.work.title, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.clickable { onBack() }) },
                    navigationIcon = {
                        IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Front page") }
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
                    if (currentBook != null) {
                        Box {
                            TextButton(onClick = { showBooks = true }) { Text(if (currentBook.named) currentBook.name else currentBook.title) }
                            DropdownMenu(expanded = showBooks, onDismissRequest = { showBooks = false }) {
                                for (b in data.books) {
                                    DropdownMenuItem(
                                        text = { Text(b.title, fontWeight = if (b.number == currentBook.number) FontWeight.Bold else null) },
                                        onClick = { showBooks = false; if (b.number != currentBook.number) goToBook(b) },
                                    )
                                }
                            }
                        }
                    }
                    if (documents.isNotEmpty()) {
                        IconButton(onClick = { showDocuments = true }) {
                            Icon(Icons.Filled.Info, contentDescription = "Introduction and other parts of the edition")
                        }
                    }
                    IconButton(onClick = onSearch) {
                        Icon(painterResource(Res.drawable.dictionary), contentDescription = "Dictionary")
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
                currentPage = scrubPage ?: (pagerState.currentPage - offset).coerceIn(0, maxOf(0, pages.size - 1)),
                span = { first, last ->
                    val prefix = currentBook?.let { "Book ${it.number}, " } ?: ""
                    if (data.verses) data.range(first, last)
                    else if (first == last) "${prefix}line ${data.lineLabel(first)}".replaceFirstChar { it.uppercase() }
                    else "${prefix}lines ${data.lineLabel(first)}–${data.lineLabel(last)}".replaceFirstChar { it.uppercase() }
                },
                scrubbing = scrubPage != null,
                noteKinds = data.commentaries.map { it.kind() }.distinct(),
                onNotes = { pageNotesKind = it },
                onScrub = { page ->
                    scrubPage = page
                    scope.launch { pagerState.scrollToPage(page + offset) }
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
            // Prose keeps a narrower column for its section marks (172, b, c ...) unless they are hidden.
            val numberColumnPx = if (data.prose) {
                if (settings.lineNumbers != LineNumberMode.NONE && !data.verses) measurer.measure("000", styles.number).size.width + with(density) { NUMBER_GAP.roundToPx() } else 0
            } else if (settings.lineNumbers == LineNumberMode.ALL) {
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
            val measureCache = remember(rows, styles, widthPx, numberColumnPx, settings.lineNumbers) { HashMap<ReaderRow, Measured>() }
            LaunchedEffect(rows, widthPx, heightPx, styles, settings.lineNumbers, settings.fitTranslation, numberColumnPx) {
                // after a pinch, the page the reader was previewing keeps its first row
                val anchorRow = pinchAnchorRow
                val anchorIndex = if (anchorRow != null) rows.indexOfFirst { it === anchorRow }.takeIf { it >= 0 } else null
                // the job works on its own copy of the cache: the shared one is touched on this thread only
                val cache = HashMap(measureCache)
                val computed = withContext(Dispatchers.Default) {
                    val enHeights = if (settings.fitTranslation && translation != null) {
                        translationHeights(bookSegments, bookLines, backgroundMeasurer, styles, widthPx, density, data::lineLabel)
                    } else emptyMap()
                    paginate(rows, backgroundMeasurer, styles, widthPx - numberColumnPx, heightPx, density, settings.lineNumbers, enHeights, anchorIndex, cache, { data.lineLabel(it.n_int, it.n_sub) }, data.prose, verseMarks(data, settings.lineNumbers != LineNumberMode.NONE)) { ensureActive() }
                }
                measureCache.putAll(cache)
                pages = computed
                pinchAnchorRow = null
                pinchSize = null  // a committed pinch keeps its preview on screen until here
                val byRow = if (anchorRow != null) computed.indexOfFirst { page -> page.rows.any { it === anchorRow } } else -1
                val target = if (byRow >= 0) byRow else computed.indexOfLast { it.firstN <= anchorN }.coerceAtLeast(0)
                // the page before the book exists once pages do
                pagerState.scrollToPage(target + (if (prevBook != null) 1 else 0))
                positioned = true
                pages.getOrNull(target)?.let { anchorN = it.firstN; onPositionChange(it.firstN) }
            }
            // Live preview during a pinch: only the current page, re-laid out at the previewed size.
            val previewStyles = pinchSize?.let { size -> stylesFor(typography, base, family, (size + 0.5f).toInt()) }
            val previewPage = if (previewStyles != null && pages.isNotEmpty()) {
                val page = pageAt(pagerState.currentPage)
                val first = page?.rows?.firstOrNull()
                val startIdx = if (first != null) rows.indexOfFirst { it === first } else -1
                if (startIdx >= 0) {
                    val enHeights = if (settings.fitTranslation && translation != null) {
                        translationHeights(bookSegments, bookLines, measurer, previewStyles, widthPx, density, data::lineLabel)
                    } else emptyMap()
                    // only as many rows as could possibly fit on one page, so the preview stays cheap
                    val endIdx = minOf(rows.size, startIdx + 120)
                    paginate(rows.subList(startIdx, endIdx), measurer, previewStyles, widthPx - numberColumnPx, heightPx, density, settings.lineNumbers, enHeights, label = { data.lineLabel(it.n_int, it.n_sub) }, prose = data.prose, marks = verseMarks(data, settings.lineNumbers != LineNumberMode.NONE)).firstOrNull()
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
                        val page = currentPages.value.getOrNull(pagerState.currentPage - offset)
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
                    val pageSegments = remember(pages, bookSegments) { segmentsByPage(pages, bookSegments, bookLines) }
                    HorizontalPager(state = pagerState, modifier = Modifier.fillMaxSize(), beyondViewportPageCount = 1) { index ->
                        if (index < offset || index >= offset + pages.size) {
                            val target = if (index < offset) prevBook else nextBook
                            if (target != null) BookStub(target, styles)
                            return@HorizontalPager
                        }
                        val page = pages.getOrNull(index - offset) ?: return@HorizontalPager
                        PageFrame(
                            greek = {
                                PageContent(
                                    page, styles, data, numberColumn, forcedColumn,
                                    onWord = { selectedTokenId = it },
                                    onSentence = { token -> syntaxSentence = token.sentence },
                                    showMarks = settings.lineNumbers != LineNumberMode.NONE,
                                )
                            },
                            english = if (translation == null) null else {
                                { TranslationPage(pageSegments.getOrNull(index - offset) ?: emptyList(), styles, showAnchors, Modifier.fillMaxSize(), anchorLabel(data)) }
                            },
                        )
                    }
                }
                if (previewPage != null && previewStyles != null) {
                    val previewSegments = if (sideBySide && translation != null) {
                        segmentsByPage(listOf(previewPage), bookSegments, bookLines).first()
                    } else emptyList()
                    PageFrame(
                        greek = { PageContent(previewPage, previewStyles, data, numberColumn, forcedColumn, onWord = {}, onSentence = {}, showMarks = settings.lineNumbers != LineNumberMode.NONE) },
                        english = if (translation == null) null else {
                            { TranslationPage(previewSegments, previewStyles, showAnchors, Modifier.fillMaxSize(), anchorLabel(data)) }
                        },
                        modifier = Modifier.background(MaterialTheme.colorScheme.background),
                    )
                }
            }
        }
    }
    // The syntax page covers the reader; back closes it. A word sheet opened from it lies on top.
    syntaxSentence?.let { sentence ->
        val tree = remember(sentence, data) { repository.sentenceTree(data, sentence) }
        val label = remember(tree, data) { sentenceLabel(tree, data) }
        Box(Modifier.fillMaxSize()) {
            SyntaxScreen(tree, label, family, onWord = { selectedTokenId = it }, onBack = { syntaxSentence = null }, automatic = data.automaticSyntax)
        }
        PlatformBackHandler { syntaxSentence = null }
    }
    }

    wordInfo?.let { info ->
        val sentence = selectedToken?.sentence
        WordSheet(
            info,
            onDismiss = { selectedTokenId = null },
            onSyntax = if (sentence == null) null else { { syntaxSentence = sentence; selectedTokenId = null } },
            showFunction = settings.wordFunction,
            order = data.dictionaryOrder,
            disabled = settings.disabledDictionaries,
        )
    }
    pageNotesKind?.let { kind ->
        val sigla = remember(kind) { if (kind == NoteKind.APPARATUS) repository.document(data, "sigla") else null }
        PageNotesSheet(kind, pageNotes, sigla, onDismiss = { pageNotesKind = null })
    }
    if (showDocuments) {
        DocumentsSheet(documents, onOpen = { showDocuments = false; openDocument = it }, onDismiss = { showDocuments = false })
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
            dictionaries = remember { repository.dictionaries() },
        )
    }
    if (showAbout) {
        val credits = remember { repository.textCredits(entry) }
        TextAboutDialog(entry.titleEn.ifEmpty { entry.title }, credits, onDismiss = { showAbout = false })
    }
}

private fun buildRows(data: WorkData): List<ReaderRow> {
    val rows = mutableListOf<ReaderRow>()
    var previous: Lines? = null
    var verseSoFar = ""
    for (line in data.lines) {
        data.sectionsByFirstLine[line.id]?.forEach { rows += ReaderRow.Section(it, line.n_int) }
        if (line.speech_start == 1L && line.speaker != null) rows += ReaderRow.Speaker(line.speaker, line.n_int)
        // a verse shared between speakers: its later parts carry a letter (591, 591a) and begin a speech
        val continues = line.n_sub.isNotEmpty() && line.speech_start == 1L && previous?.n_int == line.n_int &&
            data.sectionsByFirstLine[line.id] == null
        val after = if (continues) verseSoFar else null
        rows += ReaderRow.GreekLine(line, after)
        verseSoFar = if (continues) "$verseSoFar ${line.text}" else line.text
        previous = line
    }
    return rows
}

/** How far the later part of a shared verse is indented: the width of the verse's earlier parts,
 *  less where the part would not fit after them on the line (it then ends at the right margin),
 *  and a small indent where even that leaves too little room. */
private fun verseIndent(measurer: TextMeasurer, after: String?, part: String, style: TextStyle, textWidth: Int, reserve: Int): Int {
    if (after.isNullOrEmpty() || textWidth <= 0) return 0
    val small = textWidth / 8
    val before = measurer.measure(after + "\u2002", style, constraints = Constraints(maxWidth = textWidth))
    val width = if (before.lineCount == 1) before.getLineRight(0).toInt() else small
    val own = measurer.measure(part, style).size.width
    val room = textWidth - reserve - own
    return when {
        width <= room -> width
        room >= small -> room
        else -> small
    }
}

/** "line 12" or "lines 12–14": the lines a sentence's words stand on. */
private fun sentenceLabel(tree: no.anagnosis.data.SyntaxTree, data: WorkData): String {
    val linesById = data.lines.associateBy { it.id }
    val lines = tree.nodes.mapNotNull { it.token }.mapNotNull { linesById[it.line_id] }
    val first = lines.minByOrNull { it.ord } ?: return ""
    val last = lines.maxBy { it.ord }
    if (data.verses) return data.range(first.n_int, last.n_int)
    return if (first.id == last.id) "line ${first.n}" else "lines ${first.n}–${last.n}"
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
        if (lines.isEmpty()) break
        val line = firstLineFrom(lines, seg.from_n_int)
        out[pageOfLine[line.id] ?: (pages.size - 1)] += seg
    }
    return out
}

/** The first line at or after n (binary search; `lines` is in order), or the last line. */
private fun firstLineFrom(lines: List<Lines>, n: Long): Lines {
    var lo = 0
    var hi = lines.size - 1
    if (lines[hi].n_int < n) return lines[hi]
    while (lo < hi) {
        val mid = (lo + hi) / 2
        if (lines[mid].n_int >= n) hi = mid else lo = mid + 1
    }
    return lines[lo]
}

/** The page before or after a book: its title, leading on to it. */
@Composable
private fun BookStub(target: Book, styles: Styles) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(target.title, style = styles.section, color = MaterialTheme.colorScheme.onBackground)
        }
    }
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
    label: (Lines) -> String = { it.n },
    prose: Boolean = false,
    marks: ((Lines) -> VerseMark?)? = null,
    checkActive: () -> Unit = {},
): List<Page> {
    if (widthPx <= 0 || heightPx <= 0) return emptyList()
    fun Dp.px() = with(density) { roundToPx() }
    val textWidth = widthPx
    val constraints = Constraints(maxWidth = textWidth)
    val numberWidth = measurer.measure("0000", styles.number).size.width + NUMBER_GAP.px()
    // Prose: each line's height is its share of its paragraph, measured as a whole. A page that
    // ends inside a paragraph starts the rest on a new line, so a line's height is kept in reserve.
    val proseHeights = if (prose) proseLineHeights(rows, measurer, styles, textWidth, PARAGRAPH_GAP.px(), marks) else emptyMap()
    val pageHeight = if (prose) heightPx - measurer.measure("Α", styles.prose).size.height else heightPx

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
            is ReaderRow.GreekLine -> if (prose) Measured(row, proseHeights[row.line.id] ?: 0, false) else {
                val indent = verseIndent(measurer, row.after, row.line.text, styles.greek, textWidth, if (numbering == LineNumberMode.ALL) 0 else numberWidth)
                val layout = measurer.measure(row.line.text, styles.greek, constraints = Constraints(maxWidth = textWidth - indent))
                // In the all-lines mode the caller has already reserved a column for the numbers.
                val fits = numbering == LineNumberMode.ALL || textWidth - indent - layout.getLineRight(0) >= numberWidth
                Measured(row, layout.size.height, fits, indent)
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
        if (prose) break  // prose shows its section marks in the margin instead
        val row = lineAt(k)
        when (numbering) {
            LineNumberMode.NONE -> {}
            LineNumberMode.ALL -> if (measured[i].numberFits) numbers[row] = label(row.line)
            LineNumberMode.FIFTH -> {
                // every fifth verse; a lettered line (an extra line, or the later part of a shared
                // verse) has no number of its own in this mode. A long lyric verse that runs over a
                // fifth number no line carries (the verse 473 that covers 475) shows that number
                // beside it, as Jebb prints it.
                val n = row.line.n_int
                val next = (k + 1 until greekIdx.size).asSequence().map { lineAt(it).line }
                    .firstOrNull { it.n_sub.isEmpty() }?.n_int
                val covered = (n / 5 + 1) * 5
                val shown = when {
                    row.line.n_sub.isNotEmpty() -> null
                    n % 5 == 0L -> row.line
                    next != null && covered < next -> row.line.copy(n = covered.toString(), n_int = covered)
                    else -> null
                } ?: continue
                val own = shown === row.line
                when {
                    fitsAt(k) -> numbers[row] = label(shown)
                    own && k + 1 < greekIdx.size && fitsAt(k + 1) && lineAt(k + 1) !in numbers -> numbers[lineAt(k + 1)] = label(lineAt(k + 1).line)
                    own && k > 0 && fitsAt(k - 1) && lineAt(k - 1) !in numbers -> numbers[lineAt(k - 1)] = label(lineAt(k - 1).line)
                    else -> { numbers[row] = label(shown); forced += row }
                }
            }
        }
    }
    // Lines that must make room for a forced number are laid out narrower.
    for (i in greekIdx) {
        val row = measured[i].row
        if (row in forced) {
            val indent = measured[i].indent
            val layout = measurer.measure((row as ReaderRow.GreekLine).line.text, styles.greek, constraints = Constraints(maxWidth = textWidth - numberWidth - indent))
            measured[i] = Measured(row, layout.size.height, true, indent)
        }
    }

    fun enHeight(row: ReaderRow) = (row as? ReaderRow.GreekLine)?.let { translationHeights[it.line.id] } ?: 0
    fun isHeading(row: ReaderRow) = row is ReaderRow.Section || row is ReaderRow.Speaker

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
            if (current.isNotEmpty() && (used + needed > pageHeight || usedEn + neededEn > heightPx)) {
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
            if (current.isNotEmpty() && (used + m.height > pageHeight || usedEn + enHeight(m.row) > heightPx)) {
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
    val indents = measured.filter { it.indent > 0 }.associate { it.row to it.indent }
    return chunks.map { Page(it, numbers, forced, it.first().nInt, it.last().nInt, indents) }
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
    anchorLabel: (Long) -> String = { it.toString() },
): Map<Long, Int> {
    if (widthPx <= 0 || lines.isEmpty()) return emptyMap()
    val constraints = Constraints(maxWidth = widthPx)
    val gap = with(density) { SEGMENT_GAP.roundToPx() }
    val speakerTop = with(density) { (SPEAKER_TOP + ROW_GAP).roundToPx() }
    val out = HashMap<Long, Int>()
    fun lineOf(seg: Translation_segments) = firstLineFrom(lines, seg.from_n_int)
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
            prefix.append(anchorLabel(g.from_n_int)).append('\u2009').append(g.text)
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

private fun stylesFor(typography: androidx.compose.material3.Typography, base: TextStyle, family: androidx.compose.ui.text.font.FontFamily, size: Int) = Styles(
    section = base.merge(typography.titleLarge.copy(fontFamily = family, fontSize = (size + 5).sp, lineHeight = (size + 9).sp)),
    subsection = base.merge(typography.titleSmall.copy(fontFamily = family, fontSize = (size - 1).sp, lineHeight = (size + 3).sp)),
    speaker = base.merge(typography.titleMedium.copy(fontFamily = family, fontSize = size.sp, lineHeight = (size + 4).sp, fontWeight = FontWeight.SemiBold)),
    greek = base.merge(TextStyle(fontFamily = family, fontSize = size.sp, lineHeight = (size * 1.5f).sp, textIndent = TextIndent(restLine = 20.sp))),
    translation = base.merge(TextStyle(fontFamily = family, fontSize = (size - 1).sp, lineHeight = ((size - 1) * 1.5f).sp)),
    stage = base.merge(TextStyle(fontFamily = family, fontSize = (size - 2).sp, lineHeight = ((size - 2) * 1.4f).sp, fontStyle = FontStyle.Italic)),
    number = base.merge(typography.labelSmall),
    prose = base.merge(TextStyle(fontFamily = family, fontSize = size.sp, lineHeight = (size * 1.5f).sp, textIndent = TextIndent(firstLine = (size * 1.5f).sp))),
    proseContinued = base.merge(TextStyle(fontFamily = family, fontSize = size.sp, lineHeight = (size * 1.5f).sp)),
)

@Composable
private fun PageContent(
    page: Page,
    styles: Styles,
    data: WorkData,
    numberColumn: Dp,
    forcedColumn: Dp,
    onWord: (Long) -> Unit,
    onSentence: (Tokens) -> Unit,
    showMarks: Boolean = true,
) {
    if (data.prose) {
        ProsePage(page, styles, data, numberColumn, showMarks, onWord, onSentence)
        return
    }
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
                indentPx = page.indents[row] ?: 0,
                number = page.numbers[row],
                numberColumn = if (row in page.forced) forcedColumn else numberColumn,
                data = data,
                styles = styles,
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
    indentPx: Int,
    number: String?,
    numberColumn: Dp,
    data: WorkData,
    styles: Styles,
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
    Box(
        Modifier.fillMaxWidth().pointerInput(tokens) {
            fun tokenAt(tap: Offset): Tokens? {
                val result = layout ?: return null
                val pos = tap - Offset(indentPx.toFloat(), 0f)  // the text of an indented part starts further in
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
        val indent = with(LocalDensity.current) { indentPx.toDp() }
        Text(text = line.text, style = styles.greek, onTextLayout = { layout = it }, modifier = Modifier.fillMaxWidth().padding(start = indent, end = numberColumn))
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
private fun TranslationPage(segments: List<Translation_segments>, styles: Styles, showAnchors: Boolean, modifier: Modifier, anchorLabel: (Long) -> String = { it.toString() }) {
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
                        withStyle(anchorStyle) { append(anchorLabel(g.from_n_int)) }
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
    span: (Long, Long) -> String,
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
                    val span = span(page.firstN, page.lastN)
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


// ---------------------------------------------------------------- prose

/** Lines of prose laid out as one paragraph: the text, and where each line's text begins in it. */
private class ProseText(val text: AnnotatedString, val start: Map<Long, Int>, val end: Map<Long, Int>)

/** A word-joiner, which takes the place of a speaker label's braces: it keeps the offsets and shows nothing. */
private const val HIDDEN = '\u2060'

/**
 * Burnet's lines joined into running text. Lines are joined by a space (a word divided at a line
 * end is printed whole on its first line). A verse line ("| " at its start) is a paragraph of its
 * own with a hanging indent, and the prose after it goes on without an indent. A speaker's name
 * in braces ({ΑΠΟΛ.}) is set as a label. Offsets stay those of the lines' own text: marks that
 * are not shown are replaced by invisible characters, never removed.
 */
private fun proseText(lines: List<Lines>, label: SpanStyle, marks: ((Lines) -> VerseMark?)? = null, markColor: Color = Color.Unspecified, chapterColor: Color = Color.Unspecified): ProseText {
    val start = HashMap<Long, Int>()
    val end = HashMap<Long, Int>()
    var previousVerse = false
    var continued = false  // a paragraph style is open for prose after verse
    val text = buildAnnotatedString {
        lines.forEachIndexed { i, line ->
            val verse = line.text.startsWith("| ")
            if (verse) {
                if (continued) { pop(); continued = false }
                pushStyle(VERSE)
            } else if (previousVerse) {
                pushStyle(AFTER_VERSE)
                continued = true
            } else if (i > 0) append(" ")
            marks?.invoke(line)?.let { mark ->
                withStyle(if (mark.chapter) chapterMarkStyle(chapterColor) else verseMarkStyle(markColor)) { append(mark.text) }
                append(VERSE_GAP)
            }
            start[line.id] = length
            var t = line.text
            if (verse) t = "$HIDDEN$HIDDEN" + t.substring(2)
            var k = 0
            for (m in SPEAKER_LABEL.findAll(t)) {
                append(t.substring(k, m.range.first))
                append(HIDDEN)
                withStyle(label) { append(m.groupValues[1]) }
                append(HIDDEN)
                k = m.range.last + 1
            }
            append(t.substring(k))
            end[line.id] = length
            if (verse) pop()
            previousVerse = verse
        }
        if (continued) pop()
    }
    return ProseText(text, start, end)
}

private val VERSE = ParagraphStyle(textIndent = TextIndent(firstLine = 2.em, restLine = 3.em))
private val AFTER_VERSE = ParagraphStyle(textIndent = TextIndent(firstLine = 0.em, restLine = 0.em))

private val SPEAKER_LABEL = Regex("\\{([^}]*)\\}")

/** The number set before a verse of the New Testament: its chapter's number at the first verse. */
private class VerseMark(val text: String, val chapter: Boolean)

/** A narrow no-break space between a verse number and its verse: the number never ends a line. */
private const val VERSE_GAP = "\u202F"

/**
 * The verse numbers of a text cited by verse, when shown: the chapter's number in bold before
 * its first verse, a small raised number before the others, none before the rest of a verse a
 * paragraph divides (1.1.6b).
 */
private fun verseMarks(data: WorkData, shown: Boolean): ((Lines) -> VerseMark?)? =
    if (!data.verses || !shown) null else { line ->
        when {
            line.n_sub.isNotEmpty() -> null
            data.verseOf(line.n_int) == 1L -> VerseMark(data.chapterOf(line.n_int).toString(), chapter = true)
            else -> VerseMark(data.verseOf(line.n_int).toString(), chapter = false)
        }
    }

private fun verseMarkStyle(color: Color) = SpanStyle(fontSize = 0.6.em, baselineShift = BaselineShift.Superscript, color = color)

private fun chapterMarkStyle(color: Color) = SpanStyle(fontWeight = FontWeight.Bold, color = color)

/** How the translation marks where a Greek line begins: the verse number, chapter and verse at a chapter's start. */
private fun anchorLabel(data: WorkData): (Long) -> String =
    if (!data.verses) data::lineLabel else { n -> if (data.verseOf(n) == 1L) data.lineLabel(n) else data.verseOf(n).toString() }

private fun speakerLabelStyle(color: Color) = SpanStyle(fontWeight = FontWeight.SemiBold, fontSize = 0.8.em, color = color, letterSpacing = 0.05.em)

/** The rows' Greek lines grouped into paragraphs: a paragraph begins where speech_start is set. */
private fun paragraphsOf(rows: List<ReaderRow>): List<List<Lines>> {
    val out = mutableListOf<MutableList<Lines>>()
    var breakNext = true
    for (row in rows) {
        if (row !is ReaderRow.GreekLine) { breakNext = true; continue }
        if (breakNext || row.line.speech_start == 1L) out += mutableListOf<Lines>()
        out.last() += row.line
        breakNext = false
    }
    return out
}

/**
 * The height each line of prose adds to its page: the bottom of the visual line its last word
 * is on, less that of the line before it; the first line of a paragraph also takes the space
 * above the paragraph.
 */
private fun proseLineHeights(rows: List<ReaderRow>, measurer: TextMeasurer, styles: Styles, widthPx: Int, gapPx: Int, marks: ((Lines) -> VerseMark?)? = null): Map<Long, Int> {
    val out = HashMap<Long, Int>()
    val constraints = Constraints(maxWidth = widthPx)
    for (para in paragraphsOf(rows)) {
        val prose = proseText(para, speakerLabelStyle(Color.Unspecified), marks)
        val layout = measurer.measure(prose.text, styles.prose, constraints = constraints)
        var previous = 0f
        para.forEachIndexed { i, line ->
            val last = ((prose.end[line.id] ?: 1) - 1).coerceAtLeast(0)
            val bottom = layout.getLineBottom(layout.getLineForOffset(last))
            out[line.id] = (bottom - previous).toInt() + (if (i == 0) gapPx else 0)
            previous = bottom
        }
        // what rounding lost goes to the last line
        val total = para.sumOf { out[it.id] ?: 0 }
        val whole = layout.size.height + gapPx
        if (total < whole) out[para.last().id] = (out[para.last().id] ?: 0) + (whole - total)
    }
    return out
}

/** A page of prose: its lines as paragraphs, with the Stephanus marks in the margin. */
@Composable
private fun ProsePage(
    page: Page,
    styles: Styles,
    data: WorkData,
    margin: Dp,
    showMarks: Boolean,
    onWord: (Long) -> Unit,
    onSentence: (Tokens) -> Unit,
) {
    // headings in their place, and the lines between them as paragraphs
    val blocks = remember(page) {
        val out = mutableListOf<Any>()
        var run = mutableListOf<ReaderRow>()
        for (row in page.rows) {
            if (row is ReaderRow.GreekLine) { run += row; continue }
            if (run.isNotEmpty()) { out.addAll(paragraphsOf(run)); run = mutableListOf() }
            out += row
        }
        if (run.isNotEmpty()) out.addAll(paragraphsOf(run))
        out
    }
    for (block in blocks) {
        when (block) {
            is ReaderRow.Section -> SectionHeader(block.section, styles)
            is ReaderRow.Speaker -> Text(block.name, style = styles.speaker, color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(top = SPEAKER_TOP, bottom = ROW_GAP))
            is List<*> -> @Suppress("UNCHECKED_CAST") ProseParagraph(block as List<Lines>, styles, data, margin, showMarks, onWord, onSentence)
        }
    }
}

@Composable
private fun ProseParagraph(
    lines: List<Lines>,
    styles: Styles,
    data: WorkData,
    margin: Dp,
    showMarks: Boolean,
    onWord: (Long) -> Unit,
    onSentence: (Tokens) -> Unit,
) {
    val labelColor = MaterialTheme.colorScheme.primary
    val markColor = MaterialTheme.colorScheme.outline
    val prose = remember(lines, labelColor, markColor, showMarks) {
        proseText(lines, speakerLabelStyle(labelColor), verseMarks(data, showMarks), markColor, labelColor)
    }
    // the words with their offsets in the paragraph
    val words = remember(lines, prose) {
        lines.flatMap { line ->
            val base = prose.start[line.id] ?: 0
            (data.tokensByLine[line.id] ?: emptyList()).map { Triple(base + it.start.toInt(), base + it.end.toInt(), it) }
        }
    }
    val opens = lines.first().speech_start == 1L
    var layout by remember { mutableStateOf<TextLayoutResult?>(null) }
    val currentOnWord = rememberUpdatedState(onWord)
    val currentOnSentence = rememberUpdatedState(onSentence)
    val haptic = LocalHapticFeedback.current
    val density = LocalDensity.current
    Box(
        Modifier.fillMaxWidth().padding(top = if (opens) PARAGRAPH_GAP else 0.dp).pointerInput(words) {
            fun tokenAt(pos: Offset): Tokens? {
                val result = layout ?: return null
                val lineIndex = result.getLineForVerticalPosition(pos.y)
                if (pos.x > result.getLineRight(lineIndex) + 4.dp.toPx()) return null
                val offset = result.getOffsetForPosition(pos)
                return words.firstOrNull { offset >= it.first && offset < it.second }?.third
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
        Text(
            prose.text,
            style = if (opens) styles.prose else styles.proseContinued,
            color = MaterialTheme.colorScheme.onBackground,
            onTextLayout = { layout = it },
            modifier = Modifier.fillMaxWidth().padding(end = margin),
        )
        val result = layout
        if (showMarks && data.stephanus && result != null) {
            // Burnet's margin: the Stephanus page where it begins, the section letters b-e
            for (line in lines) {
                if (line.n_int % 100 != 1L) continue
                val section = ((line.n_int % WorkData.BOOK) / 100).toInt()
                val mark = if (section == 0) "${line.n_int / WorkData.BOOK}" else WorkData.SECTIONS[section].toString()
                val offset = (prose.start[line.id] ?: 0).coerceAtMost(maxOf(0, prose.text.length - 1))
                val top = result.getLineTop(result.getLineForOffset(offset))
                Text(
                    mark,
                    style = styles.number,
                    color = MaterialTheme.colorScheme.outline,
                    fontWeight = if (section == 0) FontWeight.SemiBold else null,
                    modifier = Modifier.align(Alignment.TopEnd).offset(y = with(density) { top.toDp() } + 5.dp),
                )
            }
        }
    }
}
