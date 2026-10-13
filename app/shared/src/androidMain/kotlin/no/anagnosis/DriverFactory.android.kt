package no.anagnosis

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import app.cash.sqldelight.db.SqlDriver
import app.cash.sqldelight.driver.android.AndroidSqliteDriver
import no.anagnosis.data.TextOwnership
import no.anagnosis.db.AnagnosisDatabase
import no.anagnosis.lexdb.LexiconDatabase
import no.anagnosis.notesdb.NotesDatabase
import java.io.File
import java.util.zip.Inflater

private const val ASSET_DIR = "data"
private const val PREFS = "anagnosis"
/** Preference key prefix: the version of a text copied in from its asset pack. */
private const val PACK_TEXT = "pack_text_"

/**
 * A text comes onto the device in one of two ways. Bought in the reader, it arrives as an asset
 * pack from the store, which [DriverFactory.installPackText] copies in. Or it is a small app of
 * its own (e.g. no.anagnosis.odyssey) whose assets hold data/<slug>.sqlite, its .version and
 * data/<slug>.catalog.json, and whose launcher activity also answers this action: the reader
 * copies the text in from every such app signed with its own key, and drops it again when the
 * app is uninstalled (unless it was also bought in the reader): the text belongs to the purchase.
 */
const val TEXT_APP_ACTION = "no.anagnosis.action.TEXT"

actual class DriverFactory(private val context: Context) {

    actual fun createDriver(name: String): SqlDriver {
        installBundleIfNeeded(name)
        val schema = if (name == "lexicon") LexiconDatabase.Schema else AnagnosisDatabase.Schema
        return AndroidSqliteDriver(schema, context, "$name.sqlite")
    }

    actual fun createNotesDriver(): SqlDriver = AndroidSqliteDriver(NotesDatabase.Schema, context, NOTES_DB)

    actual fun installedTexts(owned: Set<String>): List<String> {
        importTextApps()
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val bundled = (context.assets.list(ASSET_DIR) ?: emptyArray())
            .filter { it.endsWith(".sqlite") }.map { it.removeSuffix(".sqlite") }
        val downloaded = (downloadDir().listFiles() ?: emptyArray())
            .filter { it.name.endsWith(".sqlite") }.map { it.name.removeSuffix(".sqlite") }
        val fromApps = downloaded.filter { prefs.contains("app_text_pkg_$it") }
        val fromStore = downloaded.filter { prefs.contains("$PACK_TEXT$it") }
        // a downloaded text of neither kind (none so far) is shown as it is
        val other = downloaded - fromApps.toSet() - fromStore.toSet()
        return TextOwnership.installed(bundled + other, fromApps, fromStore, owned)
    }

    /** Texts on the device that came from a text app, which the store need not fetch. */
    fun textsFromApps(): List<String> {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        return prefs.all.keys.filter { it.startsWith("app_text_pkg_") }.map { it.removePrefix("app_text_pkg_") }
            .filter { File(downloadDir(), "$it.sqlite").exists() }
    }

    /** The version of a text downloaded from the store, or null when it is not on the device. */
    fun packTextVersion(slug: String): String? {
        if (!File(downloadDir(), "$slug.sqlite").exists()) return null
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("$PACK_TEXT$slug", null)
    }

    /**
     * Copies a text bought in the reader in from its asset pack, whose assets are at [assetsPath]
     * (data/<slug>.sqlite and its .version); the store's copy can then be removed. A text being
     * read keeps its open copy until the reader next opens it.
     */
    fun installPackText(slug: String, assetsPath: String) {
        val version = File(assetsPath, "$ASSET_DIR/$slug.sqlite.version").readText().trim()
        val tmp = File(downloadDir(), "$slug.sqlite.part")
        File(assetsPath, "$ASSET_DIR/$slug.sqlite").inputStream().use { input -> tmp.outputStream().use { input.copyTo(it) } }
        if (!tmp.renameTo(File(downloadDir(), "$slug.sqlite"))) {
            tmp.delete()
            throw java.io.IOException("could not install $slug")
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString("$PACK_TEXT$slug", version).apply()
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
        // a text that came from an app which is no longer installed goes with it, unless it was
        // also bought in the reader
        for (key in prefs.all.keys.filter { it.startsWith("app_text_pkg_") }) {
            val slug = key.removePrefix("app_text_pkg_")
            if (slug in present) continue
            if (!prefs.contains("$PACK_TEXT$slug")) {
                File(downloadDir(), "$slug.sqlite").delete()
                File(downloadDir(), "$slug.catalog.json").delete()
                context.getDatabasePath("$slug.sqlite").delete()
            }
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
