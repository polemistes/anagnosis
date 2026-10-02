package no.anagnosis.data

import no.anagnosis.db.Sentence_nodes
import no.anagnosis.db.Tokens
import java.io.File
import kotlin.test.Test

/**
 * Writes the simple syntax view of a sample of sentences of every text to
 * build/simple-syntax/<text>.txt, for checking the rules by eye. Needs the texts/ directory of
 * the repository; does nothing where it is absent. Sentences: those named in the system property
 * the environment variable ANAGNOSIS_SENTENCES ("antigone:2900074,odyssey:2185541"), or else every k-th one.
 */
class SimpleSyntaxDump {
    @Test
    fun dump() {
        val texts = File("../../texts").takeIf { it.isDirectory } ?: return
        val outDir = File("build/simple-syntax").apply { mkdirs() }
        val chosen = System.getenv("ANAGNOSIS_SENTENCES")?.split(",")?.map { it.trim() }?.filter { it.isNotEmpty() }
            ?.groupBy({ it.substringBefore(':') }, { it.substringAfter(':') })
        for (dir in texts.listFiles()!!.filter { File(it, "tokens.tsv").exists() }.sortedBy { it.name }) {
            val slug = dir.name
            val rows = File(dir, "tokens.tsv").readLines().drop(1).map { it.split('\t') }
            val nodes = File(dir, "syntax-nodes.tsv").takeIf { it.exists() }?.readLines()?.drop(1)?.map { it.split('\t') } ?: emptyList()
            val lineIds = HashMap<String, Long>()
            var id = 1L
            val tokens = rows.filter { it.size >= 9 && it[7].isNotEmpty() }.map { r ->
                val lineId = lineIds.getOrPut(r[0]) { lineIds.size + 1L }
                Tokens(id++, lineId, r[1].toLong(), 0, 0, r[2], r[3], r[3], r[4], r[5].ifEmpty { null }, r[6].toLongOrNull(), r[7], r[8])
            }
            val lineOf = lineIds.entries.associate { (n, i) -> i to n }
            val bySentence = tokens.groupBy { it.sentence!! }
            val extra = nodes.filter { it.size >= 8 }.groupBy { it[0] }.mapValues { (s, ns) ->
                ns.map { n -> Sentence_nodes(id++, 1, s, n[1].toLong(), n[2], n[3].ifEmpty { null }, n[4], n[5].ifEmpty { null }, n[6].toLongOrNull(), if (n[7].isNotEmpty()) 1 else 0) }
            }
            val order = bySentence.keys.toList()
            val sample = chosen?.get(slug) ?: run {
                val step = maxOf(1, order.size / 45)
                (order.take(5) + order.filterIndexed { i, _ -> i % step == 0 }).distinct()
            }
            // every sentence: the rules must place every word and throw on none
            var lost = 0
            val lostIds = mutableListOf<String>()
            for ((s, toks) in bySentence) {
                val tree = Syntax.build(s, toks, extra[s] ?: emptyList())
                val blocks = SimpleSyntax.blocks(tree)
                val shown = blocks.flatMap { b -> b.phrases.flatMap { it.words } }.map { it.id }
                val dup = shown.size - shown.toSet().size
                if (dup > 0) println("$slug $s: $dup words shown twice")
                if (blocks.lastOrNull()?.stray == true) { lost++; lostIds += s }
            }
            println("$slug: ${bySentence.size} sentences, $lost with words placed only by the safety net: ${lostIds.take(8)}")
            val sb = StringBuilder()
            for (s in sample) {
                val toks = bySentence[s] ?: continue
                val tree = Syntax.build(s, toks, extra[s] ?: emptyList())
                val lines = toks.map { lineOf[it.line_id] }.distinct()
                sb.append("## $slug $s (${lines.first()}${if (lines.size > 1) "–${lines.last()}" else ""})\n")
                sb.append(toks.joinToString(" ") { it.form }).append("\n\n")
                sb.append(SimpleSyntax.render(tree)).append('\n')
            }
            File(outDir, "$slug.txt").writeText(sb.toString())
            println("wrote ${File(outDir, "$slug.txt")}: ${sample.size} sentences")
        }
    }
}
