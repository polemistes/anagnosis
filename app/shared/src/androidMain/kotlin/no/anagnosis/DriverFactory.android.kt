package no.anagnosis

import android.content.Context
import app.cash.sqldelight.db.SqlDriver
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import no.anagnosis.db.AnagnosisDatabase
import no.anagnosis.lexdb.LexiconDatabase
import java.io.File
import java.util.zip.Inflater

private const val ASSET_DIR = "data"
private const val PREFS = "anagnosis"

actual class DriverFactory(private val context: Context) {

    actual fun createDriver(name: String): SqlDriver {
        installBundleIfNeeded(name)
        val schema = if (name == "lexicon") LexiconDatabase.Schema else AnagnosisDatabase.Schema
        return AndroidSqliteDriver(schema, context, "$name.sqlite")
    }

    actual fun installedTexts(): List<String> {
        val bundled = (context.assets.list(ASSET_DIR) ?: emptyArray())
            .filter { it.endsWith(".sqlite") }.map { it.removeSuffix(".sqlite") }
        val downloaded = (downloadDir().listFiles() ?: emptyArray())
            .filter { it.name.endsWith(".sqlite") }.map { it.name.removeSuffix(".sqlite") }
        return (bundled + downloaded).filter { it != "lexicon" }.distinct().sorted()
    }

    actual fun readCatalog(): String? = try {
        context.assets.open("$ASSET_DIR/catalog.json").bufferedReader().use { it.readText() }
    } catch (e: Exception) {
        null
    }

    private fun downloadDir(): File = File(context.filesDir, "texts").also { it.mkdirs() }

    /** Copy a bundled database out of the assets on first run and whenever its version changes. */
    private fun installBundleIfNeeded(name: String) {
        val target = context.getDatabasePath("$name.sqlite")
        val downloaded = File(downloadDir(), "$name.sqlite")
        if (downloaded.exists()) {
            if (!target.exists() || target.lastModified() < downloaded.lastModified()) {
                target.parentFile?.mkdirs()
                downloaded.copyTo(target, overwrite = true)
            }
            return
        }
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val key = "bundle_hash_$name"
        val available = try {
            context.assets.open("$ASSET_DIR/$name.sqlite.version").bufferedReader().use { it.readText().trim() }
        } catch (e: Exception) {
            return  // not bundled
        }
        if (target.exists() && prefs.getString(key, null) == available) return
        target.parentFile?.mkdirs()
        context.assets.open("$ASSET_DIR/$name.sqlite").use { input ->
            target.outputStream().use { output -> input.copyTo(output) }
        }
        prefs.edit().putString(key, available).apply()
    }
}

actual fun inflate(data: ByteArray): String {
    val inflater = Inflater()
    inflater.setInput(data)
    val out = java.io.ByteArrayOutputStream(data.size * 4)
    val buf = ByteArray(8192)
    while (!inflater.finished()) {
        val n = inflater.inflate(buf)
        if (n == 0 && (inflater.needsInput() || inflater.needsDictionary())) break
        out.write(buf, 0, n)
    }
    inflater.end()
    return out.toString("UTF-8")
}
