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
    // 'c' (masculine or feminine) is GLAUx's
    private val gender = mapOf('m' to "masculine", 'f' to "feminine", 'n' to "neuter", 'c' to "masculine/feminine")
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

    private val shortPos = mapOf(
        'n' to "noun", 'v' to "verb", 'a' to "adj", 'd' to "adv", 'l' to "art", 'g' to "particle",
        'c' to "conj", 'r' to "prep", 'p' to "pron", 'm' to "num", 'i' to "interj", 'u' to "punct",
        'e' to "excl", 'x' to "irreg",
    )
    private val shortNumber = mapOf('s' to "sg", 'p' to "pl", 'd' to "du")
    private val shortTense = mapOf('p' to "pres", 'i' to "impf", 'r' to "perf", 'l' to "plpf", 't' to "fut perf", 'f' to "fut", 'a' to "aor")
    private val shortMood = mapOf('i' to "ind", 's' to "subj", 'o' to "opt", 'n' to "inf", 'm' to "imper", 'p' to "part")
    private val shortVoice = mapOf('a' to "act", 'p' to "pass", 'm' to "mid", 'e' to "mid/pass")
    private val shortGender = mapOf('m' to "masc", 'f' to "fem", 'n' to "neut", 'c' to "m/f")
    private val shortCase = mapOf('n' to "nom", 'g' to "gen", 'd' to "dat", 'a' to "acc", 'v' to "voc", 'l' to "loc")
    private val shortDegree = mapOf('c' to "comp", 's' to "superl")

    /** The part of speech alone, abbreviated; a participle or an infinitive is named as such. */
    fun pos(postag: String): String {
        if (postag.length < 9) return ""
        return when (postag[4]) {
            'p' -> "ptcp"
            'n' -> "inf"
            else -> shortPos[postag[0]] ?: ""
        }
    }

    /**
     * The tag in the abbreviated form of a grammar: "verb 3rd sg pres ind act", "noun fem gen sg",
     * "part aor pass part masc nom pl". Finite verbs list person and number first; nominal forms
     * gender, case and number.
     */
    fun short(postag: String): String {
        if (postag.length < 9) return ""
        val p = postag.padEnd(9, '-')
        val parts = mutableListOf<String>()
        shortPos[p[0]]?.let { parts += it }
        val nominal = listOfNotNull(shortGender[p[6]], shortCase[p[7]], shortNumber[p[2]])
        when {
            p[4] == 'p' -> { // participle: its verbal side, then its nominal side
                shortTense[p[3]]?.let { parts += it }
                shortVoice[p[5]]?.let { parts += it }
                parts += "part"
                parts += nominal
            }
            p[4] == 'n' -> {
                shortTense[p[3]]?.let { parts += it }
                parts += "inf"
                shortVoice[p[5]]?.let { parts += it }
            }
            p[1] != '-' || p[4] != '-' -> {
                person[p[1]]?.let { parts += it }
                shortNumber[p[2]]?.let { parts += it }
                shortTense[p[3]]?.let { parts += it }
                shortMood[p[4]]?.let { parts += it }
                shortVoice[p[5]]?.let { parts += it }
            }
            else -> parts += nominal
        }
        shortDegree[p[8]]?.let { parts += it }
        return parts.joinToString(" ")
    }
}
