"""Earle's commentary and introduction for the Medea (drama_prose, notes_layout "earle"): the region
under the verses, the notes that run on inside paragraphs, the introduction read from two scans,
and the merge of the checked batches (drama.write_prose_documents). Made-up lines only: nothing
of Murray's text."""
import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.drama import PLAYS, write_prose_documents
from anagnosis_pipeline.drama_prose import (_resolve_note_headings, earle_clean, earle_markdown, earle_top,
                                            page_stem, EARLE_WINDOW)


def line(x0, y0, x1, y1, text, size):
    words = text.split()
    step = (x1 - x0) / max(1, len(words))
    return {"bbox": [x0, y0, x1, y1], "x_size": size,
            "words": [{"text": w, "bbox": [int(x0 + i * step), y0, int(x0 + (i + 1) * step - 8), y1], "conf": 95}
                      for i, w in enumerate(words)]}


class Region(unittest.TestCase):
    def test_commentary_begins_under_the_verses(self):
        body = [line(260, 470, 1120, 540, "αα ββ γγ δδ εε", 48), line(260, 540, 1040, 600, "ζζ ηη θθ ιι", 46),
                # a short lyric verse left of the gutter, and its margin number at the right
                line(300, 610, 600, 660, "κκ λλ", 47), line(1170, 615, 1220, 650, "445", 34)]
        for k in range(6):
            y = 700 + 43 * k
            body += [line(130, y, 655, y + 35, f"left column words {k}", 35),
                     line(700, y, 1225, y + 35, f"right column words {k}", 35)]
        top = earle_top(body, 1338)
        self.assertTrue(660 <= top <= 700, top)

    def test_no_columns_whole_page(self):
        self.assertEqual(earle_top([line(260, 470, 1120, 540, "αα ββ γγ", 48)], 1338), 0)


class Notes(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(earle_clean("a — b --- c 455- 458. ¢x’ 2.6. ἐπεί, 56. μέρος"),
                         "a — b — c 455-458. ‘x’ *i.e.* ἐπεί, sc. μέρος")

    def test_numbers_inside_a_paragraph(self):
        cands = []
        text = earle_clean("we have ὡς with οὐδέν. 453. Of course the μέν clause. See v. 450. 459. κἀκ τῶνδ᾽ : a "
                           "redundant word. — τοιγάρ : *i.e.* thus. Pindar (Pyth. 4. 209) calls. ἡ. Κόλχων : these")
        md = earle_markdown(text, cands, "+ ")
        self.assertEqual(md[0], "+ we have ὡς with οὐδέν.")
        # v. 450 is a reference (after "v."), Pyth. 4 one (a figure follows); "ἡ." is the figure 2
        self.assertEqual([c["n"] for c in cands], ["453", "459", "2"])
        self.assertEqual(cands[1]["body"], ["**κἀκ τῶνδ᾽**: a redundant word.", "**τοιγάρ**: *i.e.* thus. Pindar (Pyth. 4. 209) calls."])
        self.assertEqual(cands[2]["body"], ["**Κόλχων**: these"])
        self.assertTrue(all(c["join"] for c in cands))

    def test_sequence_and_join(self):
        # three pages: 20, then a reference that looks like a note (480) and 21 f., then 22; the
        # number out of the sequence goes back into its paragraph
        pages = []
        for texts, lead in ((["20. ἡμέρα : the day."], ""), (["as said. 480. Not a note. 21 f. λόγος : word."], "+ "),
                            (["22. ὁδός : way."], "")):
            cands = []
            md = []
            for t in texts:
                md += earle_markdown(earle_clean(t), cands, lead)
            pages.append({"md": "\n".join(md), "cands": cands})
        _resolve_note_headings(pages, 1419, EARLE_WINDOW)
        self.assertEqual(pages[0]["md"], "## 20\n**ἡμέρα**: the day.")
        self.assertEqual(pages[1]["md"], "+ as said. 480. Not a note.\n\n## 21\n**λόγος**: word.")
        self.assertEqual(pages[2]["md"], "## 22\n**ὁδός**: way.")

    def test_number_opening_a_page_not_kept(self):
        pages = [{"md": "", "cands": []}, {"md": "", "cands": []}]
        md = earle_markdown("5. ἔργον : work.", pages[0]["cands"])
        pages[0]["md"] = "\n".join(md)
        md = earle_markdown("1300. runs on from the page before.", pages[1]["cands"], "+ ")
        pages[1]["md"] = "\n".join(md)
        _resolve_note_headings(pages, 1419, EARLE_WINDOW)
        self.assertEqual(pages[1]["md"], "+ 1300. runs on from the page before.")


class IntroductionSources(unittest.TestCase):
    def test_stems_in_the_entries_order(self):
        play = PLAYS["medea"]
        stems = [page_stem(play, "intro", scan, leaves[0]) for scan, leaves in play.sources_for("intro")]
        self.assertEqual(stems, ["p-10014", "p-20102", "p-30073", "p-40104"])
        self.assertEqual(stems, sorted(stems))
        # Taylor's Shepherd (each scan once) keeps its stems
        hermas = PLAYS["hermas"]
        self.assertEqual(page_stem(hermas, "intro", "shepherdofhermas02hermuoft", 139), "p-30139")


NOTES = """=== p-0080
## 1-48
This opening speech is delivered by an old woman.

## 1
**αα ββ**: a made-up note.
--- flags
1 aa [greek] → αα
--- notes

=== p-0081
+ runs on here.

## 3
**γγ**: on a line our text lacks.

## 5
**εε**: the last.
--- flags
--- notes
"""
INTRO = """=== p-10014
# Introduction

## § 1
Of the facts of Euripides's life little is known.
--- flags
--- notes

=== p-30073
## Earle's notes on the hypotheses

8. **δρακόντων πτερωτῶν**: *i.e.* drawn by them.
--- flags
--- notes

=== p-20102
# The ancient hypotheses
--- flags
--- notes
"""


class Merge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.tr, self.out, self.build = root / "tr", root / "texts" / "medea", root / "build"
        for d in (self.tr, self.out, self.build):
            d.mkdir(parents=True)
        (self.tr / "notes-01.md").write_text(NOTES, encoding="utf-8")
        (self.tr / "intro-01.md").write_text(INTRO, encoding="utf-8")
        self.lines = [("1", "αα ββ"), ("2", "δδ"), ("4", "ζζ"), ("5", "εε")]

    def tearDown(self):
        self.tmp.cleanup()

    def test_commentary_and_introduction(self):
        problems = []
        write_prose_documents(PLAYS["medea"], self.tr, self.out, self.lines, self.build, problems)
        text = (self.out / "commentary-earle.md").read_text(encoding="utf-8")
        self.assertEqual(text.split("\n")[:5], [
            "# title: Commentary (Mortimer Lamson Earle)", "# author: Mortimer Lamson Earle", "# lang: eng",
            "# source: The Medea of Euripides, edited by Mortimer Lamson Earle, New York, Cincinnati, Chicago, "
            "American Book Company, 1904, the notes; transcribed from the Internet Archive scan cu31924079583609",
            "# license: CC BY-SA 4.0 (transcription; the edition is in the public domain)"])
        # the range's end we lack ends at the last line we have; 3 goes under 2 with "[3]" in front
        self.assertIn("## 1-5\nThis opening speech", text)
        self.assertIn("## 1\n**αα ββ**: a made-up note. runs on here.\n", text)
        self.assertIn("## 2\n[3] **γγ**: on a line our text lacks.", text)
        self.assertIn("## 5\n**εε**: the last.", text)
        self.assertTrue(any("line 3 is not in our numbering" in p for p in problems))
        intro = (self.out / "introduction.md").read_text(encoding="utf-8")
        head = intro.split("\n")
        self.assertEqual(head[1], "# author: Mortimer Lamson Earle; G. Murray (the ancient hypotheses and the persons)")
        self.assertIn("scan cu31924079583609", head[2])
        self.assertIn("(scan euripidisfabulae01euriuoft)", head[2])
        # Earle's introduction, then Murray's hypotheses, then Earle's notes on them (the stems' order)
        self.assertLess(intro.index("# Introduction"), intro.index("# The ancient hypotheses"))
        self.assertLess(intro.index("# The ancient hypotheses"), intro.index("## Earle's notes on the hypotheses"))

    def test_not_merged_while_a_flag_is_open(self):
        (self.tr / "notes-01.md").write_text(NOTES.replace("→ αα", "→"), encoding="utf-8")
        problems = []
        write_prose_documents(PLAYS["medea"], self.tr, self.out, self.lines, self.build, problems)
        self.assertFalse((self.out / "commentary-earle.md").exists())
        self.assertTrue((self.out / "introduction.md").exists())
        self.assertTrue(any(p.startswith("notes: not merged") for p in problems))


if __name__ == "__main__":
    unittest.main()
