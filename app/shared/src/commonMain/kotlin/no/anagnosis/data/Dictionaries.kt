package no.anagnosis.data

/** The dictionaries the word sheet can offer: their order and the names on their buttons. */
object Dictionaries {
    /** The order when a text names none: the general dictionaries first, then the special ones. */
    val DEFAULT_ORDER = listOf("ml", "lsj", "abbott-smith", "autenrieth", "dodson")

    private val LABELS = mapOf(
        "ml" to "Middle Liddell", "lsj" to "LSJ", "abbott-smith" to "Abbott-Smith",
        "autenrieth" to "Autenrieth", "dodson" to "Dodson",
    )

    fun rank(slug: String): Int = DEFAULT_ORDER.indexOf(slug).let { if (it < 0) DEFAULT_ORDER.size else it }

    /** The button's name: a short one for the known dictionaries, else the title up to its colon. */
    fun label(slug: String, title: String): String = LABELS[slug] ?: title.substringBefore(':').trim()

    /** A text's preferred order (most fitting first), then the rest in the default order. */
    fun order(preferred: List<String>): List<String> = preferred + DEFAULT_ORDER.filter { it !in preferred }

    fun isGlossary(slug: String): Boolean = slug.endsWith("-glossary")
}
