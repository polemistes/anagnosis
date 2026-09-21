package no.anagnosis.prefs

import android.content.Context
import no.anagnosis.greek.InputScheme

actual class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("anagnosis_settings", Context.MODE_PRIVATE)

    actual fun load(): ReaderSettings = ReaderSettings(
        font = prefs.getString("font", null)?.let { name -> FontChoice.entries.firstOrNull { it.name == name } } ?: FontChoice.SYSTEM,
        fontSize = prefs.getInt("font_size", 17).coerceIn(ReaderSettings.MIN_SIZE, ReaderSettings.MAX_SIZE),
        theme = prefs.getString("theme", null)?.let { name -> ColorTheme.entries.firstOrNull { it.name == name } } ?: ColorTheme.SYSTEM,
        lineNumbers = prefs.getString("line_numbers", null)?.let { name -> LineNumberMode.entries.firstOrNull { it.name == name } } ?: LineNumberMode.FIFTH,
        fitTranslation = prefs.getBoolean("fit_translation", false),
        inputScheme = prefs.getString("input_scheme", null)?.let { name -> InputScheme.entries.firstOrNull { it.name == name } } ?: InputScheme.BETA,
        exactDiacritics = prefs.getBoolean("exact_diacritics", false),
        greekKeyboard = prefs.getBoolean("greek_keyboard", false),
    )

    actual fun introSeen(): Boolean = prefs.getBoolean("intro_seen", false)

    actual fun markIntroSeen() {
        prefs.edit().putBoolean("intro_seen", true).apply()
    }

    actual fun lastText(): String? = prefs.getString("last_text", null)

    actual fun saveLastText(slug: String) {
        prefs.edit().putString("last_text", slug).apply()
    }

    actual fun lastLine(slug: String): Long? = prefs.getLong("last_line_$slug", -1L).takeIf { it >= 0 }

    actual fun saveLastLine(slug: String, nInt: Long) {
        prefs.edit().putLong("last_line_$slug", nInt).apply()
    }

    actual fun save(settings: ReaderSettings) {
        prefs.edit()
            .putString("font", settings.font.name)
            .putInt("font_size", settings.fontSize)
            .putString("theme", settings.theme.name)
            .putString("line_numbers", settings.lineNumbers.name)
            .putBoolean("fit_translation", settings.fitTranslation)
            .putString("input_scheme", settings.inputScheme.name)
            .putBoolean("exact_diacritics", settings.exactDiacritics)
            .putBoolean("greek_keyboard", settings.greekKeyboard)
            .apply()
    }
}
