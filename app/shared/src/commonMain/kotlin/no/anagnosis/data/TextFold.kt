package no.anagnosis.data

import no.anagnosis.greek.GreekNormalizer

/**
 * Folding for the text search. Every character maps to exactly one character, so that an offset
 * in the folded string is the same offset in the original and a match can be highlighted where
 * it was found.
 */
object TextFold {
    private val latin: Map<Char, Char> = buildMap {
        fun add(base: Char, variants: String) {
            variants.forEach { put(it, base) }
            variants.uppercase().forEach { put(it, base.uppercaseChar()) }
        }
        add('a', "àáâãäåā"); add('e', "èéêëē"); add('i', "ìíîïī"); add('o', "òóôõöøō")
        add('u', "ùúûüū"); add('y', "ýÿ"); add('c', "ç"); add('n', "ñ")
    }

    private const val APOSTROPHES = "’‘ʼ᾽᾿"
    private const val QUOTES = "“”„"

    /** One character folded; see [fold]. */
    fun foldChar(c: Char, ignoreAccents: Boolean, ignoreCase: Boolean): Char {
        var ch = c
        if (ignoreAccents) {
            val greek = GreekNormalizer.baseLetter(ch)
            ch = when {
                greek != null -> if (ch.isUpperCase() || ch.isTitleCase()) greek.uppercaseChar() else greek
                else -> latin[ch] ?: ch
            }
        }
        if (ignoreCase) ch = ch.lowercaseChar()
        return when (ch) {
            'ς' -> 'σ'
            '\n' -> ' '
            in APOSTROPHES -> '\''
            in QUOTES -> '"'
            else -> ch
        }
    }

    /**
     * The string with, when asked, the diacritics of Greek and Latin letters removed (case kept)
     * and the case lowered; and always final sigma as σ, the elision marks and curly apostrophes
     * as ', curly quotes as ", and a newline as a space, so that a phrase runs on over a line end.
     */
    fun fold(s: String, ignoreAccents: Boolean, ignoreCase: Boolean): String {
        val out = CharArray(s.length)
        for (i in s.indices) out[i] = foldChar(s[i], ignoreAccents, ignoreCase)
        return out.concatToString()
    }

    /**
     * A regular expression folded as [fold] folds the text, except what follows a backslash
     * (`\b`, `\s`, `\.`) and the name of a class in `\p{...}`, which keep their meaning.
     */
    fun foldPattern(pattern: String, ignoreAccents: Boolean, ignoreCase: Boolean): String {
        val sb = StringBuilder(pattern.length)
        var i = 0
        while (i < pattern.length) {
            val c = pattern[i]
            if (c == '\\' && i + 1 < pattern.length) {
                val next = pattern[i + 1]
                sb.append(c).append(next)
                i += 2
                if ((next == 'p' || next == 'P') && i < pattern.length && pattern[i] == '{') {
                    val close = pattern.indexOf('}', i)
                    val end = if (close < 0) pattern.length else close + 1
                    sb.append(pattern, i, end)
                    i = end
                }
                continue
            }
            sb.append(foldChar(c, ignoreAccents, ignoreCase))
            i++
        }
        return sb.toString()
    }
}
