package no.anagnosis.data

import no.anagnosis.db.Sentence_nodes
import no.anagnosis.db.Tokens
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Trees made on another text than the one printed (the Theogony's): which remark each word gets, and the marked tree. */
class SyntaxTextTest {
    private fun row(kind: String, tree: String? = null, extent: String? = null, token: Long? = 1, sentence: String? = null, word: Int? = null) =
        SyntaxTextWord(kind, token, sentence, word, tree, null, extent)

    @Test
    fun aReadingGivesTheTreesWordAndItsRole() {
        val r = row("reading", "αὐδὴν")
        assertTrue(SyntaxText.isReading(r, "ἀοιδὴν"))
        assertEquals("In the text the syntax was made on: αὐδὴν, object of ἐνέπνευσαν", SyntaxText.readingRole(r, "object of ἐνέπνευσαν"))
        assertEquals("In the text the syntax was made on: τῷ, sentence particle of ἐγγυάλιξεν. The word printed here stands in another construction.",
            SyntaxText.readingRole(SyntaxTextWord("reading", 1, null, null, "τῷ", null, null, 0), "sentence particle of ἐγγυάλιξεν"))
        assertNull(SyntaxText.wordRemark(r))
        val mark = SyntaxText.nodeMark(r, "ἀοιδὴν")
        assertIs<NodeMark.Reading>(mark)
        assertEquals("αὐδὴν (printed: ἀοιδὴν)", SyntaxText.displayForm("ἀοιδὴν", mark))
    }

    @Test
    fun accentCapitalOrElisionMarkAloneIsNoReading() {
        assertTrue(!SyntaxText.isReading(row("reading", "Δέ"), "δὲ"))
        assertTrue(!SyntaxText.isReading(row("reading", "θ̓"), "θʼ"))
        assertTrue(!SyntaxText.isReading(row("reading", "δ’"), "δʼ"))
        assertNull(SyntaxText.nodeMark(row("reading", "Δέ"), "δὲ"))
        assertTrue(SyntaxText.isReading(row("reading", "μοι"), "μʼ"))
        assertEquals("αἵθʼ", SyntaxText.elisionMark("αἵθ̓"))
    }

    private fun reading(tree: String, difference: String?, same: Long? = 1) =
        SyntaxTextWord("reading", 1, "s", 2, tree, null, null, same, null, difference)

    @Test
    fun onlyRealDifferencesAreMarked() {
        assertTrue(SyntaxText.isReading(reading("αὐδὴν", "word"), "ἀοιδὴν"))
        assertTrue(SyntaxText.isReading(reading("νυκτὸς", "form"), "νύκτας"))
        assertTrue(!SyntaxText.isReading(reading("μοι", "elision"), "μʼ"))
        assertTrue(!SyntaxText.isReading(reading("τέκεν", "nu"), "τέκε"))
        assertTrue(!SyntaxText.isReading(reading("μιχθεὶς", "spelling"), "μειχθεὶς"))
        assertNull(SyntaxText.nodeMark(reading("τέκεν", "nu"), "τέκε"))
        // another construction is shown whatever the difference
        assertTrue(SyntaxText.isReading(reading("παιπαλοέσσῃς", "spelling", same = 0), "παιπαλοέσσης"))
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
        val marked = Syntax.marked(tree, listOf(kai, ek, pol, verb),
            mapOf(11L to row("unit", "κἀκ", token = 11), 12L to row("unit", "κἀκ", token = 12)), emptyMap())
        assertSame(tree, marked)                       // a unit marks no node
    }

    @Test
    fun anAbsentWordSaysWhatStandsThereIfAnything() {
        assertEquals("This word is not in the text the syntax was made on; that text has τῷ here, in another construction.",
            SyntaxText.wordRemark(row("absent", "τῷ", "word")))
        assertEquals("This word is not in the text the syntax was made on.", SyntaxText.wordRemark(row("absent", null, "word")))
        assertEquals("There is no syntax for this passage: the text the syntax was made on lacks it.", SyntaxText.wordRemark(row("absent", null, "passage")))
        assertEquals("This word is not in the text the syntax was made on, which words the phrase otherwise.",
            SyntaxText.wordRemark(row("absent", null, "passage", sentence = "s")))
        assertNull(SyntaxText.nodeMark(row("absent", "τῷ", "word"), "τᾷ"))
    }

    @Test
    fun aUnitIsRemarkedUnlessTheTreesMerelyDivideIt() {
        assertEquals("The text the syntax was made on has this as part of one word: αἵθʼ.", SyntaxText.wordRemark(row("unit", "αἵθ̓")))
        assertNull(SyntaxText.wordRemark(row("unit", "οὐ δέ")))   // the trees' habit, not another text
        assertNull(SyntaxText.nodeMark(row("unit", "αἵθ̓"), "αἵ"))
    }

    @Test
    fun noRowNoRemark() {
        assertNull(SyntaxText.wordRemark(null))
        assertNull(SyntaxText.nodeMark(null, "καὶ"))
        assertEquals("καὶ", SyntaxText.displayForm("καὶ", null))
    }

    @Test
    fun theTreesHeadNamesThePrintedWordsNotInIt() {
        val byToken = mapOf(2L to row("absent", null, "word", token = 2, sentence = "s"), 1L to row("unit", "x", token = 1))
        assertEquals(listOf("ἀοιδὴν"), SyntaxText.absentForms(tokens, byToken))
        val two = byToken + (3L to row("absent", null, "passage", token = 3, sentence = "s")) + (1L to row("absent", null, "word", token = 1, sentence = "s"))
        assertEquals(listOf("Μουσάων ἀοιδὴν ἀρχώμεθ"), SyntaxText.absentForms(tokens, two))
        assertEquals(listOf("Μουσάων", "ἀρχώμεθ"), SyntaxText.absentForms(tokens, two - 2L))
        assertEquals("Not in the text the syntax was made on: ἀοιδὴν.", SyntaxText.notInTree(listOf("ἀοιδὴν")))
        assertNull(SyntaxText.notInTree(emptyList()))
        assertEquals(emptyList(), SyntaxText.absentForms(tokens, emptyMap()))
        // the absent word keeps its sentence but has no node, and no role
        val absent = tok(9, 5, "τᾷ", null, null, "").copy(word_id = null)
        val tree = Syntax.build("s", tokens + absent, emptyList())
        assertNull(tree.nodeFor(absent))
        assertNull(Syntax.roleOf(tree, absent))
        assertEquals(3, tree.nodes.size)
    }

    @Test
    fun theLegendNamesOnlyTheMarksTheSentenceHas() {
        assertNull(SyntaxText.legend(unprinted = false, reading = false))
        assertTrue(SyntaxText.legend(unprinted = true, reading = false)!!.let { "square brackets" in it && "printed:" !in it })
        assertTrue(SyntaxText.legend(unprinted = false, reading = true)!!.let { "printed:" in it && "square brackets" !in it })
    }

    private fun tok(id: Long, ord: Long, form: String, rel: String?, head: Long?, wordId: String) =
        Tokens(id, 1, ord, 0, 0, form, form, form, "", rel, head, "s", wordId)

    private val tokens = listOf(
        tok(1, 0, "Μουσάων", "ATR", 3, "1"),
        tok(2, 1, "ἀοιδὴν", "OBJ", 3, "2"),
        tok(3, 2, "ἀρχώμεθ", "PRED", 0, "3"),
    )
    private val extra = listOf(Sentence_nodes(1, 1, "s", 4, "ἔνι", null, "v3spia---", "ADV", 3, 0))

    @Test
    fun theTreeMarksUnprintedAndReadOtherwiseNodes() {
        val plain = Syntax.build("s", tokens, extra)
        val marked = Syntax.marked(plain, tokens,
            mapOf(2L to row("reading", "αὐδὴν", token = 2)),
            mapOf(("s" to 4) to row("unprinted", "ἔνι", "word", token = null, sentence = "s", word = 4)))
        val unprinted = marked.nodes.single { it.id == 4 }
        assertTrue(unprinted.isUnprinted)
        assertTrue(!unprinted.isPunctuation)                 // shown as a word, not hidden as punctuation
        assertTrue(marked.isShown(unprinted))
        assertEquals("[ἔνι]", Syntax.displayForm(unprinted))
        assertEquals("αὐδὴν (printed: ἀοιδὴν)", Syntax.displayForm(marked.nodeFor(tokens[1])!!))
        assertEquals("object of ἀρχώμεθ", Syntax.roleOf(marked, tokens[1]))
        assertEquals("ἀοιδὴν", marked.nodeFor(tokens[1])!!.form)        // the printed word is kept on the node
        assertEquals("ἔνι (not printed here)", Syntax.headLabel(unprinted))
        assertEquals("αὐδὴν", Syntax.headLabel(marked.nodeFor(tokens[1])!!))   // a head is named by the trees' word
        // without the node, the same extra node would be taken for punctuation
        assertTrue(plain.nodes.single { it.id == 4 }.isPunctuation)
    }

    @Test
    fun aTextWithoutDifferencesKeepsItsTree() {
        val plain = Syntax.build("s", tokens, extra)
        assertSame(plain, Syntax.marked(plain, tokens, emptyMap(), emptyMap()))
        assertSame(plain, Syntax.marked(plain, tokens, mapOf(9L to row("reading", "x", token = 9)), emptyMap()))
    }

    @Test
    fun aReadingInAnotherConstructionTiesOurWordToTheTreesNode() {
        // 485: our τᾷ has the sentence only; the trees' τῷ is a node of its own, tied by the row
        val ours = tok(5, 3, "τᾷ", null, null, "").copy(word_id = null)
        val node = Sentence_nodes(2, 1, "s", 5, "τῷ", null, "d--------", "AuxY", 3, 0)
        val r = SyntaxTextWord("reading", 5, "s", 5, "τῷ", "τῷ", null, 0, "d--------")
        val tree = Syntax.marked(Syntax.build("s", tokens + ours, listOf(node)), tokens + ours, mapOf(5L to r), mapOf(("s" to 5) to r))
        val n = tree.nodeFor(ours)!!
        assertEquals(5, n.id)
        assertEquals("τῷ (printed: τᾷ)", Syntax.displayForm(n))
        assertEquals("d--------", n.postag)
        assertEquals("In the text the syntax was made on: τῷ, sentence particle of ἀρχώμεθ. The word printed here stands in another construction.",
            SyntaxText.readingRole(r, Syntax.roleOf(tree, ours)!!))
    }
}
