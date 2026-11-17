package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals

class NoteLabelsTest {
    @Test
    fun aTextWithOnlyTranslatorsNotesNeverSaysCommentary() {
        assertEquals("Translation notes", NoteLabels.label(NoteKind.COMMENTARY, onlyTranslationNotes = true))
        assertEquals("Tr. notes", NoteLabels.short(NoteKind.COMMENTARY, onlyTranslationNotes = true))
        assertEquals("Notes to the translation", NoteLabels.heading(NoteKind.COMMENTARY, onlyTranslationNotes = true))
        assertEquals("Apparatus", NoteLabels.label(NoteKind.APPARATUS, onlyTranslationNotes = true))
    }

    @Test
    fun aTextWithACommentaryKeepsItsNamesAndMarksTheTranslatorsNotes() {
        assertEquals("Commentary", NoteLabels.label(NoteKind.COMMENTARY, onlyTranslationNotes = false))
        assertEquals("Comm.", NoteLabels.short(NoteKind.COMMENTARY, onlyTranslationNotes = false))
        assertEquals("Commentary", NoteLabels.heading(NoteKind.COMMENTARY, onlyTranslationNotes = false))
        assertEquals("John Gillies, notes to the translation", NoteLabels.groupName("John Gillies", translationNotes = true, onlyTranslationNotes = false))
        assertEquals("Charles Darwin Adams", NoteLabels.groupName("Charles Darwin Adams", translationNotes = false, onlyTranslationNotes = false))
        // where all are translator's notes the sheet's heading says it, the groups give the name alone
        assertEquals("Kirsopp Lake", NoteLabels.groupName("Kirsopp Lake", translationNotes = true, onlyTranslationNotes = true))
    }

    @Test
    fun creditsAndSearchNameTheKind() {
        assertEquals("Critical apparatus", NoteLabels.creditKind(apparatus = true, translationNotes = false))
        assertEquals("Notes to the translation", NoteLabels.creditKind(apparatus = false, translationNotes = true))
        assertEquals("Commentary", NoteLabels.creditKind(apparatus = false, translationNotes = false))
        assertEquals("Notes to the translation", NoteLabels.searchLabel(NoteKind.COMMENTARY, translationNotes = true))
        assertEquals("Commentary", NoteLabels.searchLabel(NoteKind.COMMENTARY, translationNotes = false))
    }
}
