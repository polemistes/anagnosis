package no.anagnosis

import app.cash.sqldelight.db.SqlDriver

/** Platform-specific: opens the prebuilt bundle shipped with the app. */
expect class DriverFactory {
    fun createDriver(): SqlDriver
}
