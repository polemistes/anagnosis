package no.anagnosis.data

/** Decodes the nine-position Perseus treebank tag, e.g. "v3spia---". */
object Morphology {
    private val pos = mapOf(
        'n' to "noun", 'v' to "verb", 'a' to "adjective", 'd' to "adverb", 'l' to "article",
        'g' to "particle", 'c' to "conjunction", 'r' to "preposition", 'p' to "pronoun",
        'm' to "numeral", 'i' to "interjection", 'u' to "punctuation", 'e' to "exclamation",
        'x' to "irregular",
    )
    private val person = mapOf('1' to "1st", '2' to "2nd", '3' to "3rd")
    private val number = mapOf('s' to "singular", 'p' to "plural", 'd' to "dual")
    private val tense = mapOf(
        'p' to "present", 'i' to "imperfect", 'r' to "perfect", 'l' to "pluperfect",
        't' to "future perfect", 'f' to "future", 'a' to "aorist",
    )
    private val mood = mapOf(
        'i' to "indicative", 's' to "subjunctive", 'o' to "optative", 'n' to "infinitive",
        'm' to "imperative", 'p' to "participle",
    )
    private val voice = mapOf('a' to "active", 'p' to "passive", 'm' to "middle", 'e' to "middle/passive")
    private val gender = mapOf('m' to "masculine", 'f' to "feminine", 'n' to "neuter")
    private val case = mapOf(
        'n' to "nominative", 'g' to "genitive", 'd' to "dative", 'a' to "accusative",
        'v' to "vocative", 'l' to "locative",
    )
    private val degree = mapOf('c' to "comparative", 's' to "superlative")

    fun describe(postag: String): String {
        if (postag.length < 9) return ""
        val p = postag.padEnd(9, '-')
        val parts = mutableListOf<String>()
        pos[p[0]]?.let { parts += it }
        person[p[1]]?.let { parts += "$it person" }
        number[p[2]]?.let { parts += it }
        tense[p[3]]?.let { parts += it }
        mood[p[4]]?.let { parts += it }
        voice[p[5]]?.let { parts += it }
        gender[p[6]]?.let { parts += it }
        case[p[7]]?.let { parts += it }
        degree[p[8]]?.let { parts += it }
        return parts.joinToString(", ")
    }
}
