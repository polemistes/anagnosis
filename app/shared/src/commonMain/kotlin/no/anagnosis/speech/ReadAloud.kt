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
 * Reading aloud: what is being read (a text and book, as a list of sentences), where, and whether
 * it plays. Lives as long as the app, so that the reader can leave the text (for the search) and
 * find the reading paused where it was. The reader screen [bind]s its text to it and gives the
 * function that turns a sentence into an utterance; synthesis runs one sentence ahead.
 */
class ReadAloud(private val scope: CoroutineScope) {
    var engine: SpeechEngine? = null
    var player: PcmPlayer? = null
    /** Words per minute; read when a sentence is synthesised. */
    var rate: Int = 150

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
    private var prepare: (suspend (Int, Long?) -> Utterance?)? = null
    private var job: Job? = null

    val available: Boolean get() = engine != null && player != null

    /** The reader shows [key] with [count] sentences; [prepare] gives a sentence's utterance (from a token on). */
    fun bind(key: String, count: Int, prepare: suspend (Int, Long?) -> Utterance?) {
        if (this.key != key) {
            stopPlayback()
            open = false
            sentence = 0
            word = null
        }
        this.key = key
        this.count = count
        this.prepare = prepare
    }

    /** Reads from sentence [index] on (from its token [fromToken] when given). */
    fun start(index: Int, fromToken: Long? = null) {
        if (!available || count == 0) return
        stopPlayback()
        open = true
        sentence = index.coerceIn(0, count - 1)
        playing = true
        job = scope.launch { run(sentence, fromToken) }
    }

    fun pause() {
        if (!playing) return
        player?.pause()
        player?.focus(false)
        playing = false
    }

    fun resume() {
        if (job?.isActive == true) {
            player?.focus(true)
            player?.resume()
            playing = true
        } else start(sentence)
    }

    fun next() { if (sentence + 1 < count) start(sentence + 1) }
    fun previous() = start((sentence - 1).coerceAtLeast(0))

    /** Closes the play bar and stops reading. */
    fun close() {
        stopPlayback()
        open = false
    }

    /** Speaks [utterance] alone (a word on the word sheet); reading, if on, is paused at its sentence. */
    fun speakOnce(utterance: Utterance) {
        val engine = engine ?: return
        val player = player ?: return
        stopPlayback()
        job = scope.launch {
            val speech = withContext(Dispatchers.Default) { engine.synthesize(utterance, rate) }
            player.focus(true)
            player.start(speech)
            while (!player.done) delay(50)
            player.focus(false)
        }
    }

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
        fun synth(i: Int, tok: Long?): Deferred<Pair<Utterance, Speech?>?> = async(Dispatchers.Default) {
            val u = prep(i, tok) ?: return@async null
            u to (if (u.words.isEmpty()) null else engine.synthesize(u, rate))
        }
        player.focus(true)
        try {
            var i = from
            var pending = synth(i, fromToken)
            while (i < count) {
                val (u, speech) = pending.await() ?: break
                val following = if (i + 1 < count) synth(i + 1, null) else null
                sentence = i
                if (speech != null && speech.pcm.isNotEmpty()) {
                    player.start(speech)
                    while (true) {
                        word = u.words.getOrNull(speech.wordAt(player.position))
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
        // the end of the book: the bar stays, with play to start again
        playing = false
        word = null
    }
}
