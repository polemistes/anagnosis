package no.anagnosis.data

import no.anagnosis.db.Tokens

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
    /** On a reading: the trees' word is a misprint in their text (shown as a real difference). */
    val misprint: Boolean = false,
)

/**
 * What the reader says about the trees' text, in one place: once, at the head of every tree and
 * on the credits page. The tree is shown as the tree of the text it was made for; words are not
 * annotated (the author, 2026-11-17).
 */
object SyntaxText {
    /** The syntax view's head, only where the sentence differs ([PrintedSentence]). */
    const val DIFFERS = "The syntax tree was made on another text. Marked words differ from the text printed here."

    /** Added to that head where the trees' word is a misprint in their text. */
    const val MISPRINT = "The text the syntax tree was made on has a misprint here."

    /** The label of the sentence as printed, in that head. */
    const val PRINTED_HERE = "Printed here:"

    /** What a screen reader says of a marked word. */
    const val MARKED = "differs from the text printed here"

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
    fun showsRole(row: SyntaxTextWord?, printed: String): Boolean = row?.kind != "absent" && !isOtherWord(row, printed)

    /**
     * Whether a reading is a real difference, marked in the syntax view: another form or another
     * word, or a word in another construction, or a misprint in the trees' text; not an elision,
     * a movable ν or a spelling (the author, 2026-11-17).
     */
    fun isRealReading(row: SyntaxTextWord?, printed: String): Boolean =
        isOtherWord(row, printed) || (row?.kind == "reading" && row.misprint)

    /** Whether the trees' word is another than ours: another form or word, or in another construction. */
    private fun isOtherWord(row: SyntaxTextWord?, printed: String): Boolean {
        if (row == null || row.kind != "reading" || row.treeForm.isNullOrBlank()) return false
        if (row.sameConstruction == 0L) return true
        return when (row.difference) {
            null -> !sameLetters(row.treeForm, printed)
            else -> row.difference in OTHER_WORD
        }
    }


    /** The printed words of a sentence that differ from the trees' text: another form or word, or not in that text. */
    fun markedTokens(tokens: List<Tokens>, byToken: Map<Long, SyntaxTextWord>): Set<Long> =
        if (byToken.isEmpty()) emptySet()
        else tokens.filter { t -> byToken[t.id]?.let { it.kind == "absent" || isRealReading(it, t.form) } == true }.map { it.id }.toSet()

    /**
     * The sentence as printed, for the head of its tree where it differs: the text of its lines
     * from its first word to its last (with the punctuation that closes it), and the ranges of the
     * [marked] words in it. [lineText] gives a line's text by its id.
     */
    fun printedSentence(tokens: List<Tokens>, marked: Set<Long>, misprint: Boolean = false, lineText: (Long) -> String?): PrintedSentence? {
        if (tokens.isEmpty()) return null
        val lines = tokens.map { it.line_id }.distinct()
        val sb = StringBuilder()
        val marks = ArrayList<IntRange>()
        for ((i, lineId) in lines.withIndex()) {
            val text = lineText(lineId) ?: continue
            val here = tokens.filter { it.line_id == lineId }
            val from = if (i == 0) here.minOf { it.start }.toInt().coerceIn(0, text.length) else 0
            var to = if (i == lines.lastIndex) here.maxOf { it.end }.toInt().coerceIn(from, text.length) else text.length
            if (i == lines.lastIndex) while (to < text.length && !text[to].isLetter() && !text[to].isWhitespace()) to++
            if (sb.isNotEmpty()) sb.append(' ')
            val base = sb.length - from
            sb.append(text, from, to)
            for (t in here) if (t.id in marked) {
                val s = t.start.toInt() + base
                val e = t.end.toInt() + base
                if (s >= base + from && e <= sb.length && s < e) marks += s until e
            }
        }
        return PrintedSentence(sb.toString(), marks, misprint)
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

/** A sentence as printed, with the ranges of the words marked as differing from the trees' text. */
class PrintedSentence(val text: String, val marks: List<IntRange>, val misprint: Boolean = false)
