package no.anagnosis.greek

/** The pause after a spoken word. */
enum class Pause { NONE, JOIN, SHORT, LONG }

/** A word of the text to be spoken: its token, where it stands in its line, its length-marked form. */
class SpeechWord(
    val tokenId: Long,
    val lineId: Long,
    val form: String,
    val start: Int,
    val end: Int,
    val marked: String? = null,
)

/** One spoken word: its token and place, its sounds for eSpeak, and the pause after it. */
class UtteranceWord(
    val tokenId: Long,
    val lineId: Long,
    val start: Int,
    val end: Int,
    val phonemes: String,
    val pause: Pause,
)

/**
 * One sentence (or line) ready for the engine. [text] is eSpeak input: every word as `[[...]]`,
 * with the pauses between; [offsets] gives where each word's `[[` starts in it.
 */
class Utterance(val words: List<UtteranceWord>, val variant: Pronunciation) {
    val text: String
    val offsets: List<Int>

    init {
        val sb = StringBuilder()
        val offs = ArrayList<Int>()
        for (w in words) {
            offs += sb.length
            sb.append("[[").append(w.phonemes).append(pauseText(w.pause)).append("]]")
            if (w.pause != Pause.JOIN) sb.append(' ')
        }
        text = sb.toString().trimEnd()
        offsets = offs
    }

    /** The index of the word whose text starts at or before [offset]. */
    fun wordAt(offset: Int): Int {
        var i = offsets.binarySearch(offset)
        if (i < 0) i = -i - 2
        return i.coerceIn(0, maxOf(0, words.size - 1))
    }

    companion object {
        /** eSpeak's pause phonemes: _ is a short pause, _: a longer one, _:: longer still. */
        fun pauseText(p: Pause): String = when (p) {
            Pause.NONE, Pause.JOIN -> ""
            Pause.SHORT -> " _:"
            Pause.LONG -> " _::"
        }
    }
}

object Utterances {
    private val LONG_STOPS = setOf('.', '·', '·', ';', ';', '!', ':', '?')
    private val SHORT_STOPS = setOf(',', '—', '–')
    /** The Greek question mark and the semicolon that stands for it. */
    private val QUESTION_MARKS = setOf(';', ';')

    /**
     * The utterance of [words] (in reading order), with pauses from the punctuation that follows
     * each word in its line. [lineText] gives a line's text by id; with [verse] the end of a line
     * is a short pause. With [melody] the sentence melody of [Melody] is laid over the tones
     * (Homeric and Attic; Koine has eSpeak's stress melody already).
     */
    fun build(words: List<SpeechWord>, lineText: (Long) -> String, variant: Pronunciation, verse: Boolean, melody: Boolean = false): Utterance {
        val out = ArrayList<UtteranceWord>()
        val questions = ArrayList<Boolean>()
        for ((i, w) in words.withIndex()) {
            val segs = Phonology.segments(w.form, w.marked, variant)
            if (segs.isEmpty()) continue
            val next = words.getOrNull(i + 1)
            val text = lineText(w.lineId)
            val sameLine = next != null && next.lineId == w.lineId
            val after = if (sameLine) text.substring(minOf(w.end, text.length), minOf(maxOf(next!!.start, w.end), text.length))
                else text.substring(minOf(w.end, text.length))
            var pause = when {
                after.any { it in LONG_STOPS } -> Pause.LONG
                after.any { it in SHORT_STOPS } -> Pause.SHORT
                !sameLine && verse -> Pause.SHORT
                else -> Pause.NONE
            }
            if (pause == Pause.NONE && Phonology.isElided(w.form) && next != null) pause = Pause.JOIN
            if (next == null && pause == Pause.NONE) pause = Pause.SHORT
            out += UtteranceWord(w.tokenId, w.lineId, w.start, w.end, Phonology.espeak(segs, variant), pause)
            questions += after.any { it in QUESTION_MARKS }
        }
        if (melody && variant != Pronunciation.KOINE) {
            val moved = Melody.apply(out.map { it.phonemes }, out.map { it.pause }, questions)
            return Utterance(out.mapIndexed { i, w -> UtteranceWord(w.tokenId, w.lineId, w.start, w.end, moved[i], w.pause) }, variant)
        }
        return Utterance(out, variant)
    }
}
