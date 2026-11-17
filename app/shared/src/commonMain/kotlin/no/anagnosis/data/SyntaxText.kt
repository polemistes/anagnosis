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

/**
 * What the reader says about the trees' text, in one place: once, at the head of every tree and
 * on the credits page. The tree is shown as the tree of the text it was made for; words are not
 * annotated (the author, 2026-11-17).
 */
object SyntaxText {
    /** The syntax view's head, for every sentence of such a text. */
    fun notice(syntaxText: String): String =
        "These trees were made on $syntaxText, which differs in places from the text printed here."

    /** The credits' line name. */
    const val CREDIT_KIND = "Trees made on"

    /** Where a word stands in a sentence without syntax, in a text that has syntax (sheet and long press). */
    const val NO_SYNTAX = "No syntax available"

    /**
     * Whether the word sheet may give the role of the tree's node as our word's: only where our
     * word is the trees' own word. A reading that differs only by elision, a movable ν or a
     * spelling is the same word; one of another form or another word, or in another
     * construction, is not (no role line). Without the record of the difference, a difference of
     * letters (not of accent, capital or elision mark) counts.
     */
    fun showsRole(row: SyntaxTextWord?, printed: String): Boolean {
        if (row == null || row.kind != "reading" || row.treeForm.isNullOrBlank()) return row?.kind != "absent"
        if (row.sameConstruction == 0L) return false
        return when (row.difference) {
            null -> sameLetters(row.treeForm, printed)
            else -> row.difference !in OTHER_WORD
        }
    }

    private val OTHER_WORD = setOf("form", "word")

    /** The same letters, whatever the accents, breathings, capitals and elision marks. */
    fun sameLetters(a: String, b: String): Boolean = letters(a) == letters(b)

    private fun letters(s: String): String =
        TextFold.fold(s, ignoreAccents = true, ignoreCase = true).filter { it.isLetter() && it.code !in 0x300..0x36f }

    /** The trees' elision mark (a combining comma above, a curly apostrophe) as the print's ʼ. */
    fun elisionMark(form: String): String =
        if (form.length > 1 && form.last() in "\u0313\u2019'᾽") form.dropLast(1) + "ʼ" else form
}
