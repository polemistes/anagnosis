package no.anagnosis.greek

import no.anagnosis.data.defaultPronunciation
import java.io.File
import kotlin.test.Test

/**
 * Turns the sample lines of `speech-samples prepare` (pipeline/build/speech-samples/input.tsv)
 * into eSpeak phonemes with the app's own phonology, one file per text and pronunciation:
 * <text>-<pronunciation>.txt, "voice<TAB>phonemes" per line. `speech-samples render` speaks them.
 * Does nothing where the input is absent.
 */
class SpeechSampleDump {
    @Test
    fun dump() {
        val dir = File("../../pipeline/build/speech-samples")
        val input = File(dir, "input.tsv").takeIf { it.exists() } ?: return
        val byFile = LinkedHashMap<String, MutableList<String>>()
        for (raw in input.readLines()) {
            val f = raw.split('\t')
            if (f.size < 6) continue
            val slug = f[0]
            val prose = f[1] == "1"
            val default = defaultPronunciation(slug, if (slug == "odyssey") "Ὅμηρος" else null, f[2].ifEmpty { null })
            val lineId = f[3].toLong()
            val text = f[4]
            val words = f[5].split(' ').filter { it.isNotEmpty() }.map { w ->
                val p = w.split('|')
                SpeechWord(p[0].toLong(), lineId, p[3], p[1].toInt(), p[2].toInt(), p.getOrNull(4)?.ifEmpty { null })
            }
            // the Odyssey also in the other two pronunciations, to compare
            val variants = if (slug == "odyssey") Pronunciation.entries else listOf(default)
            for (v in variants) {
                val u = Utterances.build(words, { text }, v, verse = !prose)
                val voice = if (v == Pronunciation.KOINE) "grc-koine" else "grc"
                byFile.getOrPut("$slug-${v.key}") { ArrayList() } += "$voice\t${u.text}"
            }
        }
        for ((name, lines) in byFile) File(dir, "$name.txt").writeText(lines.joinToString("\n") + "\n")
    }
}
