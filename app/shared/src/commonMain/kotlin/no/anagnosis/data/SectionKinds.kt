package no.anagnosis.data

/**
 * Kinds of section that are headings printed inside a text (Lysias: ΜΑΡΤΥΡΕΣ., ΝΟΜΟΣ., Hude's
 * ⟨ΨΗΦΙΣΜΑ.⟩): "heading" stands before its line, "heading-after" after it (ΝΟΜΟΙ. ΟΡΚΟΙ. ΓΡΑΦΗ.
 * after 14.47). No other text has these kinds.
 */
object SectionKinds {
    const val HEADING = "heading"
    const val HEADING_AFTER = "heading-after"

    /** Whether a section of this kind is shown after its line rather than before it. */
    fun after(kind: String): Boolean = kind == HEADING_AFTER

    /** The words a heading of this kind shows: its label as printed, or null for any other kind. */
    fun printedLabel(kind: String, label: String?): String? =
        if (kind == HEADING || kind == HEADING_AFTER) label.orEmpty() else null
}
