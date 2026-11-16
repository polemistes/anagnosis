package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals

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
    fun givenTextsAreOwnedBesideTheBoughtOnes() {
        // a granting build gives the texts it names; the store's answer does not take them away
        assertEquals(setOf("antigone", "textb", "textc"), TextOwnership.owned(setOf("antigone"), setOf("textb", "textc")))
        assertEquals(setOf("textb"), TextOwnership.owned(emptySet(), setOf("textb")))
        // a public build gives nothing
        assertEquals(setOf("antigone"), TextOwnership.owned(setOf("antigone"), emptySet()))
    }

    @Test
    fun givenTextsAreFetchedLikeBoughtOnes() {
        val owned = TextOwnership.owned(setOf("antigone"), setOf("textb"))
        val fetch = TextOwnership.toFetch(owned, mapOf("antigone" to "v1", "textb" to null),
            mapOf("antigone" to "v1", "textb" to "m1"), emptyList())
        assertEquals(listOf("textb"), fetch)
    }
}
