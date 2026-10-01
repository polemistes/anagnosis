package no.anagnosis.data

import no.anagnosis.db.Sentence_nodes
import no.anagnosis.db.Tokens

/**
 * One node of a sentence's dependency tree: a word of the text, a punctuation mark, or an
 * artificial node standing for an omitted word. [id] is the treebank's word id within the
 * sentence; [head] the id of the node it depends on, 0 for the root.
 */
class SyntaxNode(
    val id: Int,
    val form: String,
    val postag: String,
    val relation: String?,
    val head: Int?,
    /** The token of the text, when the node is a word of it. */
    val token: Tokens?,
    val artificial: Boolean,
) {
    val isWord get() = token != null
    /** The treebank's bare label, e.g. "SBJ_CO". */
    val label get() = relation ?: ""
}

/** The nodes of one sentence in text order, with the tree over them. */
class SyntaxTree(val sentence: String, val nodes: List<SyntaxNode>) {
    private val byId = nodes.associateBy { it.id }
    private val childrenOf: Map<Int, List<SyntaxNode>>
    val roots: List<SyntaxNode>

    init {
        val children = HashMap<Int, MutableList<SyntaxNode>>()
        val roots = mutableListOf<SyntaxNode>()
        for (n in nodes) {
            val h = n.head
            // a head outside the sentence, or one that leads back to the node itself, makes a root
            if (h == null || h == 0 || h !in byId || reaches(h, n.id)) roots += n
            else children.getOrPut(h) { mutableListOf() } += n
        }
        childrenOf = children
        this.roots = roots
    }

    /** Whether following heads from [from] arrives at [target] (a cycle, if target is from's dependent). */
    private fun reaches(from: Int, target: Int): Boolean {
        var cur: Int? = from
        var steps = 0
        while (cur != null && cur != 0 && steps++ < nodes.size + 1) {
            if (cur == target) return true
            cur = byId[cur]?.head
        }
        return false
    }

    fun node(id: Int): SyntaxNode? = byId[id]
    fun children(node: SyntaxNode): List<SyntaxNode> = childrenOf[node.id] ?: emptyList()
    fun headOf(node: SyntaxNode): SyntaxNode? = node.head?.let { byId[it] }?.takeIf { node !in roots }

    /** The node that stands for a token of the text. */
    fun nodeFor(token: Tokens): SyntaxNode? = nodes.firstOrNull { it.token?.id == token.id }

    /** Every node with its depth, each head before its dependents, dependents in text order. */
    fun flatten(): List<Pair<SyntaxNode, Int>> {
        val out = ArrayList<Pair<SyntaxNode, Int>>(nodes.size)
        fun visit(n: SyntaxNode, depth: Int) {
            out += n to depth
            for (c in children(n)) visit(c, depth + 1)
        }
        for (r in roots) visit(r, 0)
        return out
    }
}

/** Builds and describes the dependency trees of the Ancient Greek Dependency Treebank. */
object Syntax {
    /** The sentence tree holding the tokens of one sentence, in text order. */
    fun build(sentence: String, tokens: List<Tokens>, extra: List<Sentence_nodes>): SyntaxTree {
        val nodes = ArrayList<SyntaxNode>(tokens.size + extra.size)
        for (t in tokens) {
            // a word the treebank splits in two (κἀγώ = καί + ἐγώ) carries both ids; it keeps the first
            val id = t.word_id?.substringBefore('+')?.toIntOrNull() ?: continue
            nodes += SyntaxNode(id, t.form, t.postag, t.relation, t.head?.toInt(), t, artificial = false)
        }
        for (n in extra) {
            nodes += SyntaxNode(n.word_id.toInt(), n.form, n.postag, n.relation, n.head?.toInt(), null, n.artificial != 0L)
        }
        nodes.sortBy { it.id }
        // a dependent of the second half of a merged word belongs to the merged word
        val merged = HashMap<Int, Int>()
        for (t in tokens) {
            val ids = t.word_id?.split('+')?.mapNotNull { it.toIntOrNull() } ?: continue
            if (ids.size > 1) for (i in ids.drop(1)) merged[i] = ids[0]
        }
        val fixed = if (merged.isEmpty()) nodes else nodes.map { n ->
            val h = n.head
            if (h != null && h in merged) SyntaxNode(n.id, n.form, n.postag, n.relation, merged[h], n.token, n.artificial) else n
        }
        return SyntaxTree(sentence, fixed)
    }

    /**
     * The role a relation label names, in words: "subject", "object", "attribute" ...
     * The suffixes of the treebank are spelt out: "_CO" a member of a coordination, "_AP" of an apposition.
     */
    fun describe(relation: String?): String {
        if (relation.isNullOrEmpty()) return ""
        var base: String = relation
        val notes = mutableListOf<String>()
        while (true) {
            when {
                base.endsWith("_CO") -> { base = base.removeSuffix("_CO"); notes += "coordinated" }
                base.endsWith("_AP") -> { base = base.removeSuffix("_AP"); notes += "in apposition" }
                base.endsWith("_PA") -> { base = base.removeSuffix("_PA"); notes += "parenthetical" }
                else -> break
            }
        }
        val name = names[base] ?: base.lowercase()
        return if (notes.isEmpty()) name else "$name, ${notes.reversed().joinToString(", ")}"
    }

    /** The role in a few letters, for the label on an arc: "subj", "attr co" (coordinated), "pred nom". */
    fun shortLabel(relation: String?): String {
        if (relation.isNullOrEmpty()) return ""
        var base: String = relation
        val notes = mutableListOf<String>()
        while (true) {
            when {
                base.endsWith("_CO") -> { base = base.removeSuffix("_CO"); notes += "co" }
                base.endsWith("_AP") -> { base = base.removeSuffix("_AP"); notes += "ap" }
                base.endsWith("_PA") -> { base = base.removeSuffix("_PA"); notes += "pa" }
                else -> break
            }
        }
        return (listOf(shortNames[base] ?: base.lowercase()) + notes.reversed()).joinToString(" ")
    }

    private val shortNames = mapOf(
        "PRED" to "pred", "SBJ" to "subj", "OBJ" to "obj", "ATR" to "attr", "ADV" to "adv",
        "PNOM" to "pred nom", "OCOMP" to "obj compl", "ATV" to "compl", "AtvV" to "compl",
        "APOS" to "appos", "COORD" to "coord", "AuxP" to "prep", "AuxC" to "conj", "AuxZ" to "emph",
        "AuxY" to "ptcl", "AuxV" to "aux", "AuxX" to "punct", "AuxK" to "punct", "AuxG" to "punct",
        "ExD" to "indep", "UNDEFINED" to "?",
    )

    /** The group a relation belongs to, for colouring; null for the glue (particles, punctuation ...). */
    fun role(relation: String?): Role? {
        if (relation.isNullOrEmpty()) return null
        val base = relation.removeSuffix("_PA").removeSuffix("_CO").removeSuffix("_AP").removeSuffix("_CO")
        return when (base) {
            "PRED" -> Role.PREDICATE
            "SBJ" -> Role.SUBJECT
            "OBJ", "OCOMP" -> Role.OBJECT
            "ATR" -> Role.ATTRIBUTE
            "ADV" -> Role.ADVERBIAL
            "PNOM", "ATV", "AtvV" -> Role.COMPLEMENT
            else -> null
        }
    }

    /** The syntactic roles that get a colour of their own. */
    enum class Role(val label: String) {
        PREDICATE("predicate"), SUBJECT("subject"), OBJECT("object"), ATTRIBUTE("attribute"),
        ADVERBIAL("adverbial"), COMPLEMENT("complement"),
    }

    private val names = mapOf(
        "PRED" to "predicate",
        "SBJ" to "subject",
        "OBJ" to "object",
        "ATR" to "attribute",
        "ADV" to "adverbial",
        "PNOM" to "predicate nominal",
        "OCOMP" to "object complement",
        "ATV" to "predicative complement",
        "AtvV" to "predicative complement",
        "APOS" to "apposition",
        "COORD" to "coordinator",
        "AuxP" to "preposition",
        "AuxC" to "conjunction",
        "AuxZ" to "emphasizing particle",
        "AuxY" to "sentence particle",
        "AuxV" to "auxiliary",
        "AuxX" to "comma",
        "AuxK" to "end of sentence",
        "AuxG" to "punctuation",
        "ExD" to "independent",
        "UNDEFINED" to "undefined",
    )

    /** "subject of φέρει" or "predicate" for a root; null when the word has no syntactic annotation. */
    fun roleOf(tree: SyntaxTree, token: Tokens): String? {
        val node = tree.nodeFor(token) ?: return null
        val role = describe(node.relation)
        if (role.isEmpty()) return null
        val head = tree.headOf(node) ?: return role
        return "$role of ${headLabel(head)}"
    }

    /** How an omitted word or a punctuation mark is named when something depends on it. */
    fun headLabel(node: SyntaxNode): String = when {
        node.artificial -> "an omitted word"
        node.isWord -> node.form
        else -> "“${node.form}”"
    }

    /** How a node is shown in the tree: a word's form, an omitted word's placeholder, a punctuation mark. */
    fun displayForm(node: SyntaxNode): String = if (node.artificial) "[…]" else node.form
}
