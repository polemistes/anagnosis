package no.anagnosis.speech

import androidx.compose.runtime.Composable
import no.anagnosis.greek.Pronunciation
import no.anagnosis.greek.Utterance

/**
 * One utterance synthesised: [pcm] 16-bit mono samples at [sampleRate], and for each word of the
 * utterance the sample at which it starts ([wordStarts], same order as [Utterance.words]).
 * [playbackSpeed] below 1 plays it slower than it was made, at the same pitch: the engine
 * cannot speak slower than [MIN_ENGINE_WPM] words a minute.
 */
class Speech(val pcm: ShortArray, val sampleRate: Int, val wordStarts: IntArray, val playbackSpeed: Float = 1f) {
    /** The index of the word being spoken at sample [position]. */
    fun wordAt(position: Int): Int {
        var i = 0
        while (i + 1 < wordStarts.size && wordStarts[i + 1] <= position) i++
        return i
    }
}

/** The synthesiser (eSpeak NG on Android). */
interface SpeechEngine {
    /**
     * Speaks [utterance] into memory at [speed] per cent of the standard speed, in a man's voice
     * or a woman's ([female]). Blocks: call it off the main thread.
     */
    fun synthesize(utterance: Utterance, speed: Int, female: Boolean): Speech
    /** Cuts short a synthesis under way on another thread. */
    fun abort()
}

/** Plays synthesised speech, one utterance at a time. */
interface PcmPlayer {
    /** Starts playing [speech], ending whatever was playing; returns at once. */
    fun start(speech: Speech)
    fun pause()
    fun resume()
    fun stop()
    /** Samples of the current speech played so far. */
    val position: Int
    /** Whether the current speech has been played to its end (or stopped). */
    val done: Boolean
    /** Asks for the sound output while reading ([on]) and gives it back after. */
    fun focus(on: Boolean)
    fun release()
}

/** The engine's voice for a pronunciation: Homeric and Attic share the tonal voice. */
fun voiceOf(p: Pronunciation, female: Boolean = false): String =
    (if (p == Pronunciation.KOINE) "grc-koine" else "grc") + (if (female) "-f" else "")

/** The standard speed, 100 per cent: words per minute. */
const val STANDARD_WPM = 100

/** eSpeak speaks no slower than this; slower speech is stretched in playback. */
const val MIN_ENGINE_WPM = 80

/**
 * How speech at [speed] per cent is made: the engine's words per minute, and the playback speed
 * that brings it down further where the engine cannot go so slow.
 */
fun engineRate(speed: Int): Pair<Int, Float> {
    val wpm = STANDARD_WPM * speed / 100
    return if (wpm >= MIN_ENGINE_WPM) wpm to 1f else MIN_ENGINE_WPM to wpm.toFloat() / MIN_ENGINE_WPM
}

/**
 * Where each word of [u] starts, from the engine's word events (character offset in [Utterance.text],
 * sample). A word's phonemes start two characters after its offset (past "[["); events for the
 * pauses are not words. A word without an event (one run into the word before, as an elided
 * word is) starts where the one before it does.
 */
fun wordStarts(u: Utterance, events: List<Pair<Int, Int>>): IntArray {
    val starts = IntArray(u.words.size) { -1 }
    val byOffset = HashMap<Int, Int>()
    for ((i, o) in u.offsets.withIndex()) byOffset[o + 2] = i
    for ((pos, sample) in events) {
        val i = byOffset[pos] ?: continue
        if (starts[i] < 0) starts[i] = sample
    }
    for (i in starts.indices) if (starts[i] < 0) starts[i] = if (i == 0) 0 else starts[i - 1]
    return starts
}

/** The platform's synthesiser, or null where there is none. */
@Composable
expect fun rememberSpeechEngine(): SpeechEngine?

/** The platform's player, or null where there is none. */
@Composable
expect fun rememberPcmPlayer(): PcmPlayer?
