package no.anagnosis.speech

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.media.PlaybackParams
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import no.anagnosis.espeak.ESpeak
import no.anagnosis.greek.Utterance

/** eSpeak NG with the Ancient Greek data of Anagnosis (module :espeak). */
class AndroidSpeechEngine(private val espeak: ESpeak) : SpeechEngine {
    override fun synthesize(utterance: Utterance, speed: Int, female: Boolean, klatt: Boolean, pitch: Int): Speech {
        val (wpm, playback) = engineRate(speed)
        val s = espeak.synthesize(utterance.text, voiceOf(utterance.variant, female, klatt), wpm, pitch)
        return Speech(s.pcm, s.sampleRate, wordStarts(utterance, s.words), playback)
    }

    override fun abort() = espeak.abort()
}

/**
 * Plays speech through an AudioTrack in streaming mode: a thread writes the samples, and waits
 * while the track is paused (a paused track takes nothing, and a write that returns short must
 * not end the thread, or the rest of the sentence is never heard); the position is the track's
 * playback head.
 */
class AudioTrackPlayer(context: Context) : PcmPlayer {
    private val audio = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private val attributes = AudioAttributes.Builder()
        .setUsage(AudioAttributes.USAGE_MEDIA)
        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
        .build()
    private val focusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
        .setAudioAttributes(attributes)
        .build()
    private var focused = false

    private val lock = Object()
    @Volatile private var track: AudioTrack? = null
    @Volatile private var total = 0
    @Volatile private var stopped = true
    @Volatile private var paused = false
    /** The writer has handed the track every sample. */
    @Volatile private var written = false
    private var writer: Thread? = null
    // for telling the end on a device whose head stops short of the last sample
    private var lastHead = -1
    private var lastHeadAt = 0L

    override fun start(speech: Speech) {
        stop()
        val minBuffer = AudioTrack.getMinBufferSize(speech.sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)
        val t = AudioTrack.Builder()
            .setAudioAttributes(attributes)
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(speech.sampleRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .build()
            )
            .setBufferSizeInBytes(maxOf(minBuffer * 2, 8192))
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
        // slower than the engine can speak: stretched in time, the pitch kept
        if (speech.playbackSpeed != 1f) {
            t.playbackParams = PlaybackParams().setSpeed(speech.playbackSpeed).setPitch(1f)
        }
        track = t
        total = speech.pcm.size
        stopped = false
        paused = false
        written = false
        lastHead = -1
        t.play()
        writer = Thread {
            var off = 0
            val pcm = speech.pcm
            while (!stopped && off < pcm.size) {
                if (paused) {
                    synchronized(lock) { while (paused && !stopped) lock.wait(200) }
                    continue
                }
                val n = t.write(pcm, off, minOf(2048, pcm.size - off))
                if (n < 0) break  // an error; a short or empty write (the track was paused) is retried
                off += n
            }
            written = off >= pcm.size
        }.apply { name = "speech-writer"; start() }
    }

    override fun pause() {
        paused = true
        track?.pause()
    }

    override fun resume() {
        synchronized(lock) {
            paused = false
            lock.notifyAll()
        }
        track?.play()
    }

    override fun stop() {
        stopped = true
        synchronized(lock) { paused = false; lock.notifyAll() }
        val t = track ?: return
        track = null
        runCatching { t.pause(); t.flush(); t.stop() }
        writer?.join(500)
        writer = null
        t.release()
    }

    override val position: Int
        get() = track?.playbackHeadPosition ?: total

    override val done: Boolean
        get() {
            val t = track ?: return true
            val head = t.playbackHeadPosition
            if (head >= total) return true
            // everything written, nothing paused, and the head has not moved for a while: the end
            if (!written || paused) { lastHead = -1; return false }
            val now = System.currentTimeMillis()
            if (head != lastHead) { lastHead = head; lastHeadAt = now; return false }
            return now - lastHeadAt > 400
        }

    override fun focus(on: Boolean) {
        if (on && !focused) {
            focused = audio.requestAudioFocus(focusRequest) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        } else if (!on && focused) {
            audio.abandonAudioFocusRequest(focusRequest)
            focused = false
        }
    }

    override fun release() {
        stop()
        focus(false)
    }
}

@Composable
actual fun rememberSpeechEngine(): SpeechEngine? {
    val context = LocalContext.current
    return remember { AndroidSpeechEngine(ESpeak.get(context)) }
}

@Composable
actual fun rememberPcmPlayer(): PcmPlayer? {
    val context = LocalContext.current
    return remember { AudioTrackPlayer(context.applicationContext) }
}
