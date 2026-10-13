package no.anagnosis.data

import kotlin.coroutines.cancellation.CancellationException
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNull
import kotlin.test.assertTrue

class TextSearchTest {
    private val greek = SearchDoc(
        "odyssey", SearchSource.GREEK, "", listOf(
            SearchUnit(1001, "", "Ἄνδρα μοι ἔννεπε, Μοῦσα, πολύτροπον, ὃς μάλα πολλὰ"),
            SearchUnit(1002, "", "πλάγχθη, ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν·"),
            SearchUnit(1003, "a", "| πολλῶν δʼ ἀνθρώπων ἴδεν ἄστεα"),
        ),
    )
    private val english = SearchDoc(
        "odyssey", SearchSource.TRANSLATION, "Translation", listOf(
            SearchUnit(1001, "", "Tell me, O Muse, of the man of many devices, who wandered full many ways after he had sacked the sacred citadel of Troy. Many were the men whose cities he saw."),
        ),
    )
    private val notes = SearchDoc(
        "odyssey", SearchSource.NOTES, "Note", listOf(SearchUnit(1002, "", "Troy: compare Iliad 2.", extra = 7)),
    )
    private val all = listOf(greek, english, notes)

    private fun find(q: String, o: SearchOptions = SearchOptions(), docs: List<SearchDoc> = all) = TextSearch.search(docs, q, o)

    @Test
    fun findsWithAccentsAndCaseIgnored() {
        val r = find("ανδρα")
        assertEquals(1, r.hits.size)
        val h = r.hits.single()
        assertEquals(1001L, h.nInt)
        assertEquals(0, h.start)
        assertEquals(5, h.end)
        assertEquals("Ἄνδρα", h.unitText.substring(h.start, h.end))
    }

    @Test
    fun hitsCarryTheirUnitAndOffsets() {
        val r = find("πολλ")
        assertEquals(listOf(1001L, 1003L), r.hits.map { it.nInt })
        val second = r.hits[1]
        assertEquals("a", second.nSub)
        assertEquals("πολλ", second.unitText.substring(second.start, second.end))
        val n = find("troy").hits
        assertEquals(listOf(SearchSource.TRANSLATION, SearchSource.NOTES), n.map { it.source })
        assertEquals(7L, n.last().extra)
    }

    @Test
    fun phraseOverTwoLinesBelongsToTheFirst() {
        val h = find("πολλα πλαγχθη").hits.single()
        assertEquals(1001L, h.nInt)
        assertEquals(h.unitText.length, h.end)
    }

    @Test
    fun wholeWords() {
        assertEquals(3, find("many", docs = listOf(english)).hits.size)
        assertEquals(1, find("man", SearchOptions(wholeWords = true), listOf(english)).hits.size)
        assertEquals(0, find("ma", SearchOptions(wholeWords = true), listOf(english)).hits.size)
    }

    @Test
    fun exactCase() {
        assertEquals(1, find("Many", SearchOptions(exactCase = true), listOf(english)).hits.size)
        assertEquals(3, find("Many", docs = listOf(english)).hits.size)
    }

    @Test
    fun exactAccents() {
        assertEquals(0, find("πολλα", SearchOptions(exactAccents = true), listOf(greek)).hits.size)
        assertEquals(1, find("πολλὰ", SearchOptions(exactAccents = true), listOf(greek)).hits.size)
    }

    @Test
    fun regexAlternation() {
        val r = find("ανδρα|ανθρωπ", SearchOptions(regex = true), listOf(greek))
        assertEquals(listOf(1001L, 1003L), r.hits.map { it.nInt })
        assertNull(r.error)
    }

    @Test
    fun invalidPatternGivesAnError() {
        val r = find("(ανδρ", SearchOptions(regex = true))
        assertEquals("Not a valid pattern", r.error)
        assertTrue(r.hits.isEmpty())
    }

    @Test
    fun zeroLengthMatchesAreSkipped() {
        assertTrue(find("x*", SearchOptions(regex = true), listOf(greek)).hits.isEmpty())
    }

    @Test
    fun emptyQueryFindsNothing() {
        assertTrue(find("   ").hits.isEmpty())
    }

    @Test
    fun manyHitsAreTruncated() {
        val big = SearchDoc("t", SearchSource.GREEK, "", List(TextSearch.MAX_HITS + 10) { SearchUnit(it.toLong(), "", "καὶ") })
        val r = TextSearch.search(listOf(big), "και", SearchOptions())
        assertEquals(TextSearch.MAX_HITS, r.hits.size)
        assertTrue(r.truncated)
    }

    @Test
    fun cancelledRegexStops() {
        val big = SearchDoc("t", SearchSource.GREEK, "", List(5000) { SearchUnit(it.toLong(), "", "ἄνδρα μοι ἔννεπε") })
        assertFailsWith<CancellationException> {
            TextSearch.search(listOf(big), "ν+ε", SearchOptions(regex = true)) { false }
        }
    }

    @Test
    fun excerpts() {
        val g = find("ανθρωπ").hits.single()
        val e = TextSearch.excerpt(g)
        assertEquals("πολλῶν δʼ ἀνθρώπων ἴδεν ἄστεα", e.text)
        assertEquals("ἀνθρώπ", e.text.substring(e.start, e.end))
        val t = find("citadel").hits.single()
        val x = TextSearch.excerpt(t)
        assertTrue(x.text.startsWith("…"))
        assertTrue(x.text.endsWith("saw."))
        assertEquals("citadel", x.text.substring(x.start, x.end))
        assertTrue(x.text[1] != ' ')
    }
}
