package no.anagnosis.greek

import kotlin.test.Test
import kotlin.test.assertEquals

class PolytonicTest {
    @Test
    fun composesBreathingAndAccent() {
        var t = "α"
        t = Polytonic.apply(t, Polytonic.SMOOTH)
        assertEquals("ἀ", t)
        t = Polytonic.apply(t, Polytonic.ACUTE)
        assertEquals("ἄ", t)
        t = Polytonic.apply(t, Polytonic.CIRCUMFLEX)   // accent replaces accent
        assertEquals("ἆ", t)
        t = Polytonic.apply(t, Polytonic.SUBSCRIPT)
        assertEquals("ᾆ", t)
        t = Polytonic.apply(t, Polytonic.SUBSCRIPT)    // toggles off
        assertEquals("ἆ", t)
        t = Polytonic.apply(t, Polytonic.ROUGH)        // breathing replaces breathing
        assertEquals("ἇ", t)
    }

    @Test
    fun wordEndings() {
        assertEquals("ἀγαθὸ", Polytonic.apply("ἀγαθο", Polytonic.GRAVE))
        assertEquals("ἀγαθον", Polytonic.apply("ἀγαθον", Polytonic.GRAVE))  // marks go on the vowel just typed
        assertEquals("λό", Polytonic.apply("λο", Polytonic.ACUTE))
        assertEquals("λογος", Polytonic.apply("λογος", Polytonic.ACUTE))  // final sigma is not a vowel
        assertEquals("ῥ", Polytonic.apply("ρ", Polytonic.ROUGH))
        assertEquals("κ", Polytonic.apply("κ", Polytonic.ACUTE))  // consonants unchanged
    }

    @Test
    fun exactKeyDistinguishesAccents() {
        assertEquals("ἀγαθὸν", Polytonic.exactKey("ἀγαθὸν"))
        assertEquals("ἀγαθός", Polytonic.exactKey("ἀγαθόσ"))
        assert(Polytonic.exactKey("ἀγαθὸν") != Polytonic.exactKey("ἀγαθόν"))
        assertEquals(GreekNormalizer.looseKey("ἀγαθὸν"), GreekNormalizer.looseKey("ἀγαθόν"))
    }

    @Test
    fun lengthMarksAreTakenOut() {
        // Woodhouse's breve on a letter that also has a breathing, as combining marks
        assertEquals("ἀπολείπειν", Polytonic.withoutLength("ᾰ\u0313πολείπειν"))
        assertEquals("καταλείπειν", Polytonic.withoutLength("κᾰτᾰλείπειν"))
        assertEquals("ἐκλιμπάνειν", Polytonic.withoutLength("ἐκλιμπᾰ\u0301νειν"))
        assertEquals("μεθίεσθαι", Polytonic.withoutLength("μεθῑ\u0301εσθαι"))
        assertEquals("μεθιέναι", Polytonic.withoutLength("μεθι\u0304έναι"))
    }
}
