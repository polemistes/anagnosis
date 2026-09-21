package no.anagnosis.prefs

import android.content.Context

actual class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("anagnosis_settings", Context.MODE_PRIVATE)

    actual fun load(): ReaderSettings = ReaderSettings(
        font = prefs.getString("font", null)?.let { name -> FontChoice.entries.firstOrNull { it.name == name } } ?: FontChoice.SYSTEM,
        fontSize = prefs.getInt("font_size", 17).coerceIn(ReaderSettings.MIN_SIZE, ReaderSettings.MAX_SIZE),
        theme = prefs.getString("theme", null)?.let { name -> ColorTheme.entries.firstOrNull { it.name == name } } ?: ColorTheme.SYSTEM,
        lineNumbers = prefs.getString("line_numbers", null)?.let { name -> LineNumberMode.entries.firstOrNull { it.name == name } } ?: LineNumberMode.FIFTH,
        fitTranslation = prefs.getBoolean("fit_translation", false),
    )

    actual fun introSeen(): Boolean = prefs.getBoolean("intro_seen", false)

    actual fun markIntroSeen() {
        prefs.edit().putBoolean("intro_seen", true).apply()
    }

    actual fun save(settings: ReaderSettings) {
        prefs.edit()
            .putString("font", settings.font.name)
            .putInt("font_size", settings.fontSize)
            .putString("theme", settings.theme.name)
            .putString("line_numbers", settings.lineNumbers.name)
            .putBoolean("fit_translation", settings.fitTranslation)
            .apply()
    }
}
