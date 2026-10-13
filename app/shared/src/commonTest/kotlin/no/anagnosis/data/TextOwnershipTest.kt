package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class TextOwnershipTest {
    @Test
    fun storeTextsShowOnlyWhileOwned() {
        val shown = TextOwnership.installed(
            bundled = listOf("lexicon"),
            fromApps = listOf("odyssey"),
            fromStore = listOf("antigone", "ajax"),
            owned = setOf("antigone"),
        )
        // Ajax is on the device but was refunded: hidden, not deleted
        assertEquals(listOf("antigone", "odyssey"), shown)
    }

    @Test
    fun aTextFromBothWaysIsShownOnce() {
        val shown = TextOwnership.installed(emptyList(), listOf("antigone"), listOf("antigone"), setOf("antigone"))
        assertEquals(listOf("antigone"), shown)
    }

    @Test
    fun ownedTextsMissingOrOutOfDateAreFetched() {
        val fetch = TextOwnership.toFetch(
            owned = setOf("antigone", "ajax", "odyssey", "electra", "phantom"),
            storeVersions = mapOf("antigone" to "v1", "ajax" to "old", "odyssey" to null),
            catalogVersions = mapOf("antigone" to "v1", "ajax" to "v2", "odyssey" to "v3", "electra" to "v4"),
            fromApps = listOf("electra"),
        )
        // Antigone is up to date, Electra came with its app, and a product without a text in
        // the catalog is not fetched
        assertEquals(listOf("ajax", "odyssey"), fetch)
    }

    @Test
    fun productIds() {
        assertEquals("text_newtestament", productId("newtestament"))
        assertEquals("newtestament", slugOfProduct("text_newtestament"))
        assertNull(slugOfProduct("bundle_sophocles"))
    }
}
