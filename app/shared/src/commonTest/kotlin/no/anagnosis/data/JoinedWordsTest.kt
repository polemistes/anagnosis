package no.anagnosis.data

import no.anagnosis.db.Tokens
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertSame

/** The print's two words that the hand-made tree has as one (Theogony 2: αἵ θʼ for the tree's αἵθʼ). */
class JoinedWordsTest {
    private fun tok(id: Long, ord: Long, form: String, rel: String?, head: Long?, wordId: String) =
        Tokens(id, 1, ord, 0, 0, form, form, form, "", rel, head, "s", wordId)

    private val tokens = listOf(
        tok(1, 0, "αἵ", "SBJ", 8, "6"),
        tok(2, 1, "θʼ", null, null, "=6"),
        tok(3, 2, "Ἑλικῶνος", "ATR", 9, "7"),
        tok(4, 3, "ἔχουσιν", "PRED", 0, "8"),
        tok(5, 4, "ὄρος", "OBJ", 8, "9"),
    )

    @Test
    fun theTwoWordsAreOneNodeWithBothForms() {
        val tree = Syntax.build("s", tokens, emptyList())
        val node = tree.nodeFor(tokens[0])!!
        assertEquals("αἵ θʼ", node.form)
        assertSame(node, tree.nodeFor(tokens[1]))       // either word finds the node
        assertEquals(4, tree.nodes.size)                 // no node of its own for θʼ
        assertEquals("subject of ἔχουσιν", Syntax.roleOf(tree, tokens[1]))
    }

    @Test
    fun wordIdsWithoutTheMarkAreAsBefore() {
        assertNull(Syntax.joinedNode("6"))
        assertNull(Syntax.joinedNode("6+7"))
        assertNull(Syntax.joinedNode(null))
        assertEquals(6, Syntax.joinedNode("=6"))
        val plain = Syntax.build("s", tokens.filter { it.id != 2L }, emptyList())
        assertEquals("αἵ", plain.nodeFor(tokens[0])!!.form)
    }
}
