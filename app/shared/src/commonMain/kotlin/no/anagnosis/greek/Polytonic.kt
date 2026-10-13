package no.anagnosis.greek

/**
 * Composition of polytonic Greek: applies a breathing, accent, iota subscript or diaeresis to a
 * vowel, the way the standard Greek polytonic keyboard's dead keys do. Works on the precomposed
 * characters (Greek Extended block) by decomposing, adjusting, and recomposing.
 */
object Polytonic {
    const val SMOOTH = '̓'   // ψιλή
    const val ROUGH = '̔'    // δασεῖα
    const val ACUTE = '́'    // ὀξεῖα
    const val GRAVE = '̀'    // βαρεῖα
    const val CIRCUMFLEX = '͂' // περισπωμένη
    const val SUBSCRIPT = 'ͅ' // ὑπογεγραμμένη
    const val DIAERESIS = '̈'

    private val vowels = "αεηιουωΑΕΗΙΟΥΩρΡ"

    /**
     * Toggles [mark] on the last character of [text] when that character is a vowel (or rho for
     * breathings). Breathings replace each other, as do accents; the subscript and diaeresis
     * toggle independently. Returns the text unchanged when nothing applies.
     */
    fun apply(text: String, mark: Char): String {
        if (text.isEmpty()) return text
        val last = text.last()
        val (base, marks) = decompose(last)
        if (base !in vowels) return text
        if (base == 'ρ' || base == 'Ρ') {
            if (mark != SMOOTH && mark != ROUGH) return text
        }
        val newMarks = marks.toMutableSet()
        when (mark) {
            SMOOTH, ROUGH -> { val had = mark in newMarks; newMarks -= setOf(SMOOTH, ROUGH); if (!had) newMarks += mark }
            ACUTE, GRAVE, CIRCUMFLEX -> { val had = mark in newMarks; newMarks -= setOf(ACUTE, GRAVE, CIRCUMFLEX); if (!had) newMarks += mark }
            SUBSCRIPT, DIAERESIS -> if (mark in newMarks) newMarks -= mark else newMarks += mark
            else -> return text
        }
        val composed = compose(base, newMarks) ?: return text
        return text.dropLast(1) + composed
    }

    // --- tables -------------------------------------------------------------------------

    private val decomposition: Map<Char, Pair<Char, Set<Char>>> by lazy { buildTables().first }
    private val composition: Map<Pair<Char, Set<Char>>, Char> by lazy { buildTables().second }

    fun decompose(c: Char): Pair<Char, Set<Char>> = decomposition[c] ?: (c to emptySet())
    fun compose(base: Char, marks: Set<Char>): Char? = if (marks.isEmpty()) base else composition[base to marks]

    private fun buildTables(): Pair<Map<Char, Pair<Char, Set<Char>>>, Map<Pair<Char, Set<Char>>, Char>> {
        val dec = HashMap<Char, Pair<Char, Set<Char>>>()
        val comp = HashMap<Pair<Char, Set<Char>>, Char>()
        fun add(c: Char, base: Char, vararg marks: Char) {
            val set = marks.toSet()
            dec[c] = base to set
            comp[base to set] = c
        }
        // Basic Greek with tonos (treated as acute) and dialytika
        add('ά', 'α', ACUTE); add('έ', 'ε', ACUTE); add('ή', 'η', ACUTE); add('ί', 'ι', ACUTE); add('ό', 'ο', ACUTE); add('ύ', 'υ', ACUTE); add('ώ', 'ω', ACUTE)
        add('ϊ', 'ι', DIAERESIS); add('ϋ', 'υ', DIAERESIS); add('ΐ', 'ι', DIAERESIS, ACUTE); add('ΰ', 'υ', DIAERESIS, ACUTE)
        add('Ά', 'Α', ACUTE); add('Έ', 'Ε', ACUTE); add('Ή', 'Η', ACUTE); add('Ί', 'Ι', ACUTE); add('Ό', 'Ο', ACUTE); add('Ύ', 'Υ', ACUTE); add('Ώ', 'Ω', ACUTE)
        add('Ϊ', 'Ι', DIAERESIS); add('Ϋ', 'Υ', DIAERESIS)
        // Greek Extended: for each vowel the eight breathing/accent combinations
        val order = listOf(setOf(SMOOTH), setOf(ROUGH), setOf(SMOOTH, GRAVE), setOf(ROUGH, GRAVE), setOf(SMOOTH, ACUTE), setOf(ROUGH, ACUTE), setOf(SMOOTH, CIRCUMFLEX), setOf(ROUGH, CIRCUMFLEX))
        fun block(start: Int, base: Char, upperStart: Int?, upper: Char, count: Int = 8) {
            for (i in 0 until count) add((start + i).toChar(), base, *order[i].toCharArray())
            if (upperStart != null) for (i in 0 until count) add((upperStart + i).toChar(), upper, *order[i].toCharArray())
        }
        block(0x1F00, 'α', 0x1F08, 'Α'); block(0x1F10, 'ε', 0x1F18, 'Ε', 6); block(0x1F20, 'η', 0x1F28, 'Η')
        block(0x1F30, 'ι', 0x1F38, 'Ι'); block(0x1F40, 'ο', 0x1F48, 'Ο', 6); block(0x1F50, 'υ', null, 'Υ'); block(0x1F60, 'ω', 0x1F68, 'Ω')
        add('Ὑ', 'Υ', ROUGH); add('Ὓ', 'Υ', ROUGH, GRAVE); add('Ὕ', 'Υ', ROUGH, ACUTE); add('Ὗ', 'Υ', ROUGH, CIRCUMFLEX)
        // grave and acute (1F70-1F7D)
        add('ὰ', 'α', GRAVE); add('ά', 'α', ACUTE); add('ὲ', 'ε', GRAVE); add('έ', 'ε', ACUTE); add('ὴ', 'η', GRAVE); add('ή', 'η', ACUTE)
        add('ὶ', 'ι', GRAVE); add('ί', 'ι', ACUTE); add('ὸ', 'ο', GRAVE); add('ό', 'ο', ACUTE); add('ὺ', 'υ', GRAVE); add('ύ', 'υ', ACUTE); add('ὼ', 'ω', GRAVE); add('ώ', 'ω', ACUTE)
        // with iota subscript: 1F80-1FAF (breathing+accent+subscript), then 1FB2-1FB7 etc.
        fun subBlock(start: Int, base: Char, upperStart: Int, upper: Char) {
            for (i in 0 until 8) add((start + i).toChar(), base, *(order[i] + SUBSCRIPT).toCharArray())
            for (i in 0 until 8) add((upperStart + i).toChar(), upper, *(order[i] + SUBSCRIPT).toCharArray())
        }
        subBlock(0x1F80, 'α', 0x1F88, 'Α'); subBlock(0x1F90, 'η', 0x1F98, 'Η'); subBlock(0x1FA0, 'ω', 0x1FA8, 'Ω')
        add('ᾲ', 'α', GRAVE, SUBSCRIPT); add('ᾳ', 'α', SUBSCRIPT); add('ᾴ', 'α', ACUTE, SUBSCRIPT); add('ᾶ', 'α', CIRCUMFLEX); add('ᾷ', 'α', CIRCUMFLEX, SUBSCRIPT); add('ᾼ', 'Α', SUBSCRIPT)
        add('ῂ', 'η', GRAVE, SUBSCRIPT); add('ῃ', 'η', SUBSCRIPT); add('ῄ', 'η', ACUTE, SUBSCRIPT); add('ῆ', 'η', CIRCUMFLEX); add('ῇ', 'η', CIRCUMFLEX, SUBSCRIPT); add('ῌ', 'Η', SUBSCRIPT)
        add('ῒ', 'ι', DIAERESIS, GRAVE); add('ΐ', 'ι', DIAERESIS, ACUTE); add('ῖ', 'ι', CIRCUMFLEX); add('ῗ', 'ι', DIAERESIS, CIRCUMFLEX)
        add('ῢ', 'υ', DIAERESIS, GRAVE); add('ΰ', 'υ', DIAERESIS, ACUTE); add('ῦ', 'υ', CIRCUMFLEX); add('ῧ', 'υ', DIAERESIS, CIRCUMFLEX)
        add('ῤ', 'ρ', SMOOTH); add('ῥ', 'ρ', ROUGH); add('Ῥ', 'Ρ', ROUGH)
        add('ῲ', 'ω', GRAVE, SUBSCRIPT); add('ῳ', 'ω', SUBSCRIPT); add('ῴ', 'ω', ACUTE, SUBSCRIPT); add('ῶ', 'ω', CIRCUMFLEX); add('ῷ', 'ω', CIRCUMFLEX, SUBSCRIPT); add('ῼ', 'Ω', SUBSCRIPT)
        return dec to comp
    }

    /**
     * The word without marks of vowel length (Woodhouse's ᾰ, ῑ, and a combining macron or breve),
     * its other combining marks composed again with their letter: ᾰ̓πολείπειν gives ἀπολείπειν.
     */
    fun withoutLength(s: String): String {
        val sb = StringBuilder(s.length)
        for (c in s) {
            when {
                c == '\u0304' || c == '\u0306' -> {}
                c in LENGTH_LETTERS -> sb.append(LENGTH_LETTERS.getValue(c))
                c in COMBINING && sb.isNotEmpty() -> {
                    val (base, marks) = decompose(sb.last())
                    val composed = compose(base, marks + c)
                    if (composed != null) sb.setCharAt(sb.length - 1, composed) else sb.append(c)
                }
                else -> sb.append(c)
            }
        }
        return sb.toString()
    }

    private val LENGTH_LETTERS = mapOf('ᾰ' to 'α', 'ᾱ' to 'α', 'ῐ' to 'ι', 'ῑ' to 'ι', 'ῠ' to 'υ', 'ῡ' to 'υ', 'Ᾰ' to 'Α', 'Ᾱ' to 'Α', 'Ῐ' to 'Ι', 'Ῑ' to 'Ι', 'Ῠ' to 'Υ', 'Ῡ' to 'Υ')
    private val COMBINING = setOf(SMOOTH, ROUGH, ACUTE, GRAVE, CIRCUMFLEX, SUBSCRIPT, DIAERESIS)

    /** Exact search key: NFC lower case with diacritics kept, final sigma normalised to ς. */
    fun exactKey(s: String): String {
        val t = s.trim().lowercase().replace('σ', 'σ')
        return if (t.endsWith('σ')) t.dropLast(1) + 'ς' else t
    }
}
