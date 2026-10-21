package no.anagnosis.speech

import no.anagnosis.db.Lines
import no.anagnosis.db.Tokens

/**
 * The speakers' names that reading aloud says between the speeches of a dialogue. A play gives
 * the speaker's full name on the line that begins a speech; a prose dialogue prints an
 * abbreviation in the text, in braces ({ΚΑΛ.}), which [fullSpeakerName] expands.
 */
object Speakers {
    private val LABEL = Regex("\\{([^}]*)\\}")

    /**
     * Plato's abbreviations in Burnet's text, with the speakers' names in full. An abbreviation
     * missing here is said as it is printed, without its full stop.
     */
    private val PLATO = mapOf(
        // Gorgias
        "ΣΩ" to "Σωκράτης",
        "ΚΑΛ" to "Καλλικλῆς",
        "ΠΩΛ" to "Πῶλος",
        "ΓΟΡ" to "Γοργίας",
        "ΧΑΙ" to "Χαιρεφῶν",
        // Symposium
        "ΑΠΟΛ" to "Ἀπολλόδωρος",
        "ΕΤΑΙ" to "Ἑταῖρος",
    )

    /** Numbers in a speaker's name ("Ἡμιχόριον 1"), said as Greek ordinals. */
    private val ORDINALS = mapOf("1" to "πρῶτον", "2" to "δεύτερον", "3" to "τρίτον", "4" to "τέταρτον")

    /** A speaker's name as it is to be said: an abbreviation in full, numbers as words. */
    fun fullSpeakerName(label: String): String {
        val bare = label.trim().trimEnd('.').trim()
        val name = PLATO[bare] ?: bare
        return name.split(' ').filter { it.isNotBlank() }.joinToString(" ") { ORDINALS[it] ?: it }
    }

    /**
     * The words that begin a speech, by token id, with the full name of their speaker: the first
     * word of a play's line that begins a speech, and the word after each label of a prose
     * dialogue (the first word of the next line when a label ends its line).
     */
    fun cues(lines: List<Lines>, tokensByLine: Map<Long, List<Tokens>>): Map<Long, String> {
        val out = HashMap<Long, String>()
        var pending: String? = null
        for (line in lines) {
            val tokens = tokensByLine[line.id].orEmpty()
            if (line.speech_start == 1L && !line.speaker.isNullOrBlank()) pending = fullSpeakerName(line.speaker!!)
            if (pending != null && tokens.isNotEmpty()) {
                out[tokens.first().id] = pending
                pending = null
            }
            for (m in LABEL.findAll(line.text)) {
                val name = fullSpeakerName(m.groupValues[1])
                if (name.isEmpty()) continue
                val next = tokens.firstOrNull { it.start > m.range.last }
                if (next != null) out[next.id] = name else pending = name
            }
        }
        return out
    }

    /** The words of a speaker's [name], with the length-marked form of each when one is known. */
    fun words(name: String, marked: (String) -> String?): List<no.anagnosis.greek.SpeechWord> {
        val out = ArrayList<no.anagnosis.greek.SpeechWord>()
        var pos = 0
        for (w in name.split(' ')) {
            if (w.isNotEmpty()) out += no.anagnosis.greek.SpeechWord(0, 0, w, pos, pos + w.length, marked(w))
            pos += w.length + 1
        }
        return out
    }
}
