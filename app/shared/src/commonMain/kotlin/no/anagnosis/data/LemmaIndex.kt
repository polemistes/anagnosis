package no.anagnosis.data

import no.anagnosis.greek.GreekNormalizer

/** A lemma of one text and how often its words occur there. */
class LemmaEntry(val slug: String, val key: String, val lemma: String, val count: Int)

/**
 * One line of the lemma search: a lemma, joined with the spellings the other texts give it
 * (an alias such as Homeric ἠέλιος for ἥλιος, or a middle in -ομαι for an active in -ω).
 * [spellings] are the lemmas as the texts write them, the most frequent first; [keysBySlug]
 * the lemma keys under which each text has the word.
 */
class LemmaRow(
    val spellings: List<String>,
    val keys: List<String>,
    val keysBySlug: Map<String, List<String>>,
    val countsBySlug: Map<String, Int>,
) {
    val total: Int = countsBySlug.values.sum()
    val looseKeys: List<String> = spellings.map { GreekNormalizer.looseKey(it) }
    val looseKey: String get() = looseKeys.firstOrNull() ?: ""

    /** The short definition, filled in for the rows shown. */
    var gloss: String? = null

    fun contains(key: String): Boolean = key in keys
}

object LemmaIndex {
    private const val MIDDLE = "ομαι"

    /**
     * Joins the texts' lemmas into rows. A key is joined to its alias target ([aliases]: per text,
     * lemma key to target key) when the target is a lemma of some text, and a key in -ομαι to the
     * same key in -ω when that is one. Keys that differ only in their accents stay apart (βίος, βιός).
     */
    fun merge(entries: List<LemmaEntry>, aliases: Map<String, Map<String, String>> = emptyMap()): List<LemmaRow> {
        val keys = entries.mapTo(LinkedHashSet()) { it.key }
        val parent = HashMap<String, String>()
        fun find(k: String): String {
            var r = k
            while (true) { val p = parent[r] ?: return r; if (p == r) return r; r = p }
        }
        fun union(a: String, b: String) {
            val ra = find(a)
            val rb = find(b)
            if (ra != rb) parent[ra] = rb
        }
        for (map in aliases.values) for ((k, target) in map) if (k in keys && target in keys) union(k, target)
        for (k in keys) if (k.endsWith(MIDDLE)) {
            val active = k.dropLast(MIDDLE.length) + "ω"
            if (active in keys) union(k, active)
        }
        return entries.groupBy { find(it.key) }.values.map { group ->
            val byKey = group.groupBy { it.key }
            val keyOrder = byKey.entries.sortedByDescending { e -> e.value.sumOf { it.count } }
            // a key's spelling: the lemma of the text that has it most
            val spellings = keyOrder.map { e -> e.value.maxBy { it.count }.lemma }.distinct()
            LemmaRow(
                spellings = spellings,
                keys = keyOrder.map { it.key },
                keysBySlug = group.groupBy { it.slug }.mapValues { e -> e.value.map { it.key }.distinct() },
                countsBySlug = group.groupBy { it.slug }.mapValues { e -> e.value.sumOf { it.count } },
            )
        }
    }

    /**
     * The rows any of whose spellings begin with the typed Greek, accents ignored: the rows that
     * are the typed word itself first, then in alphabetical order.
     */
    fun suggest(rows: List<LemmaRow>, typed: String, limit: Int = 80): List<LemmaRow> {
        val key = GreekNormalizer.looseKey(typed)
        if (key.isEmpty()) return emptyList()
        val prefix = GreekNormalizer.prefixKey(typed)
        return rows.asSequence()
            .filter { r -> r.looseKeys.any { it.startsWith(key) || it.startsWith(prefix) } }
            .sortedWith(compareBy<LemmaRow>({ r -> if (r.looseKeys.any { it == key }) 0 else 1 }, { it.looseKey }, { -it.total }))
            .take(limit).toList()
    }

    /** A row for a lemma no installed text has (the word sheet of a dictionary headword). */
    fun lonely(key: String, lemma: String): LemmaRow = LemmaRow(listOf(lemma), listOf(key), emptyMap(), emptyMap())
}
