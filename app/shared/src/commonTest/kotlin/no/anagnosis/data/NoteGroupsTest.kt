package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class NoteGroupsTest {
    @Test
    fun severalSetsNameTheirCommentator() {
        assertFalse(NoteGroups.nameEachGroup(1))  // one commentary: no names, as before
        assertTrue(NoteGroups.nameEachGroup(2))   // Lucian, Hermas
        assertTrue(NoteGroups.nameEachGroup(4))   // Lysias: Adams, Gillies, Morgan, Shuckburgh
    }
}
