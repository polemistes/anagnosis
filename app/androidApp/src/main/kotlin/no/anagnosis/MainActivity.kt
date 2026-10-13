package no.anagnosis

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.prefs.SettingsStore
import no.anagnosis.shop.PlayTextShop
import no.anagnosis.ui.App

class MainActivity : ComponentActivity() {
    /** Counts the times the app comes to the front, so that newly installed texts are found. */
    private val resumes = mutableIntStateOf(0)

    /** The texts bought in the app, through Google Play. */
    private lateinit var shop: PlayTextShop

    /** A text to open, asked for by the app that sells it (extra "open_text"). */
    private val openText = mutableStateOf<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        val driverFactory = DriverFactory(applicationContext)
        val repository = AnagnosisRepository(driverFactory)
        shop = PlayTextShop(this, driverFactory, repository.textsOnSale())
        val settingsStore = SettingsStore(applicationContext)
        val version = packageManager.getPackageInfo(packageName, 0).versionName ?: "?"
        if (savedInstanceState == null) openText.value = intent?.getStringExtra(EXTRA_OPEN_TEXT)
        setContent {
            App(
                repository, settingsStore, version,
                resumeCount = resumes.intValue,
                openText = openText.value,
                onOpenTextHandled = { openText.value = null },
                shop = shop,
            )
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        intent.getStringExtra(EXTRA_OPEN_TEXT)?.let { openText.value = it }
    }

    override fun onResume() {
        super.onResume()
        resumes.intValue++
        // a purchase may have been made or refunded elsewhere, or a pending one completed
        shop.refresh()
    }

    override fun onDestroy() {
        shop.close()
        super.onDestroy()
    }

    companion object {
        const val EXTRA_OPEN_TEXT = "open_text"
    }
}
