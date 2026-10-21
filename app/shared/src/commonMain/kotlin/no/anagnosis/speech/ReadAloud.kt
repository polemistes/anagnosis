package no.anagnosis.speech

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import no.anagnosis.db.Lines
import no.anagnosis.db.Tokens
import no.anagnosis.greek.Utterance
import no.anagnosis.greek.UtteranceWord

/** The sentences of [lines] in reading order, as their tokens: a new one where the sentence id changes. */
fun sentencesOf(lines: List<Lines>, tokensByLine: Map<Long, List<Tokens>>): List<List<Tokens>> {
    val out = ArrayList<List<Tokens>>()
    var current = ArrayList<Tokens>()
    var id: String? = null
    for (line in lines) {
        for (t in tokensByLine[line.id].orEmpty()) {
            val s = t.sentence ?: "line ${line.id}"
            if (current.isNotEmpty() && s != id) {
                out += current
                current = ArrayList()
            }
            id = s
            current += t
        }
    }
    if (current.isNotEmpty()) out += current
    return out
}

/**
 * A part of a sentence as it is spoken: its words, or ([speaker]) the name of the speaker whose
 * speech begins there, said in a deeper voice and not marked in the text.
 */
class SpokenPart(val utterance: Utterance, val speaker: Boolean = false)

/**
 * Reading aloud: what is being read (a text and book, as a list of sentences), where, and whether
 * it plays. Lives as long as the app, so that the reader can leave the text (for the search) and
 * find the reading paused where it was. The reader screen [bind]s its text to it and gives the
 * function that turns a sentence into its spoken parts; synthesis runs one sentence ahead.
 */
class ReadAloud(private val scope: CoroutineScope) {
    var engine: SpeechEngine? = null
    var player: PcmPlayer? = null
    /** Per cent of the standard speed; a change is heard at once (see [voiceChanged]). */
    var speed: Int = 100
        set(v) { if (field != v) { field = v; voiceChanged() } }
    /** A woman's voice or a man's; a change is heard at once. */
    var female: Boolean = false
        set(v) { if (field != v) { field = v; voiceChanged() } }

    /** The text and book being read ("slug/book"), or null. */
    var key by mutableStateOf<String?>(null)
        private set
    /** The play bar is shown. */
    var open by mutableStateOf(false)
        private set
    var playing by mutableStateOf(false)
        private set
    /** The sentence being read (index into the bound list). */
    var sentence by mutableStateOf(0)
        private set
    /** The word being spoken, or null. */
    var word by mutableStateOf<UtteranceWord?>(null)
        private set

    private var count = 0
    private var prepare: (suspend (Int, Long?) -> List<SpokenPart>?)? = null
    private var job: Job? = null
    /** [job] reads the text (not a single word for the word sheet). */
    private var jobReads = false
    /** Where a reading that was stopped, not ended, goes on: sentence and token. */
    private var resumeAt: Pair<Int, Long?>? = null
    private var restyle: Job? = null

    val available: Boolean get() = engine != null && player != null

    /** Whether play goes on with a reading (paused, or stopped by a word said alone) rather than starting one. */
    val canResume: Boolean get() = (jobReads && job?.isActive == true) || resumeAt != null

    /** The reader shows [key] with [count] sentences; [prepare] gives a sentence's parts (from a token on). */
    fun bind(key: String, count: Int, prepare: suspend (Int, Long?) -> List<SpokenPart>?) {
        if (this.key != key) {
            stopPlayback()
            open = false
            sentence = 0
            word = null
            resumeAt = null
        }
        this.key = key
        this.count = count
        this.prepare = prepare
    }

    /** Reads from sentence [index] on (from its token [fromToken] when given). */
    fun start(index: Int, fromToken: Long? = null) {
        if (!available || count == 0) return
        stopPlayback()
        resumeAt = null
        open = true
        sentence = index.coerceIn(0, count - 1)
        playing = true
        jobReads = true
        job = scope.launch { run(sentence, fromToken) }
    }

    fun pause() {
        if (!playing) return
        player?.pause()
        player?.focus(false)
        playing = false
    }

    /** Goes on with a paused or stopped reading; nothing when there is none (see [canResume]). */
    fun resume() {
        if (jobReads && job?.isActive == true) {
            player?.focus(true)
            player?.resume()
            playing = true
        } else resumeAt?.let { (s, t) -> start(s, t) }
    }

    fun next() { if (sentence + 1 < count) start(sentence + 1) }
    fun previous() = start((sentence - 1).coerceAtLeast(0))

    /** Closes the play bar and stops reading. */
    fun close() {
        restyle?.cancel()
        stopPlayback()
        resumeAt = null
        open = false
    }

    /**
     * The voice has changed (speed, man or woman, pronunciation): a reading under way is made
     * again from the word being spoken, so that the change is heard at once; a paused one goes
     * on in the new voice. Changes in quick succession (a slider drawn along) wait for the last.
     */
    fun voiceChanged() {
        if (!(jobReads && job?.isActive == true) && resumeAt == null) return
        restyle?.cancel()
        restyle = scope.launch {
            delay(300)
            if (jobReads && job?.isActive == true) {
                val at = here()
                if (playing) start(at.first, at.second) else { stopPlayback(); resumeAt = at }
            }
        }
    }

    /** Speaks [utterance] alone (a word on the word sheet); a reading under way stops, and play goes on with it. */
    fun speakOnce(utterance: Utterance) {
        val engine = engine ?: return
        val player = player ?: return
        if (jobReads && job?.isActive == true) resumeAt = here()
        stopPlayback()
        jobReads = false
        job = scope.launch {
            val speech = withContext(Dispatchers.Default) { engine.synthesize(utterance, speed, female) }
            player.focus(true)
            player.start(speech)
            while (!player.done) delay(50)
            player.focus(false)
        }
    }

    /** The place of the reading: its sentence, and the word being spoken (none between words). */
    private fun here(): Pair<Int, Long?> = sentence to word?.tokenId?.takeIf { it != 0L }

    private fun stopPlayback() {
        job?.cancel()
        job = null
        engine?.abort()
        player?.stop()
        player?.focus(false)
        playing = false
        word = null
    }

    private suspend fun run(from: Int, fromToken: Long?) = coroutineScope {
        val engine = engine ?: return@coroutineScope
        val player = player ?: return@coroutineScope
        val prep = prepare ?: return@coroutineScope
        fun synth(i: Int, tok: Long?): Deferred<List<Pair<SpokenPart, Speech?>>?> = async(Dispatchers.Default) {
            val parts = prep(i, tok) ?: return@async null
            parts.map { p ->
                val pitch = if (p.speaker) SPEAKER_PITCH else STANDARD_PITCH
                p to (if (p.utterance.words.isEmpty()) null else engine.synthesize(p.utterance, speed, female, pitch))
            }
        }
        player.focus(true)
        try {
            var i = from
            var pending = synth(i, fromToken)
            while (i < count) {
                val parts = pending.await() ?: break
                val following = if (i + 1 < count) synth(i + 1, null) else null
                sentence = i
                for ((part, speech) in parts) {
                    if (speech == null || speech.pcm.isEmpty()) continue
                    // paused while this part was being made, or as the last one ended: wait for play
                    while (!playing) delay(50)
                    player.start(speech)
                    while (true) {
                        word = if (part.speaker) null else part.utterance.words.getOrNull(speech.wordAt(player.position))
                        if (player.done) break
                        delay(40)
                    }
                }
                i++
                pending = following ?: break
            }
        } catch (e: CancellationException) {
            throw e
        } finally {
            player.focus(false)
        }
        // the end of the book: the bar stays, and play asks where to begin
        playing = false
        word = null
    }
}
