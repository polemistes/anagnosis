package no.anagnosis.data

import no.anagnosis.db.Sentence_nodes
import no.anagnosis.db.Tokens
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/**
 * Trees made on another text than the one printed (the Theogony's): the tree is shown as the tree
 * of that text, and the word sheet gives a role only where our word is the trees' own word.
 */
class SyntaxTextTest {
    private fun row(kind: String, tree: String? = null, token: Long? = 1, sentence: String? = "s", word: Int? = null,
                    same: Long? = null, postag: String? = null, difference: String? = null) =
        SyntaxTextWord(kind, token, sentence, word, tree, null, null, same, postag, difference)

    private fun reading(tree: String, difference: String?, same: Long? = 1) = row("reading", tree, same = same, difference = difference)

    @Test
    fun theRoleIsGivenOnlyForTheTreesOwnWord() {
        assertTrue(SyntaxText.showsRole(null, "Μουσάων"))                          // no record: as before
        assertTrue(SyntaxText.showsRole(row("unit", "αἵθ̓"), "αἵ"))
        assertTrue(SyntaxText.showsRole(reading("μοι", "elision"), "μʼ"))
        assertTrue(SyntaxText.showsRole(reading("τέκεν", "nu"), "τέκε"))
        assertTrue(SyntaxText.showsRole(reading("μιχθεὶς", "spelling"), "μειχθεὶς"))
        assertFalse(SyntaxText.showsRole(reading("νυκτὸς", "form"), "νύκτας"))
        assertFalse(SyntaxText.showsRole(reading("αὐδὴν", "word"), "ἀοιδὴν"))
        assertFalse(SyntaxText.showsRole(reading("παιπαλοέσσῃς", "spelling", same = 0), "παιπαλοέσσης"))
        assertFalse(SyntaxText.showsRole(row("absent"), "τᾷ"))
        // without the record of the difference: letters, not accents, capitals or elision marks
        assertTrue(SyntaxText.showsRole(reading("Δέ", null), "δὲ"))
        assertTrue(SyntaxText.showsRole(reading("θ̓", null), "θʼ"))
        assertFalse(SyntaxText.showsRole(reading("αὐδὴν", null), "ἀοιδὴν"))
        assertEquals("αἵθʼ", SyntaxText.elisionMark("αἵθ̓"))
    }

    private fun tok(id: Long, ord: Long, form: String, rel: String?, head: Long?, wordId: String?) =
        Tokens(id, 1, ord, 0, 0, form, form, form, "n-s---fa-", rel, head, "s", wordId)

    private val tokens = listOf(
        tok(1, 0, "Μουσάων", "ATR", 3, "1"),
        tok(2, 1, "ἀοιδὴν", "OBJ", 3, "2"),
        tok(3, 2, "ἀρχώμεθ", "PRED", 0, "3"),
    )
    private val extra = listOf(Sentence_nodes(1, 1, "s", 4, "ἔνι", null, "v3spia---", "ADV", 3, 0))

    @Test
    fun theTreeShowsTheTreesOwnWords() {
        val plain = Syntax.build("s", tokens, extra)
        val tree = Syntax.asTreesText(plain,
            mapOf(2L to row("reading", "αὐδὴν", token = 2, word = 2, same = 1, postag = "n-s---fa-", difference = "word")),
            mapOf(("s" to 4) to row("unprinted", "ἔνι", token = null, word = 4)))
        val read = tree.nodeFor(tokens[1])!!
        assertEquals("αὐδὴν", Syntax.displayForm(read))                  // the trees' word alone
        assertEquals("αὐδὴν", Syntax.headLabel(read))
        val unprinted = tree.nodes.single { it.id == 4 }
        assertEquals("ἔνι", Syntax.displayForm(unprinted))                 // like any other word, no brackets
        assertFalse(unprinted.isPunctuation)
        assertTrue(tree.isShown(unprinted))
        assertEquals("ἔνι", Syntax.headLabel(unprinted))
        assertTrue(plain.nodes.single { it.id == 4 }.isPunctuation)        // without the record it would be hidden
    }

    @Test
    fun aReadingInAnotherConstructionIsTheTreesNodeAndOurWordHasNoRole() {
        // 485: our τᾷ carries the sentence only; the trees' τῷ is a node of its own
        val ours = tok(5, 3, "τᾷ", null, null, null)
        val node = Sentence_nodes(2, 1, "s", 5, "τῷ", null, "d--------", "AuxY", 3, 0)
        val r = row("reading", "τῷ", token = 5, word = 5, same = 0, postag = "d--------", difference = "word")
        val tree = Syntax.asTreesText(Syntax.build("s", tokens + ours, listOf(node)), mapOf(5L to r), mapOf(("s" to 5) to r))
        val n = tree.nodes.single { it.id == 5 }
        assertEquals("τῷ", Syntax.displayForm(n))
        assertFalse(n.isPunctuation)
        assertNull(tree.nodeFor(ours))                                       // our word is not singled out
        assertFalse(SyntaxText.showsRole(r, "τᾷ"))
    }

    @Test
    fun onlyRealDifferencesAreMarkedOnEitherSide() {
        // 31: μʼ / μοι (elision) is not a difference, ἀοιδὴν / αὐδὴν (another word) is
        val ws = listOf(tok(1, 0, "ἐνέπνευσαν", "PRED", 0, "1"), tok(2, 1, "δέ", "AuxY", 1, "2"),
            tok(3, 2, "μʼ", "OBJ", 1, "3"), tok(4, 3, "ἀοιδὴν", "OBJ", 1, "4"))
        val byToken = mapOf(
            3L to row("reading", "μοι", token = 3, word = 3, same = 1, difference = "elision"),
            4L to row("reading", "αὐδὴν", token = 4, word = 4, same = 1, difference = "word"))
        val tree = Syntax.asTreesText(Syntax.build("s", ws, emptyList()), byToken, emptyMap())
        val moi = tree.nodeFor(ws[2])!!
        assertEquals("μοι", moi.form)                 // the trees' own word, unmarked
        assertFalse(moi.differs)
        assertTrue(tree.nodeFor(ws[3])!!.differs)
        assertEquals(setOf(4L), SyntaxText.markedTokens(ws, byToken))
        // a sentence with only an elision, a ν or a spelling does not differ
        val nu = mapOf(3L to row("reading", "μοι", token = 3, word = 3, same = 1, difference = "nu"))
        assertTrue(SyntaxText.markedTokens(ws, nu).isEmpty())
        assertTrue(Syntax.asTreesText(Syntax.build("s", ws, emptyList()), nu, emptyMap()).nodes.none { it.differs })
    }

    @Test
    fun absentAndUnprintedWordsAreMarked() {
        // 48: our θεαὶ λήγουσαί τʼ are not in the trees' text; their καὶ ἐκλήγουσαι are not printed
        val ws = listOf(tok(1, 0, "ὑμνεῦσι", "PRED", 0, "1"), tok(2, 1, "θεαὶ", null, null, null), tok(3, 2, "λήγουσαί", null, null, null))
        val extra = listOf(Sentence_nodes(1, 1, "s", 2, "καὶ", null, "c--------", "COORD", 1, 0),
            Sentence_nodes(2, 1, "s", 3, "ἐκλήγουσαι", null, "v-pppafn-", "ADV_CO", 2, 0))
        val byToken = mapOf(2L to row("absent", token = 2), 3L to row("absent", token = 3))
        val byNode = mapOf(("s" to 2) to row("unprinted", "καὶ", token = null, word = 2), ("s" to 3) to row("unprinted", "ἐκλήγουσαι", token = null, word = 3))
        val tree = Syntax.asTreesText(Syntax.build("s", ws, extra), byToken, byNode)
        assertEquals(listOf("καὶ", "ἐκλήγουσαι"), tree.nodes.filter { it.differs }.map { it.form })
        assertEquals(setOf(2L, 3L), SyntaxText.markedTokens(ws, byToken))
    }

    @Test
    fun theSentenceAsPrintedRunsOverItsLinesWithItsMarks() {
        val lineA = "ἀρχόμεναί θʼ ὑμνεῦσι θεαὶ λήγουσαί τʼ ἀοιδῆς,"
        val lineB = "ὅσσον φέρτατός ἐστι θεῶν κράτεΐ τε μέγιστος. ἐνθ"
        fun t(id: Long, line: Long, form: String, text: String) = Tokens(id, line, id, text.indexOf(form).toLong(),
            (text.indexOf(form) + form.length).toLong(), form, form, form, "", null, null, "s", null)
        val ws = listOf(t(1, 10, "ὑμνεῦσι", lineA), t(2, 10, "θεαὶ", lineA), t(3, 10, "ἀοιδῆς", lineA),
            t(4, 11, "ὅσσον", lineB), t(5, 11, "μέγιστος", lineB))
        val p = SyntaxText.printedSentence(ws, setOf(2L)) { if (it == 10L) lineA else lineB }!!
        assertEquals("ὑμνεῦσι θεαὶ λήγουσαί τʼ ἀοιδῆς, ὅσσον φέρτατός ἐστι θεῶν κράτεΐ τε μέγιστος.", p.text)
        assertEquals(listOf("θεαὶ"), p.marks.map { p.text.substring(it) })
    }

    @Test
    fun anAbsentWordKeepsItsSentenceButHasNoNode() {
        val absent = tok(9, 5, "τᾷ", null, null, null)
        val tree = Syntax.build("s", tokens + absent, emptyList())
        assertNull(tree.nodeFor(absent))
        assertNull(Syntax.roleOf(tree, absent))
        assertEquals(3, tree.nodes.size)
    }

    @Test
    fun aUnitWhoseFirstWordCarriesTheMarkIsOneNode() {
        // 447: καὶ ἐκ, the trees' κἀκ; the node on ἐκ, καὶ "=21"
        val kai = tok(11, 0, "καὶ", null, null, "=21")
        val ek = tok(12, 1, "ἐκ", "AuxP", 23, "21")
        val pol = tok(13, 2, "πολλῶν", "ADV", 21, "22")
        val verb = tok(14, 3, "βριάει", "PRED", 0, "23")
        val tree = Syntax.build("s", listOf(kai, ek, pol, verb), emptyList())
        val node = tree.nodeFor(kai)!!
        assertSame(node, tree.nodeFor(ek))
        assertEquals("καὶ ἐκ", node.form)
        assertEquals(3, tree.nodes.size)
        assertEquals("adverbial of καὶ ἐκ", Syntax.roleOf(tree, pol))
        assertEquals("καὶ ἐκ together: preposition of βριάει", Syntax.roleLine(tree, kai))
        assertEquals("καὶ ἐκ together: preposition of βριάει", Syntax.roleLine(tree, ek))
        val shown = Syntax.asTreesText(tree, mapOf(11L to row("unit", "κἀκ", token = 11), 12L to row("unit", "κἀκ", token = 12)), emptyMap())
        assertSame(tree, shown)                                              // a unit changes no node
    }

    @Test
    fun aTextWithoutTheRecordKeepsItsTree() {
        val plain = Syntax.build("s", tokens, extra)
        assertSame(plain, Syntax.asTreesText(plain, emptyMap(), emptyMap()))
        assertSame(plain, Syntax.asTreesText(plain, mapOf(9L to row("reading", "x", token = 9)), emptyMap()))
    }
}
