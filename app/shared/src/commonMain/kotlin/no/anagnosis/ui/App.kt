package no.anagnosis.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.data.CatalogEntry
import no.anagnosis.data.WorkData
import no.anagnosis.prefs.ColorTheme
import no.anagnosis.prefs.SettingsStore

/** The app's screens: the library of texts, a text's own page, and the reader. */
sealed interface Screen {
    data object Library : Screen
    data class TextHome(val slug: String) : Screen
    data class Reader(val slug: String) : Screen
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
) {
    var settings by remember { mutableStateOf(settingsStore.load()) }
    var showIntro by remember { mutableStateOf(false) }
    val systemDark = isSystemInDarkTheme()
    val colors = remember(settings.theme, systemDark) { colorScheme(settings.theme, systemDark) }

    var catalog by remember { mutableStateOf<List<CatalogEntry>?>(null) }
    var screen by remember { mutableStateOf<Screen>(Screen.Library) }
    val loaded = remember { HashMap<String, WorkData>() }
    var current by remember { mutableStateOf<WorkData?>(null) }

    // Read the catalog whenever the app comes to the front: a text bought as an app of its own
    // is copied in then.
    LaunchedEffect(resumeCount) {
        val list = withContext(Dispatchers.Default) { repository.catalog() }
        catalog = list
        // A fresh start opens on the front page; the reading position is kept per text, so
        // "Read the text" continues where the reader left off.
    }
    // the app that sells a text asked for it to be opened
    LaunchedEffect(openText, catalog) {
        val slug = openText ?: return@LaunchedEffect
        val list = catalog ?: return@LaunchedEffect
        if (list.any { it.slug == slug && it.installed }) screen = Screen.TextHome(slug)
        onOpenTextHandled()
    }
    val wantedSlug = ((screen as? Screen.Search)?.from as? Screen.Reader)?.slug ?: (screen as? Screen.Reader)?.slug
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
                    SearchScreen(repository, settings, onSettingsChange = { settings = it; settingsStore.save(it) }, onBack = { screen = s.from })
                    PlatformBackHandler { screen = s.from }
                }
                Screen.Library -> if (list == null) Loading() else LibraryScreen(
                    catalog = list,
                    appVersion = appVersion,
                    repository = repository,
                    onOpen = { screen = Screen.TextHome(it) },
                    onSearch = { screen = Screen.Search(Screen.Library) },
                )
                is Screen.TextHome -> {
                    val entry = list?.firstOrNull { it.slug == s.slug }
                    if (entry == null) Loading() else TextHomeScreen(
                        repository = repository,
                        entry = entry,
                        appVersion = appVersion,
                        onRead = { screen = Screen.Reader(s.slug) },
                        onBack = { screen = Screen.Library },
                        onSearch = { screen = Screen.Search(s) },
                    )
                    PlatformBackHandler { screen = Screen.Library }
                }
                is Screen.Reader -> {
                    val data = current
                    if (data == null || data.slug != s.slug) Loading() else {
                        ReaderScreen(
                            repository = repository,
                            data = data,
                            settings = settings,
                            onSettingsChange = { settings = it; settingsStore.save(it) },
                            onHelp = { showIntro = true },
                            onBack = { screen = Screen.TextHome(s.slug) },
                            onHome = { screen = Screen.Library },
                            onSearch = { screen = Screen.Search(s) },
                            startLine = settingsStore.lastLine(s.slug) ?: 1L,
                            onPositionChange = { settingsStore.saveLastText(s.slug); settingsStore.saveLastLine(s.slug, it) },
                            appVersion = appVersion,
                        )
                        if (showIntro) {
                            IntroDialog(onDismiss = { showIntro = false; settingsStore.markIntroSeen() })
                        }
                        PlatformBackHandler { screen = Screen.TextHome(s.slug) }
                    }
                }
            }
        }
    }
}

@Composable
private fun Loading() {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
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
