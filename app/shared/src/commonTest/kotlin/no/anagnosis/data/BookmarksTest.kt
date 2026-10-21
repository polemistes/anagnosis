package no.anagnosis.data

import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
import no.anagnosis.db.Tokens
import no.anagnosis.db.Works
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

class BookmarksTest {
    private val word = Regex("[\\p{L}\\p{M}᾽ʼ']+")

    /** A text from (n_int, n_sub, text) rows; every word of a line is a token, punctuation and a speaker label in braces are not. */
    private fun text(rows: List<Triple<Long, String, String>>, verses: Boolean = false, stephanus: Boolean = false, sections: List<Sections> = emptyList()): WorkData {
        var tokenId = 1L
        val lines = rows.mapIndexed { i, (n, sub, t) -> Lines(i + 1L, 1, i.toLong(), "$n$sub", n, sub, null, null, 0, t) }
        val tokens = lines.associate { line ->
            line.id to word.findAll(line.text).filter { m -> m.range.first == 0 || line.text[m.range.first - 1] != '{' }.mapIndexed { k, m ->
                Tokens(tokenId++, line.id, k.toLong(), m.range.first.toLong(), m.range.last + 1L, m.value, m.value, m.value, "", null, null, null, null)
            }.toList()
        }
        return WorkData(
            "test", Works(1, "test", "Test", "Author", "grc", null, null, null), lines, tokens, emptyMap(),
            sections.groupBy { it.first_line_id!! }, emptyList(), emptyList(), emptySet(),
            stephanus = stephanus, verses = verses,
        )
    }

    private val antigone = text(listOf(
        Triple(1L, "", "ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα,"),
        Triple(2L, "", "| ἆρ᾽ οἶσθ᾽ ὅ τι Ζεὺς τῶν ἀπ᾽ Οἰδίπου κακῶν"),
        Triple(3L, "", "{ΧΟ.} οὐδὲν γὰρ. οὔτ᾽ ἀλγεινὸν"),
    ))

    private fun token(n: Long, ord: Long) = antigone.tokensByLine.getValue(antigone.lines.first { it.n_int == n }.id)[ord.toInt()]

    private fun bookmark(n: Long, w: Long, quote: String, sub: String = "", name: String = "", id: Long = 1) =
        Bookmark(id, "test", WordAnchor(n, sub, w), name, quote, 0)

    @Test
    fun theQuoteIsEightWordsRunningOnPastAShortSentence() {
        assertEquals("ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα, ἆρ᾽ οἶσθ᾽ ὅ…", Bookmarks.quote(antigone, token(1, 0)))
        assertEquals("κάρα, ἆρ᾽ οἶσθ᾽ ὅ τι Ζεὺς τῶν ἀπ᾽…", Bookmarks.quote(antigone, token(1, 4)))
        // the speaker label stays in the text but is not a word; exactly eight words remain: no mark of a cut
        assertEquals("ὅ τι Ζεὺς τῶν ἀπ᾽ Οἰδίπου κακῶν ΧΟ. οὐδὲν…", Bookmarks.quote(antigone, token(2, 2)))
        assertEquals("τῶν ἀπ᾽ Οἰδίπου κακῶν ΧΟ. οὐδὲν γὰρ. οὔτ᾽ ἀλγεινὸν", Bookmarks.quote(antigone, token(2, 5)))
        // fewer than eight at the end of the text
        assertEquals("οὐδὲν γὰρ. οὔτ᾽ ἀλγεινὸν", Bookmarks.quote(antigone, token(3, 0)))
    }

    @Test
    fun aBookmarkIsPlacedWhenItsTextReadsAsItDid() {
        val placed = Bookmarks.placementOf(bookmark(1, 0, "ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα, ἆρ᾽ οἶσθ᾽ ὅ…"), antigone)
        assertNotNull(placed)
        assertEquals("ὦ", placed.second.form)
        assertNotNull(Bookmarks.placementOf(bookmark(3, 0, "οὐδὲν γὰρ. οὔτ᾽ ἀλγεινὸν"), antigone))
    }

    @Test
    fun aChangedTextWithTheSameFirstWordIsStillPlaced() {
        assertNotNull(Bookmarks.placementOf(bookmark(1, 0, "ὤ κοινον αὐτάδελφον"), antigone))
        assertNotNull(Bookmarks.placementOf(bookmark(1, 1, "κοινον"), antigone))
    }

    @Test
    fun aDifferentFirstWordOrAMissingPlaceIsUnplaced() {
        assertNull(Bookmarks.placementOf(bookmark(1, 0, "ἆρ᾽ οἶσθ᾽ ὅ τι"), antigone))
        assertNull(Bookmarks.placementOf(bookmark(9, 0, "ὦ κοινὸν"), antigone))
        assertNull(Bookmarks.placementOf(bookmark(1, 40, "ὦ κοινὸν"), antigone))
        assertNull(Bookmarks.placementOf(bookmark(1, 0, "ὦ κοινὸν", sub = "a"), antigone))
        assertNull(Bookmarks.placementOf(bookmark(1, 0, ""), antigone))
        val placed = Bookmarks.place(listOf(bookmark(1, 0, "ὦ", id = 1), bookmark(9, 0, "x", id = 2)), antigone)
        assertNotNull(placed[0].token)
        assertNull(placed[1].line)
    }

    @Test
    fun labelsFollowTheTextsCitation() {
        assertEquals("Line 1", Bookmarks.label(antigone, WordAnchor(1, "", 0)))
        assertEquals("Line 591a", Bookmarks.label(antigone, WordAnchor(591, "a", 2)))
        val plato = text(listOf(Triple(172001L, "", "δοκῶ μοι")), stephanus = true)
        assertEquals("Line 172a1", Bookmarks.label(plato, WordAnchor(172001, "", 0)))
        val matthew = text(
            listOf(Triple(1005003L, "", "μακάριοι οἱ πτωχοὶ")),
            verses = true,
            sections = listOf(Sections(1, 1, 0, 1, "book", "Matthew · ΚΑΤΑ ΜΑΘΘΑΙΟΝ", 1)),
        )
        assertEquals("Matthew 5:3", Bookmarks.label(matthew, WordAnchor(1005003, "", 0)))
    }
}
