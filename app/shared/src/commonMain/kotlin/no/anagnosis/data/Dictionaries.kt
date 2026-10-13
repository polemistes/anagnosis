package no.anagnosis.data

/** The dictionaries the word sheet can offer: their order and the names on their buttons. */
object Dictionaries {
    /** The order when a text names none: the general dictionaries first, then the special ones. */
    val DEFAULT_ORDER = listOf("ml", "lsj", "abbott-smith", "autenrieth", "dodson", WOODHOUSE)

    /** Woodhouse's English-Greek Dictionary: looked up by English headword, in the search only. */
    const val WOODHOUSE = "woodhouse"

    private val LABELS = mapOf(
        "ml" to "Middle Liddell", "lsj" to "LSJ", "abbott-smith" to "Abbott-Smith",
        "autenrieth" to "Autenrieth", "dodson" to "Dodson", WOODHOUSE to "Woodhouse",
    )

    fun rank(slug: String): Int = DEFAULT_ORDER.indexOf(slug).let { if (it < 0) DEFAULT_ORDER.size else it }

    /** The button's name: a short one for the known dictionaries, else the title up to its colon. */
    fun label(slug: String, title: String): String = LABELS[slug] ?: title.substringBefore(':').trim()

    /** A text's preferred order (most fitting first), then the rest in the default order. */
    fun order(preferred: List<String>): List<String> = preferred + DEFAULT_ORDER.filter { it !in preferred }

    fun isGlossary(slug: String): Boolean = slug.endsWith("-glossary")

    /**
     * The search key of an English headword, as the pipeline makes it (woodhouse.english_key):
     * lower case, letters and single spaces only ("Advised, Be" gives "advised be", "Ædile" "aedile").
     */
    fun englishKey(s: String): String {
        val sb = StringBuilder(s.length)
        for (c in s.lowercase()) {
            when (c) {
                in 'a'..'z' -> sb.append(c)
                'æ' -> sb.append("ae")
                'œ' -> sb.append("oe")
                else -> sb.append(LATIN_ACCENTED[c] ?: ' ')
            }
        }
        return sb.split(' ').filter { it.isNotEmpty() }.joinToString(" ")
    }

    private val LATIN_ACCENTED: Map<Char, Char> = buildMap {
        fun add(base: Char, variants: String) = variants.forEach { put(it, base) }
        add('a', "àáâãäå"); add('c', "ç"); add('e', "èéêë"); add('i', "ìíîï"); add('n', "ñ")
        add('o', "òóôõö"); add('u', "ùúûü"); add('y', "ýÿ")
    }
}
