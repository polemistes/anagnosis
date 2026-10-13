package no.anagnosis.ui

import androidx.compose.ui.text.input.TextFieldValue
import kotlin.test.Test
import kotlin.test.assertEquals
import no.anagnosis.data.SearchOptions
import no.anagnosis.data.SearchSource
import no.anagnosis.greek.InputScheme
import no.anagnosis.prefs.ReaderSettings

class StatusLineTest {
    private val settings = ReaderSettings(inputScheme = InputScheme.BETA)

    @Test
    fun emptyWhenNothingIsSet() {
        val s = SearchState()
        assertEquals("", s.statusLine(settings, null))
        s.mode = SearchMode.TEXT
        assertEquals("Greek, Translation", s.statusLine(settings, "antigone"))
        // no source chosen: nothing will be searched, and the line says nothing
        s.sources = emptySet()
        s.query = TextFieldValue("logos")
        assertEquals("", s.statusLine(settings, "antigone"))
    }

    @Test
    fun echoesTheGreekThatLatinLettersMake() {
        val s = SearchState()
        s.query = TextFieldValue("logos")
        assertEquals("λογος", s.statusLine(settings, null))
        s.query = TextFieldValue("λόγος")
        assertEquals("", s.statusLine(settings, null))
    }

    @Test
    fun namesTheChoicesAwayFromTheUsual() {
        val s = SearchState()
        s.mode = SearchMode.TEXT
        s.query = TextFieldValue("logos")
        s.options = SearchOptions(wholeWords = true, regex = true)
        s.thisText = false
        s.sources = setOf(SearchSource.GREEK, SearchSource.COMMENTARY)
        assertEquals("λογος · Whole words · Regex · All texts · Greek, Commentary", s.statusLine(settings, "antigone"))
        // on the front page there is no text to be "this text"
        assertEquals("λογος · Whole words · Regex · Greek, Commentary", s.statusLine(settings, null))
        s.searchEnglish = true
        assertEquals("English · Whole words · Regex · Greek, Commentary", s.statusLine(settings, null))
        s.sources = SearchSource.entries.toSet()
        assertEquals("English · Whole words · Regex · All sources", s.statusLine(settings, null))
    }

    @Test
    fun analysisAndEnglishToGreek() {
        val s = SearchState()
        s.mode = SearchMode.ANALYSER
        assertEquals("Diacritics", s.statusLine(settings.copy(exactDiacritics = true), null))
        s.mode = SearchMode.DICTIONARY
        s.englishOffered = true
        s.english = true
        s.query = TextFieldValue("abandon")
        assertEquals("Woodhouse", s.statusLine(settings, null))
    }
}
