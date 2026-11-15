"""Jebb's Sophocles on the drama route: the prose batches (intro-NN.md, appendix-NN.md) merged by
sophocles.write_prose (sophocles-prose), and what merge-drama leaves alone (drama.py)."""
import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.drama import PLAYS as DRAMA, apparatus_meta, check_text_name
from anagnosis_pipeline.sophocles import PROSE_HOW, write_prose
from anagnosis_pipeline.sophocles_pages import appendix_header

APPENDIX = """=== p-0259
## Lines 11–14

As to the coins of Acarnania, see Barclay Head, *Hist. Numorum*, p. 63.

With regard to the third shape,—ἀνδρείῳ κύτει βούπρῳρος,—two views are
--- flags
1 Aist. [latin] → *Hist.*
--- notes

=== p-0260
+ possible. (1) According to the first view, κύτει means the whole body.¹

[Note: ¹ So the schol.]

## Line 29 f.

**νὺξ γὰρ εἰσάγει | καὶ νὺξ ἀπωθεῖ διαδεδεγμένη πόνον.**

A modified form of the interpre-
--- flags
1 yap [latin] → γὰρ
--- notes
"""
APPENDIX_2 = """=== p-0261
+ tation given in the commentary is one which governs πόνον᾽.
--- flags
--- notes
"""
INTRO = """=== p-0055
# Manuscripts, editions, etc.

## § 1 — MSS.

Twelve of the MSS., other than L, have been described in former
--- flags
1 TweLVE [conf] → Twelve
--- notes

=== p-0077
+ volumes.

# The ancient argument

## The argument

The *Trachiniae*, alone among the seven plays, has no ancient ὑπόθεσις.
--- flags
--- notes
"""
PERSEUS = """<?xml version="1.0"?>
<TEI.2><text><body>
<div1 type="introduction">
<div2 type="section" n="1"><p>The story of Heracles.</p></div2>
<div2 type="section" n="2"><p>Deianeira.</p></div2>
</div1>
</body></text></TEI.2>
"""


class WriteProse(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.sources, self.texts, self.tr = root / "sources", root / "texts", root / "tr"
        for d in (self.sources, self.texts / "trachiniae", self.tr):
            d.mkdir(parents=True)
        (self.tr / "appendix-01.md").write_text(APPENDIX, encoding="utf-8")
        (self.tr / "appendix-02.md").write_text(APPENDIX_2, encoding="utf-8")
        (self.tr / "intro-01.md").write_text(INTRO, encoding="utf-8")
        self.kept = {name: f"# {name}\n" for name in ("grc.txt", "tokens.tsv", "syntax-nodes.tsv", "eng-jebb.txt", "commentary-jebb.md")}
        for name, text in self.kept.items():
            (self.texts / "trachiniae" / name).write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_appendix_as_merge_sophocles_appendix_writes_it(self):
        self.assertEqual(write_prose("trachiniae", self.sources, self.texts, self.tr), 0)
        text = (self.texts / "trachiniae" / "appendix.md").read_text(encoding="utf-8")
        self.assertEqual(text, appendix_header("trachiniae", PROSE_HOW) + "\n" + "\n\n".join([
            "## Lines 11–14",
            "As to the coins of Acarnania, see Barclay Head, *Hist. Numorum*, p. 63.",
            "With regard to the third shape,—ἀνδρείῳ κύτει βούπρῳρος,—two views are possible. (1) According to "
            "the first view, κύτει means the whole body.¹",
            "[Note: ¹ So the schol.]",
            "## Line 29 f.",
            "**νὺξ γὰρ εἰσάγει | καὶ νὺξ ἀπωθεῖ διαδεδεγμένη πόνον.**",
            "A modified form of the interpretation given in the commentary is one which governs πόνον’.",
        ]) + "\n")
        self.assertTrue(text.startswith("# title: Appendix\n# author: Richard C. Jebb\n# source: Sophocles, The Plays and "
                                        "Fragments, Part V: The Trachiniae, Cambridge University Press, first edition 1892; "
                                        "Internet Archive sophocles05soph (Boston College) (Appendix), read by OCR"))

    def test_introduction_after_the_perseus_chapters(self):
        (self.sources / "jebb-trachiniae-commentary.xml").write_text(PERSEUS, encoding="utf-8")
        write_prose("trachiniae", self.sources, self.texts, self.tr)
        text = (self.texts / "trachiniae" / "introduction.md").read_text(encoding="utf-8")
        head, _, body = text.partition("\n\n")
        self.assertIn("# source: Perseus Digital Library, jebb.soph.trach_eng.xml", head)
        self.assertIn("; the chapters after § 2 from Sophocles: The Plays and Fragments, Part V: The Trachiniae, "
                      "Cambridge University Press, first edition 1892; Internet Archive sophocles05soph (Boston College), "
                      "read by OCR and checked against the page images", head)
        self.assertIn("# license: CC BY-SA 3.0 US (Perseus); the transcribed chapters CC BY-SA 4.0", head)
        self.assertEqual([l for l in body.splitlines() if l.startswith("#")],
                         ["# Introduction", "## § 1", "## § 2", "# Manuscripts, editions, etc.", "## § 1 — MSS.",
                          "# The ancient argument", "## The argument"])
        self.assertIn("Twelve of the MSS., other than L, have been described in former volumes.\n", body)
        # run again: the same file (the Perseus chapters are made afresh, not added twice)
        write_prose("trachiniae", self.sources, self.texts, self.tr)
        self.assertEqual((self.texts / "trachiniae" / "introduction.md").read_text(encoding="utf-8"), text)
        for name, kept in self.kept.items():
            self.assertEqual((self.texts / "trachiniae" / name).read_text(encoding="utf-8"), kept)

    def test_commentary_made_afresh_and_refiled(self):
        # Perseus's commentary: spaces at tag boundaries, metrical schemes in signs, notes on lines
        # our numbering lacks re-filed; a second run gives the same file
        xml = PERSEUS.replace("</body>", """<div1 type="commentary"><div2><head>94-140</head><p>Parodos.</p>
<div3 n="97" type="commLine"><p><lemma lang="greek">tou=to</lemma>: cp. <bibl n="Hom. Il. 18.126"><title>Il.</title>18. 126</bibl><quote lang="greek">mhde/</quote>, &macr;&breve;&breve;&macr;.</p></div3>
<div3 n="99" type="commLine"><p><lemma lang="greek">w)= lampra=|</lemma>, as below; <quote lang="greek">a)e/&breve;lion</quote>, time of &breve;.</p></div3>
</div2></div1></body>""")
        (self.sources / "jebb-trachiniae-commentary.xml").write_text(xml, encoding="utf-8")
        (self.texts / "trachiniae" / "grc.txt").write_text(
            "# title: Τραχίνιαι\n\n97\tτοῦτο καρῦξαι, τὸν Ἀλκμήνας πόθι μοι πόθι παῖς\n"
            "98\tναίει ποτʼ, ὦ λαμπρᾷ στεροπᾷ φλεγέθων,\n", encoding="utf-8")
        write_prose("trachiniae", self.sources, self.texts, self.tr)
        path = self.texts / "trachiniae" / "commentary-jebb.md"
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# title: Commentary on Sophocles: Trachiniae\n# author: Richard C. Jebb\n"
                                        "# lang: eng\n# source: Perseus Digital Library, jebb.soph.trach_eng.xml"))
        self.assertIn("## 97\n**τοῦτο**: cp. *Il.* 18. 126 μηδέ, –⏑⏑–.\n", text)
        # a breve after a vowel is its length mark, set over it; a free one is a metrical sign
        self.assertIn("## 98\n[99] **ὦ λαμπρᾷ**, as below; ἀε\u0306\u0301λιον, time of ⏑.\n", text)
        write_prose("trachiniae", self.sources, self.texts, self.tr)
        self.assertEqual(path.read_text(encoding="utf-8"), text)
        self.assertFalse(path.with_name(path.name + ".part").exists())

    def test_introduction_without_perseus_chapters(self):
        write_prose("trachiniae", self.sources, self.texts, self.tr)
        text = (self.texts / "trachiniae" / "introduction.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# title: Introduction\n# author: Richard C. Jebb\n# source: Sophocles: The Plays "
                                        "and Fragments, Part V: The Trachiniae"))
        self.assertIn("\n\n# Manuscripts, editions, etc.\n\n## § 1 — MSS.\n\n", text)
        self.assertFalse((self.texts / "trachiniae" / "introduction.md.part").exists())

    def test_unchecked_batches_are_not_merged(self):
        (self.tr / "appendix-02.md").write_text(APPENDIX_2.replace("--- flags\n", "--- flags\n1 tation [conf] →\n"),
                                                encoding="utf-8")
        self.assertEqual(write_prose("trachiniae", self.sources, self.texts, self.tr), 1)
        self.assertFalse((self.texts / "trachiniae" / "appendix.md").exists())
        self.assertTrue((self.texts / "trachiniae" / "introduction.md").exists())


class MergeDramaKeepsJebb(unittest.TestCase):
    def test_translation_kept_and_headers(self):
        from anagnosis_pipeline.drama import _translation

        play = DRAMA["trachiniae"]
        self.assertEqual(play.translation, "kept")
        with tempfile.TemporaryDirectory() as t:
            out = Path(t)
            (out / "eng-jebb.txt").write_text("Jebb\n", encoding="utf-8")
            _translation(play, out, out, [("1", "λόγος")], [], {}, [], out)
            self.assertEqual([p.name for p in out.iterdir()], ["eng-jebb.txt"])
            self.assertEqual((out / "eng-jebb.txt").read_text(encoding="utf-8"), "Jebb\n")
        self.assertEqual(check_text_name(play), "Jebb's text in the Perseus Digital Library (soph.trach_gk.xml)")
        self.assertEqual(check_text_name(DRAMA["oedipustyrannus"]),
                         "Jebb's text in the Perseus Digital Library (soph.ot_gk.xml)")
        meta = apparatus_meta(play)
        self.assertEqual((meta["title"], meta["author"], meta["lang"]), ("Critical apparatus", "Richard C. Jebb", "eng"))
        self.assertTrue(meta["source"].startswith("Sophocles, The Plays and Fragments, Part V: The Trachiniae, Cambridge "
                                                  "University Press, first edition 1892; Internet Archive sophocles05soph"))
        self.assertEqual(apparatus_meta(DRAMA["clouds"])["title"], "Critical apparatus (W. J. M. Starkie)")


class AppendixDraft(unittest.TestCase):
    def test_headings_settled_over_the_pages(self):
        from anagnosis_pipeline.drama_prose import _resolve_headings

        pages = [
            {"md": "\x000\n\n\x001", "cands": [
                {"kind": "line", "options": [(11, "## Lines 11–14")], "body": "As to the coins", "orig": "11—14 As to the coins"},
                {"kind": "line", "options": [(1, "## Line 1")], "body": "Bothe", "orig": "1 Bothe"}]},
            {"md": "### The Oracle at Dodona.\n\n\x000", "cands": [
                {"kind": "line", "options": [(8563, "## Line 8563 ff."), (563, "## Line 563 ff."), (853, "## Line 853 ff.")],
                 "body": "The traditional text", "orig": "8563 ff. The traditional text"}]},
        ]
        _resolve_headings(pages, "appendix")
        self.assertEqual(pages[0]["md"], "## Lines 11–14\n\nAs to the coins\n\n1 Bothe")
        self.assertEqual(pages[1]["md"], "## Line 563 ff.\n\n### The Oracle at Dodona.\n\nThe traditional text")

    def test_sections(self):
        from anagnosis_pipeline.drama_prose import _resolve_headings

        pages = [{"md": "# Manuscripts, editions, etc.\n\n\x000\n\n\x001\n\n\x002", "cands": [
            {"kind": "sec", "nums": [1], "explicit": False, "margin": "MSS.", "bodies": ["Twelve"], "orig": "δι. Twelve"},
            {"kind": "sec", "nums": [56, 6], "explicit": False, "margin": None, "bodies": ["The text", "The text"], "orig": "56. The text"},
            {"kind": "sec", "nums": [2], "explicit": False, "margin": None, "bodies": ["x"], "orig": "56. x"}]}]
        _resolve_headings(pages, "intro")
        self.assertEqual(pages[0]["md"], "# Manuscripts, editions, etc.\n\n## § 1 — MSS.\n\nTwelve\n\n56. The text\n\n## § 2\n\nx")

    def test_margin_note_taken_out_of_its_line(self):
        from anagnosis_pipeline.drama_prose import _jebb_margins

        def line(y, x0, x1, words):
            step = (x1 - x0) // len(words)
            ws = [{"text": t, "bbox": [x0 + i * step, y, x0 + (i + 1) * step - 10, y + 60], "conf": 90}
                  for i, t in enumerate(words)]
            return {"bbox": [x0, y, x1, y + 60], "words": ws}

        body = [line(400 + 80 * i, 120, 2110, ["word"] * 8) for i in range(10)]
        body[3]["words"].append({"text": "MSS.", "bbox": [2140, 640, 2260, 700], "conf": 90})
        body[3]["bbox"][2] = 2260
        stamp = line(100, 2420, 2446, ["SN"])
        out = _jebb_margins(body + [stamp], (2454, 4104))
        self.assertEqual(len(out), 10)
        self.assertEqual(out[3]["margin"], "MSS.")
        self.assertEqual(out[3]["bbox"][2], out[3]["words"][-1]["bbox"][2])
        self.assertEqual([w["text"] for w in out[3]["words"]], ["word"] * 8)
        self.assertEqual([l.get("margin") for k, l in enumerate(out) if k != 3], [None] * 9)


COMMENTARY = """# title: Commentary on Sophocles: Trachiniae
# author: Richard C. Jebb

## 98
**ναίει**: dwells.

## 99
**ὦ … φλεγέθων**: for this direct invocation.

## 119
**ἀλλά**: *yet* he is not suffered to perish.

## 124
It is the statement.

## 1004-1043
This passage consists of lyrics.

## 1040
**αὔτως**: for the smooth breathing.
"""
GRC = """# title: Τραχίνιαι

@ Χορός
98	ναίει ποτʼ, ὦ λαμπρᾷ στεροπᾷ φλεγέθων,
100	ἢ ποντίας αὐλῶνας,
116	οὕτω δὲ τὸν Καδμογενῆ στρέφει,
120	Κρήσιον. ἀλλά τις θεῶν
122	ὧν ἐπιμεμφομένα σʼ αἰδοῖα μέν,
125	φαμὶ γὰρ οὐκ ἀποτρύειν
1004	ἒ ἔ,
1040	αὔτως, ὧδʼ αὔτως, ὥς μʼ ὤλεσεν.
1042	ὠκυπέτᾳ μόρῳ τὸν μέλεον φθίσας.
"""


class RefileCommentary(unittest.TestCase):
    """sophocles-prose files Jebb's notes on verses our numbering lacks as merge-drama files the
    apparatus: under the line that holds the lemma (the earlier or the next one), else the
    nearest earlier line, the printed number kept in front."""

    def test_notes_refiled_and_safe_to_run_again(self):
        from anagnosis_pipeline.sophocles import refile_commentary

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "commentary-jebb.md").write_text(COMMENTARY, encoding="utf-8")
            (work / "grc.txt").write_text(GRC, encoding="utf-8")
            moves = refile_commentary(work)
            text = (work / "commentary-jebb.md").read_text(encoding="utf-8")
            self.assertEqual(len(moves), 4)
            self.assertEqual(text, """# title: Commentary on Sophocles: Trachiniae
# author: Richard C. Jebb

## 98
**ναίει**: dwells.

[99] **ὦ … φλεγέθων**: for this direct invocation.

## 120
[119] **ἀλλά**: *yet* he is not suffered to perish.

## 122
[124] It is the statement.

## 1004-1042
This passage consists of lyrics.

## 1040
**αὔτως**: for the smooth breathing.
""")
            # again: nothing moves, the file stays as it is
            self.assertEqual(refile_commentary(work), [])
            self.assertEqual((work / "commentary-jebb.md").read_text(encoding="utf-8"), text)

    def test_heading_perseus_lost_put_right(self):
        from anagnosis_pipeline.sophocles import refile_notes

        lines = {"633": "ὦ ναύλοχα καὶ πετραῖα", "638": "Πυλάτιδες κλέονται·", "640": "ὁ καλλιβόας"}
        fixes = {"639 **<*> ναύλοχα**": ("633-639", "**ὦ ναύλοχα**")}
        want = "## 633-638\n**ὦ ναύλοχα** κ.τ.λ. Wishing\n"
        # from Perseus's heading, and from the state an earlier run without the fix left
        for text in ("## 639\n**<*> ναύλοχα** κ.τ.λ. Wishing\n", "## 638\n[639] **<*> ναύλοχα** κ.τ.λ. Wishing\n"):
            new, _moves = refile_notes(text, lines, fixes)
            self.assertEqual(new, want)
            self.assertEqual(refile_notes(new, lines, fixes), (want, []))


if __name__ == "__main__":
    unittest.main()


class RangeHeadings(unittest.TestCase):
    def test_range_put_back_in_the_heading(self):
        from anagnosis_pipeline.sophocles import range_headings
        text = "## 981\n**εἰς τόδʼ**, x.\n\n## 982\n—*984* He has just said.\n\n## 986\n**δυσστομεῖν**\n"
        self.assertEqual(range_headings(text),
                         "## 981\n**εἰς τόδʼ**, x.\n\n## 982-984\nHe has just said.\n\n## 986\n**δυσστομεῖν**\n")
        self.assertEqual(range_headings(range_headings(text)), range_headings(text))

