package no.anagnosis.prefs

enum class FontChoice(val label: String) {
    SYSTEM("System"),
    GENTIUM("Gentium Plus"),
    CARDO("Cardo"),
    DIDOT("GFS Didot"),
    NEOHELLENIC("GFS Neohellenic"),
}

/** Background and text colour presets. SYSTEM follows the device's light/dark setting. */
enum class ColorTheme(val label: String, val background: Long, val text: Long, val dark: Boolean) {
    SYSTEM("System", 0, 0, false),
    PAPER("Paper", 0xFFFFFFFF, 0xFF1A1A1A, false),
    SEPIA("Sepia", 0xFFF4ECD8, 0xFF4A3B2A, false),
    GREY("Grey", 0xFF2E2E2E, 0xFFD8D8D8, true),
    BLACK("Black", 0xFF000000, 0xFFC8C8C8, true),
}

enum class LineNumberMode(val label: String) { ALL("All"), FIFTH("Every 5th"), NONE("None") }

data class ReaderSettings(
    val font: FontChoice = FontChoice.SYSTEM,
    val fontSize: Int = 17,
    val theme: ColorTheme = ColorTheme.SYSTEM,
    val lineNumbers: LineNumberMode = LineNumberMode.FIFTH,
    /** End a Greek page early when its translation would not fit on one screen. */
    val fitTranslation: Boolean = false,
) {
    companion object {
        const val MIN_SIZE = 13
        const val MAX_SIZE = 26
    }
}

/** Platform key-value storage for the settings. */
expect class SettingsStore {
    fun load(): ReaderSettings
    fun save(settings: ReaderSettings)
    fun introSeen(): Boolean
    fun markIntroSeen()
    /** Line number (n_int) of the page last read, or null when reading has not started. */
    fun lastLine(): Long?
    fun saveLastLine(nInt: Long)
}
