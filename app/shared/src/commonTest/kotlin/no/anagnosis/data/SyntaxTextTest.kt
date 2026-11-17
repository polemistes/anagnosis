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
