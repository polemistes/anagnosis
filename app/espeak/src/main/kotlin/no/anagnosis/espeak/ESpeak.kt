package no.anagnosis.espeak

import android.content.Context
import java.io.File

/** The native functions of libanagnosisspeech (src/main/cpp/speech_jni.c). */
internal object ESpeakNative {
    init { System.loadLibrary("anagnosisspeech") }
    @JvmStatic external fun init(dataPath: String): Int
    @JvmStatic external fun setVoice(name: String): Boolean
    @JvmStatic external fun synth(text: String, wpm: Int): ShortArray
    @JvmStatic external fun wordEvents(): IntArray
    @JvmStatic external fun abort()
}

/**
 * Speech synthesised by eSpeak: [pcm] 16-bit mono at [sampleRate]; [words] the start of every
 * word eSpeak reported, as (character offset of the word in the input, sample).
 */
class Synthesized(val pcm: ShortArray, val sampleRate: Int, val words: List<Pair<Int, Int>>)

/**
 * The reader's voice: eSpeak NG with the Ancient Greek data of Anagnosis (assets/espeak-ng-data,
 * made by the pipeline's build-speech-data). The data is copied to the app's files on first use
 * and again whenever its version changes, since eSpeak reads real files. One instance per process.
 */
class ESpeak private constructor(private val context: Context) {
    private val lock = Any()
    private var sampleRate = 0
    private var voice: String? = null

    private fun ensureReady() {
        if (sampleRate > 0) return
        val root = File(context.filesDir, "espeak")
        val data = File(root, "espeak-ng-data")
        val bundled = context.assets.open("espeak-ng-data/version").bufferedReader().use { it.readText().trim() }
        val installed = File(data, "version").takeIf { it.exists() }?.readText()?.trim()
        if (installed != bundled) {
            data.deleteRecursively()
            copyAssets("espeak-ng-data", data)
        }
        sampleRate = ESpeakNative.init(root.absolutePath)
        check(sampleRate > 0) { "eSpeak NG did not start ($sampleRate)" }
    }

    private fun copyAssets(path: String, to: File) {
        val children = context.assets.list(path).orEmpty()
        if (children.isEmpty()) {
            to.parentFile?.mkdirs()
            context.assets.open(path).use { input -> to.outputStream().use { input.copyTo(it) } }
            return
        }
        to.mkdirs()
        for (c in children) copyAssets("$path/$c", File(to, c))
    }

    /**
     * Speaks [text] (eSpeak input; the app sends phonemes in [[ ]]) with [voiceName] ("grc" for
     * Homeric and Attic, "grc-koine" for Koine) at [wpm] words per minute. Blocks; call it off the
     * main thread.
     */
    fun synthesize(text: String, voiceName: String, wpm: Int): Synthesized = synchronized(lock) {
        ensureReady()
        if (voice != voiceName) {
            check(ESpeakNative.setVoice(voiceName)) { "eSpeak NG has no voice $voiceName" }
            voice = voiceName
        }
        val pcm = ESpeakNative.synth(text, wpm)
        val ev = ESpeakNative.wordEvents()
        val words = (0 until ev.size / 2).map { ev[2 * it] to ev[2 * it + 1] }
        Synthesized(pcm, sampleRate, words)
    }

    /** Ends a synthesis under way early (from another thread); it returns what it has made. */
    fun abort() = ESpeakNative.abort()

    companion object {
        @Volatile private var instance: ESpeak? = null
        fun get(context: Context): ESpeak = instance ?: synchronized(this) {
            instance ?: ESpeak(context.applicationContext).also { instance = it }
        }
    }
}
