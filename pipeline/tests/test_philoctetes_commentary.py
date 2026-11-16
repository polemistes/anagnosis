"""Jebb's commentary on the Philoctetes, which Perseus lacks: read by the prose OCR route (kind
notes, the two columns under the rule of every page) and written by sophocles-prose as
commentary-jebb.md from the checked notes batches (sophocles.write_transcribed_commentary), then
re-filed as the other plays' commentary is; and the draft's mechanical help (drama_prose)."""
import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.drama import PLAYS as DRAMA
from anagnosis_pipeline.drama_prose import _resolve_note_headings, jebb_dashes, jebb_f, jebb_lemma, split_lemmas
from anagnosis_pipeline.sophocles import PROSE_HOW, write_prose, write_transcribed_commentary

NOTES_1 = """=== p-0120
Scene:—*A lonely place on the N.E. coast of Lemnos.*

## 249
**ἢ γὰρ** in eager question: 322, *O. C.* 64.

**ἐγὼ** with emphasis: cp. 1213.
--- flags
1 7) [greek] → ἢ
--- notes

=== p-0121
## 255
**οὐ μηδὲ** κ.τ.λ., a man of whom no report (the generic μή, 170 n.) had come.

**οἴκαδε**, to Malis (4 n.),—where the tidings would have had a special inter-
--- flags
--- notes
"""
NOTES_2 = """=== p-0122
+ est: μηδʼ Ἑλλάδος γῆς.

## 264-269
These verses describe the putting ashore, ¯˘˘¯.

## 1471
**νόστου**, said by the Chorus.
--- flags
1 vóorov [greek] → νόστου
--- notes
"""
GRC = """# title: Φιλοκτήτης

@ Φιλοκτήτης
249	ἦ γὰρ μετέσχες καὶ σὺ τοῦδε τοῦ πόνου;
250	οὐ γάρ σʼ ἔγωγʼ οἶδʼ ὅντινʼ εἰσορῶ ποτέ.
254	ὦ πόλλʼ ἐγὼ μοχθηρός, ὦ πικρὸς θεοῖς,
256	ἀλλʼ οἱ μὲν ἐκβαλόντες ἀνοσίως ἐμὲ
264	ἐγώ σʼ ἐκεῖνός εἰμι, ὃν κλύεις ἴσως
268	ὁ δῆτʼ ἐκεῖνος πρὸς τὸ λοιπὸν ἦν
1471	νόστου τοῦδʼ ἐπαρωγούς.
"""


class TranscribedCommentary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.sources, self.texts, self.tr = root / "sources", root / "texts", root / "tr"
        for d in (self.sources, self.texts / "philoctetes", self.tr):
            d.mkdir(parents=True)
        (self.tr / "notes-01.md").write_text(NOTES_1, encoding="utf-8")
        (self.tr / "notes-02.md").write_text(NOTES_2, encoding="utf-8")
        (self.texts / "philoctetes" / "grc.txt").write_text(GRC, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_written_with_the_header_and_refiled(self):
        self.assertEqual(write_prose("philoctetes", self.sources, self.texts, self.tr), 0)
        text = (self.texts / "philoctetes" / "commentary-jebb.md").read_text(encoding="utf-8")
        self.assertEqual(text, "\n".join([
            "# title: Commentary on Sophocles: Philoctetes",
            "# author: Richard C. Jebb",
            "# lang: eng",
            "# source: Sophocles: The Plays and Fragments, Part IV: The Philoctetes, ed. R. C. Jebb, Cambridge "
            "University Press, second edition 1898, reprinted 1914; Internet Archive playsfragmentswi04sophuoft "
            f"(University of Toronto), {PROSE_HOW}",
            "# license: CC BY-SA 4.0 (transcription; the edition is in the public domain)",
            "",
            # what stands before the first number goes under the first heading
            "## 249",
            "Scene:—*A lonely place on the N.E. coast of Lemnos.*",
            "",
            "**ἢ γὰρ** in eager question: 322, *O. C.* 64.",
            "",
            "**ἐγὼ** with emphasis: cp. 1213.",
            "",
            # 255 is not a line of ours: filed under 256, which holds no word of the lemma, so
            # under the nearest earlier line, the printed number in front
            "## 254",
            "[255] **οὐ μηδὲ** κ.τ.λ., a man of whom no report (the generic μή, 170 n.) had come.",
            "",
            # run on over the page; the elision after a Greek letter as in the other plays' files
            "**οἴκαδε**, to Malis (4 n.),—where the tidings would have had a special interest: μηδ’ Ἑλλάδος γῆς.",
            "",
            # a range whose end we lack ends at the last line we have inside it; the metrical
            # scheme in metrical signs
            "## 264-268",
            "These verses describe the putting ashore, –⏑⏑–.",
            "",
            "## 1471",
            "**νόστου**, said by the Chorus.",
            "",
        ]))
        # again: the same file
        write_prose("philoctetes", self.sources, self.texts, self.tr)
        self.assertEqual((self.texts / "philoctetes" / "commentary-jebb.md").read_text(encoding="utf-8"), text)

    def test_not_written_until_every_flag_is_answered(self):
        (self.tr / "notes-02.md").write_text(NOTES_2.replace("→ νόστου", "→"), encoding="utf-8")
        self.assertEqual(write_transcribed_commentary("philoctetes", self.texts, self.tr), -1)
        self.assertFalse((self.texts / "philoctetes" / "commentary-jebb.md").exists())
        self.assertEqual(write_prose("philoctetes", self.sources, self.texts, self.tr), 1)

    def test_two_notes_on_one_number_are_one_note(self):
        # "927 ff." at the foot of one page and "927 πῦρ" at the top of the next: one `## 927`
        (self.tr / "notes-02.md").write_text(NOTES_2.replace("## 264-269", "## 255"), encoding="utf-8")
        write_transcribed_commentary("philoctetes", self.texts, self.tr)
        text = (self.texts / "philoctetes" / "commentary-jebb.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("## 255"), 1)
        self.assertIn("## 255\n**οὐ μηδὲ**", text)
        self.assertIn("μηδ’ Ἑλλάδος γῆς.\n\nThese verses describe", text)

    def test_no_batches(self):
        for p in self.tr.glob("notes-*.md"):
            p.unlink()
        self.assertEqual(write_transcribed_commentary("philoctetes", self.texts, self.tr), 0)
        self.assertFalse((self.texts / "philoctetes" / "commentary-jebb.md").exists())


class FootnoteRest(unittest.TestCase):
    def test_rest_of_a_footnote_joined(self):
        from anagnosis_pipeline.sophocles import join_footnote_rests

        paras = ["text ¹", "[Note: ¹ Each chief has his own men. And Neoptolemus can propose to]", "## § 10",
                 "more text", "[Note: sail with Philoctetes, for Malis (1402 ff.).]",
                 "[Note: cp. Plato, *Legg.* 967 A.]"]
        self.assertEqual(join_footnote_rests(paras), [
            "text ¹", "[Note: ¹ Each chief has his own men. And Neoptolemus can propose to sail with Philoctetes, "
            "for Malis (1402 ff.).]", "## § 10", "more text",
            # the footnote before ends with a stop: a footnote of its own
            "[Note: cp. Plato, *Legg.* 967 A.]"])
        self.assertEqual(join_footnote_rests(["a", "[Note: di-]", "[Note: vided word.]"]), ["a", "[Note: divided word.]"])


class Draft(unittest.TestCase):
    def test_play_entry(self):
        play = DRAMA["philoctetes"]
        self.assertEqual(play.leaves("notes"), list(range(76, 298)))
        self.assertEqual((play.notes_editor, play.app_rule, play.layout), ("jebb", "under", "jebb"))
        self.assertEqual(DRAMA["clouds"].app_rule, "")  # the Clouds keeps its own region

    def test_dashes_and_lemmas(self):
        self.assertEqual(jebb_dashes("vv. 264--269 R. ; πόλιν.---ἀλμέμπτως"), "vv. 264—269 R. ; πόλιν.—ἀλμέμπτως")
        self.assertEqual(jebb_dashes("cp. O. 7. 638 and Ο. C. 792"), "cp. *O. T.* 638 and *O. C.* 792")
        self.assertEqual(jebb_f("258 ΖΦ. σῖγʼ ἔχοντες"), "258 f. σῖγʼ ἔχοντες")
        self.assertEqual(jebb_f("1153 £f. ἀλλʼ"), "1153 ff. ἀλλʼ")
        self.assertEqual(jebb_lemma("ἔα κακῶς κ.τ.λ. The absence"), "**ἔα κακῶς** κ.τ.λ. The absence")
        self.assertEqual(split_lemmas("this constraint on thee.—ἐμᾶς, Bergk’s correction: cp. 1095 ff.—Not so."),
                         ["this constraint on thee.", "**ἐμᾶς**, Bergk’s correction: cp. 1095 ff.—Not so."])
        self.assertEqual(split_lemmas("πότμος...δαιμόνων: Ant. 157", first=True), ["**πότμος...δαιμόνων**: Ant. 157"])

    def test_note_headings_settled_over_the_pages(self):
        def cand(n, body, orig):
            return {"kind": "note", "n": n, "body": [body], "orig": [orig]}

        pages = [{"md": "\x000\n\nmore\n\n\x001", "cands": [cand("249", "**ἢ γὰρ** x", "249 ἢ γὰρ x"),
                                                         cand("2555", "**οὐ** y", "2555. οὐ y")]},
                 {"md": "\x000\n\n\x001\n\n\x002", "cands": [cand("117", "ἐπὶ μεῖζον", "117 ἐπὶ μεῖζον"),
                                                           cand("258-259", "**σίγ’** z", "258 f. σίγ’ z"),
                                                           cand("1760", "w", "1760 w")]}]
        _resolve_note_headings(pages, 1471)
        self.assertEqual(pages[0]["md"], "## 249\n**ἢ γὰρ** x\n\nmore\n\n## 255\n**οὐ** y")
        # 117 is lower than the last note, 1760 beyond the play: back into the text as read
        self.assertEqual(pages[1]["md"], "117 ἐπὶ μεῖζον\n\n## 258-259\n**σίγ’** z\n\n1760 w")

    def test_one_misread_number_does_not_shut_out_the_rest(self):
        # "30" read "80" (old-style 3 for 8): the sequence 29, 30, 31, 32 wins over 29, 80
        def cand(n):
            return {"kind": "note", "n": n, "body": [f"note {n}"], "orig": [f"{n} as read"]}

        pages = [{"md": "\n\n".join(f"\x00{k}" for k in range(5)), "cands": [cand(x) for x in ("29", "80", "31", "32", "33")]}]
        _resolve_note_headings(pages, 1471)
        self.assertEqual([l for l in pages[0]["md"].split("\n") if l.startswith("## ")], ["## 29", "## 30", "## 31", "## 32", "## 33"])


if __name__ == "__main__":
    unittest.main()


class JebbAsterisks(unittest.TestCase):
    def test_conjecture_mark_escaped_italics_kept(self):
        from anagnosis_pipeline.sophocles import escape_jebb_asterisks

        self.assertEqual(escape_jebb_asterisks("**ὦ παλάμαι *θεῶν**: the ‘devices’ … cp. *Ant.* 360"),
                         "**ὦ παλάμαι \\*θεῶν**: the ‘devices’ … cp. *Ant.* 360")
        self.assertEqual(escape_jebb_asterisks("**τῶνδ’ *οὑκ μελάθρων**. For ἐκ, *i.e.*, the cave"),
                         "**τῶνδ’ \\*οὑκ μελάθρων**. For ἐκ, *i.e.*, the cave")
        # already escaped, and an asterisk closing italics before Greek, are left alone
        self.assertEqual(escape_jebb_asterisks("**\\*ὀρεία δ’**, S. Mekler’s *conj.*θ"),
                         "**\\*ὀρεία δ’**, S. Mekler’s *conj.*θ")
