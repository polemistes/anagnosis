package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class SectionKindsTest {
    @Test
    fun aHeadingAfterItsLineStandsAfterIt() {
        assertTrue(SectionKinds.after("heading-after"))
        assertFalse(SectionKinds.after("heading"))
        assertFalse(SectionKinds.after("book"))
        assertFalse(SectionKinds.after("episode"))
    }

    @Test
    fun aHeadingShowsItsLabelAsPrinted() {
        assertEquals("ΜΑΡΤΥΡΕΣ.", SectionKinds.printedLabel("heading", "ΜΑΡΤΥΡΕΣ."))
        assertEquals("⟨ΜΑΡΤΥΡΕΣ.⟩ ΨΗΦΙΣΜΑ.", SectionKinds.printedLabel("heading", "⟨ΜΑΡΤΥΡΕΣ.⟩ ΨΗΦΙΣΜΑ."))
        assertEquals("ΝΟΜΟΙ. ΟΡΚΟΙ. ΓΡΑΦΗ.", SectionKinds.printedLabel("heading-after", "ΝΟΜΟΙ. ΟΡΚΟΙ. ΓΡΑΦΗ."))
        // every other kind keeps its own labelling
        assertNull(SectionKinds.printedLabel("book", "1 · Α"))
        assertNull(SectionKinds.printedLabel("strophe", "1"))
    }
}
