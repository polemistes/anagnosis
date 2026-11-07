package no.anagnosis.prefs

import android.content.Context
import no.anagnosis.greek.InputScheme

actual class SettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("anagnosis_settings", Context.MODE_PRIVATE)

    actual fun load(): ReaderSettings = ReaderSettings(
        font = prefs.getString("font", null)?.let { name -> FontChoice.entries.firstOrNull { it.name == name } } ?: FontChoice.SYSTEM,
        fontSize = prefs.getInt("font_size", 17).coerceIn(ReaderSettings.MIN_SIZE, ReaderSettings.MAX_SIZE),
        lineLength = prefs.getInt("line_length", 65).coerceIn(ReaderSettings.MIN_LINE_LENGTH, ReaderSettings.MAX_LINE_LENGTH),
        theme = prefs.getString("theme", null)?.let { name -> ColorTheme.entries.firstOrNull { it.name == name } } ?: ColorTheme.SYSTEM,
        lineNumbers = prefs.getString("line_numbers", null)?.let { name -> LineNumberMode.entries.firstOrNull { it.name == name } } ?: LineNumberMode.FIFTH,
        fitTranslation = prefs.getBoolean("fit_translation", false),
        wordFunction = prefs.getBoolean("word_function", true),
        disabledDictionaries = prefs.getString("disabled_dictionaries", "")!!.split(',').filter { it.isNotBlank() }.toSet(),
        inputScheme = prefs.getString("input_scheme", null)?.let { name -> InputScheme.entries.firstOrNull { it.name == name } } ?: InputScheme.BETA,
        exactDiacritics = prefs.getBoolean("exact_diacritics", false),
        greekKeyboard = prefs.getBoolean("greek_keyboard", false),
        noteMarks = prefs.getBoolean("note_marks", true),
        noteTicks = prefs.getBoolean("note_ticks", true),
        bookmarkTicks = prefs.getBoolean("bookmark_ticks", true),
        showDescription = prefs.getBoolean("show_description", true),
        pronunciation = no.anagnosis.greek.Pronunciation.fromKey(prefs.getString("pronunciation", null)),
        speechSpeed = prefs.getInt("speech_speed", 100).coerceIn(ReaderSettings.MIN_SPEED, ReaderSettings.MAX_SPEED),
        femaleVoice = prefs.getBoolean("female_voice", false),
        klattVoice = prefs.getBoolean("klatt_voice", false),
        speakSpeakers = prefs.getBoolean("speak_speakers", true),
        sentenceMelody = prefs.getBoolean("sentence_melody", false),
        screenReaderLines = prefs.getBoolean("screen_reader_lines", false),
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
            .putInt("line_length", settings.lineLength)
            .putString("theme", settings.theme.name)
            .putString("line_numbers", settings.lineNumbers.name)
            .putBoolean("fit_translation", settings.fitTranslation)
            .putBoolean("word_function", settings.wordFunction)
            .putString("disabled_dictionaries", settings.disabledDictionaries.sorted().joinToString(","))
            .putString("input_scheme", settings.inputScheme.name)
            .putBoolean("exact_diacritics", settings.exactDiacritics)
            .putBoolean("greek_keyboard", settings.greekKeyboard)
            .putBoolean("note_marks", settings.noteMarks)
            .putBoolean("note_ticks", settings.noteTicks)
            .putBoolean("bookmark_ticks", settings.bookmarkTicks)
            .putBoolean("show_description", settings.showDescription)
            .putString("pronunciation", settings.pronunciation?.key)
            .putInt("speech_speed", settings.speechSpeed)
            .putBoolean("female_voice", settings.femaleVoice)
            .putBoolean("klatt_voice", settings.klattVoice)
            .putBoolean("speak_speakers", settings.speakSpeakers)
            .putBoolean("sentence_melody", settings.sentenceMelody)
            .remove("speech_rate")
            .putBoolean("screen_reader_lines", settings.screenReaderLines)
            .apply()
    }
}
