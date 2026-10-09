package no.anagnosis.ui

import kotlin.test.Test
import kotlin.test.assertEquals
import no.anagnosis.data.CatalogEntry

class ReferencesTest {
    private fun entry(edition: String, translation: String, commentary: String) =
        CatalogEntry("x", "", "", "", "", "", "", false, refEdition = edition, refTranslation = translation, refCommentary = commentary)

    @Test
    fun partsFromOneBookShareALine() {
        assertEquals(listOf("Edition, translation and commentary" to "Jebb"), references(entry("Jebb", "Jebb", "Jebb")))
        assertEquals(listOf("Edition and commentary" to "A", "Translation" to "B"), references(entry("A", "B", "A")))
    }

    @Test
    fun missingPartsAreLeftOut() {
        assertEquals(listOf("Edition" to "SBL", "Translation" to "BSB"), references(entry("SBL", "BSB", "")))
    }

    @Test
    fun textsAreGroupedByAuthorWithTheAuthorlessFirst() {
        fun text(title: String, author: String) = CatalogEntry(title, "", "", title, author, "", "", true)
        val groups = byAuthor(listOf(text("Electra", "Sophocles"), text("Odyssey", "Homer"), text("New Testament", ""), text("Ajax", "Sophocles")))
        assertEquals(listOf("", "Homer", "Sophocles"), groups.map { it.first })
        assertEquals(listOf("Ajax", "Electra"), groups.last().second.map { it.titleEn })
    }
}
