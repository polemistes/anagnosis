package no.anagnosis.ui

import no.anagnosis.prefs.LineNumberMode

/**
 * Which line of a page carries which number in the right margin (see paginate in ReaderScreen),
 * from the lines alone: their numbers, whether a number fits beside their first row, and whether
 * they are wordless.
 */
internal object MarginNumbers {
    /** A Greek line of the page: its number ([nInt], [nSub] a letter such as "a"), whether a number fits beside it, whether it has no words. */
    class Line(val nInt: Long, val nSub: String, val fits: Boolean, val wordless: Boolean = false)

    /** The number shown at a line: [nInt] with [nSub]; [own] when it is the line's own; [forced] when the line must be re-wrapped around it. */
    data class Mark(val nInt: Long, val nSub: String, val own: Boolean, val forced: Boolean = false)

    /**
     * A line with no word: no token and no letter in its text (a printed line of signs: the
     * Electra's metrical signs after 1264, the Theogony's asterisks after 1022). The editions
     * print no number beside it, so it carries none in any mode, nor another line's.
     */
    fun isWordless(text: String, tokenCount: Int): Boolean = tokenCount == 0 && text.none { it.isLetter() }

    /**
     * The marks by the lines' indices. All: every line its own number where it fits. Every
     * fifth: a verse whose number is a multiple of five, or a long verse that runs over a fifth
     * number no line carries (the verse 473 that covers 475, as Jebb prints it); the number
     * goes on its own line if it fits there, else on the following line, else on the preceding
     * one (each showing its own number), else on its own line, which is re-wrapped around it.
     * A lettered line has no number of its own in this mode; a wordless line none in any mode,
     * and it never takes a neighbour's.
     */
    fun choose(lines: List<Line>, mode: LineNumberMode): Map<Int, Mark> {
        val out = LinkedHashMap<Int, Mark>()
        fun own(k: Int) = Mark(lines[k].nInt, lines[k].nSub, own = true)
        fun canTake(k: Int) = k in lines.indices && lines[k].fits && !lines[k].wordless && k !in out
        for ((k, line) in lines.withIndex()) {
            when (mode) {
                LineNumberMode.NONE -> {}
                LineNumberMode.ALL -> if (line.fits && !line.wordless) out[k] = own(k)
                LineNumberMode.FIFTH -> {
                    if (line.wordless || line.nSub.isNotEmpty()) continue
                    val n = line.nInt
                    val next = (k + 1 until lines.size).asSequence().map { lines[it] }
                        .firstOrNull { it.nSub.isEmpty() && !it.wordless }?.nInt
                    val covered = (n / 5 + 1) * 5
                    val shown = when {
                        n % 5 == 0L -> own(k)
                        next != null && covered < next -> Mark(covered, "", own = false)
                        else -> null
                    } ?: continue
                    when {
                        line.fits -> out[k] = shown
                        shown.own && canTake(k + 1) -> out[k + 1] = own(k + 1)
                        shown.own && canTake(k - 1) -> out[k - 1] = own(k - 1)
                        else -> out[k] = shown.copy(forced = true)
                    }
                }
            }
        }
        return out
    }
}
