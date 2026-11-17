package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals

/** The word sheet's buttons: a name's glossary entry is reachable also where the name has a short definition. */
class SheetButtonsTest {
    private fun e(slug: String, title: String = slug) = Entry(slug, title, "Κέφαλος", 0L, "<p>…</p>")
    private val entries = listOf(e("lysias-glossary", "Glossary of names in Lysias"), e("lsj"), e("ml"))

    @Test
    fun withAShortDefinitionTheGlossaryHasAButtonFirst() {
        assertEquals(listOf("lysias-glossary" to "Glossary", "ml" to "Middle Liddell", "lsj" to "LSJ"),
            Dictionaries.sheetButtons(entries, hasShortDefinition = true, disabled = emptySet(), preferred = emptyList()))
    }

    @Test
    fun withoutOneTheGlossaryStandsOnTheSheetAndHasNoButton() {
        assertEquals(listOf("ml" to "Middle Liddell", "lsj" to "LSJ"),
            Dictionaries.sheetButtons(entries, hasShortDefinition = false, disabled = emptySet(), preferred = emptyList()))
    }

    @Test
    fun aDictionaryTurnedOffHasNoButton() {
        assertEquals(listOf("lysias-glossary" to "Glossary", "lsj" to "LSJ"),
            Dictionaries.sheetButtons(entries, hasShortDefinition = true, disabled = setOf("ml"), preferred = emptyList()))
    }
}
