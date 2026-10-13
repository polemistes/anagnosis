package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertEquals

class DictionariesTest {
    @Test
    fun englishKeysMatchThePipeline() {
        // the same keys as woodhouse.english_key in the pipeline
        assertEquals("abandon", Dictionaries.englishKey("Abandon"))
        assertEquals("advised be", Dictionaries.englishKey("Advised, Be"))
        assertEquals("adige river", Dictionaries.englishKey("Adige (River)"))
        assertEquals("aedile", Dictionaries.englishKey("Ædile"))
        assertEquals("debris", Dictionaries.englishKey("Débris"))
        assertEquals("well doing", Dictionaries.englishKey("  Well-doing "))
    }
}
