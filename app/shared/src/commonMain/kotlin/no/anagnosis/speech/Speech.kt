package no.anagnosis.speech

import androidx.compose.runtime.Composable
import no.anagnosis.greek.Pronunciation
import no.anagnosis.greek.Utterance

/**
 * One utterance synthesised: [pcm] 16-bit mono samples at [sampleRate], and for each word of the
 * utterance the sample at which it starts ([wordStarts], same order as [Utterance.words]).
 */
class Speech(val pcm: ShortArray, val sampleRate: Int, val wordStarts: IntArray) {
    /** The index of the word being spoken at sample [position]. */
    fun wordAt(position: Int): Int {
        var i = 0
        while (i + 1 < wordStarts.size && wordStarts[i + 1] <= position) i++
        return i
    }
}

/** The synthesiser (eSpeak NG on Android). */
interface SpeechEngine {
    /** Speaks [utterance] at [rate] words per minute into memory. Blocks: call it off the main thread. */
    fun synthesize(utterance: Utterance, rate: Int): Speech
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
fun voiceOf(p: Pronunciation): String = if (p == Pronunciation.KOINE) "grc-koine" else "grc"

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
