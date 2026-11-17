package no.anagnosis.data

/** How the notes of one kind (commentary or apparatus) are grouped on the notes sheet. */
object NoteGroups {
    /**
     * Whether each group of notes names its commentator: when the text has more than one set of
     * notes of the kind, so that a reader always knows whose note it is (before 2026-11-17 only
     * on a page where two sets met).
     */
    fun nameEachGroup(setsOfKind: Int): Boolean = setsOfKind > 1
}
