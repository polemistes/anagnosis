package no.anagnosis.data

import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
import no.anagnosis.db.Tokens
import no.anagnosis.db.Works
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class NotesTest {
    private val word = Regex("[\\p{L}\\p{M}᾽ʼ']+")

    /** A text from (n_int, n_sub, text) rows; every word of a line is a token, punctuation is not. */
    private fun text(
        rows: List<Triple<Long, String, String>>,
        verses: Boolean = false,
        stephanus: Boolean = false,
        bookNumbered: Boolean = false,
        sections: List<Sections> = emptyList(),
    ): WorkData {
        var tokenId = 1L
        val lines = rows.mapIndexed { i, (n, sub, t) ->
            Lines(i + 1L, 1, i.toLong(), "$n$sub", n, sub, null, null, 0, t)
        }
        val tokens = lines.associate { line ->
            line.id to word.findAll(line.text).mapIndexed { k, m ->
                Tokens(tokenId++, line.id, k.toLong(), m.range.first.toLong(), m.range.last + 1L, m.value, m.value, m.value, "", null, null, null, null)
            }.toList()
        }
        return WorkData(
            "test", Works(1, "test", "Test", "Author", "grc", null, null, null), lines, tokens, emptyMap(),
            sections.groupBy { it.first_line_id!! }, emptyList(), emptyList(), emptySet(),
            bookNumbered = bookNumbered, stephanus = stephanus, verses = verses,
        )
    }

    private val antigone = text(listOf(
        Triple(1L, "", "ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα,"),
        Triple(2L, "", "ἆρ᾽ οἶσθ᾽ ὅ τι Ζεὺς τῶν ἀπ᾽ Οἰδίπου κακῶν"),
        Triple(3L, "", "| ὁποῖον οὐχὶ νῷν ἔτι ζώσαιν τελεῖ;"),
        Triple(4L, "", "οὐδὲν γὰρ οὔτ᾽ ἀλγεινὸν οὔτ᾽ ἄτης ἄτερ"),
    ))

    private fun note(from: WordAnchor, to: WordAnchor, quote: String, id: Long = 1, body: String = "A note.") =
        Note(id, "test", from, to, quote, body, 0, 0)

    private fun a(n: Long, word: Long, sub: String = "") = WordAnchor(n, sub, word)

    @Test
    fun aOneLineNoteIsPlacedAndQuoted() {
        val p = Notes.placementOf(note(a(1, 1), a(1, 3), "κοινὸν αὐτάδελφον Ἰσμήνης"), antigone)
        assertNotNull(p)
        assertEquals("κοινὸν", p.firstToken.form)
        assertEquals("Ἰσμήνης", p.lastToken.form)
        assertEquals("κοινὸν αὐτάδελφον Ἰσμήνης", Notes.quote(antigone, p))
    }

    @Test
    fun aQuoteRunsOverLinesWithoutVerseMarks() {
        // an empty stored quote has no end words to compare
        assertNull(Notes.placementOf(note(a(1, 3), a(4, 1), ""), antigone))
        val placed = Notes.placementOf(note(a(1, 3), a(4, 1), "Ἰσμήνης κάρα, ἆρ᾽ οἶσθ᾽ ὅ τι Ζεὺς τῶν ἀπ᾽ Οἰδίπου κακῶν ὁποῖον οὐχὶ νῷν ἔτι ζώσαιν τελεῖ; οὐδὲν γὰρ"), antigone)
        assertNotNull(placed)
        assertEquals("Ἰσμήνης κάρα, ἆρ᾽ οἶσθ᾽ ὅ τι Ζεὺς τῶν ἀπ᾽ Οἰδίπου κακῶν ὁποῖον οὐχὶ νῷν ἔτι ζώσαιν τελεῖ; οὐδὲν γὰρ", Notes.quote(antigone, placed))
    }

    @Test
    fun aMissingLineOrWordLeavesTheNoteUnplaced() {
        assertNull(Notes.placementOf(note(a(1, 1), a(9, 0), "κοινὸν"), antigone))
        assertNull(Notes.placementOf(note(a(1, 1), a(1, 40), "κοινὸν"), antigone))
        assertNull(Notes.placementOf(note(a(1, 1), a(1, 1, "a"), "κοινὸν"), antigone))
    }

    @Test
    fun aChangedQuoteWithTheSameEndWordsIsStillPlaced() {
        // an accent corrected inside the passage, and the end words stored with other diacritics
        assertNotNull(Notes.placementOf(note(a(1, 1), a(1, 3), "κοινον αὐτἀδελφον Ισμηνης"), antigone))
    }

    @Test
    fun aChangedQuoteWithOtherEndWordsIsNotPlaced() {
        // the edition was renumbered: line 1 now holds other words
        assertNull(Notes.placementOf(note(a(1, 1), a(1, 3), "οἶσθ᾽ ὅ τι"), antigone))
    }

    @Test
    fun aPassageEndingBeforeItBeginsIsNotPlaced() {
        assertNull(Notes.placementOf(note(a(2, 0), a(1, 1), "ἆρ᾽ κοινὸν"), antigone))
        assertNull(Notes.placementOf(note(a(1, 3), a(1, 1), "Ἰσμήνης κοινὸν"), antigone))
    }

    @Test
    fun orderOfAnchors() {
        assertTrue(Notes.isBefore(antigone, a(1, 4), a(2, 0)))
        assertTrue(Notes.isBefore(antigone, a(2, 0), a(2, 1)))
        assertFalse(Notes.isBefore(antigone, a(2, 1), a(2, 1)))
        assertFalse(Notes.isBefore(antigone, a(3, 0), a(1, 4)))
    }

    @Test
    fun spansCoverEachLineFromTheFirstWordToTheLast() {
        val placed = Notes.place(listOf(note(a(1, 3), a(3, 1), "Ἰσμήνης κάρα, ἆρ᾽ οἶσθ᾽ ὅ τι Ζεὺς τῶν ἀπ᾽ Οἰδίπου κακῶν ὁποῖον οὐχὶ", id = 7)), antigone)
        val spans = Notes.spansByLine(placed, antigone)
        assertEquals(setOf(1L, 2L, 3L), spans.keys)
        val l1 = antigone.lines[0].text
        val s1 = spans.getValue(1L).single()
        assertEquals("Ἰσμήνης κάρα", l1.substring(s1.start, s1.end))
        val l2 = antigone.lines[1].text
        val s2 = spans.getValue(2L).single()
        assertEquals(l2, l2.substring(s2.start, s2.end))
        val l3 = antigone.lines[2].text
        val s3 = spans.getValue(3L).single()
        assertEquals("ὁποῖον οὐχὶ", l3.substring(s3.start, s3.end))
        assertEquals(7L, s3.noteId)
    }

    @Test
    fun unplacedNotesHaveNoSpans() {
        val placed = Notes.place(listOf(note(a(1, 1), a(1, 3), "other words here")), antigone)
        assertNull(placed.single().placement)
        assertTrue(Notes.spansByLine(placed, antigone).isEmpty())
    }

    @Test
    fun headingsFollowTheTextsCitation() {
        assertEquals("Line 12", Notes.rangeLabel(antigone, a(12, 0), a(12, 3)))
        assertEquals("Lines 12–14", Notes.rangeLabel(antigone, a(12, 0), a(14, 3)))
        assertEquals("Lines 591–591a", Notes.rangeLabel(antigone, a(591, 0), a(591, 0, "a")))

        val plato = text(listOf(Triple(172001L, "", "δοκῶ μοι περὶ ὧν πυνθάνεσθε"), Triple(172103L, "", "οὐκ ἀμελέτητος εἶναι")), stephanus = true)
        assertEquals("Lines 172a1–172b3", Notes.rangeLabel(plato, a(172001, 0), a(172103, 1)))

        val odyssey = text(listOf(Triple(1001L, "", "ἄνδρα μοι ἔννεπε"), Triple(1003L, "", "πολλῶν δ᾽ ἀνθρώπων")), bookNumbered = true)
        assertEquals("Lines 1.1–1.3", Notes.rangeLabel(odyssey, a(1001, 0), a(1003, 1)))

        val matthew = text(
            listOf(Triple(1005003L, "", "μακάριοι οἱ πτωχοὶ"), Triple(1005007L, "", "μακάριοι οἱ ἐλεήμονες")),
            verses = true,
            sections = listOf(Sections(1, 1, 0, 1, "book", "Matthew · ΚΑΤΑ ΜΑΘΘΑΙΟΝ", 1)),
        )
        assertEquals("Matthew 5:3–7", Notes.rangeLabel(matthew, a(1005003, 0), a(1005007, 2)))
        assertEquals("Matthew 5:3", Notes.rangeLabel(matthew, a(1005003, 0), a(1005003, 2)))
    }

    @Test
    fun markdownListsPlacedNotesThenLostOnes() {
        val placed = Notes.place(listOf(
            note(a(1, 0), a(1, 4), "ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα", id = 1, body = "Vocative.\n"),
            note(a(9, 0), a(9, 1), "οὐ γάρ", id = 2, body = "Lost."),
        ), antigone)
        val md = Notes.markdown(antigone, "Antigone", "Sophocles", "Jebb 1900.", placed)
        assertEquals(
            """
            # Notes on Antigone

            Sophocles, Antigone. Edition: Jebb 1900.
            Exported from Anagnosis.

            ## Line 1

            > ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα

            Vocative.

            ## Passages not found in the current text

            ### Line 9

            > οὐ γάρ

            Lost.

            """.trimIndent(),
            md,
        )
    }
}
