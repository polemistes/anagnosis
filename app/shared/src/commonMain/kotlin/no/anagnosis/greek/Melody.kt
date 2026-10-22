package no.anagnosis.greek

/**
 * The sentence melody of Homeric and Attic Greek, laid over the pitch accent when the reader
 * turns it on (an option, off by default): the pitch steps down over each stretch between
 * pauses, falls at a full stop and rises before a question mark. Every accent keeps its shape;
 * only its level moves. eSpeak's tone phonemes (app/espeak/phsource/ph_grc) give the four
 * tones at four levels: 1x the highest, 2x, x alone, 3x the lowest; 40 is a final fall and 41
 * a final rise, for a last syllable without an accent.
 */
object Melody {
    /** A tone digit after a vowel's mnemonic. */
    private val TONE = Regex("(?<=[A-Za-z:])([0-3])")
    private val LEVEL = arrayOf("1", "2", "", "3")

    /**
     * The eSpeak [phonemes] of the words of one utterance, each with the [pauses] after it and
     * whether a question mark follows it ([questions]), with their tones moved. A stretch ends
     * at a short or a long pause; one that begins after a long pause (or the start, [afterLong])
     * runs through all four levels, one after a short pause begins a level lower.
     */
    fun apply(phonemes: List<String>, pauses: List<Pause>, questions: List<Boolean>, afterLong: Boolean = true): List<String> {
        val out = ArrayList<String>(phonemes.size)
        var start = 0
        var fromLong = afterLong
        while (start < phonemes.size) {
            var last = start
            while (last < phonemes.size - 1 && pauses[last] != Pause.SHORT && pauses[last] != Pause.LONG) last++
            val long = pauses[last] == Pause.LONG
            val question = questions[last]
            val n = (start..last).sumOf { TONE.findAll(phonemes[it]).count() }
            var i = 0
            for (w in start..last) {
                out += if (n == 0) phonemes[w] else TONE.replace(phonemes[w]) { m ->
                    val level = if (fromLong) minOf(3, 4 * i / n) else 1 + minOf(2, 3 * i / n)
                    val isLast = i == n - 1
                    i++
                    when {
                        isLast && long && m.value == "0" && question -> "41"
                        isLast && long && m.value == "0" -> "40"
                        else -> LEVEL[level] + m.value
                    }
                }
            }
            fromLong = long
            start = last + 1
        }
        return out
    }
}
