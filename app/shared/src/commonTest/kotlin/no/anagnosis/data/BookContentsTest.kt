package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class BookContentsTest {
    private val bookOf = { n: Long -> (n / 1000).toInt() }

    @Test
    fun aTextWhoseBooksDifferMarksEachBook() {
        // speech 1: translation only; 12: translation and commentary; 6: neither
        val marks = BookContents.of(listOf(1, 6, 12), bookOf, listOf(1001, 1016, 12001), listOf(12003, 12004))
        assertEquals("Translation", marks?.get(1)?.label)
        assertEquals("Translation · Commentary", marks?.get(12)?.label)
        assertEquals("No translation or commentary", marks?.get(6)?.label)
        assertEquals("Commentary", BookContents(translation = false, commentary = true).label)
    }

    @Test
    fun aUniformTextHasNoMarks() {
        assertNull(BookContents.of(listOf(1, 2), bookOf, listOf(1001, 2001), listOf(1002, 2005)))  // every book has both
        assertNull(BookContents.of(listOf(1, 2), bookOf, listOf(1001, 2001), emptyList()))          // every book a translation only
        assertNull(BookContents.of(listOf(1, 2), bookOf, emptyList(), emptyList()))                 // none has either
        assertNull(BookContents.of(listOf(1), bookOf, listOf(1001), emptyList()))                    // one book
    }

    @Test
    fun aTranslatorsNotesAreNotACommentary() {
        assertTrue(BookContents.isTranslationNotes("commentary-gillies", "Notes to the translation (John Gillies)", emptySet()))
        assertFalse(BookContents.isTranslationNotes("commentary-adams", "Commentary (Charles Darwin Adams)", emptySet()))
        // when the data names them, the name decides
        assertTrue(BookContents.isTranslationNotes("commentary-gillies", "Gillies's notes", setOf("commentary-gillies")))
        assertFalse(BookContents.isTranslationNotes("commentary-x", "Notes to the translation (X)", setOf("commentary-gillies")))
    }
}
