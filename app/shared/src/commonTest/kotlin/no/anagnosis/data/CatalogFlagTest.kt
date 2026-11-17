package no.anagnosis.data

import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class CatalogFlagTest {
    @Test
    fun aJsonTrueOrYesIsReadAndNothingElse() {
        assertTrue(catalogFlag("{\n  \"slug\": \"lysias\",\n  \"free\": true\n}", "free"))
        assertTrue(catalogFlag("{\"free\":\"yes\"}", "free"))
        assertFalse(catalogFlag("{\"slug\": \"antigone\", \"google_play\": \"yes\"}", "free"))
        assertFalse(catalogFlag("{\"free\": false}", "free"))
    }
}
