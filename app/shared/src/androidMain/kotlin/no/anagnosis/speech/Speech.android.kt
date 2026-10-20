package no.anagnosis.speech

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import no.anagnosis.espeak.ESpeak
import no.anagnosis.greek.Utterance

/** eSpeak NG with the Ancient Greek data of Anagnosis (module :espeak). */
class AndroidSpeechEngine(private val espeak: ESpeak) : SpeechEngine {
    override fun synthesize(utterance: Utterance, rate: Int): Speech {
        val s = espeak.synthesize(utterance.text, voiceOf(utterance.variant), rate)
        return Speech(s.pcm, s.sampleRate, wordStarts(utterance, s.words))
    }

    override fun abort() = espeak.abort()
}

/**
 * Plays speech through an AudioTrack in streaming mode: a thread writes the samples, which blocks
 * while the track is paused; the position is the track's playback head.
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

    @Volatile private var track: AudioTrack? = null
    @Volatile private var total = 0
    @Volatile private var stopped = true
    private var writer: Thread? = null

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
        track = t
        total = speech.pcm.size
        stopped = false
        t.play()
        writer = Thread {
            var off = 0
            val pcm = speech.pcm
            while (!stopped && off < pcm.size) {
                val n = t.write(pcm, off, minOf(2048, pcm.size - off))
                if (n <= 0) break
                off += n
            }
        }.apply { name = "speech-writer"; start() }
    }

    override fun pause() { track?.pause() }

    override fun resume() { track?.play() }

    override fun stop() {
        stopped = true
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
            return t.playbackHeadPosition >= total
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
