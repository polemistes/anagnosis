package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ReleaseGateTest {
    private fun entry(slug: String, release: String = "", onSale: Boolean = false) =
        CatalogEntry(slug, slug, "", slug, "", "", "", false, onGooglePlay = onSale, productId = "p_$slug", version = "v", release = release)

    @Test
    fun aTextExistsFromItsReleaseDay() {
        assertFalse(ReleaseGate.released("2028-01-01", "2027-12-31"))
        assertTrue(ReleaseGate.released("2028-01-01", "2028-01-01"))
        assertTrue(ReleaseGate.released("2028-01-01", "2028-01-02"))
        assertTrue(ReleaseGate.released("", "2026-11-16"))
    }

    @Test
    fun aReleaseValueThatIsNotADateHoldsTheTextBack() {
        assertFalse(ReleaseGate.released("soon", "2099-01-01"))
        assertFalse(ReleaseGate.released("2028-1-1", "2099-01-01"))
    }

    @Test
    fun hiddenBeforeTheDayUnlessGranted() {
        val entries = listOf(entry("a"), entry("later", "2028-01-01"), entry("given", "2028-01-01"))
        assertEquals(setOf("later", "given"), ReleaseGate.hidden(entries, "2026-11-16", emptySet()))
        assertEquals(setOf("later"), ReleaseGate.hidden(entries, "2026-11-16", setOf("given")))
        assertEquals(emptySet(), ReleaseGate.hidden(entries, "2028-01-01", emptySet()))
    }

    @Test
    fun aDatedTextIsOfferedFromItsDayWithoutASaleMark() {
        assertFalse(ReleaseGate.offered(entry("later", "2028-01-01"), "2027-12-31"))
        assertTrue(ReleaseGate.offered(entry("later", "2028-01-01"), "2028-01-02"))
        // a sale mark does not bring a dated text forward
        assertFalse(ReleaseGate.offered(entry("later", "2028-01-01", onSale = true), "2027-12-31"))
    }

    @Test
    fun anUndatedTextIsOfferedByItsSaleMarkAsBefore() {
        assertTrue(ReleaseGate.offered(entry("sold", onSale = true), "2026-11-16"))
        assertFalse(ReleaseGate.offered(entry("unsold"), "2026-11-16"))
    }
}
