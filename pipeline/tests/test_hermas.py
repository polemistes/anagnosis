import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline import greek
from anagnosis_pipeline.drama import PLAYS
from anagnosis_pipeline.hermas_text import (beta_item, chapters_in, cite, compare_form, continuous_chapter, first1k_marks,
                                            lake_notes, lake_translation, tauber_text)
from anagnosis_pipeline.lake_merge import assemble, taylor_ref, title_label
from anagnosis_pipeline.lake_pages import VNUM, _ocr_noise, _weak_number, marks_in, ocr_roman, plain, read_batches, roman, to_roman, to_sup

TAUBER = """1.0.0 Ὅρασις αʹ
1.1.1 Ὁ θρέψας με πέπρακέν με Ῥόδῃ τινὶ εἰς Ῥώμην.
1.1.2 μετὰ χρόνον τινὰ δι’ ἀνοδίας.
1.2.1 Μετὰ τὸ λαλῆσαι αὐτὴν
26.30.2 ἐπεὶ οὖν οἱ πιστεύσαντες
26.30.3 Quodsi de ceteris montibus adiecisset, πιστεύσαντες καὶ
"""

F1K = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="edition">
<div type="textpart" subtype="book" n="1"><div type="textpart" subtype="chapter" n="1">
<div type="textpart" subtype="section" n="1"><p> Ὁ θρέψας με πέπρακέν με Ῥόδῃ τινὶ <note n="1">pro\\s gunai=ka/ tina AL1, omitting</note> εἰς Ῥώμην.</p></div>
<div type="textpart" subtype="section" n="2"><p> μετὰ χρόνον <note><bibl>Ps. 2, 4;</bibl></note> τινὰ δι’ ἀνοδίας.</p></div>
</div><div type="textpart" subtype="chapter" n="2">
<div type="textpart" subtype="section" n="1"><p> Μετὰ τὸ λαλῆσαι αὐτὴν <note n="2">to/pw| N%2 L1, tro/pw| Nc AL2(E).</note></p></div>
</div></div></div></body></text></TEI>
"""

ENG = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="translation">
<div type="textpart" subtype="book" n="1"><head>Vision 1</head>
<div type="textpart" subtype="chapter" n="1">
<div type="textpart" subtype="section" n="1"><p>He who brought me up sold me to a certain<note type="marginal">Hermas and Rhoda</note> Rhoda at Rome.<note type="footnote">Hardly intelligible.</note></p></div>
<div type="textpart" subtype="section" n="2"><p>And she said: <q>Hail, Hermas.</q></p></div>
</div></div></div></body></text></TEI>
"""


class Sources(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.tauber, self.f1k, self.eng = d / "t.txt", d / "f.xml", d / "e.xml"
        self.tauber.write_text(TAUBER, encoding="utf-8")
        self.f1k.write_text(F1K, encoding="utf-8")
        self.eng.write_text(ENG, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_tauber(self):
        g = tauber_text(self.tauber)
        self.assertEqual([t["sec"] for t in g if t["newsec"]], ["1.1.1", "1.1.2", "1.2.1", "26.30.2"])
        self.assertEqual([t["sec"] for t in g if t["newchapter"]], ["1.1.1", "1.2.1", "26.30.2"])
        self.assertIn("διʼ", [t["t"] for t in g])  # elision as ʼ
        lat = tauber_text(self.tauber, part="latin")
        self.assertEqual(lat[0]["t"], "Quodsi")
        self.assertTrue(lat[0]["latin"])
        self.assertFalse(lat[-1]["latin"])

    def test_first1k_marks(self):
        m = first1k_marks(self.f1k, self.tauber)
        g = tauber_text(self.tauber)
        self.assertEqual([(x["kind"], x["sec"], g[x["after"]]["t"]) for x in m],
                         [("app", "1.1.1", "τινὶ"), ("bibl", "1.1.2", "χρόνον"), ("app", "1.2.1", "αὐτὴν")])
        self.assertEqual(m[0]["text"], "πρὸς γυναῖκά tina AL₁, omitting")
        self.assertEqual(m[2]["text"], "τόπῳ ℵ* L₁, τρόπῳ ℵᶜ AL₂(E).")

    def test_beta_item(self):
        self.assertEqual(beta_item("kw/mas N AE, the editors emend to *kou/mas (Cumae)."),
                         "κώμας ℵ AE, the editors emend to Κούμας (Cumae).")
        self.assertEqual(beta_item("h( gunh/ A"), "ἡ γυνή A")

    def test_compare_form(self):
        ours = "τόπῳ ℵ* L₁, τρόπῳ ℵᶜAL₂(E)."
        self.assertEqual(compare_form(ours), compare_form("to/pw| N%2 L1, tro/pw| Nc AL2(E).", beta=True))

    def test_translation_and_notes(self):
        tr = lake_translation(self.eng)
        self.assertEqual(tr[0], ("1.1.1", "He who brought me up sold me to a certain Rhoda at Rome."))
        self.assertEqual(tr[1][1], "And she said: “Hail, Hermas.”")
        notes = lake_notes(self.eng)
        self.assertEqual([(n["kind"], n["text"]) for n in notes],
                         [("marginal", "Hermas and Rhoda"), ("footnote", "Hardly intelligible.")])

    def test_numbering(self):
        self.assertEqual(cite("26.30.2"), "Similitude 9.30.2")
        self.assertEqual(cite("9.1.2"), "Mandate 4.1.2")
        self.assertEqual(continuous_chapter(3, 1), 9)
        self.assertEqual(continuous_chapter(26, 33), 110)
        self.assertEqual(continuous_chapter(27, 4), 114)
        self.assertEqual(taylor_ref("## Mandate 4.1.2"), "9.1.2")
        self.assertEqual(taylor_ref("## Mandate 1.3"), "6.1.3")
        self.assertEqual(taylor_ref("## Similitude 9.30.2"), "26.30.2")
        self.assertIsNone(taylor_ref("## 12"))


class Page(unittest.TestCase):
    def test_leaves(self):
        p = PLAYS["hermas"]
        self.assertEqual(p.leaves("text")[:3], [18, 20, 22])
        self.assertEqual(p.leaves("text")[-1], 302)
        self.assertEqual(len(PLAYS["truestory"].leaves("text")), 80)

    def test_numbers(self):
        self.assertEqual((roman("XXIX"), roman("IV"), ocr_roman("ΙΙ"), ocr_roman("ἐδ")), (29, 4, 2, None))
        self.assertEqual(to_roman(29), "XXIX")
        self.assertEqual(VNUM.match("12.").group(1), "12")
        self.assertIsNotNone(VNUM.match("ὅ."))
        self.assertIsNone(VNUM.match("ὅτι"))
        self.assertEqual(to_sup(12), "¹²")
        self.assertEqual(marks_in("τινὶ¹ εἰς Ῥώμην,² καὶ"), [1, 2])
        self.assertEqual(plain("τινὶ¹ εἰς"), "τινὶ εἰς")
        # the Greek model's misreadings on Lake's type
        self.assertTrue(_weak_number({"text": "Ἰ.", "conf": 32}))
        self.assertTrue(_weak_number({"text": "9", "conf": 96}))
        self.assertFalse(_weak_number({"text": "ὁ", "conf": 95}))
        self.assertFalse(_weak_number({"text": "ἐν", "conf": 40}))
        self.assertTrue(_ocr_noise("χρόνον", "ρόνον"))
        self.assertTrue(_ocr_noise("ἱλαρὸς", "ἱχαρὸς"))
        self.assertTrue(_ocr_noise("ζωὴ", "ἕωὴ"))
        self.assertFalse(_ocr_noise("ὅτι", "ὅτε"))
        self.assertFalse(_ocr_noise("μετανοίας", "μενανοίας"))
        self.assertEqual((chapters_in(1), chapters_in(6), chapters_in(26), chapters_in(27)), (4, 1, 33, 4))

    def test_batches_and_assemble(self):
        batch = ("=== p-0018\n--- text\n[title]\tΠΟΙΜΗΝ\n[chapter]\tI\n¶\n1.1.1\tὉ θρέψας τινὶ¹ εἰς\n"
                 "1.1.2\tμετὰ χρόνον\n--- apparatus\n1\tπρὸς γυναῖκά τινα AL₁\n--- margin\n1.1.2\tPs. 2, 4;\n--- notes\n\n"
                 "=== p-0020\n--- text\n1.1.2+\tτινὰ¹ διʼ ἀνοδίας.\n[chapter]\tII\n1.2.1\tΜετὰ τὸ\n"
                 "--- apparatus\n1\tτινὰ A\n--- margin\n--- notes\n")
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "batch-01.md").write_text(batch, encoding="utf-8")
            pages = read_batches(Path(t))
        self.assertEqual(pages["p-0018"]["margin"], [("1.1.2", "Ps. 2, 4;")])
        index = [{"stem": "p-0018"}, {"stem": "p-0020"}]
        text = assemble(pages, index)
        self.assertEqual([v["sec"] for v in text["verses"]], ["1.1.1", "1.1.2", "1.2.1"])
        self.assertEqual(plain(" ".join(text["verses"][1]["words"])), "μετὰ χρόνον τινὰ διʼ ἀνοδίας.")
        self.assertEqual(text["marks"], {("p-0018", 1): "1.1.1", ("p-0020", 1): "1.1.2"})
        self.assertEqual([v["para"] for v in text["verses"]], [True, False, True])
        self.assertEqual(text["titles"], {1: ["ΠΟΙΜΗΝ"]})
        self.assertEqual(text["problems"], [])

    def test_numerals_keep_their_keraia(self):
        self.assertEqual([w for w, _s, _e in greek.words("οἱ μʹ λίθοι, λεʹ καὶ διʼ αὐτοῦ")],
                         ["οἱ", "μʹ", "λίθοι", "λεʹ", "καὶ", "διʼ", "αὐτοῦ"])

    def test_misprints(self):
        from anagnosis_pipeline import lake_merge
        text = {"verses": [{"sec": "22.1.1", "words": ["ὄρος", "τι", "κα", "εὐχαριστῶν"]},
                           {"sec": "24.1.4", "words": ["τὰς", "ἁμαρτιας", "ἐν", "θίψεσι¹"]},
                           {"sec": "8.1.1", "words": ["Πνεῦμα"]}],
                "titles": {8: ["Εντολὴ γʹ."]}}
        problems: list = []
        notes = lake_merge.correct_misprints("hermas", text, problems)
        self.assertEqual(text["verses"][0]["words"][2], "καὶ")
        self.assertEqual(text["verses"][1]["words"][1:], ["ἁμαρτίας", "ἐν", "θλίψεσι¹"])
        self.assertEqual(text["titles"][8], ["Ἐντολὴ γʹ."])
        self.assertIn(("8.1.1", "Ἐντολὴ [Print has: Εντολὴ, in the title]"), notes)

    def test_apparatus_misprints(self):
        from anagnosis_pipeline import lake_merge
        placed = [("16.1.8", "τὸ ἄνωθεν AL₁, τὸ θεῖαν τὸ ἄνωθεν EL₂."), ("16.1.8", "another item"),
                  ("3.1.5", "ἁμαρτίας μου—ἀμαρτίας μου om. per homoiot. ℵL₂.")]
        problems: list = []
        out = lake_merge.correct_apparatus_misprints("hermas", placed, problems)
        self.assertEqual(out, [
            ("16.1.8", "τὸ ἄνωθεν AL₁, τὸ θεῖον τὸ ἄνωθεν EL₂. [Print has: θεῖαν]"),
            ("16.1.8", "another item"),
            ("3.1.5", "ἁμαρτίας μου—ἁμαρτίας μου om. per homoiot. ℵL₂. [Print has: ἀμαρτίας]")])
        # the three not in these items are reported
        self.assertEqual(len(problems), 3)

    def test_titles(self):
        self.assertEqual(title_label("Ὅρασις βʹ."), "Ὅρασις βʹ")
        self.assertEqual(title_label("Ἐντολὴ α΄.¹"), "Ἐντολὴ αʹ")
        batch = ("=== p-0080\n--- text\n[title]\tἈποκάλυψις εʹ.¹\n1.1.1\tΠροσευξαμένου μου\n"
                 "--- apparatus\n1\tἈποκάλυψις ε W\n--- margin\n--- notes\n")
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "batch-06.md").write_text(batch, encoding="utf-8")
            text = assemble(read_batches(Path(t)), [{"stem": "p-0080"}])
        self.assertEqual(text["marks"], {("p-0080", 1): "1.1.1"})


if __name__ == "__main__":
    unittest.main()
