package no.anagnosis

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import app.cash.sqldelight.db.SqlDriver
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import no.anagnosis.db.AnagnosisDatabase
import no.anagnosis.lexdb.LexiconDatabase
import no.anagnosis.notesdb.NotesDatabase
import java.io.File
import java.util.zip.Inflater

private const val ASSET_DIR = "data"
private const val PREFS = "anagnosis"

/**
 * A text sold separately is a small app of its own (e.g. no.anagnosis.odyssey) whose assets hold
 * data/<slug>.sqlite, its .version and data/<slug>.catalog.json, and whose launcher activity
 * also answers this action. The reader copies the text in from every such app signed with its
 * own key, and drops it again when the app is uninstalled: the text belongs to the purchase.
 */
const val TEXT_APP_ACTION = "no.anagnosis.action.TEXT"

actual class DriverFactory(private val context: Context) {

    actual fun createDriver(name: String): SqlDriver {
        installBundleIfNeeded(name)
        val schema = if (name == "lexicon") LexiconDatabase.Schema else AnagnosisDatabase.Schema
        return AndroidSqliteDriver(schema, context, "$name.sqlite")
    }

    actual fun createNotesDriver(): SqlDriver = AndroidSqliteDriver(NotesDatabase.Schema, context, NOTES_DB)

    actual fun installedTexts(): List<String> {
        importTextApps()
        val bundled = (context.assets.list(ASSET_DIR) ?: emptyArray())
            .filter { it.endsWith(".sqlite") }.map { it.removeSuffix(".sqlite") }
        val downloaded = (downloadDir().listFiles() ?: emptyArray())
            .filter { it.name.endsWith(".sqlite") }.map { it.name.removeSuffix(".sqlite") }
        return (bundled + downloaded).filter { it != "lexicon" }.distinct().sorted()
    }

    actual fun readCatalog(): String? {
        val main = try {
            context.assets.open("$ASSET_DIR/catalog.json").bufferedReader().use { it.readText() }
        } catch (e: Exception) {
            null
        }
        // entries of texts added by their own apps, after the bundled catalog
        val extra = (downloadDir().listFiles() ?: emptyArray())
            .filter { it.name.endsWith(".catalog.json") }
            .joinToString("\n") { it.readText() }
        return listOfNotNull(main, extra.ifEmpty { null }).joinToString("\n").ifEmpty { null }
    }

    /** Copy in the texts of installed text apps; remove those whose app has gone. */
    private fun importTextApps() {
        val pm = context.packageManager
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val apps = try {
            pm.queryIntentActivities(Intent(TEXT_APP_ACTION), 0).map { it.activityInfo.packageName }.distinct()
        } catch (e: Exception) {
            emptyList()
        }
        val present = mutableSetOf<String>()
        for (pkg in apps) {
            if (pm.checkSignatures(context.packageName, pkg) != PackageManager.SIGNATURE_MATCH) continue
            val assets = try {
                context.createPackageContext(pkg, 0).assets
            } catch (e: Exception) {
                continue
            }
            val slugs = (assets.list(ASSET_DIR) ?: emptyArray()).filter { it.endsWith(".sqlite") }.map { it.removeSuffix(".sqlite") }
            for (slug in slugs) {
                present += slug
                val version = try {
                    assets.open("$ASSET_DIR/$slug.sqlite.version").bufferedReader().use { it.readText().trim() }
                } catch (e: Exception) {
                    continue
                }
                val target = File(downloadDir(), "$slug.sqlite")
                if (target.exists() && prefs.getString("app_text_$slug", null) == version) continue
                val tmp = File(downloadDir(), "$slug.sqlite.part")
                assets.open("$ASSET_DIR/$slug.sqlite").use { input -> tmp.outputStream().use { input.copyTo(it) } }
                tmp.renameTo(target)
                try {
                    val entry = assets.open("$ASSET_DIR/$slug.catalog.json").bufferedReader().use { it.readText() }
                    File(downloadDir(), "$slug.catalog.json").writeText(entry)
                } catch (e: Exception) {
                    // the library then names the text from its database
                }
                prefs.edit().putString("app_text_$slug", version).putString("app_text_pkg_$slug", pkg).apply()
            }
        }
        // a text that came from an app which is no longer installed goes with it
        for (key in prefs.all.keys.filter { it.startsWith("app_text_pkg_") }) {
            val slug = key.removePrefix("app_text_pkg_")
            if (slug in present) continue
            File(downloadDir(), "$slug.sqlite").delete()
            File(downloadDir(), "$slug.catalog.json").delete()
            context.getDatabasePath("$slug.sqlite").delete()
            prefs.edit().remove(key).remove("app_text_$slug").apply()
        }
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

/** The reader's notes; no text is ever called "notes", and nothing that installs or removes texts touches it. */
private const val NOTES_DB = "notes.sqlite"

actual fun nowMillis(): Long = System.currentTimeMillis()

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
