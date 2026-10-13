package no.anagnosis.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.CatalogEntry
import no.anagnosis.data.NoTextShop
import no.anagnosis.data.NoteKind
import no.anagnosis.data.SearchHit
import no.anagnosis.data.SearchSource
import no.anagnosis.data.SearchTarget
import no.anagnosis.data.TextShop
import no.anagnosis.data.WorkData
import no.anagnosis.prefs.ColorTheme
import no.anagnosis.prefs.SettingsStore

/** The app's screens: the front page, the shop, and the reader. */
sealed interface Screen {
    data object Home : Screen
    data object Available : Screen
    /** A text being read; `backTo` is where the back arrow leads (the search, when a hit was opened). */
    data class Reader(val slug: String, val backTo: Screen = Home) : Screen
    /** The dictionary and analyser; `from` is the screen to return to. */
    data class Search(val from: Screen) : Screen
}

@Composable
fun App(
    repository: AnagnosisRepository,
    settingsStore: SettingsStore,
    appVersion: String,
    resumeCount: Int = 0,
    openText: String? = null,
    onOpenTextHandled: () -> Unit = {},
    shop: TextShop = NoTextShop,
) {
    val shopState by shop.state.collectAsState()
    var settings by remember { mutableStateOf(settingsStore.load()) }
    var showIntro by remember { mutableStateOf(false) }
    val systemDark = isSystemInDarkTheme()
    val colors = remember(settings.theme, systemDark) { colorScheme(settings.theme, systemDark) }

    var catalog by remember { mutableStateOf<List<CatalogEntry>?>(null) }
    var screen by remember { mutableStateOf<Screen>(Screen.Home) }
    // the text opened out on the front page, which stays so when the reader goes back there
    var expanded by remember { mutableStateOf<String?>(null) }
    val loaded = remember { HashMap<String, WorkData>() }
    var current by remember { mutableStateOf<WorkData?>(null) }
    // The search lives for the session, so that coming back from a hit finds it as it was.
    val search = remember { SearchState() }
    val homeList = remember { LazyListState() }
    // Where a hit of the search opens the reader; the reader takes it once and gives it back.
    var target by remember { mutableStateOf<SearchTarget?>(null) }
    /** Opens a hit in the reader; back from there returns to the screen it was found on. */
    fun openHit(hit: SearchHit, from: Screen) {
        target = SearchTarget(
            hit.slug, hit.source, hit.nInt, hit.nSub, hit.start, hit.end,
            noteKind = if (hit.source == SearchSource.COMMENTARY) NoteKind.entries.firstOrNull { it.label == hit.label } else null,
            noteId = if (hit.source == SearchSource.NOTES) hit.extra else null,
        )
        expanded = hit.slug
        // a reader reached from a hit goes back to the search, which goes back to the text (not further)
        val back = if (from is Screen.Search) Screen.Search(stripBack(from.from)) else from
        screen = Screen.Reader(hit.slug, backTo = back)
    }

    // Read the catalog whenever the app comes to the front, when a text bought in the app has
    // arrived and when what is owned changes: a text bought as an app of its own is copied in
    // when the app comes to the front.
    LaunchedEffect(resumeCount, shopState.revision) {
        repository.ownedTexts = shop.state.value.owned
        val list = withContext(Dispatchers.Default) { repository.catalog() }
        catalog = list
        // A fresh start opens on the front page; the reading position is kept per text, so
        // "Read this text" continues where the reader left off.
    }
    // the app that sells a text asked for it to be opened
    LaunchedEffect(openText, catalog) {
        val slug = openText ?: return@LaunchedEffect
        val list = catalog ?: return@LaunchedEffect
        if (list.any { it.slug == slug && it.installed }) { expanded = slug; screen = Screen.Reader(slug) }
        onOpenTextHandled()
    }
    // The text is loaded in the background once its title is opened out on the front page, so
    // that it is ready, or nearly, when the reader asks for it; the long ones take a few seconds.
    val wantedSlug = ((screen as? Screen.Search)?.from as? Screen.Reader)?.slug ?: (screen as? Screen.Reader)?.slug
        ?: expanded.takeIf { screen == Screen.Home }
    LaunchedEffect(wantedSlug) {
        if (wantedSlug != null) {
            current = loaded[wantedSlug] ?: withContext(Dispatchers.Default) { repository.loadWork(wantedSlug) }.also { loaded[wantedSlug] = it }
        }
    }

    MaterialTheme(colorScheme = colors) {
        Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            val list = catalog
            when (val s = screen) {
                is Screen.Search -> {
                    SearchScreen(
                        repository, search, settings,
                        onSettingsChange = { settings = it; settingsStore.save(it) },
                        textSlug = (s.from as? Screen.Reader)?.slug,
                        installed = list.orEmpty().filter { it.installed },
                        onOpen = { openHit(it, s) },
                        onBack = { screen = s.from },
                    )
                    PlatformBackHandler { screen = s.from }
                }
                Screen.Home -> if (list == null) Loading() else HomeScreen(
                    catalog = list,
                    appVersion = appVersion,
                    repository = repository,
                    settings = settings,
                    onSettingsChange = { settings = it; settingsStore.save(it) },
                    expanded = expanded,
                    onExpand = { expanded = it },
                    onRead = { screen = Screen.Reader(it) },
                    onAvailable = { screen = Screen.Available },
                    search = search,
                    onOpenHit = { openHit(it, Screen.Home) },
                    listState = homeList,
                )
                Screen.Available -> {
                    if (list == null) Loading() else AvailableTextsScreen(
                        catalog = list,
                        shop = shopState,
                        onBuy = { shop.buy(it) },
                        onDownload = { shop.download(it) },
                        onOpen = { expanded = it; screen = Screen.Reader(it) },
                        onBack = { screen = Screen.Home },
                    )
                    PlatformBackHandler { screen = Screen.Home }
                }
                is Screen.Reader -> {
                    val data = current
                    if (data == null || data.slug != s.slug) Loading("Opening ${list?.firstOrNull { it.slug == s.slug }?.let { e -> e.titleEn.ifEmpty { e.title } } ?: "the text"} …") else {
                        ReaderScreen(
                            repository = repository,
                            data = data,
                            settings = settings,
                            onSettingsChange = { settings = it; settingsStore.save(it) },
                            onHelp = { showIntro = true },
                            onBack = { screen = s.backTo },
                            onSearch = { screen = Screen.Search(stripBack(s)) },
                            startLine = target?.takeIf { it.slug == s.slug }?.nInt ?: settingsStore.lastLine(s.slug) ?: 1L,
                            target = target?.takeIf { it.slug == s.slug },
                            onTargetShown = { target = null },
                            onSearchLemma = { key, lemma ->
                                search.openLemma(key, lemma)
                                search.thisText = true
                                screen = Screen.Search(stripBack(s))
                            },
                            onPositionChange = { settingsStore.saveLastText(s.slug); settingsStore.saveLastLine(s.slug, it) },
                            entry = list?.firstOrNull { it.slug == s.slug } ?: CatalogEntry(s.slug, data.work.title, data.work.author ?: "", "", "", "", "", true),
                        )
                        if (showIntro) {
                            IntroDialog(onDismiss = { showIntro = false; settingsStore.markIntroSeen() })
                        }
                        PlatformBackHandler { screen = s.backTo }
                    }
                }
            }
        }
    }
}

/** A reader screen whose back arrow leads to the front page: the chain of screens never grows. */
private fun stripBack(screen: Screen): Screen = if (screen is Screen.Reader) Screen.Reader(screen.slug) else screen

/** A spinner, with a line saying what is being waited for when that takes a moment. */
@Composable
private fun Loading(message: String? = null) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator()
            if (message != null) {
                Text(
                    message,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 16.dp),
                )
            }
        }
    }
}

private fun colorScheme(theme: ColorTheme, systemDark: Boolean): ColorScheme {
    if (theme == ColorTheme.SYSTEM) return if (systemDark) darkColorScheme() else lightColorScheme()
    val base = if (theme.dark) darkColorScheme() else lightColorScheme()
    val bg = Color(theme.background)
    val fg = Color(theme.text)
    val raised = lerp(bg, fg, 0.06f)
    return base.copy(
        background = bg,
        onBackground = fg,
        surface = bg,
        onSurface = fg,
        onSurfaceVariant = lerp(fg, bg, 0.25f),
        surfaceContainerLow = raised,
        surfaceContainer = raised,
        surfaceContainerHigh = lerp(bg, fg, 0.10f),
        surfaceVariant = lerp(bg, fg, 0.12f),
        outline = lerp(fg, bg, 0.45f),
    )
}
