package no.anagnosis.ui

import kotlin.test.Test
import kotlin.test.assertEquals

class DependencyLayoutTest {
    @Test
    fun anArcBridgingOthersGoesAboveThem() {
        // [0,1] and [1,2] side by side at level 1; [0,2] over both; [0,3] over that one
        assertEquals(listOf(1, 1, 2, 3), arcLevels(listOf(0f to 1f, 1f to 2f, 0f to 2f, 0f to 3f)))
        // crossing arcs share a level
        assertEquals(listOf(1, 1), arcLevels(listOf(0f to 2f, 1f to 3f)))
        assertEquals(emptyList(), arcLevels(emptyList()))
    }
}
