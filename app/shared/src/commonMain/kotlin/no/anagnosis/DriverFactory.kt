package no.anagnosis

import app.cash.sqldelight.db.SqlDriver

/**
 * Platform access to the data bundles: the shared lexicon database, the catalog of texts, and
 * one database per text. Bundled databases are copied out of the app package on first use and
 * whenever their version changes; downloaded texts live next to them.
 */
expect class DriverFactory {
    /** Opens the database called `name` (e.g. "lexicon", "antigone"), installing it first if needed. */
    fun createDriver(name: String): SqlDriver

    /** Slugs of the texts whose database is available (bundled or downloaded). */
    fun installedTexts(): List<String>

    /** The catalog of texts as JSON text, or null when absent. */
    fun readCatalog(): String?
}

/** Decompresses zlib data to a UTF-8 string (the shared lexicon stores entries this way). */
expect fun inflate(data: ByteArray): String
