package no.anagnosis

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import no.anagnosis.data.AnagnosisRepository
import no.anagnosis.prefs.SettingsStore
import no.anagnosis.ui.App

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        val repository = AnagnosisRepository(DriverFactory(applicationContext))
        val settingsStore = SettingsStore(applicationContext)
        val version = packageManager.getPackageInfo(packageName, 0).versionName ?: "?"
        setContent {
            App(repository, settingsStore, version)
        }
    }
}
