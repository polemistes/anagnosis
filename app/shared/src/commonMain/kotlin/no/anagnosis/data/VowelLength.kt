package no.anagnosis.data

import no.anagnosis.greek.Phonology
import no.anagnosis.greek.Pronunciation

/**
 * Which of the analyser's length-marked forms (Morpheus's, see pipeline forms.py) belongs to a
 * word of the text. The spelling does not show whether α ι υ are long, and the same spelling
 * can be long in one analysis and short in another (πολλά: feminine singular with a long α in
 * some dialects, neuter plural with a short one), so the token's own lemma and parse decide.
 */
object VowelLength {
    /**
     * The token's [form] with its hidden long vowels marked, or null when none is known: the
     * analyses with the token's lemma and parse when they agree, else those with its lemma when
     * they agree. An analysis without a marked form counts as "no hidden long vowel".
     */
    fun choose(form: String, lemmaKey: String, postag: String, analyses: List<FormAnalysis>): String? {
        val exact = analyses.filter { it.lemmaKey == lemmaKey && it.postag == postag }
        decide(form, exact)?.let { return it.ifEmpty { null } }
        decide(form, analyses.filter { it.lemmaKey == lemmaKey })?.let { return it.ifEmpty { null } }
        return null
    }

    /** A word without a lemma or parse of its own (a speaker's name): marked when all its analyses agree. */
    fun ofForm(form: String, analyses: List<FormAnalysis>): String? = decide(form, analyses)?.ifEmpty { null }

    /** The one marked form the analyses agree on ("" for none), or null when they disagree or are empty. */
    private fun decide(form: String, analyses: List<FormAnalysis>): String? {
        if (analyses.isEmpty()) return null
        val patterns = analyses.map { a -> a.marked?.let { Phonology.transferLength(form, it) } ?: "" }.toSet()
        return patterns.singleOrNull()
    }
}

/**
 * The pronunciation a text is read in by default: the bundle's own choice (meta key
 * "pronunciation") when it has one, else Homeric for Homer, Koine for the New Testament and
 * Attic for everything else.
 */
fun defaultPronunciation(slug: String, author: String?, meta: String?): Pronunciation =
    Pronunciation.fromKey(meta) ?: when {
        author == "Ὅμηρος" || author == "Homer" -> Pronunciation.HOMERIC
        slug == "newtestament" -> Pronunciation.KOINE
        else -> Pronunciation.ATTIC
    }
