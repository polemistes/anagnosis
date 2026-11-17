package no.anagnosis.data

/**
 * Where a text's syntax trees were made on another text than the one printed (the Theogony's
 * trees on the Perseus text, Rzach's text printed): one row of how the two differ (table
 * syntax_text_words). [kind] is "unit", "reading", "absent" or "unprinted".
 */
class SyntaxTextWord(
    val kind: String,
    val tokenId: Long?,
    val sentence: String?,
    val wordId: Int?,
    val treeForm: String?,
    val treeLemma: String?,
    val extent: String?,
    /** On a reading: 1 when the trees' word stands in the same construction as ours, 0 when not, null when not said. */
    val sameConstruction: Long? = null,
    /** The trees' word's morphological tag, where the row has a tree word. */
    val treePostag: String? = null,
    /** On a reading, how the two words differ: elision, nu, spelling (not shown), form, word (shown). */
    val difference: String? = null,
)

/** A tree node's mark where the trees' text differs: not printed here, or read otherwise there. */
sealed class NodeMark {
    object Unprinted : NodeMark()
    /** The tree shows the trees' own word [treeForm] at this node; [printed] is the word printed here. */
    class Reading(val treeForm: String, val printed: String) : NodeMark()
}

/**
 * Every remark the reader makes about the trees' text, in one place. The notice names the text
 * once, at the head of the syntax view, on the credits page and in the shop; the remarks on
 * words are made where the difference is.
 */
object SyntaxText {
    /** The syntax view's head, for every sentence of such a text. */
    fun notice(syntaxText: String): String =
        "These trees were made on $syntaxText, which differs in places from the text printed here."

    /** After the notice, when the sentence shown has a difference: only the marks it has are explained. */
    fun legend(unprinted: Boolean, reading: Boolean): String? {
        val parts = buildList {
            if (reading) add("a word followed by “(printed: …)” is that text's word, and the word printed here is given in brackets")
            if (unprinted) add("[a word in square brackets] is in that text but not printed here")
        }
        return if (parts.isEmpty()) null else "In this sentence the two texts differ: " + parts.joinToString("; ") + "."
    }

    /** After the notice, when printed words of the sentence are not in the trees' text (and so not in the tree). */
    fun notInTree(forms: List<String>): String? =
        if (forms.isEmpty()) null else "Not in the text the syntax was made on: ${forms.joinToString(", ")}."

    /** The printed words of a sentence that are not in its tree (absent from the trees' text), neighbours together: "θεαὶ λήγουσαί τʼ". */
    fun absentForms(tokens: List<no.anagnosis.db.Tokens>, byToken: Map<Long, SyntaxTextWord>): List<String> {
        if (byToken.isEmpty()) return emptyList()
        val out = ArrayList<String>()
        var last = -2
        tokens.forEachIndexed { i, t ->
            if (byToken[t.id]?.kind != "absent") return@forEachIndexed
            if (i == last + 1 && out.isNotEmpty()) out[out.lastIndex] = out.last() + " " + t.form else out += t.form
            last = i
        }
        return out
    }

    /** The credits' line name. */
    const val CREDIT_KIND = "Trees made on"

    /**
     * The word sheet's syntax line for a word whose place the trees' text reads otherwise: the
     * role is that of the trees' word ([role] as [Syntax.roleOf] gives it, "object of ἐνέπνευσαν").
     */
    fun readingRole(row: SyntaxTextWord, role: String): String {
        val tree = elisionMark(row.treeForm.orEmpty())
        val other = if (row.sameConstruction == 0L) ". The word printed here stands in another construction." else ""
        return "In the text the syntax was made on: $tree, $role$other"
    }

    /** What the word sheet says by the word's syntax (beyond [readingRole]), or null when the word needs no remark. */
    fun wordRemark(row: SyntaxTextWord?): String? {
        row ?: return null
        val tree = row.treeForm?.takeIf { it.isNotBlank() }?.let(::elisionMark)
        return when (row.kind) {
            "absent" -> when {
                row.extent == "passage" && row.sentence == null ->
                    "There is no syntax for this passage: the text the syntax was made on lacks it."
                row.extent == "passage" -> "This word is not in the text the syntax was made on, which words the phrase otherwise."
                tree != null -> "This word is not in the text the syntax was made on; that text has $tree here, in another construction."
                else -> "This word is not in the text the syntax was made on."
            }
            // the trees divide οὐδέ as "οὐ δέ": their habit, not a difference of text
            "unit" -> if (tree == null || ' ' in tree) null else "The text the syntax was made on has this as part of one word: $tree."
            else -> null
        }
    }

    /**
     * Whether a reading row is a real difference, to be shown: another form or another word, or a
     * word in another construction; not an elision, a movable ν or a spelling (the author, 2026-11-17).
     * Without the record of the difference, any difference of letters (not of accent, capital or elision mark).
     */
    fun isReading(row: SyntaxTextWord?, printed: String): Boolean {
        if (row?.kind != "reading" || row.treeForm.isNullOrBlank()) return false
        if (row.sameConstruction == 0L) return true
        return when (row.difference) {
            null -> !sameLetters(row.treeForm, printed)
            else -> row.difference in REAL
        }
    }

    private val REAL = setOf("form", "word")

    /** A node's mark in the tree view; [printed] is our word at a word node. */
    fun nodeMark(row: SyntaxTextWord?, printed: String?): NodeMark? = when {
        row?.kind == "unprinted" -> NodeMark.Unprinted
        printed != null && isReading(row, printed) -> NodeMark.Reading(elisionMark(row!!.treeForm!!), printed)
        else -> null
    }

    /** How a marked node is shown: "[καὶ]" for one not printed here, "αὐδὴν (printed: ἀοιδὴν)" for the trees' word where ours differs. */
    fun displayForm(form: String, mark: NodeMark?): String = when (mark) {
        NodeMark.Unprinted -> "[$form]"
        is NodeMark.Reading -> "${mark.treeForm} (printed: ${mark.printed})"
        null -> form
    }

    /** How a head not printed here is named on the word sheet: "subject of ἔνι (not printed here)". */
    fun unprintedHead(form: String): String = "$form (not printed here)"

    /** The same letters, whatever the accents, breathings, capitals and elision marks. */
    fun sameLetters(a: String, b: String): Boolean = letters(a) == letters(b)

    private fun letters(s: String): String =
        TextFold.fold(s, ignoreAccents = true, ignoreCase = true).filter { it.isLetter() && it.code !in 0x300..0x36f }

    /** The trees' elision mark (a combining comma above, a curly apostrophe) as the print's ʼ. */
    fun elisionMark(form: String): String =
        if (form.length > 1 && form.last() in "\u0313\u2019'᾽") form.dropLast(1) + "ʼ" else form
}
