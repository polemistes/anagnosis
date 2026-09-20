package no.anagnosis

import android.content.Context
import app.cash.sqldelight.db.SqlDriver
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import no.anagnosis.db.AnagnosisDatabase

private const val DB_NAME = "antigone.sqlite"
private const val PREFS = "anagnosis"
private const val KEY_BUNDLE_VERSION = "bundle_hash"

actual class DriverFactory(private val context: Context) {
    actual fun createDriver(): SqlDriver {
        installBundleIfNeeded()
        return AndroidSqliteDriver(AnagnosisDatabase.Schema, context, DB_NAME)
    }

    /** Copy the prebuilt database out of the APK assets on first run and whenever the bundle changes. */
    private fun installBundleIfNeeded() {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val installed = prefs.getString(KEY_BUNDLE_VERSION, null)
        val available = context.assets.open("$DB_NAME.version").bufferedReader().use { it.readText().trim() }
        val target = context.getDatabasePath(DB_NAME)
        if (target.exists() && installed == available) return
        target.parentFile?.mkdirs()
        context.assets.open(DB_NAME).use { input ->
            target.outputStream().use { output -> input.copyTo(output) }
        }
        prefs.edit().putString(KEY_BUNDLE_VERSION, available).apply()
    }
}
