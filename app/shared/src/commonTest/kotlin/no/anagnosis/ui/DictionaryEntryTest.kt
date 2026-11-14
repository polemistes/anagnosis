package no.anagnosis.ui

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

class DictionaryEntryTest {
    private val forms = Color(0xFF7D5260)
    private val muted = Color(0xFF888888)
    private val link = Color(0xFF6750A4)

    /** The head of λαμβάνω as the pipeline delivers it (shortened), followed by two senses. */
    private val verb = """<p class="head"><b class="orth">λαμβάνω</b>, <span class="gram tns">fut.</span> """ +
        """<span class="foreign">λήψομαι</span>, al.:<br><span class="gram tns">aor. 2</span> ἔλαβον, etc.:<br>""" +
        """<span class="gram tns">pf.</span> εἴληφα:<br><br>—<span class="gram"> <span class="gram voice">Med.</span> </span>, """ +
        """<span class="gram tns">aor. 2</span> ἐλαβόμην, etc.</p>""" +
        """<p class="sense"><b>A.</b> <i class="tr">take,</i> in <span class="gram tns">aor.</span> """ +
        """<span class="gram"> <span class="gram voice">Pass.</span> </span> …</p>""" +
        """<p class="sense"><b>II.</b> <i class="tr">receive</i> …</p>"""

    private fun annotated(html: String, formsColor: Color?) =
        htmlToAnnotated(html, linkColor = link, onNoteLink = null, mutedColor = muted, formsColor = formsColor)

    /** The colour and weight in force at the first letter of [word]: the innermost style wins. */
    private fun styleAt(text: AnnotatedString, word: String): Pair<Color, FontWeight?> {
        val at = text.text.indexOf(word)
        assertTrue(at >= 0, "$word is not in the text")
        val covering = text.spanStyles.filter { at >= it.start && at < it.end }
        // spans are listed outer first, so the last one that sets an attribute is the one in force
        val color = covering.lastOrNull { it.item.color != Color.Unspecified }?.item?.color ?: Color.Unspecified
        return color to covering.lastOrNull { it.item.fontWeight != null }?.item?.fontWeight
    }

    @Test
    fun splitsAfterTheHeadParagraph() {
        val parts = assertNotNull(splitEntry(verb))
        assertTrue(parts.head.startsWith("""<p class="head">"""))
        assertTrue(parts.head.endsWith("etc.</p>"))
        assertTrue(parts.rest.startsWith("""<p class="sense"><b>A.</b>"""))
        assertTrue(parts.rest.endsWith("receive</i> …</p>"))
        assertTrue(parts.hasLineBreaks)
        // nothing is lost or doubled
        assertEquals(verb, parts.head + parts.rest)
    }

    @Test
    fun anEntryWithNothingToTreatIsNotSplit() {
        // one short line, as in most of LSJ and in every other dictionary
        assertNull(splitEntry("""<p class="head"><b class="orth">ἀγαθός</b>, ή, όν,</p><p class="sense"><b>I.</b> good</p>"""))
        assertNull(splitEntry("""<p class="head"><span class="gram">Ion.</span> form of ἀγαθός</p>"""))
        // no head paragraph at all
        assertNull(splitEntry("""<p class="sense"><span class="gram tns">aor.</span> take</p>"""))
        assertNull(splitEntry("plain text"))
        assertNull(splitEntry(""))
    }

    @Test
    fun aSingleLineHeadWithALabelIsSplitButNotHung() {
        val parts = assertNotNull(splitEntry("""<p class="head"><b>φέρω</b>, <span class="gram tns">fut.</span> οἴσω</p><p class="sense">carry</p>"""))
        assertTrue(!parts.hasLineBreaks)
        assertEquals("""<p class="sense">carry</p>""", parts.rest)
    }

    @Test
    fun anEntryThatIsOnlyAHeadHasNoRest() {
        val parts = assertNotNull(splitEntry("""<p class="head">a<br>b</p>"""))
        assertEquals("", parts.rest)
        assertTrue(parts.hasLineBreaks)
    }

    @Test
    fun breaksAreWrittenSeveralWays() {
        assertNotNull(splitEntry("""<p class="head">a<br/>b</p>"""))
        assertNotNull(splitEntry("""<p class="head">a<BR />b</p>"""))
    }

    @Test
    fun labelsOfTheFormsSectionStandOutInTheHead() {
        val head = assertNotNull(splitEntry(verb)).head
        val text = annotated(head, forms)
        assertEquals(forms to FontWeight.SemiBold, styleAt(text, "fut."))
        assertEquals(forms to FontWeight.SemiBold, styleAt(text, "aor. 2"))
        // the voice label sits in a plain "gram" span; the inner class wins
        assertEquals(forms to FontWeight.Bold, styleAt(text, "Med."))
        // the other grammatical labels and the words stay as they are
        assertEquals(Color.Unspecified, styleAt(text, "ἔλαβον").first)
    }

    @Test
    fun otherLabelsStayMuted() {
        val text = annotated("""<p class="head"><span class="gram"> <span class="gram">Ion.</span> </span> x</p>""", forms)
        assertEquals(muted, styleAt(text, "Ion.").first)
    }

    @Test
    fun labelsAreMutedWithoutTheFormsColour() {
        // the senses, glossaries, notes and documents: tense and voice look like every "gram" label
        val text = annotated(assertNotNull(splitEntry(verb)).rest, null)
        assertEquals(muted, styleAt(text, "aor.").first)
        assertEquals(muted, styleAt(text, "Pass.").first)
        assertEquals(null, styleAt(text, "aor.").second)
        assertTrue(text.spanStyles.none { it.item.color == forms })
    }

    @Test
    fun theHeadKeepsItsLineBreaks() {
        val text = annotated(assertNotNull(splitEntry(verb)).head, forms)
        // two single breaks and a double one, before the voice label
        assertEquals(4, text.text.count { it == '\n' })
        assertTrue("\n\n—" in text.text)
    }

    @Test
    fun aHeadOfElevenLinesIsShownWhole() {
        assertTrue(!foldable(1))
        assertTrue(!foldable(FORMS_SHOWN_LINES))
        assertTrue(!foldable(FORMS_SHOWN_LINES + FORMS_MIN_HIDDEN_LINES - 1))
        assertEquals(Int.MAX_VALUE, formsMaxLines(11, open = false))
        assertEquals(Int.MAX_VALUE, formsMaxLines(11, open = true))
    }

    @Test
    fun aHeadOfTwelveLinesFoldsToEight() {
        assertTrue(foldable(12))
        assertTrue(foldable(40))
        assertEquals(8, formsMaxLines(12, open = false))
        assertEquals(8, formsMaxLines(40, open = false))
    }

    @Test
    fun anOpenHeadHasNoLimit() {
        assertEquals(Int.MAX_VALUE, formsMaxLines(12, open = true))
        assertEquals(Int.MAX_VALUE, formsMaxLines(40, open = true))
    }

    @Test
    fun theTwoConstantsAreWhatTheBriefSays() {
        assertEquals(8, FORMS_SHOWN_LINES)
        assertEquals(4, FORMS_MIN_HIDDEN_LINES)
    }
}
