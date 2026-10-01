package no.anagnosis.data

import no.anagnosis.db.Sentence_nodes
import no.anagnosis.db.Tokens
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class SyntaxTest {
    private var nextId = 1L

    private fun token(wordId: String, form: String, relation: String?, head: Long?, postag: String = "n-s---fn-") =
        Tokens(nextId++, 1, 0, 0, 0, form, form, form, postag, relation, head, "s1", wordId)

    private fun node(wordId: Long, form: String, relation: String, head: Long, artificial: Boolean = false) =
        Sentence_nodes(nextId++, 1, "s1", wordId, form, null, if (artificial) "" else "u--------", relation, head, if (artificial) 1 else 0)

    // ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα , [verb omitted] ... a sentence with a comma and an elliptic node
    private val tokens = listOf(
        token("1", "ὦ", "AuxZ", 5, "i--------"),
        token("2", "κοινὸν", "ATR", 5, "a-s---nv-"),
        token("3", "αὐτάδελφον", "ATR", 5, "a-s---nv-"),
        token("4", "Ἰσμήνης", "ATR", 5, "n-s---fg-"),
        token("5", "κάρα", "ExD", 8, "n-s---nv-"),
        token("7", "ἆρ", "AuxY", 8, "g--------"),
    )
    private val extra = listOf(node(6, ",", "AuxX", 8), node(8, "[0]", "PRED", 0, artificial = true))

    @Test
    fun treeHangsWordsUnderTheirHeadsInTextOrder() {
        val tree = Syntax.build("s1", tokens, extra)
        val flat = tree.flatten().map { (n, d) -> "${"  ".repeat(d)}${Syntax.displayForm(n)}" }
        // the comma hangs on the omitted verb but nothing depends on it, so it is not shown
        assertEquals(
            listOf("[…]", "  κάρα", "    ὦ", "    κοινὸν", "    αὐτάδελφον", "    Ἰσμήνης", "  ἆρ"),
            flat,
        )
    }

    @Test
    fun aCommaThatHeadsACoordinationIsShown() {
        val verb = token("1", "λέγω", "PRED", 0, "v1spia---")
        val a = token("2", "ταῦτα", "OBJ_CO", 3)
        val b = token("4", "ἐκεῖνα", "OBJ_CO", 3)
        val comma = node(3, ",", "COORD", 1)
        val stop = node(5, ".", "AuxK", 0)
        val tree = Syntax.build("s1", listOf(verb, a, b), listOf(comma, stop))
        assertEquals(listOf("λέγω", ",", "ταῦτα", "ἐκεῖνα"), tree.flatten().map { it.first.form })
        assertEquals(listOf("λέγω", "ταῦτα", ",", "ἐκεῖνα"), tree.shownNodes.map { it.form })
    }

    @Test
    fun roleNamesTheHead() {
        val tree = Syntax.build("s1", tokens, extra)
        assertEquals("attribute of κάρα", Syntax.roleOf(tree, tokens[1]))
        assertEquals("independent of an omitted word", Syntax.roleOf(tree, tokens[4]))
    }

    @Test
    fun missingHeadsAndCyclesBecomeRoots() {
        val a = token("1", "α", "SBJ", 2)
        val b = token("2", "β", "PRED", 1)   // a cycle
        val c = token("3", "γ", "OBJ", 9)   // head outside the sentence
        val tree = Syntax.build("s1", listOf(a, b, c), emptyList())
        assertEquals(listOf("α", "β", "γ").sorted(), tree.roots.map { it.form }.sorted())
        assertEquals(3, tree.flatten().size)
        assertNull(tree.headOf(tree.nodeFor(c)!!))
    }

    @Test
    fun mergedWordKeepsItsFirstIdAndItsDependents() {
        val merged = token("1+2", "κἀγώ", null, null)
        val verb = token("3", "λέγω", "PRED", 0, "v1spia---")
        val dep = token("4", "τι", "OBJ", 2)  // depends on the second half of the merged word
        val tree = Syntax.build("s1", listOf(merged, verb, dep), emptyList())
        assertEquals("κἀγώ", tree.headOf(tree.nodeFor(dep)!!)?.form)
        assertNull(Syntax.roleOf(tree, merged))
    }

    @Test
    fun labelsAreSpeltOut() {
        assertEquals("subject", Syntax.describe("SBJ"))
        assertEquals("predicate, coordinated", Syntax.describe("PRED_CO"))
        assertEquals("object, in apposition, coordinated", Syntax.describe("OBJ_AP_CO"))
        assertEquals(Syntax.Role.OBJECT, Syntax.role("OBJ_CO"))
        assertNull(Syntax.role("AuxP"))
    }

    @Test
    fun shortLabelsAndPartsOfSpeech() {
        assertEquals("subj", Syntax.shortLabel("SBJ"))
        assertEquals("attr co", Syntax.shortLabel("ATR_CO"))
        assertEquals("obj ap co", Syntax.shortLabel("OBJ_AP_CO"))
        assertEquals("ptcp", Morphology.pos("v-pappmn-"))
        assertEquals("inf", Morphology.pos("v--pna---"))
        assertEquals("noun", Morphology.pos("n-s---fg-"))
        assertEquals("", Morphology.pos(""))
    }

    @Test
    fun shortMorphology() {
        assertEquals("verb 3rd sg pres ind act", Morphology.short("v3spia---"))
        assertEquals("noun fem gen sg", Morphology.short("n-s---fg-"))
        assertEquals("verb aor pass part masc nom pl", Morphology.short("v-pappmn-"))
        assertEquals("verb pres inf act", Morphology.short("v--pna---"))
        assertEquals("adj neut acc pl comp", Morphology.short("a-p---nac"))
        assertEquals("particle", Morphology.short("g--------"))
    }
}
