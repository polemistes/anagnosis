package no.anagnosis.greek

/**
 * Latin-letter input schemes for typing Greek without a Greek keyboard. Both map single Latin
 * letters to Greek base letters; diacritics are never typed, since search ignores them.
 *
 * BETA follows the Beta Code / TLG / Logeion convention (q = θ, w = ω, c = ξ, y = ψ, h = η, x = χ).
 * KEYBOARD follows the layout of a Greek keyboard on a QWERTY machine (u = θ, v = ω, j = ξ, c = ψ, h = η, x = χ).
 */
enum class InputScheme(val label: String, val hint: String) {
    BETA("Beta code (TLG, Logeion)", "q = θ, w = ω, c = ξ, y = ψ, h = η"),
    KEYBOARD("Greek keyboard layout", "u = θ, v = ω, j = ξ, c = ψ, h = η"),
}

object Transliteration {
    private val common = mapOf(
        'a' to 'α', 'b' to 'β', 'g' to 'γ', 'd' to 'δ', 'e' to 'ε', 'z' to 'ζ', 'h' to 'η',
        'i' to 'ι', 'k' to 'κ', 'l' to 'λ', 'm' to 'μ', 'n' to 'ν', 'o' to 'ο', 'p' to 'π',
        'r' to 'ρ', 's' to 'σ', 't' to 'τ', 'f' to 'φ', 'x' to 'χ',
    )
    private val beta = common + mapOf('q' to 'θ', 'w' to 'ω', 'c' to 'ξ', 'y' to 'ψ', 'u' to 'υ', 'v' to 'ϝ', 'j' to 'ς')
    private val keyboard = common + mapOf('u' to 'θ', 'v' to 'ω', 'j' to 'ξ', 'c' to 'ψ', 'y' to 'υ', 'w' to 'ς', 'q' to ';')

    /** Converts Latin letters to Greek base letters; Greek input passes through unchanged. */
    fun toGreek(input: String, scheme: InputScheme): String {
        val table = if (scheme == InputScheme.BETA) beta else keyboard
        val sb = StringBuilder(input.length)
        for (ch in input) {
            val lower = ch.lowercaseChar()
            val g = table[lower]
            sb.append(if (g != null && ch in 'A'..'z') g else ch)
        }
        return sb.toString()
    }

    /** Search key: Greek base letters only, final sigma folded, no diacritics, lower case. */
    fun looseKey(s: String): String = GreekNormalizer.looseKey(s)
}

/** Diacritic stripping shared by search and the pipeline's strip_diacritics. */
object GreekNormalizer {
    private val strip: Map<Char, Char> = buildMap {
        fun add(base: Char, variants: String) = variants.forEach { put(it, base) }
        add('α', "ἀἁἂἃἄἅἆἇὰάᾀᾁᾂᾃᾄᾅᾆᾇᾰᾱᾲᾳᾴᾶᾷάΆἈἉἊἋἌἍἎἏᾈᾉᾊᾋᾌᾍᾎᾏᾼ")
        add('ε', "ἐἑἒἓἔἕὲέέΈἘἙἚἛἜἝ")
        add('η', "ἠἡἢἣἤἥἦἧὴήᾐᾑᾒᾓᾔᾕᾖᾗῂῃῄῆῇήΉἨἩἪἫἬἭἮἯᾘᾙᾚᾛᾜᾝᾞᾟῌ")
        add('ι', "ἰἱἲἳἴἵἶἷὶίῐῑῒΐῖῗίϊΐΊἸἹἺἻἼἽἾἿΪ")
        add('ο', "ὀὁὂὃὄὅὸόόΌὈὉὊὋὌὍ")
        add('υ', "ὐὑὒὓὔὕὖὗὺύῠῡῢΰῦῧύϋΰΎὙὛὝὟΫ")
        add('ω', "ὠὡὢὣὤὥὦὧὼώᾠᾡᾢᾣᾤᾥᾦᾧῲῳῴῶῷώΏὨὩὪὫὬὭὮὯᾨᾩᾪᾫᾬᾭᾮᾯῼ")
        add('ρ', "ῤῥῬ")
    }

    /**
     * Matches the pipeline's strip_diacritics: base letters, lower case, no diacritics. A final
     * sigma is written ς at the end of the key, as the stored keys have it, so that a search
     * typed with σ or in Latin letters still matches.
     */
    fun looseKey(s: String): String {
        val sb = StringBuilder(s.length)
        for (raw in s) {
            val ch = strip[raw] ?: raw.lowercaseChar()
            val base = strip[ch] ?: ch
            if (base in 'α'..'ω' || base == 'ϝ') sb.append(base)
        }
        if (sb.isNotEmpty() && sb[sb.length - 1] == 'σ') sb.setCharAt(sb.length - 1, 'ς')
        return sb.toString()
    }

    /** The key with a medial sigma at the end, for prefix searches where the word goes on. */
    fun prefixKey(s: String): String {
        val k = looseKey(s)
        return if (k.endsWith('ς')) k.dropLast(1) + 'σ' else k
    }
}
