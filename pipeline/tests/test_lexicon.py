"""Tests for the LSJ forms section and the Middle Liddell head of anagnosis_pipeline.lexicon.

The entries are small synthetic ones in the shape of the Perseus file (Greek in Betacode inside
elements with lang="greek"; the senses are flat siblings with n and level). The tests look at the
plain text of the head paragraph and of the paragraph that carries "A.", at where the line breaks
fall, at the label classes and at the rule that the repair reports; never at a whole HTML string.
"""
import re
import tempfile
import unittest
from html import unescape
from pathlib import Path

from lxml import etree

from anagnosis_pipeline.lexicon import (
    _greek, _split_key, parse_lexicon, parse_lsj, read_lsj_decisions, render_entry, render_lsj_entry,
)

BIBL = '<bibl><author>Il.</author> <biblScope>1.1</biblScope></bibl>'    # reads "Il. 1.1"
CIT = f'<cit><quote lang="greek">{{}}</quote> {BIBL}</cit>'              # a quoted form with its citation


def render(xml, decision=None):
    html, repair = render_lsj_entry(etree.fromstring(xml), decision)
    return html, repair


def paragraphs(html):
    """(class, inner HTML) of each paragraph, in order."""
    return re.findall(r'<p class="(\w+)">(.*?)</p>', html, re.S)


def plain(inner):
    """The text of some HTML, without its tags and with one space for any white space."""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", inner))).strip()


def head_of(html):
    """The inner HTML of the one head paragraph."""
    heads = [inner for cls, inner in paragraphs(html) if cls == "head"]
    assert len(heads) == 1, heads
    return heads[0]


def senses_of(html):
    """The plain text of each sense paragraph, in order."""
    return [plain(inner) for cls, inner in paragraphs(html) if cls == "sense"]


def lines_of(inner):
    """The lines of a head: its plain text between the <br> breaks (an empty line is "")."""
    return [plain(line) for line in inner.split("<br>")]


class SectionARepairTest(unittest.TestCase):
    """Where the file opens its section "A" in the wrong place, "A." goes to where the meanings start."""

    def test_forms_then_numbered_meanings_a_goes_before_the_first_number(self):
        html, repair = render(f'''
            <entryFree id="n42827" key="e)/rxomai" type="main">
              <orth extent="full" lang="greek">e)/rxomai</orth>
              {BIBL}, etc.: <tns>impf.</tns>
              <sense id="n42827.0" n="A" level="1">
                {CIT.format("h)rxo/mhn")}: <tns>fut.</tns>
                <foreign lang="greek">e)leu/somai</foreign>, <bibl><author>Hom.</author></bibl>:
              </sense>
              <sense id="n42827.1" n="I" level="2"><tr>start, set out,</tr> <foreign lang="greek">e)rxome/nw|</foreign></sense>
              <sense id="n42827.2" n="II" level="2"><tr>come</tr> or <tr>go</tr></sense>
            </entryFree>''')
        self.assertEqual(repair[0], "next section")
        self.assertEqual(lines_of(head_of(html)), [
            "ἔρχομαι Il. 1.1, etc.:",
            "impf. ἠρχόμην Il. 1.1:",
            "fut. ἐλεύσομαι, Hom.:",
        ])
        senses = senses_of(html)
        self.assertEqual(len(senses), 2)
        self.assertTrue(senses[0].startswith("A. I. start, set out"), senses[0])
        self.assertTrue(senses[1].startswith("II. come"), senses[1])
        self.assertEqual(html.count("<b>A.</b>"), 1)

    def test_dash_after_forms_in_the_same_section_opens_the_meaning(self):
        html, repair = render(f'''
            <entryFree id="n8665" key="a)nh/r" type="main">
              <orth extent="full" lang="greek">a)nh/r</orth>, <gen lang="greek">o(</gen>,
              <gen lang="greek">a)ndro/s</gen>, <case>dat.</case>
              <sense id="n8665.0" n="A" level="1">{CIT.format("a)/ndresi")}: ... (<etym lang="greek">a)-</etym>):—<tr>man,</tr> opp. woman</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "dash")
        head = plain(head_of(html))
        self.assertTrue(head.startswith("ἀνήρ, ὁ, ἀνδρός, dat. ἄνδρεσι Il. 1.1:"), head)
        self.assertTrue(head.endswith("(ἀ-):—"), head)
        self.assertEqual(senses_of(html), ["A. man, opp. woman"])

    def test_voices_each_get_an_empty_line_before_their_dash(self):
        html, repair = render(f'''
            <entryFree id="n3" key="kti/nw" type="main">
              <orth lang="greek">kti/nw</orth>, <tns>fut.</tns> <foreign lang="greek">kte/nw</foreign>
              <sense n="A" level="1">
                {CIT.format("e)/kteina")}:—<gramGrp><gram type="voice">Med.</gram></gramGrp>, <foreign lang="greek">kteino/menos</foreign> {BIBL}:—<gramGrp><gram type="voice">Pass.</gram></gramGrp>, <tns>aor.</tns> <foreign lang="greek">e)kta/qhn</foreign> {BIBL}:—<tr>kill, slay,</tr> {BIBL}
              </sense>
            </entryFree>''')
        self.assertEqual(repair[0], "dash")
        head = head_of(html)
        self.assertEqual(lines_of(head), [
            "κτίνω,",
            "fut. κτένω ἔκτεινα Il. 1.1:",
            "",
            "—Med., κτεινόμενος Il. 1.1:",
            "",
            "—Pass., aor. ἐκτάθην Il. 1.1:—",
        ])
        self.assertIn('<span class="gram voice">Med.</span>', head)
        self.assertIn('<span class="gram voice">Pass.</span>', head)
        self.assertEqual(senses_of(html), ["A. kill, slay, Il. 1.1"])

    def test_a_inside_an_etymology_bracket_takes_the_bracket_into_the_head(self):
        html, repair = render(f'''
            <entryFree id="n4" key="polua/ndrion" type="main">
              <orth lang="greek">polua/ndrion</orth>, <gen lang="greek">to/</gen>, (<sense n="A" level="1"><cit><quote lang="greek">sh=ma</quote> <bibl><biblScope>3</biblScope></bibl></cit>) <tr>full of tombs,</tr> {BIBL}</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "bracket")
        head = plain(head_of(html))
        self.assertTrue(head.endswith("(σῆμα 3)"), head)
        self.assertEqual(senses_of(html), ["A. full of tombs, Il. 1.1"])

    def test_a_meaning_in_plain_words_after_a_bracket_is_found_too(self):
        html, repair = render(f'''
            <entryFree id="n18239" key="a)fe/ths" type="main">
              <orth lang="greek">a)fe/t-hs</orth>, <itype lang="greek">ou</itype>, <gen lang="greek">o(</gen>, (<sense n="A" level="1"><cit><quote lang="greek">a)fi/hmi)</quote> one who lets off a military engine, {BIBL}</cit>. </sense>
            </entryFree>''')
        self.assertEqual(repair[0], "bracket")
        head = plain(head_of(html))
        self.assertTrue(head.endswith("(ἀφίημι)"), head)
        senses = senses_of(html)
        self.assertEqual(len(senses), 1)
        self.assertTrue(senses[0].startswith("A. one who lets off a military engine"), senses[0])

    def test_meaning_already_in_the_head_as_a_title_moves_a_back_to_it(self):
        html, repair = render(f'''
            <entryFree id="n56524" key="*keltoi/" type="main">
              <orth lang="greek">*keltoi/</orth>, <gen lang="greek">oi(</gen>, <title>Celts</title>, {BIBL}:—hence <orth lang="greek">*keltiko/s</orth>, <itype lang="greek">h/</itype>, <itype lang="greek">o/n</itype>, <sense n="A" level="1"><tr>Celtic, Gallic</tr>, {BIBL}</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "head")
        self.assertEqual(plain(head_of(html)), "Κελτοί, οἱ,")
        senses = senses_of(html)
        self.assertEqual(len(senses), 1)
        self.assertTrue(senses[0].startswith("A. Celts"), senses[0])
        # the derived word and its meaning stay in the section
        self.assertIn("hence Κελτικός", senses[0])
        self.assertIn("Celtic, Gallic", senses[0])

    def test_definition_by_reference_after_the_dash_is_the_meaning(self):
        html, repair = render(f'''
            <entryFree id="n102896" key="te/kos" type="main">
              <orth lang="greek">te/kos</orth>, <itype lang="greek">eos</itype>, <gen lang="greek">to/</gen>, <gramGrp><gram type="dialect">Ep.</gram></gramGrp> dat. pl.
              <sense n="A" level="1">{CIT.format("te/kessi")}, al.:—poet. for <foreign lang="greek">te/knon</foreign>, {BIBL}</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "dash")
        head = plain(head_of(html))
        self.assertTrue(head.endswith("dat. pl. τέκεσσι Il. 1.1, al.:—"), head)
        senses = senses_of(html)
        self.assertEqual(len(senses), 1)
        self.assertTrue(senses[0].startswith("A. poet. for τέκνον"), senses[0])

    def test_the_lexicons_own_printed_a_dissolves_the_files_section(self):
        html, repair = render(f'''
            <entryFree id="n8" key="ba/llw" type="main">
              <orth lang="greek">ba/llw</orth> <tns>pf.</tns>
              <sense n="A" level="1"><foreign lang="greek">be/blhka</foreign>, <tns>aor.</tns> <foreign lang="greek">e)/balon</foreign></sense>
              <sense n="A" level="1"><tr>in the above tenses,</tr> {BIBL}</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "printed A.")
        self.assertEqual(html.count("<b>A.</b>"), 1)
        head = plain(head_of(html))
        self.assertIn("pf. βέβληκα", head)
        self.assertIn("aor. ἔβαλον", head)
        self.assertEqual(senses_of(html), ["A. in the above tenses, Il. 1.1"])

    def test_entry_of_forms_only_has_no_a_at_all(self):
        html, repair = render(f'''
            <entryFree id="n9" key="a)/xw" type="main">
              <orth lang="greek">a)/xw</orth>, <tns>aor.</tns>
              <sense n="A" level="1">{CIT.format("h)/xon")}, <tns>pf.</tns> <foreign lang="greek">h)/xa</foreign></sense>
            </entryFree>''')
        self.assertEqual(repair[0], "no A.")
        self.assertEqual([cls for cls, _ in paragraphs(html)], ["head"])
        self.assertNotIn("<b>A.</b>", html)
        head = plain(head_of(html))
        self.assertIn("aor. ἤχον", head)
        self.assertTrue(head.endswith("pf. ἤχα"), head)

    def test_a_that_already_opens_with_a_translation_is_left_alone(self):
        html, repair = render('''
            <entryFree id="n260" key="a)gaqo/s" type="main">
              <orth lang="greek">a)gaqo/s</orth>, <itype lang="greek">h/</itype>, <itype lang="greek">o/n</itype>, <sense n="A" level="1"><tr>good</tr>:</sense>
            </entryFree>''')
        self.assertIsNone(repair)
        self.assertEqual(plain(head_of(html)), "ἀγαθός, ή, όν,")
        self.assertEqual(senses_of(html), ["A. good:"])

    def test_synonym_entry_is_left_as_it_is(self):
        html, repair = render(f'''
            <entryFree id="n11" key="ka/ppari" type="main">
              <orth lang="greek">ka/ppari</orth>, <itype lang="greek">ios</itype>, <sense n="A" level="1"><xr><lbl>=</lbl> <ref lang="greek">ka/pparis</ref></xr>, {BIBL}</sense>
            </entryFree>''')
        self.assertIsNone(repair)
        self.assertEqual(plain(head_of(html)), "κάππαρι, ιος,")
        self.assertEqual(senses_of(html), ["A. = κάππαρις, Il. 1.1"])

    def test_a_bracket_never_closed_in_the_forms_does_not_hide_the_meaning(self):
        html, repair = render(f'''
            <entryFree id="n3398" key="a)kou/w" type="main">
              <orth lang="greek">a)kou/w</orth>: <tns>impf.</tns>
              <sense n="A" level="1">{CIT.format("h)/kouon")}: <tns>fut.</tns> <foreign lang="greek">a)kou/somai</foreign> (<gramGrp><gram type="voice">Act.</gram></gramGrp> <foreign lang="greek">a)kou/sw</foreign> first in {BIBL}, etc.:—<tr>hear</tr> {BIBL}</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "dash")
        head = plain(head_of(html))
        self.assertIn("fut. ἀκούσομαι (Act. ἀκούσω first in", head)
        self.assertTrue(head.endswith("etc.:—"), head)
        senses = senses_of(html)
        self.assertEqual(len(senses), 1)
        self.assertTrue(senses[0].startswith("A. hear"), senses[0])

    def test_a_quotation_that_opens_with_a_comma_takes_the_comma_and_etymology_into_the_head(self):
        html, repair = render(f'''
            <entryFree id="n75354" key="o)rrw/dhs" type="main">
              <orth lang="greek">o)rrw/dhs</orth>, <itype lang="greek">es</itype>
              <sense n="A" level="1"><cit><quote lang="greek">, (o)/rros)</quote> <tr>pertaining to the rump,</tr> <bibl><author>Hp.</author></bibl></cit></sense>
            </entryFree>''')
        self.assertEqual(repair[0], "comma")
        head = plain(head_of(html))
        self.assertTrue(head.startswith("ὀρρώδης, ες"), head)
        self.assertTrue(head.endswith(", (ὄρρος)"), head)
        senses = senses_of(html)
        self.assertEqual(len(senses), 1)
        self.assertTrue(senses[0].startswith("A. pertaining to the rump"), senses[0])

    def test_translation_that_opens_a_clause_among_the_forms_starts_the_meaning(self):
        html, repair = render(f'''
            <entryFree id="n7" key="logi/zomai" type="main">
              <orth lang="greek">logi/zomai</orth>, <tns>aor.</tns>
              <sense n="A" level="1"><foreign lang="greek">e)logisa/mhn</foreign> {BIBL}; <tr>reckon,</tr> {BIBL}</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "clause")
        head = plain(head_of(html))
        self.assertTrue(head.endswith("aor. ἐλογισάμην Il. 1.1;"), head)
        senses = senses_of(html)
        self.assertEqual(len(senses), 1)
        self.assertTrue(senses[0].startswith("A. reckon,"), senses[0])

    def test_meaning_in_plain_words_after_a_dash_is_taken_with_a_note(self):
        html, repair = render(f'''
            <entryFree id="n6" key="*)iw/" type="main">
              <orth lang="greek">*)iw/</orth>, <gen lang="greek">ou=s</gen>, <gen lang="greek">h(</gen>, voc.
              <sense n="A" level="1">{CIT.format("*)ioi=")}, etc.:—Io, daughter of Inachus</sense>
            </entryFree>''')
        self.assertEqual(repair[0], "plain words")
        self.assertTrue(repair[1])      # a judgment: the note says why
        head = plain(head_of(html))
        self.assertTrue(head.endswith("etc.:—"), head)
        self.assertEqual(senses_of(html), ["A. Io, daughter of Inachus"])

    def test_entry_without_a_section_a_is_not_repaired(self):
        html, repair = render(f'''
            <entryFree id="n5" key="a)/llos" type="main">
              <orth lang="greek">a)/llos</orth>, <itype lang="greek">h</itype>
              <sense n="I" level="2"><tr>other</tr> {BIBL}</sense>
            </entryFree>''')
        self.assertIsNone(repair)
        self.assertEqual(senses_of(html), ["I. other Il. 1.1"])


class DecisionTest(unittest.TestCase):
    """The editor's decision for an entry (lsj-forms.tsv) wins over the rules."""

    ENTRY = f'''
        <entryFree id="n8665" key="a)nh/r" type="main">
          <orth lang="greek">a)nh/r</orth>, <case>dat.</case>
          <sense n="A" level="1">{CIT.format("a)/ndresi")}: ... (<etym lang="greek">a)-</etym>):—<tr>man,</tr> opp. woman</sense>
        </entryFree>'''

    def test_first_words_of_the_meaning_set_a_before_them(self):
        html, repair = render(self.ENTRY, decision="man, opp. woman")
        self.assertEqual(repair, ("decided", ""))
        head = plain(head_of(html))
        self.assertTrue(head.endswith(":—"), head)
        self.assertEqual(senses_of(html), ["A. man, opp. woman"])

    def test_a_decision_may_name_a_different_place_than_the_rules_would(self):
        html, repair = render(self.ENTRY, decision="opp. woman")
        self.assertEqual(repair, ("decided", ""))
        head = plain(head_of(html))
        self.assertTrue(head.endswith("man,"), head)
        self.assertEqual(senses_of(html), ["A. opp. woman"])

    def test_a_dash_puts_everything_in_the_head_and_leaves_a_out(self):
        html, repair = render(self.ENTRY, decision="-")
        self.assertEqual(repair, ("decided", ""))
        self.assertEqual([cls for cls, _ in paragraphs(html)], ["head"])
        self.assertTrue(plain(head_of(html)).endswith("man, opp. woman"))

    def test_an_equals_sign_leaves_the_entry_as_the_file_has_it(self):
        entry = f'''
            <entryFree id="n42827" key="e)/rxomai" type="main">
              <orth lang="greek">e)/rxomai</orth> {BIBL}, etc.: <tns>impf.</tns>
              <sense n="A" level="1">{CIT.format("h)rxo/mhn")}: <tns>fut.</tns> <foreign lang="greek">e)leu/somai</foreign>:</sense>
              <sense n="I" level="2"><tr>start, set out,</tr></sense>
            </entryFree>'''
        _, repaired = render(entry)
        self.assertEqual(repaired[0], "next section")      # what the rules would do
        html, repair = render(entry, decision="=")
        self.assertIsNone(repair)
        self.assertEqual(lines_of(head_of(html)), ["ἔρχομαι Il. 1.1, etc.:", "impf."])
        senses = senses_of(html)
        self.assertTrue(senses[0].startswith("A. ἠρχόμην"), senses[0])
        self.assertTrue(senses[1].startswith("I. start"), senses[1])

    def test_words_that_do_not_occur_raise_value_error(self):
        with self.assertRaises(ValueError) as caught:
            render(self.ENTRY, decision="no such words")
        self.assertIn("no such words", str(caught.exception))

    def test_a_decision_for_an_entry_without_section_a_raises_value_error(self):
        with self.assertRaises(ValueError):
            render(f'''
                <entryFree id="n5" key="a)/llos" type="main">
                  <orth lang="greek">a)/llos</orth>
                  <sense n="I" level="2"><tr>other</tr> {BIBL}</sense>
                </entryFree>''', decision="other")


class LinesTest(unittest.TestCase):
    """The head's own dividers shown as lines (_lines, through render_lsj_entry)."""

    @staticmethod
    def head(forms):
        """The head of an entry whose section A opens at a translation, so that nothing is repaired."""
        html, repair = render(f'<entryFree id="n1" key="x" type="main"><orth lang="greek">lamba/nw</orth>, {forms}'
                              '<sense n="A" level="1"><tr>take</tr></sense></entryFree>')
        assert repair is None, repair
        return head_of(html)

    def test_break_after_a_colon_and_before_a_dash(self):
        head = self.head('<tns>fut.</tns> <foreign lang="greek">lh/yomai</foreign>: <tns>aor.</tns> <foreign lang="greek">e)/labon</foreign>:—later ')
        self.assertEqual(lines_of(head), ["λαμβάνω,", "fut. λήψομαι:", "aor. ἔλαβον:", "—later"])

    def test_no_break_after_a_colon_inside_round_brackets(self):
        head = self.head('<tns>aor.</tns> <foreign lang="greek">e)/labon</foreign> (cf. this: that): <tns>pf.</tns> <foreign lang="greek">ei)/lhfa</foreign> ')
        self.assertEqual(lines_of(head), ["λαμβάνω,", "aor. ἔλαβον (cf. this: that):", "pf. εἴληφα"])

    def test_no_break_after_a_colon_inside_square_brackets(self):
        head = self.head('<tns>aor.</tns> <foreign lang="greek">e)/labon</foreign> [say: this]: <tns>pf.</tns> <foreign lang="greek">ei)/lhfa</foreign> ')
        self.assertEqual(lines_of(head), ["λαμβάνω,", "aor. ἔλαβον [say: this]:", "pf. εἴληφα"])

    def test_no_break_at_the_very_end_of_the_head(self):
        head = self.head('<tns>fut.</tns> <foreign lang="greek">lh/yomai</foreign>: ')
        self.assertFalse(head.endswith("<br>"), head)
        self.assertEqual(lines_of(head), ["λαμβάνω, fut. λήψομαι:"])

    def test_no_break_at_a_dash_that_ends_the_head(self):
        head = self.head('<tns>fut.</tns> <foreign lang="greek">lh/yomai</foreign>:—')
        self.assertNotIn("<br>", head)
        self.assertTrue(plain(head).endswith("λήψομαι:—"))

    def test_headword_followed_by_a_tense_gets_its_own_line_when_there_are_other_lines(self):
        head = self.head('<tns>fut.</tns> <foreign lang="greek">lh/yomai</foreign>: <tns>aor.</tns> <foreign lang="greek">e)/labon</foreign> ')
        self.assertEqual(lines_of(head)[0], "λαμβάνω,")
        self.assertTrue(head.startswith('<b class="orth">λαμβάνω</b>,<br>'), head)

    def test_headword_followed_by_a_tense_stays_on_the_line_when_there_is_no_other_break(self):
        head = self.head('<tns>fut.</tns> <foreign lang="greek">lh/yomai</foreign>, <tns>aor.</tns> <foreign lang="greek">e)/labon</foreign> ')
        self.assertNotIn("<br>", head)
        self.assertEqual(plain(head), "λαμβάνω, fut. λήψομαι, aor. ἔλαβον")

    def test_headword_followed_by_something_else_gets_no_line_of_its_own(self):
        head = self.head('<gen lang="greek">o(</gen>: <tns>fut.</tns> <foreign lang="greek">lh/yomai</foreign> ')
        self.assertEqual(lines_of(head), ["λαμβάνω, ὁ:", "fut. λήψομαι"])

    def test_dash_that_opens_a_voice_gets_an_empty_line_before_it(self):
        head = self.head('<tns>aor.</tns> <foreign lang="greek">e)/labon</foreign>:—Med., <foreign lang="greek">lamba/nomai</foreign> ')
        self.assertEqual(lines_of(head), ["λαμβάνω,", "aor. ἔλαβον:", "", "—Med., λαμβάνομαι"])

    def test_dash_that_does_not_open_a_voice_gets_a_single_break(self):
        head = self.head('<tns>aor.</tns> <foreign lang="greek">e)/labon</foreign>:—hence <foreign lang="greek">lh=yis</foreign> ')
        self.assertEqual(lines_of(head), ["λαμβάνω,", "aor. ἔλαβον:", "—hence λῆψις"])

    def test_lone_bracket_does_not_hold_back_the_breaks_after_it(self):
        head = self.head('<tns>aor.</tns> <foreign lang="greek">e)/labon</foreign> ( first in this: <tns>pf.</tns> <foreign lang="greek">ei)/lhfa</foreign> ')
        self.assertEqual(lines_of(head), ["λαμβάνω,", "aor. ἔλαβον ( first in this:", "pf. εἴληφα"])


class LabelClassTest(unittest.TestCase):
    def test_tense_mood_and_voice_labels_carry_their_classes(self):
        html, _ = render(f'''
            <entryFree id="n1" key="x" type="main">
              <orth lang="greek">lu/w</orth>, <tns>fut.</tns> <foreign lang="greek">lu/sw</foreign>, <mood>inf.</mood>
              <foreign lang="greek">lu/ein</foreign>, <gramGrp><gram type="voice">Act.</gram></gramGrp>
              <gramGrp><gram type="dialect">Ep.</gram></gramGrp>
              <sense n="A" level="1"><tr>loose</tr></sense>
            </entryFree>''')
        head = head_of(html)
        self.assertIn('<span class="gram tns">fut.</span>', head)
        self.assertIn('<span class="gram mood">inf.</span>', head)
        self.assertIn('<span class="gram voice">Act.</span>', head)
        # any other label is a plain gram, never a voice
        self.assertEqual(head.count('class="gram voice"'), 1)
        self.assertIn('<span class="gram">Ep.</span>', head)


class GreekTest(unittest.TestCase):
    """Betacode to Unicode, keeping the brackets that stand inside Greek text."""

    def test_bracket_that_closes_a_parenthesis_after_a_word_with_its_breathing(self):
        self.assertEqual(_greek("(ai)/qw)"), "(αἴθω)")

    def test_breathing_alone_stays_a_breathing(self):
        self.assertEqual(_greek("a)"), "ἀ")
        self.assertEqual(_greek("oi("), "οἱ")

    def test_closing_bracket_after_a_word_that_has_its_breathing(self):
        self.assertEqual(_greek("au)to/s)"), "αὐτός)")

    def test_bracket_around_a_lone_vowel_with_a_breathing(self):
        self.assertEqual(_greek("(a))"), "(ἀ)")

    def test_word_without_brackets_is_converted_plain(self):
        self.assertEqual(_greek("e)/rxomai"), "ἔρχομαι")
        self.assertEqual(_greek("*keltoi/"), "Κελτοί")

    def test_closing_bracket_after_a_consonant_is_a_bracket_not_a_breathing(self):
        self.assertEqual(_greek("a) b)"), "ἀ β)")

    def test_stops_after_the_bracket_are_kept(self):
        self.assertEqual(_greek("(ai)/qw);"), "(αἴθω);")
        self.assertEqual(_greek("(ai)/qw), oi("), "(αἴθω), οἱ")

    def test_white_space_and_empty_text_are_kept(self):
        self.assertEqual(_greek(""), "")
        self.assertEqual(_greek("a)  b)"), "ἀ  β)")


class MiddleLiddellTest(unittest.TestCase):
    def render(self, xml):
        return render_entry(etree.fromstring(xml))

    def test_head_notes_each_on_their_own_line_and_stem_codes_left_out(self):
        html = self.render('''
            <entry key="fe/rw" type="main" id="n1">
              <form><orth extent="full" lang="greek">fe/rw</orth></form>
              <etym n="note">The forms <foreign lang="greek">oi)/sw</foreign> come from another stem.</etym>
              <etym n="note">Second note.</etym>
              <gramGrp><pos>n</pos><note anchored="yes">xyz is_ews fem</note></gramGrp>
              <sense level="1" n="A" id="n1.0"><trans><tr>to bear</tr></trans>, <usg>Hom.</usg></sense>
            </entry>''')
        paras = paragraphs(html)
        self.assertEqual([cls for cls, _ in paras], ["head", "sense"])
        head = paras[0][1]
        self.assertEqual(lines_of(head), ["φέρω", "The forms οἴσω come from another stem.", "Second note."])
        self.assertNotIn("xyz", html)
        self.assertNotIn("is_ews", html)
        self.assertEqual(senses_of(html), ["A. to bear, Hom."])

    def test_a_note_of_alternative_forms_is_a_line_of_its_own(self):
        html = self.render('''
            <entry key="diakw/lusis" type="main" id="n7864">
              <form><orth extent="full" lang="greek">diakw/lusis</orth></form>
              <note anchored="yes" type="alt" lang="greek">diakw/lusis, ews</note>
              <gramGrp><pos>n</pos><note anchored="yes">diakwlu_s is_ews fem</note></gramGrp>
              <etym>from <ref targOrder="U" lang="greek">diakwlu/w</ref></etym>
              <sense level="0" n="0" id="n7864.0"><trans><tr>a hindering</tr></trans>, <usg>Plat.</usg></sense>
            </entry>''')
        head = head_of(html)
        self.assertEqual(lines_of(head), ["διακώλυσις", "διακώλυσις, εως", "from διακωλύω"])
        self.assertNotIn("is_ews", html)
        # a sense numbered "0" is a section without a number: no label
        self.assertEqual(senses_of(html), ["a hindering, Plat."])

    def test_a_grammar_group_without_a_note_stays(self):
        html = self.render('''
            <entry key="a)/llos" type="main" id="n2">
              <form><orth lang="greek">a)/llos</orth></form>
              <gramGrp><pos>adj</pos></gramGrp>
              <sense level="1" n="A"><trans><tr>other</tr></trans></sense>
            </entry>''')
        self.assertIn("adj", plain(head_of(html)))


class ParseTest(unittest.TestCase):
    """Keys, files and the decisions file (all in a temporary directory)."""

    XML = '''<TEI.2><text><body>
        <entryFree id="n1" key="a)1" type="main"><orth lang="greek">a)</orth>, <sense n="A" level="1"><tr>alpha</tr></sense></entryFree>
        <entryFree id="n2" key="" type="main"><orth lang="greek">zz</orth></entryFree>
        <entryFree id="n3" key="a)gaqo/s" type="main"><orth lang="greek">a)gaqo/s</orth>, <sense n="A" level="1"><tr>good</tr></sense></entryFree>
    </body></text></TEI.2>'''

    def test_split_key_takes_the_homograph_number_off(self):
        self.assertEqual(_split_key("a)1"), ("a)", 1))
        self.assertEqual(_split_key("a)gaqo/s"), ("a)gaqo/s", 0))
        self.assertEqual(_split_key("a)12"), ("a)", 12))

    def test_parse_lexicon_makes_entries_and_skips_those_without_a_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "grc.lsj.perseus-eng1.xml"
            path.write_text(self.XML, encoding="utf-8")
            entries = parse_lexicon(path, "lsj", p4=False)
        self.assertEqual([e.key for e in entries], ["a)1", "a)gaqo/s"])
        first, second = entries
        self.assertEqual((first.lexicon, first.headword, first.homograph), ("lsj", "ἀ", 1))
        self.assertEqual((second.headword, second.homograph, second.sort_key), ("ἀγαθός", 0, "αγαθος"))
        self.assertTrue(second.html.startswith('<p class="head">'))

    def test_parse_lexicon_collects_the_repairs_and_applies_decisions(self):
        xml = f'''<TEI.2><text><body>
            <entryFree id="n9" key="a)/xw" type="main"><orth lang="greek">a)/xw</orth>, <tns>aor.</tns>
              <sense n="A" level="1">{CIT.format("h)/xon")}, <tns>pf.</tns> <foreign lang="greek">h)/xa</foreign></sense></entryFree>
            <entryFree id="n10" key="a)gaqo/s" type="main"><orth lang="greek">a)gaqo/s</orth>, <sense n="A" level="1"><tr>good</tr></sense></entryFree>
            </body></text></TEI.2>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "grc.lsj.perseus-eng1.xml"
            path.write_text(xml, encoding="utf-8")
            repairs = []
            parse_lexicon(path, "lsj", p4=False, repairs=repairs)
            self.assertEqual([(key, rule) for key, rule, _ in repairs], [("a)/xw", "no A.")])
            decided = []
            entries = parse_lexicon(path, "lsj", p4=False, repairs=decided, decisions={"a)/xw": "="})
            self.assertEqual(decided, [])
            self.assertIn("A. ", plain(entries[0].html))
            with self.assertRaises(ValueError) as caught:
                parse_lexicon(path, "lsj", p4=False, decisions={"a)/xw": "no such words"})
            self.assertTrue(str(caught.exception).startswith("a)/xw: "))

    def test_read_lsj_decisions_skips_comments_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lsj-forms.tsv"
            path.write_text("# a comment\n\na)/xw\t-\tforms only\ne)/rxomai\t= \n  \nte/kos\tpoet. for\n", encoding="utf-8")
            self.assertEqual(read_lsj_decisions(path), {"a)/xw": "-", "e)/rxomai": "=", "te/kos": "poet. for"})
            self.assertEqual(read_lsj_decisions(Path(tmp) / "missing.tsv"), {})

    def test_parse_lsj_reads_the_files_in_numeric_order_and_checks_the_decisions(self):
        def one(key, word):
            return (f'<TEI.2><text><body><entryFree id="n" key="{key}" type="main"><orth lang="greek">{key}</orth>, '
                    f'<sense n="A" level="1"><tr>{word}</tr></sense></entryFree></body></text></TEI.2>')

        with tempfile.TemporaryDirectory() as tmp:
            sources = Path(tmp) / "sources"
            (sources / "lsj").mkdir(parents=True)
            (sources / "lsj" / "grc.lsj.perseus-eng10.xml").write_text(one("bai/nw", "walk"), encoding="utf-8")
            (sources / "lsj" / "grc.lsj.perseus-eng2.xml").write_text(one("a)gaqo/s", "good"), encoding="utf-8")
            self.assertEqual([e.key for e in parse_lsj(sources)], ["a)gaqo/s", "bai/nw"])
            (Path(tmp) / "lsj-forms.tsv").write_text("nothing/\t-\tno such entry\n", encoding="utf-8")
            with self.assertRaises(ValueError) as caught:
                parse_lsj(sources)
            self.assertIn("nothing/", str(caught.exception))
            (Path(tmp) / "lsj-forms.tsv").write_text("bai/nw\t=\tleave as it is\n", encoding="utf-8")
            self.assertEqual(len(parse_lsj(sources)), 2)


if __name__ == "__main__":
    unittest.main()
