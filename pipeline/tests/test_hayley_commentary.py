"""Hayley's commentary and introduction for the Alcestis (drama_prose, notes_layout "hayley"), and
the checker's report of a Latin capital standing as Homer's book letter. Made-up lines only:
nothing of Murray's text."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from anagnosis_pipeline import drama_prose
from anagnosis_pipeline.drama_prose import homer_latin_letters


class Notes(unittest.TestCase):
    def test_headings(self):
        from anagnosis_pipeline.drama import HAYLEY_NOTE, note_heading
        self.assertEqual(note_heading("Verse 1. Scene", HAYLEY_NOTE), ("1", 8))
        self.assertEqual(note_heading("28-37. The system", HAYLEY_NOTE)[0], "28-37")
        self.assertEqual(note_heading("86 ff. x", HAYLEY_NOTE)[0], "86")

    def test_further_lemmas_cut(self):
        self.assertEqual(drama_prose.hayley_split("ὁδός : way, as Ant. 3 ὁδὸν ἄγει. λόγος : word.", first=True),
                         ["**ὁδός**: way, as Ant. 3 ὁδὸν ἄγει.", "**λόγος**: word."])
        # Greek quoted after a reference's figure, before a colon, is no lemma
        self.assertEqual(drama_prose.hayley_split("Cf. Ant. 4 ὁδὸς ἄγει : Hipp. 10. λόγος : word."),
                         ["Cf. Ant. 4 ὁδὸς ἄγει : Hipp. 10.", "**λόγος**: word."])
        # nor Greek after sc. (his gloss, before a colon)
        self.assertEqual(drama_prose.hayley_split("ὁδός : sc. ὁδὸν ἐλθεῖν : the word. λόγος : word.", first=True),
                         ["**ὁδός**: sc. ὁδὸν ἐλθεῖν : the word.", "**λόγος**: word."])
        # a note that begins in English keeps no bold
        self.assertEqual(drama_prose.hayley_split("Wakefield reads ὁδόν.", first=True), ["Wakefield reads ὁδόν."])

    def test_clean(self):
        self.assertEqual(drama_prose.hayley_clean("a -- b ¢word’ ὁδός :: so"), "a — b ‘word’ ὁδός : so")

    def test_gap_dots_not_cut(self):
        self.assertEqual(drama_prose.hayley_split("εἰ τὴν ὁδὸν . . . γυναῖκ᾽ : a taunt.", first=True),
                         ["**εἰ τὴν ὁδὸν . . . γυναῖκ᾽**: a taunt."])

    def test_his_order_going_back_kept(self):
        # 42, 44, then 41 (his order goes back a little: kept), then 2 (far below: a reference
        # at a paragraph's start, back into the text), then 45
        pages = [{"md": "", "cands": []}]
        for n in ("42", "44", "41", "2", "45"):
            c = pages[0]["cands"]
            c.append({"kind": "note", "n": n, "body": [f"text {n}."], "orig": [f"{n}. text {n}."],
                      "back": drama_prose.HAYLEY_BACK})
            pages[0]["md"] += f"\x00{len(c) - 1}\n\n"
        drama_prose._resolve_note_headings(pages, 1163)
        heads = [l for l in pages[0]["md"].split("\n") if l.startswith("## ")]
        self.assertEqual(heads, ["## 42", "## 44", "## 41", "## 45"])
        self.assertIn("2. text 2.", pages[0]["md"])


class HomerLetters(unittest.TestCase):
    def test_latin_capitals_reported(self):
        self.assertEqual(homer_latin_letters("cp. Hom. A 282 and B 3."), ["A 282", "B 3"])
        self.assertEqual(homer_latin_letters("Hom. Il. A 282, Β 5 f., K 34"), ["A 282", "K 34"])
        self.assertEqual(homer_latin_letters("as Homer O 545 has it"), ["O 545"])

    def test_greek_letters_and_other_references_pass(self):
        for text in ("Il. Ζ 146, Ι 63", "Od. ε 264", "Hom. Α 282", "Il. 9. 63", "Od. xi 34", "see Il. ix. 63",
                     "Soph. O. C. 1138", "Ant. 173 f."):
            self.assertEqual(homer_latin_letters(text), [], text)

    def test_roman_numeral_read_as_greek_reported(self):
        from anagnosis_pipeline.drama_prose import homer_greek_numerals
        self.assertEqual(homer_greek_numerals("so Od. ΧΙ. 253 and Il. XΙΙ. 3"), ["Od. ΧΙ", "Il. XΙΙ"])
        for text in ("Od. XI. 253", "Il. Χ 63", "Il. Ι 63", "Il. Ζ 146"):
            self.assertEqual(homer_greek_numerals(text), [], text)

    def test_check_prose_reports_it(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            out = root / "build" / "drama-prose" / "medea"
            out.mkdir(parents=True)
            (out / "notes.json").write_text(json.dumps([{"stem": "p-0100", "batch": 1}]), encoding="utf-8")
            batch = root / "notes-01.md"
            batch.write_text("=== p-0100\n## 20\n**ἡμέρα**: so Hom. A 282 and Il. Ζ 146.\n--- flags\n--- notes\n",
                             encoding="utf-8")
            with mock.patch.object(drama_prose, "PIPELINE", root):
                remarks = drama_prose.check_prose("medea", "notes", batch, root / "texts")
        self.assertEqual(len([r for r in remarks if "Latin capital" in r]), 1, remarks)
        self.assertIn("A 282", " ".join(remarks))


NOTES = """=== p-0159
## 1
Scene in front of the palace.

**ὦ δῶμα**: the address.

## 3
**γγ**: on a line our text lacks.
--- flags
1 δῶμα [accent] → ok
--- notes
=== p-0160
+ runs on here.

## 4
**ζζ**: the last.
--- flags
--- notes
"""

INTRO = """=== p-10021
# Introduction

# A. The Myth of Alcestis

Few Greek myths.
--- flags
--- notes
=== p-20054
# The ancient hypotheses

## ΥΠΟΘΕΣΙΣ

αα ββ.
--- flags
--- notes
=== p-30056
# The persons of the drama

ΑΠΟΛΛΩΝ · ΘΑΝΑΤΟΣ
--- flags
--- notes
"""


class Merge(unittest.TestCase):
    def test_commentary_and_introduction(self):
        from anagnosis_pipeline.drama import PLAYS, write_prose_documents
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            tr, out, build = root / "tr", root / "texts" / "alcestis", root / "build"
            for d in (tr, out, build):
                d.mkdir(parents=True)
            (tr / "notes-01.md").write_text(NOTES, encoding="utf-8")
            (tr / "intro-01.md").write_text(INTRO, encoding="utf-8")
            problems = []
            write_prose_documents(PLAYS["alcestis"], tr, out, [("1", "αα"), ("2", "ββ"), ("4", "ζζ")], build, problems)
            text = (out / "commentary-hayley.md").read_text(encoding="utf-8")
            intro = (out / "introduction.md").read_text(encoding="utf-8")
        self.assertIn("# title: Commentary (Harry Wilson Hayley)", text)
        self.assertIn("scan alcestisofeuripi00euriuoft", text)
        self.assertIn("## 1\nScene in front of the palace.\n\n**ὦ δῶμα**: the address.", text)
        self.assertIn("## 2\n[3] **γγ**: on a line our text lacks. runs on here.", text)
        head = intro.split("\n")
        self.assertEqual(head[1], "# author: Harry Wilson Hayley; G. Murray (the ancient hypotheses and the persons)")
        self.assertIn("the introduction (Internet Archive scan alcestisofeuripi00euriuoft)", head[2])
        self.assertNotIn("notes on the hypothesis", head[2])
        self.assertIn("from 1 January 2028", head[3])  # Murray's hypotheses and persons stand in it
        self.assertLess(intro.index("# A. The Myth"), intro.index("# The ancient hypotheses"))
        self.assertLess(intro.index("# The ancient hypotheses"), intro.index("# The persons of the drama"))


class Omit(unittest.TestCase):
    def test_stretch_left_out_and_marker(self):
        from anagnosis_pipeline.drama import Play
        play = Play("x", "", "", "", "", "", "", "scan", "m", "M", "p",
                    prose_omit=[("scan", 53, r"^The editions", r"^Barnes", ""), ("scan", 58, "", r"^ed\. IV", "[list of editions omitted]")])
        def lines(*texts):
            return [{"words": [{"text": w} for w in t.split()]} for t in texts]
        kept = drama_prose._omit(play, "scan", 53, lines("of the scholia.", "The editions of the play", "1. Aldine,", "Barnes’ comments"))
        self.assertEqual([" ".join(w["text"] for w in l["words"]) for l in kept], ["of the scholia."])
        self.assertFalse(any(l.get("omit_after") or l.get("omit_before") for l in kept))
        kept = drama_prose._omit(play, "scan", 58, lines("Mnemosyne V.", "ed. IV. p. 70 f., etc.", "D. QUESTIONS"))
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["omit_before"], "[list of editions omitted]")
        # another leaf, or another scan: nothing left out
        self.assertEqual(len(drama_prose._omit(play, "other", 58, lines("a", "ed. IV. p. 70"))), 2)


if __name__ == "__main__":
    unittest.main()
