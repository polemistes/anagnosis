package no.anagnosis.data

/**
 * How the reader names its kinds of notes. A translator's notes to his translation are never
 * called a commentary: in a text whose only notes besides the apparatus are such notes (the
 * Shepherd of Hermas) the button reads "Translation notes" and the sheet "Notes to the
 * translation"; in a text with both (Lysias) the button stays "Commentary" and each group of a
 * translator's notes says so ([groupName]).
 */
object NoteLabels {
    const val TRANSLATION_NOTES = "Notes to the translation"

    fun label(kind: NoteKind, onlyTranslationNotes: Boolean): String =
        if (kind == NoteKind.COMMENTARY && onlyTranslationNotes) "Translation notes" else kind.label

    fun short(kind: NoteKind, onlyTranslationNotes: Boolean): String =
        if (kind == NoteKind.COMMENTARY && onlyTranslationNotes) "Tr. notes" else kind.short

    fun heading(kind: NoteKind, onlyTranslationNotes: Boolean): String =
        if (kind == NoteKind.COMMENTARY && onlyTranslationNotes) TRANSLATION_NOTES else kind.label

    /** The name a group of notes carries ("John Gillies, notes to the translation" where the text also has a commentary). */
    fun groupName(name: String, translationNotes: Boolean, onlyTranslationNotes: Boolean): String =
        if (translationNotes && !onlyTranslationNotes) "$name, notes to the translation" else name

    /** The kind a credit line gives a note set. */
    fun creditKind(apparatus: Boolean, translationNotes: Boolean): String = when {
        apparatus -> "Critical apparatus"
        translationNotes -> TRANSLATION_NOTES
        else -> "Commentary"
    }

    /** The label of a search hit in a note set. */
    fun searchLabel(kind: NoteKind, translationNotes: Boolean): String =
        if (kind == NoteKind.COMMENTARY && translationNotes) TRANSLATION_NOTES else kind.label
}
