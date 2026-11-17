package no.anagnosis.data

/** What a book (a speech of Lysias) comes with beside the Greek, for the book chooser. */
data class BookContents(val translation: Boolean, val commentary: Boolean) {
    /** The chooser's second line under the book's name. */
    val label: String
        get() = when {
            translation && commentary -> "Translation · Commentary"
            translation -> "Translation"
            commentary -> "Commentary"
            else -> "No translation or commentary"
        }

    companion object {
        /**
         * Each book's contents, or null when every book has the same (the chooser then shows no
         * marks: the New Testament, the Odyssey). [translationStarts] are the lines where the
         * translation's passages begin, [commentaryStarts] where notes on the Greek begin (not the
         * critical apparatus, not a translator's notes to his translation).
         */
        fun of(books: List<Int>, bookOf: (Long) -> Int, translationStarts: Collection<Long>, commentaryStarts: Collection<Long>): Map<Int, BookContents>? {
            if (books.size < 2) return null
            val translated = translationStarts.map(bookOf).toSet()
            val annotated = commentaryStarts.map(bookOf).toSet()
            val out = books.associateWith { BookContents(it in translated, it in annotated) }
            return if (out.values.distinct().size > 1) out else null
        }

        /**
         * Whether a set of notes is a translator's notes to his translation rather than a
         * commentary on the Greek: named in the text's meta `translation_notes` (commentary
         * slugs), or, until the data says so, titled "Notes to the translation …".
         */
        fun isTranslationNotes(slug: String, title: String?, declared: Set<String>): Boolean =
            slug in declared || (declared.isEmpty() && title.orEmpty().startsWith("Notes to the translation"))
    }
}
