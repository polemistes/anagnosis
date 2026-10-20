package no.anagnosis.greek

/**
 * The pronunciation the reader's voice uses. Homeric and Attic have vowel length and a pitch
 * accent; Koine (Hellenistic Greek) has neither, and a stress accent. The sound tables are in
 * app/PLAN-speech.md, section 1.
 */
enum class Pronunciation(val label: String, val description: String, val key: String) {
    HOMERIC("Homeric", "Ionic Greek of the epics, about 700 BC", "homeric"),
    ATTIC("Attic", "Athens, about 400 BC", "attic"),
    KOINE("Koine", "Hellenistic Greek of the New Testament, about AD 100", "koine");

    companion object {
        fun fromKey(key: String?): Pronunciation? = entries.firstOrNull { it.key == key }
    }
}

/** The pitch (or stress) of a vowel. */
enum class Tone { HIGH, RISING, FALLING, STRESS }

/**
 * One sound of a word. [ipa] is its IPA spelling (a vowel with its length mark: "ɛː", "ai");
 * [vowel] marks the nucleus of a syllable; [tone] is set on vowels only. [coda] marks a
 * consonant that closes its syllable whatever follows (Koine αυ ευ ηυ: the v or f).
 */
class Segment(
    val ipa: String,
    val vowel: Boolean = false,
    val long: Boolean = false,
    val tone: Tone? = null,
    val coda: Boolean = false,
) {
    override fun toString(): String = ipa + (tone?.let { "/$it" } ?: "")
}

object Phonology {
    private const val SMOOTH = '̓'
    private const val ROUGH = '̔'
    private const val ACUTE = '́'
    private const val GRAVE = '̀'
    private const val CIRCUMFLEX = '͂'
    private const val DIAERESIS = '̈'
    private const val SUBSCRIPT = 'ͅ'
    private const val MACRON = '̄'
    private const val BREVE = '̆'

    /** Combining marks read from decomposed input, with the variants that mean the same. */
    private val COMBINING = mapOf(
        SMOOTH to SMOOTH, ROUGH to ROUGH, ACUTE to ACUTE, GRAVE to GRAVE, CIRCUMFLEX to CIRCUMFLEX,
        DIAERESIS to DIAERESIS, SUBSCRIPT to SUBSCRIPT, MACRON to MACRON, BREVE to BREVE,
        '́' to ACUTE, '̀' to GRAVE, '̓' to SMOOTH, '̂' to CIRCUMFLEX, '̃' to CIRCUMFLEX,
        '̈́' to DIAERESIS,
    )

    /** Letters with a length mark, which [Polytonic.decompose] does not know. */
    private val LENGTH_LETTERS = mapOf(
        'ᾰ' to ('α' to BREVE), 'ᾱ' to ('α' to MACRON), 'ῐ' to ('ι' to BREVE), 'ῑ' to ('ι' to MACRON),
        'ῠ' to ('υ' to BREVE), 'ῡ' to ('υ' to MACRON), 'Ᾰ' to ('α' to BREVE), 'Ᾱ' to ('α' to MACRON),
        'Ῐ' to ('ι' to BREVE), 'Ῑ' to ('ι' to MACRON), 'Ῠ' to ('υ' to BREVE), 'Ῡ' to ('υ' to MACRON),
    )

    /** The marks of elision at the end of a word. */
    private val ELISION = setOf('ʼ', '’', '᾽', '\'', '᾿', '‘')

    private const val VOWELS = "αεηιουω"
    private val DIPHTHONGS = setOf("αι", "ει", "οι", "υι", "αυ", "ευ", "ηυ", "ου", "ωυ")

    /** A letter of the word with its marks: [base] lower case, [original] as written (capital, final sigma). */
    private class Letter(val base: Char, val marks: MutableSet<Char> = mutableSetOf(), val original: Char = base)

    /** A vowel or diphthong of the word: [key] its letters ("ου", "α", "ᾳ" written "ᾳ"). */
    private class Nucleus(
        val key: String,
        val long: Boolean,
        val accent: Char?,
        val rough: Boolean,
    )

    /** Either a consonant letter or a nucleus, in order. */
    private sealed class Unit {
        class C(val letter: Char, val rough: Boolean) : Unit()
        class V(val nucleus: Nucleus) : Unit()
    }

    /** The letters of a word, lower case and with their marks; [elided] when it ends in an elision mark. */
    private fun letters(form: String): Pair<List<Letter>, Boolean> {
        val out = ArrayList<Letter>()
        var elided = false
        for (c in form) {
            val mark = COMBINING[c]
            if (mark != null) {
                out.lastOrNull()?.marks?.add(mark)
                continue
            }
            if (c in ELISION) {
                if (out.isNotEmpty()) elided = true
                continue
            }
            val length = LENGTH_LETTERS[c]
            if (length != null) {
                out += Letter(length.first, mutableSetOf(length.second), if (c.isUpperCase()) length.first.uppercaseChar() else length.first)
                elided = false
                continue
            }
            val (base0, marks) = Polytonic.decompose(c)
            var base = base0.lowercaseChar()
            if (base == 'ς' || base == 'ϲ') base = 'σ'
            if (base == 'ϐ') base = 'β'
            if (base == 'ϑ') base = 'θ'
            if (base == 'ϕ') base = 'φ'
            if (base !in 'α'..'ω') continue
            out += Letter(base, marks.toMutableSet(), base0)
            elided = false
        }
        return out to elided
    }

    /** The word cut into consonants and nuclei. */
    private fun units(letters: List<Letter>): List<Unit> {
        val out = ArrayList<Unit>()
        var i = 0
        while (i < letters.size) {
            val l = letters[i]
            if (l.base !in VOWELS) {
                val rough = l.base == 'ρ' && ROUGH in l.marks && out.isEmpty()
                out += Unit.C(l.base, rough)
                i++
                continue
            }
            val next = letters.getOrNull(i + 1)
            val pair = if (next != null) "${l.base}${next.base}" else ""
            val diphthong = next != null && pair in DIPHTHONGS && DIAERESIS !in next.marks &&
                l.marks.none { it == SMOOTH || it == ROUGH || it == ACUTE || it == GRAVE || it == CIRCUMFLEX || it == SUBSCRIPT || it == MACRON || it == BREVE }
            val marks = if (diphthong) l.marks + next!!.marks else l.marks.toSet()
            val accent = when {
                CIRCUMFLEX in marks -> CIRCUMFLEX
                ACUTE in marks -> ACUTE
                GRAVE in marks -> GRAVE
                else -> null
            }
            // the breathing of the first nucleus of the word (an inner one is a koronis)
            val rough = ROUGH in marks && out.isEmpty()
            val key: String
            val long: Boolean
            if (diphthong) {
                key = pair
                long = true
            } else if (SUBSCRIPT in l.marks) {
                key = "${l.base}$SUBSCRIPT"
                long = true
            } else {
                key = l.base.toString()
                long = when (l.base) {
                    'η', 'ω' -> true
                    'ε', 'ο' -> false
                    else -> BREVE !in l.marks && (MACRON in l.marks || CIRCUMFLEX in l.marks)
                }
            }
            out += Unit.V(Nucleus(key, long, accent, rough))
            i += if (diphthong) 2 else 1
        }
        return out
    }

    /**
     * Copies the vowel-length marks of [marked] (the same word with macrons from the analyser)
     * onto [form], so that the form keeps its own accents, breathings and capitals. Null when
     * the two are not the same letters.
     */
    fun transferLength(form: String, marked: String): String? {
        val (a, _) = letters(form)
        val (b, _) = letters(marked)
        if (a.size != b.size || a.indices.any { a[it].base != b[it].base }) return null
        for (i in a.indices) {
            if (MACRON in b[i].marks && a[i].marks.none { it == MACRON || it == BREVE }) a[i].marks += MACRON
        }
        return buildString {
            for (l in a) {
                append(l.original)
                for (m in l.marks.sortedBy { MARK_ORDER.indexOf(it) }) append(m)
            }
        }
    }

    private val MARK_ORDER = listOf(MACRON, BREVE, DIAERESIS, SMOOTH, ROUGH, ACUTE, GRAVE, CIRCUMFLEX, SUBSCRIPT)

    /**
     * The sounds of one word in [variant]. [marked] is the form with vowel-length marks (see
     * [transferLength]), or null when none is known; its marks are used, the form's own spelling
     * otherwise. Gives nothing for a token without Greek letters.
     */
    fun segments(form: String, marked: String?, variant: Pronunciation): List<Segment> {
        val (letters, _) = letters(marked ?: form)
        if (letters.isEmpty()) return emptyList()
        val units = units(letters)
        return when (variant) {
            Pronunciation.KOINE -> koine(units)
            else -> classical(units, variant)
        }
    }

    /** Whether the word ends in an elision mark (ἀλλ᾽, δ᾽): it is then run into the next word. */
    fun isElided(form: String): Boolean = letters(form).second

    // --- Attic and Homeric -------------------------------------------------------------------

    private val CLASSICAL_VOWELS = mapOf(
        "α" to "a", "ε" to "e", "η" to "ɛː", "ι" to "i", "ο" to "o", "ω" to "ɔː", "υ" to "y",
        "αι" to "ai", "ει" to "eː", "οι" to "oi", "υι" to "yi", "αυ" to "au", "ευ" to "eu", "ηυ" to "ɛːu",
        "ου" to "uː", "ωυ" to "ɔːu", "α$SUBSCRIPT" to "aːi", "η$SUBSCRIPT" to "ɛːi", "ω$SUBSCRIPT" to "ɔːi",
    )

    private val HOMERIC_VOWELS = CLASSICAL_VOWELS + mapOf("υ" to "u", "υι" to "ui", "ου" to "oː")

    private val CLASSICAL_CONSONANTS = mapOf(
        'β' to "b", 'γ' to "g", 'δ' to "d", 'ζ' to "zd", 'θ' to "tʰ", 'κ' to "k", 'λ' to "l", 'μ' to "m",
        'ν' to "n", 'ξ' to "ks", 'π' to "p", 'ρ' to "r", 'σ' to "s", 'τ' to "t", 'φ' to "pʰ", 'χ' to "kʰ", 'ψ' to "ps",
    )

    private fun classical(units: List<Unit>, variant: Pronunciation): List<Segment> {
        val vowels = if (variant == Pronunciation.HOMERIC) HOMERIC_VOWELS else CLASSICAL_VOWELS
        val out = ArrayList<Segment>()
        for ((i, u) in units.withIndex()) {
            val next = units.getOrNull(i + 1)
            when (u) {
                is Unit.C -> {
                    if (u.rough) out += Segment("h")
                    out += Segment(consonant(u.letter, next, CLASSICAL_CONSONANTS))
                }
                is Unit.V -> {
                    val n = u.nucleus
                    if (n.rough) out += Segment("h")
                    var ipa = vowels.getValue(n.key)
                    // a long α ι υ: the macron or circumflex makes the plain vowel long
                    if (n.long && n.key.length == 1 && !ipa.contains('ː')) ipa += "ː"
                    val tone = when (n.accent) {
                        ACUTE -> if (n.long) Tone.RISING else Tone.HIGH
                        CIRCUMFLEX -> Tone.FALLING
                        else -> null
                    }
                    out += Segment(ipa, vowel = true, long = n.long, tone = tone)
                }
            }
        }
        return out
    }

    /** A consonant letter with the changes its neighbour makes: γ before a velar, σ before a voiced one. */
    private fun consonant(letter: Char, next: Unit?, table: Map<Char, String>): String {
        val following = (next as? Unit.C)?.letter
        return when {
            letter == 'γ' && following != null && following in "γκχξ" -> "ŋ"
            letter == 'σ' && following != null && following in "βγδμ" -> "z"
            else -> table.getValue(letter)
        }
    }

    // --- Koine ---------------------------------------------------------------------------------

    private val KOINE_VOWELS = mapOf(
        "α" to "a", "ε" to "ɛ", "η" to "e", "ι" to "i", "ο" to "o", "ω" to "o", "υ" to "y",
        "αι" to "ɛ", "ει" to "i", "οι" to "y", "υι" to "y", "ου" to "u",
        "α$SUBSCRIPT" to "a", "η$SUBSCRIPT" to "e", "ω$SUBSCRIPT" to "o", "ωυ" to "ou",
    )

    /** αυ ευ ηυ: the vowel, then v (or f before a voiceless consonant and at the end of the word). */
    private val KOINE_V_DIPHTHONGS = mapOf("αυ" to "a", "ευ" to "e", "ηυ" to "e")

    private val KOINE_CONSONANTS = mapOf(
        'β' to "v", 'γ' to "ɣ", 'δ' to "ð", 'ζ' to "z", 'θ' to "θ", 'κ' to "k", 'λ' to "l", 'μ' to "m",
        'ν' to "n", 'ξ' to "ks", 'π' to "p", 'ρ' to "r", 'σ' to "s", 'τ' to "t", 'φ' to "f", 'χ' to "x", 'ψ' to "ps",
    )

    private fun koine(units: List<Unit>): List<Segment> {
        val out = ArrayList<Segment>()
        var stressed = false
        for ((i, u) in units.withIndex()) {
            val next = units.getOrNull(i + 1)
            when (u) {
                is Unit.C -> {
                    var ipa = consonant(u.letter, next, KOINE_CONSONANTS)
                    // γγ γκ γχ γξ: the nasal, then a stop for the second γ
                    if (u.letter == 'γ' && out.lastOrNull()?.ipa == "ŋ") ipa = "g"
                    // double consonants are one sound
                    if (out.lastOrNull()?.let { !it.vowel && it.ipa == ipa } == true) continue
                    out += Segment(ipa)
                }
                is Unit.V -> {
                    val n = u.nucleus
                    val tone = if (n.accent != null && !stressed) Tone.STRESS.also { stressed = true } else null
                    val vd = KOINE_V_DIPHTHONGS[n.key]
                    if (vd != null) {
                        out += Segment(vd, vowel = true, tone = tone)
                        val voiceless = next == null || (next is Unit.C && next.letter in "πτκφθχξψσ")
                        out += Segment(if (voiceless) "f" else "v", coda = true)
                    } else {
                        out += Segment(KOINE_VOWELS.getValue(n.key), vowel = true, tone = tone)
                    }
                }
            }
        }
        return out
    }

    // --- spelling the sounds -------------------------------------------------------------------

    private val STOPS = setOf("p", "b", "t", "d", "k", "g", "pʰ", "tʰ", "kʰ", "f", "v", "θ", "ð", "x", "ɣ")
    private val LIQUIDS_NASALS = setOf("l", "r", "m", "n")

    /** Whether the consonants [c] can begin a Greek word, and so begin the syllable they precede. */
    private fun legalOnset(c: List<String>): Boolean = when (c.size) {
        0, 1 -> true
        2 -> (c[0] == "s" && (c[1] in STOPS || c[1] == "m")) ||
            (c[0] in STOPS && (c[1] in STOPS || c[1] in LIQUIDS_NASALS)) ||
            (c[0] == "m" && c[1] == "n")
        3 -> c[0] == "s" && c[1] in STOPS && c[2] in setOf("l", "r")
        else -> false
    }

    /** The word in IPA with its tones: "anɛ̌ːr", "ˈanθropos". */
    fun ipa(segments: List<Segment>): String {
        val sb = StringBuilder()
        for ((i, s) in segments.withIndex()) {
            if (s.vowel && s.tone == Tone.STRESS) {
                // the consonants before the vowel that can begin a syllable go after the stress mark
                var j = i
                while (j > 0 && !segments[j - 1].vowel && !segments[j - 1].coda) j--
                val cluster = segments.subList(j, i).map { it.ipa }
                var k = j
                while (!legalOnset(cluster.subList(k - j, cluster.size))) k++
                val consonants = segments.subList(k, i).sumOf { it.ipa.length }
                sb.insert(sb.length - consonants, 'ˈ')
                sb.append(s.ipa)
                continue
            }
            if (s.vowel && s.tone != null) {
                val mark = when (s.tone) {
                    Tone.HIGH -> '́'
                    Tone.RISING -> '̌'
                    Tone.FALLING -> '̂'
                    else -> null
                }
                sb.append(s.ipa[0])
                if (mark != null) sb.append(mark)
                sb.append(s.ipa, 1, s.ipa.length)
                continue
            }
            sb.append(s.ipa)
        }
        return sb.toString()
    }

    /** The IPA of a word as it is shown on the word sheet. */
    fun ipa(form: String, marked: String?, variant: Pronunciation): String = ipa(segments(form, marked, variant))

    // --- eSpeak --------------------------------------------------------------------------------

    /** IPA to the mnemonics of our eSpeak phoneme table (app/espeak/phsource/ph_grc). */
    private val ESPEAK = mapOf(
        "a" to "a", "aː" to "a:", "e" to "e", "eː" to "e:", "ɛ" to "E", "ɛː" to "E:", "i" to "i", "iː" to "i:",
        "o" to "o", "oː" to "o:", "ɔː" to "O:", "u" to "u", "uː" to "u:", "y" to "y", "yː" to "y:",
        "ai" to "aI", "au" to "aU", "oi" to "oI", "ou" to "oU", "yi" to "yI", "ui" to "uI", "eu" to "eU", "ɛːu" to "EU",
        "ɔːu" to "OU", "aːi" to "aaI", "ɛːi" to "EEI", "ɔːi" to "OOI",
        "p" to "p", "b" to "b", "t" to "t", "d" to "d", "k" to "k", "g" to "g", "pʰ" to "pH", "tʰ" to "tH", "kʰ" to "kH",
        "f" to "f", "v" to "v", "θ" to "T", "ð" to "D", "x" to "x", "ɣ" to "Q", "s" to "s", "z" to "z",
        "m" to "m", "n" to "n", "ŋ" to "N", "l" to "l", "r" to "r", "h" to "h",
        "zd" to "zd", "ks" to "ks", "ps" to "ps",
    )

    /**
     * eSpeak phoneme mnemonics for one word (without the [[ ]]). Homeric and Attic: every vowel is
     * followed by a tone phoneme (0 level, 1 high, 2 rising, 3 falling). Koine: the stress mark '
     * goes before the stressed syllable, and a word without an accent gets the unstressed mark %,
     * so that eSpeak does not stress it on its own.
     */
    fun espeak(segments: List<Segment>, variant: Pronunciation): String {
        val sb = StringBuilder()
        val tonal = variant != Pronunciation.KOINE
        for ((i, s) in segments.withIndex()) {
            val m = ESPEAK[s.ipa] ?: error("no eSpeak phoneme for ${s.ipa}")
            if (!tonal && s.vowel && s.tone == Tone.STRESS) {
                var j = i
                while (j > 0 && !segments[j - 1].vowel && !segments[j - 1].coda) j--
                val cluster = segments.subList(j, i).map { it.ipa }
                var k = j
                while (!legalOnset(cluster.subList(k - j, cluster.size))) k++
                val consonants = segments.subList(k, i).sumOf { (ESPEAK[it.ipa] ?: "").length }
                sb.insert(sb.length - consonants, '\'')
            }
            sb.append(m)
            if (tonal && s.vowel) {
                sb.append(
                    when (s.tone) {
                        Tone.HIGH -> '1'
                        Tone.RISING -> '2'
                        Tone.FALLING -> '3'
                        else -> '0'
                    }
                )
            }
        }
        if (!tonal && segments.none { it.tone == Tone.STRESS }) {
            val first = segments.indexOfFirst { it.vowel }
            if (first >= 0) {
                val before = segments.subList(0, first).sumOf { (ESPEAK[it.ipa] ?: "").length }
                sb.insert(before, '%')
            }
        }
        return sb.toString()
    }
}
