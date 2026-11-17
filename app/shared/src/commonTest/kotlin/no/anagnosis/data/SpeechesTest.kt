package no.anagnosis.data

import no.anagnosis.db.Lines
import no.anagnosis.db.Sections
import no.anagnosis.db.Tokens
import no.anagnosis.db.Works
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** A text of speeches numbered book.section (Lysias): the syntax label per speech and the chooser's titles. */
class SpeechesTest {
    private fun text(syntax: Boolean, byBook: Map<Int, String>, labels: Map<Int, String> = emptyMap()): WorkData {
        val ns = listOf(1001L, 1002L, 12001L, 13000L, 13001L, 26001L)
        val lines = ns.mapIndexed { i, n -> Lines(i + 1L, 1, i.toLong(), "${n / 1000}.${n % 1000}", n, "", null, null, 0, "λόγος") }
        val tokens = lines.associate { l ->
            l.id to listOf(Tokens(l.id, l.id, 0, 0, 5, "λόγος", "λόγος", "λογος", "n-s---mn-", null, null, "s${l.n_int / 1000}", null))
        }
        val sections = labels.map { (b, label) ->
            Sections(b.toLong(), 1, b.toLong(), 1, "book", label, lines.first { it.n_int / 1000 == b.toLong() }.id)
        }.groupBy { it.first_line_id!! }
        return WorkData("lysias", Works(1, "lysias", "Λυσίας", null, "grc", null, null, null), lines, tokens, emptyMap(),
            sections, emptyList(), emptyList(), emptySet(), bookNumbered = true, prose = true,
            automaticSyntax = syntax, syntaxByBook = byBook)
    }

    @Test
    fun theMetaValueIsReadBookByBook() {
        assertEquals(mapOf(1 to "manual", 14 to "manual", 12 to "none"), Book.parseSyntaxByBook("1=manual 14=manual 12=none"))
        assertEquals(emptyMap(), Book.parseSyntaxByBook(null))
        assertEquals(mapOf(2 to "automatic"), Book.parseSyntaxByBook(" x=manual 2=automatic 3= "))
    }

    @Test
    fun eachSpeechSaysWhoMadeItsSyntax() {
        val lysias = text(syntax = true, byBook = Book.parseSyntaxByBook("1=manual 12=none 13=none"))
        assertFalse(lysias.automaticSyntaxAt(1001))   // hand-made
        assertFalse(lysias.automaticSyntaxAt(12001))  // none
        assertTrue(lysias.automaticSyntaxAt(26001))   // the text's own: automatic
        assertFalse(lysias.automaticSyntaxOfSentence("s1"))
        assertTrue(lysias.automaticSyntaxOfSentence("s26"))
    }

    @Test
    fun aTextWithoutTheKeyIsAsBefore() {
        val auto = text(syntax = true, byBook = emptyMap())
        assertTrue(auto.automaticSyntaxAt(1001))
        assertTrue(auto.automaticSyntaxOfSentence("s1"))
        val hand = text(syntax = false, byBook = emptyMap())
        assertFalse(hand.automaticSyntaxAt(26001))
    }

    @Test
    fun aSpeechIsOfferedByNumberAndName() {
        val lysias = text(true, emptyMap(), mapOf(1 to "1 · Ὑπὲρ τοῦ Ἐρατοσθένους φόνου ἀπολογία", 12 to "12 · Κατὰ Ἐρατοσθένους",
            13 to "13 · Κατὰ Ἀγοράτου", 26 to "26 · Περὶ τῆς Εὐάνδρου δοκιμασίας"))
        val b = lysias.books.first { it.number == 12 }
        assertTrue(b.named)
        assertEquals("12 · Κατὰ Ἐρατοσθένους", b.title)
        assertEquals("12", b.name)
    }

    @Test
    fun anEpicsBooksKeepTheirOldTitles() {
        assertFalse(Book.hasTitle("1 · Α"))
        assertFalse(Book.hasTitle("24 · Ω"))
        assertFalse(Book.hasTitle("Matthew · ΚΑΤΑ ΜΑΘΘΑΙΟΝ"))  // the New Testament is named by `verses`
        assertEquals("Book 1 · Α", Book(1, "1 · Α", 1001, 1444, named = Book.hasTitle("1 · Α")).title)
        assertTrue(Book.hasTitle("3 · Πρὸς Σίμωνα ἀπολογία"))
    }

    @Test
    fun eachSpeechShowsTheTranslationItHas() {
        fun tr(id: Long, books: List<Long>) = TranslationData(
            no.anagnosis.db.Translations(id, 1, "t$id", "Speeches", null, "eng", null, null, null),
            books.mapIndexed { i, b -> no.anagnosis.db.Translation_segments(i + 1L, id, i.toLong(), "speech", null, 1, b * 1000 + 1, "", b * 1000 + 1, "", "English") })
        val base = text(true, emptyMap())
        val lysias = WorkData(base.slug, base.work, base.lines, base.tokensByLine, emptyMap(), emptyMap(),
            listOf(tr(1, listOf(2, 12)), tr(2, listOf(1, 26))), emptyList(), emptySet(), bookNumbered = true, prose = true)
        assertEquals(2L, lysias.translationFor(1000, 1999)?.translation?.id)   // Gillies's speech
        assertEquals(1L, lysias.translationFor(12000, 12999)?.translation?.id) // the 1898 version
        assertEquals(1L, lysias.translationFor(6000, 6999)?.translation?.id)   // none has it: the first
    }

    @Test
    fun aSectionRenderedWithTheOneBeforeShowsThatPassage() {
        fun seg(id: Long, from: Long, to: Long, kind: String = "speech") =
            no.anagnosis.db.Translation_segments(id, 2, id, kind, null, 0, from, "", to, "", "English $id")
        val segs = listOf(seg(1, 1002, 1002), seg(2, 1003, 1004), seg(3, 1005, 1005), seg(4, 1011, 1012))
        assertEquals(2L, TranslationPaging.covering(segs, 1004)?.id)   // 1.4 under 1.3
        assertEquals(4L, TranslationPaging.covering(segs, 1012)?.id)   // 1.12 under 1.11
        assertEquals(null, TranslationPaging.covering(segs, 1003))     // 1.3 has its own
        assertEquals(null, TranslationPaging.covering(segs, 1007))     // nothing covers it
        assertEquals(null, TranslationPaging.covering(listOf(seg(5, 1003, 1004, "stage")), 1004))
    }
}
