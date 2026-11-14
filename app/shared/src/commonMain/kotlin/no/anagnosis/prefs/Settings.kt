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
    /** The text size in the sheets: dictionary entries, commentary, apparatus, documents, the reader's notes. */
    val sheetFontSize: Int = DEFAULT_SHEET_SIZE,
    /** The widest a column of text is set, in characters of Greek at the chosen size (so it grows with the text). */
    val lineLength: Int = 65,
    val theme: ColorTheme = ColorTheme.SYSTEM,
    val lineNumbers: LineNumberMode = LineNumberMode.FIFTH,
    /** End a Greek page early when its translation would not fit on one screen. */
    val fitTranslation: Boolean = false,
    /** The word popup names the word's function in its sentence (subject of φέρει). */
    val wordFunction: Boolean = true,
    /** Dictionaries (by slug: ml, lsj, abbott-smith, dodson ...) the reader has turned off. */
    val disabledDictionaries: Set<String> = emptySet(),
    /** Latin-letter input scheme for the dictionary search. */
    val inputScheme: no.anagnosis.greek.InputScheme = no.anagnosis.greek.InputScheme.BETA,
    /** Word analysis matches the typed diacritics exactly instead of ignoring them. */
    val exactDiacritics: Boolean = false,
    /** Show the app's own Greek keyboard in the search screen. */
    val greekKeyboard: Boolean = false,
    /** Underline the passages that carry one of the reader's notes. */
    val noteMarks: Boolean = true,
    /** Mark the pages that carry a note on the progress bar. */
    val noteTicks: Boolean = true,
    /** Mark the pages where a bookmarked sentence starts on the progress bar. */
    val bookmarkTicks: Boolean = true,
    /** Show the description of the app at the top of the front page. */
    val showDescription: Boolean = true,
    /** The pronunciation of the reading voice for every text; null reads each text in its own. */
    val pronunciation: no.anagnosis.greek.Pronunciation? = null,
    /** The speed of the reading voice, in per cent of the standard speed (100 words a minute). */
    val speechSpeed: Int = 100,
    /** The reading voice is a woman's rather than a man's. */
    val femaleVoice: Boolean = false,
    /** In a play or a dialogue, reading aloud says the speaker's name before each speech. */
    val speakSpeakers: Boolean = true,
    /** The reading voice is made by eSpeak's Klatt synthesiser (darker, softer) rather than the formant one. */
    val klattVoice: Boolean = false,
    /** Homeric and Attic: the pitch steps down over each sentence, falls at its end and rises before a question mark (see Melody). */
    val sentenceMelody: Boolean = false,
    /** With a screen reader: whole lines with look-up actions (for braille) instead of words one by one. */
    val screenReaderLines: Boolean = false,
) {
    companion object {
        const val MIN_SIZE = 13
        const val MAX_SIZE = 26
        /** The sheets' text size before it could be set: Material's body text. */
        const val DEFAULT_SHEET_SIZE = 14
        const val MIN_SHEET_SIZE = 12
        const val MAX_SHEET_SIZE = 26
        const val MIN_LINE_LENGTH = 40
        const val MAX_LINE_LENGTH = 100
        /** The slider moves the line length in steps of this many characters. */
        const val LINE_LENGTH_STEP = 5
        const val MIN_SPEED = 50
        const val MAX_SPEED = 200
    }
}

/** Platform key-value storage for the settings. */
expect class SettingsStore {
    fun load(): ReaderSettings
    fun save(settings: ReaderSettings)
    fun introSeen(): Boolean
    fun markIntroSeen()
    /** The text last read, or null when reading has not started. */
    fun lastText(): String?
    fun saveLastText(slug: String)
    /** Line number (n_int) of the page last read in a text, or null. */
    fun lastLine(slug: String): Long?
    fun saveLastLine(slug: String, nInt: Long)
}
