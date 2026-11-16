import unittest

from lxml import etree

from anagnosis_pipeline.commentary import _md, _txt
from anagnosis_pipeline.sophocles import _printed, apply_text_check, numbering_suspects, perseus_anchors, refile_translation
from anagnosis_pipeline.textfmt import parse, serialize
from anagnosis_pipeline.sophocles_pages import bold_lemmas
from anagnosis_pipeline.textfmt import Document, Line


def doc_of(*lines: tuple[str, str]) -> Document:
    doc = Document(meta={})
    for n, text in lines:
        doc.items.append(Line(n, text))
    return doc


class TextCheck(unittest.TestCase):
    def test_difference_found_by_its_words_near_a_shifted_number(self):
        # the transcriber numbered by the print, one higher than this import
        doc = doc_of(("10", "ἀλλʼ ὦ φίλαι"), ("11", "τίς ἐστιν οὗτος;"), ("12", "ὦ τέκνον, εἰ σοί"))
        _, _, warnings = apply_text_check(doc, [], [("12", False, "οὗτος;", "οὗτος.")], set())
        self.assertEqual(warnings, [])
        self.assertEqual(doc.lines[1].text, "τίς ἐστιν οὗτος.")

    def test_reference_text_decides_between_lines_with_the_same_words(self):
        doc = doc_of(("1", "ὦ παῖ, λέγε."), ("2", "ὦ παῖ, σίγα."))
        reference = {"5": "ὦ παῖ, σίγα."}
        apply_text_check(doc, [], [("5", False, "ὦ παῖ,", "ὦ παῖ")], set(), reference)
        self.assertEqual([l.text for l in doc.lines], ["ὦ παῖ, λέγε.", "ὦ παῖ σίγα."])

    def test_inserted_line_follows_the_reference_line(self):
        doc = doc_of(("554", "ἐν τῷ φρονεῖν γὰρ μηδὲν ἥδιστος βίος,"), ("555", "ἕως τὸ χαίρειν"))
        reference = {"554": "ἐν τῷ φρονεῖν γὰρ μηδὲν ἥδιστος βίος,"}
        apply_text_check(doc, [], [("554", True, "", "[τὸ μὴ φρονεῖν γὰρ κάρτʼ ἀνώδυνον κακόν,]")], set(), reference)
        self.assertEqual(doc.lines[1].text, "[τὸ μὴ φρονεῖν γὰρ κάρτʼ ἀνώδυνον κακόν,]")

    def test_printed_conventions(self):
        self.assertEqual(_printed("*τοιοῖσδ’ <γὰρ>"), "τοιοῖσδʼ ⟨γὰρ⟩")
        self.assertEqual(_printed("* * * μή"), "* * * μή")

    def test_perseus_anchor_kept_only_far_from_printed_numbers(self):
        doc = doc_of(*[(str(n), "λόγος") for n in range(1, 41)])
        lines = doc.lines
        stated = {id(lines[4]): "5", id(lines[34]): "35"}
        printed = {9: "10"}
        self.assertEqual(perseus_anchors(lines, stated, printed), {34: "35"})


    def test_lyric_pass_splits_and_joins_verses(self):
        doc = doc_of(("1", "ἰὼ πόροι ἁλίρροθοι πάραλά τʼ ἄντρα"), ("2", "καὶ νέμος"), ("3", "ἐπάκτιον,"))
        lyrics = [("1", False, "ἁλίρροθοι πάραλά", "ἁλίρροθοι | πάραλά"),
                  ("3", False, "ἐπάκτιον,", ""), ("2", False, "καὶ νέμος", "καὶ νέμος ἐπάκτιον,")]
        _, _, warnings = apply_text_check(doc, [], [], set(), None, lyrics)
        self.assertEqual(warnings, [])
        self.assertEqual([l.text for l in doc.lines],
                         ["ἰὼ πόροι ἁλίρροθοι", "πάραλά τʼ ἄντρα", "καὶ νέμος ἐπάκτιον,"])


class Commentary(unittest.TestCase):
    def test_english_aside_inside_greek_quotation(self):
        x = '<p><quote lang="greek">e)/stai <note place="inline" lang="en">(we shall hear of him)</note> a)namixqh/setai</quote></p>'
        self.assertEqual(" ".join(_md(etree.fromstring(x), False).split()), "ἔσται (we shall hear of him) ἀναμιχθήσεται")

    def test_parentheses_and_elisions_in_betacode(self):
        self.assertEqual(_txt("kai\\ a)\\n xrh/sima (o)/nta) e)reuna=|", True), "καὶ ἂν χρήσιμα (ὄντα) ἐρευνᾷ")
        self.assertEqual(_txt("e)ntau=q) h)\\ )gw/", True), "ἐνταῦθʼ ἢ ʼγώ")
        self.assertEqual(_txt("w)= xqo/ni) *(ermh=", True), "ὦ χθόνιʼ Ἑρμῆ")
        self.assertEqual(_txt("ka)gw/ tou)/noma prou)/sthn", True), "κἀγώ τοὔνομα προὔστην")

    def test_parenthesis_opened_in_english_closed_in_greek(self):
        x = '<p>wore garlands (<quote lang="greek">e)stefanwme/noi)</quote>, and</p>'
        self.assertEqual(_md(etree.fromstring(x), False).strip(), "wore garlands (ἐστεφανωμένοι), and")


class Lemmas(unittest.TestCase):
    def test_lemma_does_not_run_over_a_full_stop(self):
        self.assertEqual(bold_lemmas("Nauck, s. v. ὑπόβλητον. σαυτοῦ] σεαυτοῦ L."),
                         "Nauck, s. v. ὑπόβλητον. **σαυτοῦ**] σεαυτοῦ L.")


class NumberingSuspects(unittest.TestCase):
    LINES = [("96", "Ἅλιον, Ἅλιον αἰτῶ"),
             ("97", "τοῦτο καρῦξαι, τὸν Ἀλκμήνας πόθι μοι πόθι παῖς"),
             ("98", "ναίει ποτʼ, ὦ λαμπρᾷ στεροπᾷ φλεγέθων,"),
             ("100", "ἢ ποντίας αὐλῶνας, ἢ δισσαῖσιν ἀπείροις κλιθείς·"),
             ("101", "εἴπʼ, ὦ κρατιστεύων κατʼ ὄμμα."),
             ("102", "ποθουμένᾳ γὰρ φρενὶ πυνθάνομαι")]
    APP = """# title: Critical apparatus

## 97
τοῦτο r: τούτωι L.—**καρῦξαι**] κᾱρύξαι L.

## 98
πόθι μοι L.

[99] λαμπρᾶι στεροπᾶι made by S from λαμπρὰ στεροπὰ in L.

## 100
**ἢ ποντίας...κλιθείς**] ποντίασ L.

## 101
**Κατʼ ὄμμα**] Nauck conj. πανόπτα.

## 102
**Ἥλιον**] not near.
"""

    def test_lemma_in_a_nearby_verse_and_printed_numbers(self):
        items = numbering_suspects(self.LINES, self.APP)
        self.assertEqual([(i["kind"], i["note"], i["lemma"], i["filed"], i["found"]) for i in items], [
            ("printed", "99", "λαμπρᾶι στεροπᾶι", "98", "98"),
        ])
        # the lemma of the note filed under 102 stands in 101 (case and accents ignored); a lemma in
        # its own verse (100, up to the "..."), or in no verse within reach (Ἥλιον), is not listed
        app = self.APP.replace("## 101\n**Κατʼ ὄμμα**", "## 101\n**εἴπʼ**").replace(
            "## 102\n**Ἥλιον**] not near.", "## 102\n**κατʼ ὄμμα**] Nauck.\n\n## 96\n**Ἥλιον**] not near.")
        items = numbering_suspects(self.LINES, app)
        self.assertEqual([(i["kind"], i["note"], i["lemma"], i["filed"], i["found"]) for i in items], [
            ("printed", "99", "λαμπρᾶι στεροπᾶι", "98", "98"),
            ("lemma", "102", "κατʼ ὄμμα", "102", "101"),
        ])
        self.assertEqual([n for n, _t in items[1]["context"]], ["98", "100", "101", "102"])


class RefileTranslation(unittest.TestCase):
    TR = """# title: T

== episode
@ Chorus
105\tlike some mournful bird,
110\tby her anxious bed.
@ Nurse
112\tFor just as one may see
113\tbillow after billow
@ Chorus
876a\tSurely she is not dead?
@ Nurse
876b\tMy tale is told.
@ Chorus
881a\tShe destroyed herself.
@ Nurse
881b\tWhat impulse drove her?
@ Chorus
977b\tIs he alive?
"""
    GRC = ["105", "106", "109", "111", "112", "114", "876", "876a", "881", "882", "977", "977a"]

    def test_rules(self):
        doc = parse(self.TR, "t")
        moves, left = refile_translation(doc, self.GRC)
        self.assertEqual([(i.n, i.text) for i in doc.items if hasattr(i, "n")], [
            ("105", "like some mournful bird,"), ("109", "by her anxious bed."),
            ("112", "For just as one may see billow after billow"), ("876", "Surely she is not dead?"),
            ("876a", "My tale is told."), ("881", "She destroyed herself."), ("881b", "What impulse drove her?"),
            ("977a", "Is he alive?")])
        # the speakers stay where they were, none lost or doubled
        self.assertEqual(serialize(doc).count("@ "), self.TR.count("@ "))
        self.assertEqual(len(moves), 6)
        self.assertEqual(left, ["translation: 881b left as it is (grc.txt has 1 part(s) of verse 881)"])
        # (the letters follow Perseus's convention, so the step must start from Perseus's file,
        # never from its own output: write_translation always does)

    def test_join_to_the_segment_of_the_covering_verse(self):
        doc = parse("@ Chorus\n112\tFor just as\n113\tbillow after billow\n@ Nurse\n115\tNo.\n", "t")
        moves, left = refile_translation(doc, ["112", "115"])
        self.assertEqual(serialize(doc), "@ Chorus\n112\tFor just as billow after billow\n\n@ Nurse\n115\tNo.\n")
        self.assertEqual((len(moves), left), (1, []))

    def test_no_join_across_a_change_of_speaker(self):
        # the later segment takes the next verse (where the build would show it), the order kept
        doc = parse("112\tA.\n@ Nurse\n113\tB.\n", "t")
        moves, left = refile_translation(doc, ["110", "112", "114"])
        self.assertEqual(moves, [])
        self.assertEqual([i.n for i in doc.items if hasattr(i, "n")], ["112", "114"])
        self.assertEqual(serialize(doc).count("@ Nurse"), 1)
        self.assertEqual(len(left), 1)

    def test_numbers_that_name_other_verses(self):
        # Perseus counts 886-888 where the print has 887-889 (our 885 covers 886): the Nurse's
        # "By a stroke …" (Perseus 886) begins a speech, our 885 does not; the word map puts it at
        # 887, and the two segments after it, which land on verses already taken across a change
        # of speaker, follow on to 888 and 889
        doc = parse("@ Chorus\n885\tthis death upon death?\n@ Nurse\n886\tBy a stroke of the sword.\n"
                    "@ Chorus\n887\tDid you witness it?\n@ Nurse\n888\tI did.\n@ Chorus\n890\tWhat was it?\n", "t")
        numbers = ["883", "885", "887", "888", "889", "890"]
        starts = {"883", "887", "888", "889", "890"}
        perseus = {"885": "885", "886": "887", "887": "888", "888": "889", "890": "890"}
        moves, left = refile_translation(doc, numbers, starts, perseus.get)
        self.assertEqual([(i.n, i.text) for i in doc.items if hasattr(i, "n")], [
            ("885", "this death upon death?"), ("887", "By a stroke of the sword."), ("888", "Did you witness it?"),
            ("889", "I did."), ("890", "What was it?")])
        self.assertEqual(serialize(doc).count("@ "), 5)
        # without the word map, the nearest earlier verse (and the order rule) only
        doc = parse("@ Chorus\n885\tA.\n@ Nurse\n886\tB.\n", "t")
        refile_translation(doc, numbers)
        self.assertEqual([i.n for i in doc.items if hasattr(i, "n")], ["885", "887"])

    def test_fixed_numbers(self):
        # TRANSLATION_NUMBERS: Perseus's 211-214 are the print's 212-212c; a "…" for a lost verse
        # our text has no line for is dropped with its speaker; the rest by the rules
        doc = parse("@ Chorus\n180a\tLead him onward.\n@ Antigone\n181a\t…\n@ Antigone\n181c\tCome, follow.\n"
                    "@ Chorus\n211\tWhat does this mean?\n@ Oedipus\n212\tHorrid the birth—\n"
                    "@ Chorus\n213\tSpeak!\n@ Oedipus\n214\tMy child!\n@ Chorus\n215\tWhat is your lineage?\n", "t")
        numbers = ["180a", "181", "182", "210", "212", "212a", "212b", "212c", "215"]
        fixed = {"181a": None, "181c": "182", "211": "212", "212": "212a", "213": "212b", "214": "212c"}
        moves, left = refile_translation(doc, numbers, fixed=fixed)
        self.assertEqual([(i.n, i.text) for i in doc.items if hasattr(i, "n")], [
            ("180a", "Lead him onward."), ("182", "Come, follow."), ("212", "What does this mean?"),
            ("212a", "Horrid the birth—"), ("212b", "Speak!"), ("212c", "My child!"), ("215", "What is your lineage?")])
        self.assertEqual(left, [])
        self.assertEqual(serialize(doc).count("@ Antigone"), 1)


if __name__ == "__main__":
    unittest.main()


class LabelParts(unittest.TestCase):
    """Each top-level section takes the division in which most of its verses fall."""

    def test_majority_not_first_line(self):
        from anagnosis_pipeline.sophocles import PLAYS, label_parts
        from anagnosis_pipeline.textfmt import Section

        def sec(kind, numbers):
            return [Section(1, kind, "x")] + [Line(str(n), "…") for n in numbers]

        # Perseus's boundaries a verse early: 462 (in the First episode) heads the stasimon,
        # 512 (in the First stasimon) heads the Second episode; the kommos 649-697 lies inside it
        doc = Document(items=sec("episode", range(216, 462)) + sec("choral", range(462, 512))
                       + sec("episode", range(512, 649)) + sec("choral", range(649, 698))
                       + sec("episode", range(698, 863)))
        label_parts(doc, PLAYS["oedipustyrannus"])
        labels = [i.label for i in doc.items if isinstance(i, Section)]
        self.assertEqual(labels, ["First episode", "First stasimon", "Second episode",
                                  "Second episode (continued)", "Second episode (continued)"])

    def test_a_division_named_nowhere_keeps_its_section(self):
        from anagnosis_pipeline.sophocles import PLAYS, label_parts
        from anagnosis_pipeline.textfmt import Section

        def sec(kind, numbers):
            return [Section(1, kind, "x")] + [Line(str(n), "…") for n in numbers]

        # Electra: the third stasimon 1384-1397 and the kommos 1398-1441 in one section
        doc = Document(items=sec("episode", range(1288, 1384)) + sec("choral", range(1384, 1442))
                       + sec("episode", range(1442, 1511)))
        label_parts(doc, PLAYS["electra"])
        labels = [i.label for i in doc.items if isinstance(i, Section)]
        self.assertEqual(labels, ["Third episode", "Third stasimon", "Exodos"])


class MergeRepeatedSubsections(unittest.TestCase):
    def test_one_heading_per_stanza(self):
        from anagnosis_pipeline.sophocles import merge_repeated_subsections
        from anagnosis_pipeline.textfmt import Section, Speaker

        # Philoctetes 1169-1182: Perseus's "epode" at every change of speaker; a new top-level
        # section or another stanza ends the run
        items = [Section(1, "choral", "Second kommos"), Section(2, "antistrophe", "2"), Line("1168", "…"),
                 Section(2, "epode", ""), Speaker("Φιλοκτήτης"), Line("1169", "…"),
                 Section(2, "epode", ""), Speaker("Χορός"), Line("1173", "…"),
                 Section(2, "epode", ""), Speaker("Φιλοκτήτης"), Line("1173a", "…"),
                 Section(1, "episode", "Exodos"), Section(2, "epode", ""), Line("1218", "…"),
                 Section(2, "strophe", "1"), Line("1219", "…"), Section(2, "strophe", "2"), Line("1220", "…")]
        doc = Document(items=items)
        self.assertEqual(merge_repeated_subsections(doc), 2)
        seq = [(i.kind, i.label) if isinstance(i, Section) else getattr(i, "n", getattr(i, "name", ""))
               for i in doc.items]
        self.assertEqual(seq, [("choral", "Second kommos"), ("antistrophe", "2"), "1168", ("epode", ""),
                               "Φιλοκτήτης", "1169", "Χορός", "1173", "Φιλοκτήτης", "1173a",
                               ("episode", "Exodos"), ("epode", ""), "1218", ("strophe", "1"), "1219",
                               ("strophe", "2"), "1220"])


class NumberingSuspectsUnbolded(unittest.TestCase):
    def test_murray_items_without_a_lemma_mark(self):
        # Murray's items mostly lack "]": the first Greek words are the lemma (unbolded=True)
        # made-up verses and items (nothing of Murray's own text or apparatus in a public file)
        lines = [("10", "ἄνδρες πολῖται χαίρετε"), ("11", "λόγος δὲ τοῦδε μακρός"), ("12", "ἐγὼ δʼ ἀπειμι νῦν")]
        app = "## 10\nχαίρετε A B: χαίρετʼ C\n\n## 12\nτοῦδε A: τοῦ B\n"
        self.assertEqual(numbering_suspects(lines, app), [])
        items = numbering_suspects(lines, app, unbolded=True)
        self.assertEqual([(i["kind"], i["note"], i["lemma"], i["found"]) for i in items], [("lemma", "12", "τοῦδε", "11")])


class AlignPartStarts(unittest.TestCase):
    def test_section_begun_at_a_subsection(self):
        from anagnosis_pipeline.sophocles import align_part_starts, label_parts
        from anagnosis_pipeline.textfmt import Section, Speaker

        class P:  # the Alcestis: the third stasimon 962 inside Perseus's choral section from 861
            parts = [(1, "Third episode"), (962, "Third stasimon")]
        items = ([Section(1, "choral", ""), Speaker("Χορός"), Line("861", "…"), Line("961", "…"),
                  Section(2, "strophe", "1"), Speaker("Χορός"), Line("962", "…")])
        doc = Document(items=items)
        self.assertEqual(align_part_starts(doc, P), ["section choral begun at 962 (Jebb's Third stasimon)"])
        label_parts(doc, P)
        self.assertEqual([(i.kind, i.label) for i in doc.items if isinstance(i, Section)],
                         [("choral", "Third episode"), ("choral", "Third stasimon"), ("strophe", "1")])

    def test_section_moved_before_a_lyric_subsection(self):
        from anagnosis_pipeline.sophocles import align_part_starts, label_parts
        from anagnosis_pipeline.textfmt import Section, Speaker

        class P:  # Earle's Medea: the parodos at 131, Perseus's choral section from 96
            parts = [(1, "Prologue"), (131, "Parodos")]
        items = ([Section(1, "episode", ""), Speaker("Τροφός"), Line("95", "…"), Section(1, "choral", ""),
                  Section(2, "anapests", ""), Speaker("Μήδεια"), Line("96", "…"), Line("130", "…"),
                  Section(2, "lyric", ""), Speaker("Χορός"), Line("131", "…")])
        doc = Document(items=items)
        self.assertEqual(len(align_part_starts(doc, P, window=40)), 1)
        seq = [type(i).__name__ + ":" + getattr(i, "n", getattr(i, "name", getattr(i, "kind", ""))) for i in doc.items]
        self.assertEqual(seq[-5:], ["Line:130", "Section:choral", "Section:lyric", "Speaker:Χορός", "Line:131"])
        label_parts(doc, P)
        self.assertEqual([i.label for i in doc.items if isinstance(i, Section) and i.level == 1], ["Prologue", "Parodos"])

    def test_section_moved_to_the_division_start(self):
        from anagnosis_pipeline.sophocles import PLAYS, align_part_starts, label_parts
        from anagnosis_pipeline.textfmt import Section, Speaker

        # OC: the Third episode begins at 1096 (the Chorus's trimeters), Perseus's section at 1099;
        # the antistrophe of the stasimon ends with 1095
        items = ([Section(1, "choral", ""), Section(2, "antistrophe", "2"), Speaker("Χορός")]
                 + [Line(str(n), "…") for n in range(1090, 1099)]
                 + [Section(1, "episode", ""), Speaker("Οἰδίπους"), Line("1099", "…"), Line("1100", "…")])
        doc = Document(items=items)
        moves = align_part_starts(doc, PLAYS["oedipuscoloneus"])
        self.assertEqual(moves, ["section episode moved from 1099 to 1096 (Jebb's Third episode)"])
        seq = [(type(i).__name__, getattr(i, "n", getattr(i, "name", getattr(i, "kind", "")))) for i in doc.items]
        k = seq.index(("Section", "episode"))
        self.assertEqual(seq[k - 1], ("Line", "1095"))
        self.assertEqual(seq[k + 1:k + 3], [("Speaker", "Χορός"), ("Line", "1096")])
        self.assertEqual(seq[-4:], [("Line", "1098"), ("Speaker", "Οἰδίπους"), ("Line", "1099"), ("Line", "1100")])
        label_parts(doc, PLAYS["oedipuscoloneus"])
        self.assertEqual([i.label for i in doc.items if isinstance(i, Section) and i.level == 1],
                         ["Second stasimon", "Third episode"])
        # safe to run again; a section already at its division is left alone
        self.assertEqual(align_part_starts(doc, PLAYS["oedipuscoloneus"]), [])

    def test_section_too_far_or_later_moved_forward(self):
        from anagnosis_pipeline.sophocles import PLAYS, align_part_starts
        from anagnosis_pipeline.textfmt import Section, Speaker

        # a section beginning a verse before the division (718 for 719) moves on to it; the
        # verse left behind joins the section before
        items = ([Section(1, "choral", ""), Speaker("Χορός"), Line("716", "…"), Line("717", "…"),
                  Section(1, "episode", ""), Speaker("Χορός"), Line("718", "…"), Speaker("Ἄγγελος"), Line("719", "…")])
        doc = Document(items=items)
        self.assertEqual(align_part_starts(doc, PLAYS["ajax"]),
                         ["section episode moved from 718 to 719 (Jebb's Third episode)"])
        seq = [type(i).__name__ + ":" + getattr(i, "n", getattr(i, "name", getattr(i, "kind", ""))) for i in doc.items]
        self.assertEqual(seq[4:], ["Speaker:Χορός", "Line:718", "Section:episode", "Speaker:Ἄγγελος", "Line:719"])


class PlainHeading(unittest.TestCase):
    def test_no_italics_markers_or_backslashes(self):
        from anagnosis_pipeline.sophocles import plain_heading
        self.assertEqual(plain_heading("## § 18 — The *Oedipus* of Seneca."), "## § 18 — The Oedipus of Seneca.")
        self.assertEqual(plain_heading("### § 1. *Opening* Scene\\_"), "### § 1. Opening Scene")


class TranslationStages(unittest.TestCase):
    def test_stage_inside_a_verse_set_apart_and_milestone_space(self):
        import tempfile
        from pathlib import Path

        from anagnosis_pipeline.import_perseus import tei_to_document
        from anagnosis_pipeline.sophocles import split_translation_stages
        from anagnosis_pipeline.textfmt import Speaker, Stage

        xml = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="textpart" subtype="section" n="1">
<sp><speaker>Philoctetes</speaker>
<l n="1215">for leaving your sacred stream! I am nothing now!  <stage rend="italic">Exit Philoctetes into the cave.</stage>
</l></sp>
<sp><speaker>Antigone</speaker><l n="1270">but can never be made worse.<milestone unit="para"/>Why are you silent?</l></sp>
</div></body></text></TEI>"""
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / "eng.xml"
            path.write_text(xml, encoding="utf-8")
            doc = tei_to_document(path, {})
            changes = split_translation_stages(doc, path)
        seq = [(type(i).__name__, getattr(i, "text", getattr(i, "name", ""))) for i in doc.items
               if not type(i).__name__ == "Section"]
        self.assertEqual(seq, [("Speaker", "Philoctetes"), ("Line", "for leaving your sacred stream! I am nothing now!"),
                               ("Stage", "Exit Philoctetes into the cave."), ("Speaker", "Antigone"),
                               ("Line", "but can never be made worse. Why are you silent?")])
        self.assertEqual(len(changes), 2)
