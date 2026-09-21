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
import no.anagnosis.data.WorkData
import no.anagnosis.prefs.ColorTheme
import no.anagnosis.prefs.ReaderSettings
import no.anagnosis.prefs.SettingsStore

const val WORK_SLUG = "antigone"

@Composable
fun App(repository: AnagnosisRepository, settingsStore: SettingsStore, appVersion: String) {
    var settings by remember { mutableStateOf(settingsStore.load()) }
    var showIntro by remember { mutableStateOf(false) }  // the home page covers the first-launch introduction
    val systemDark = isSystemInDarkTheme()
    val colors = remember(settings.theme, systemDark) { colorScheme(settings.theme, systemDark) }
    MaterialTheme(colorScheme = colors) {
        Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            var data by remember { mutableStateOf<WorkData?>(null) }
            LaunchedEffect(Unit) {
                data = withContext(Dispatchers.Default) { repository.loadWork(WORK_SLUG) }
            }
            val loaded = data
            var showHome by remember { mutableStateOf(settingsStore.lastLine() == null) }
            var homeDocument by remember { mutableStateOf<String?>(null) }
            if (loaded == null) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            } else if (showHome) {
                HomeScreen(
                    repository = repository,
                    data = loaded,
                    appVersion = appVersion,
                    onRead = { showHome = false },
                    onOpenDocument = { homeDocument = it },
                )
                homeDocument?.let { slug ->
                    val doc = remember(slug) { repository.document(loaded, slug) }
                    if (doc != null) DocumentSheet(doc, onDismiss = { homeDocument = null }) else homeDocument = null
                }
            } else {
                ReaderScreen(
                    repository = repository,
                    data = loaded,
                    settings = settings,
                    onSettingsChange = { settings = it; settingsStore.save(it) },
                    onHelp = { showIntro = true },
                    onHome = { showHome = true },
                    startLine = settingsStore.lastLine() ?: 1L,
                    onPositionChange = { settingsStore.saveLastLine(it) },
                    appVersion = appVersion,
                )
                if (showIntro) {
                    IntroDialog(onDismiss = { showIntro = false; settingsStore.markIntroSeen() })
                }
            }
        }
    }
}

private fun colorScheme(theme: ColorTheme, systemDark: Boolean): ColorScheme {
    if (theme == ColorTheme.SYSTEM) return if (systemDark) darkColorScheme() else lightColorScheme()
    val base = if (theme.dark) darkColorScheme() else lightColorScheme()
    val bg = Color(theme.background)
    val fg = Color(theme.text)
    val raised = lerp(bg, fg, 0.06f) // sheets and dialogs, slightly lifted from the page
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
