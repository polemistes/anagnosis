import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.lucian_merge import _find, assemble, lemma_of
from anagnosis_pipeline.lucian_pages import perseus_prose, plain, read_batches, translation_sections

TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="edition">
<head>ΑΛΗΘΩΝ<note n="n.0">title note</note></head>
<div type="textpart" subtype="book" n="1">
<div type="textpart" subtype="section" n="1"><p>ὥσπερ τοῖς ἀθλητικοῖς<note n="n.1">ἀθλητικοῖς Γ</note> — μέρος γοῦν, τοῦτ’ ἔστιν</p></div>
<div type="textpart" subtype="section" n="2"><p>γένοιτο δʼ ἂν ἔμελλον<note n="n.2">Supply οἷον</note> <gap reason="lost"/> </p>
<p><quote><l>Λουκιανὸς τάδε</l> <l>εἶδέ τε</l></quote> τέλος.</p></div>
</div>
<div type="textpart" subtype="book" n="2">
<div type="textpart" subtype="section" n="1"><p>Τὸ δὲ ἀπὸ τούτου</p></div>
</div></div></body></text></TEI>
"""

ENG = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="translation">
<head>A True Story<note>long note</note></head>
<div subtype="book" n="1"><head>I</head>
<div subtype="section" n="1"><p>Men interested<note>fn</note> in athletics</p></div>
<div subtype="section" n="2"><p>It would be</p><quote><l>Lucian saw</l><l>all this</l></quote></div>
</div></div></body></text></TEI>
"""


class PerseusProse(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "grc.xml"
        self.path.write_text(TEI, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_tokens(self):
        toks, notes = perseus_prose(self.path)
        self.assertEqual([t["t"] for t in toks][:5], ["ὥσπερ", "τοῖς", "ἀθλητικοῖς —", "μέρος", "γοῦν,"])
        self.assertEqual([t["sec"] for t in toks if t["newsec"]], ["1.1", "1.2", "2.1"])
        self.assertEqual(toks[5]["t"], "τοῦτʼ")  # elision as U+02BC
        self.assertTrue(next(t for t in toks if t["t"] == "ἔμελλον")["gap"])
        self.assertEqual([t["t"] for t in toks if t["inverse"]], ["Λουκιανὸς", "τάδε", "εἶδέ", "τε"])
        self.assertTrue(next(t for t in toks if t["t"] == "εἶδέ")["verse"])

    def test_notes(self):
        toks, notes = perseus_prose(self.path)
        self.assertEqual([(n["sec"], n["after"]) for n in notes], [("1.1", -1), ("1.1", 2), ("1.2", 10)])
        self.assertEqual(toks[notes[1]["after"]]["t"], "ἀθλητικοῖς —")
        self.assertEqual(notes[1]["text"], "ἀθλητικοῖς Γ")

    def test_translation(self):
        p = Path(self.tmp.name) / "eng.xml"
        p.write_text(ENG, encoding="utf-8")
        self.assertEqual(translation_sections(p), [("1.1", "Men interested in athletics"), ("1.2", "It would be Lucian saw all this")])


BATCH = """=== p-0196
--- text
129.1	[title] ΑΛΗΘΩΝ ΔΙΗΓΗΜΑΤΩΝ Α
¶
129.2	§1.1 Ὥσπερ τοῖς ἀθλητικοῖς καὶ
129.3	παρασκευάζειν. §1.2 γένοιτο δʼ ἂν
¶
129.4	| Λουκιανὸς τάδε πάντα
--- apparatus
1	ἀληθῶν διηγημάτων Γ
3	γένοιτο ΓΩ γένοιντο Z
-	Libri: ΓΩS
--- notes
"""


class Merge(unittest.TestCase):
    def test_assemble(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "batch-01.md").write_text(BATCH, encoding="utf-8")
            pages = read_batches(Path(t))
        text = assemble(pages, [{"stem": "p-0196", "page": 129}])
        self.assertEqual([(u["n"], u["para"], " ".join(w for w, _k in u["words"])) for u in text["units"]],
                         [("1.1", True, "Ὥσπερ τοῖς ἀθλητικοῖς καὶ παρασκευάζειν."), ("1.2", False, "γένοιτο δʼ ἂν"),
                          ("1.2b", True, "Λουκιανὸς τάδε πάντα")])
        self.assertEqual(text["titles"], {"1": "ΑΛΗΘΩΝ ΔΙΗΓΗΜΑΤΩΝ Α"})
        self.assertEqual([u for u, _i, _w in text["lines"]["129.3"]], [0, 1, 1, 1])
        self.assertEqual(text["problems"], [])

    def test_lemma(self):
        self.assertEqual(lemma_of("πνέοντι ΓΩS πνεύματι ZNFI"), (["πνέοντι"], []))
        self.assertEqual(lemma_of("ἄν — διπλασιάσαντος] multiplex"), (["ἄν"], ["διπλασιάσαντος"]))
        self.assertEqual(lemma_of("pro οὐ spat. vel ras."), ([], []))
        self.assertEqual(lemma_of("τοὺς λόγους] ΓΩIS λόγους ZN Fv"), (["τοὺς", "λόγους"], []))
        cands = [(0, k, w) for k, w in enumerate("οὐκέτʼ οὐδὲ στεῖλαι".split())]
        self.assertEqual(_find(["οὐδὲ"], cands), 1)
        self.assertEqual(_find(["οὐκέτι"], cands), 0)  # close enough: a variant of the word printed
        self.assertIsNone(_find(["ἄνεμος"], cands))

    def test_plain(self):
        self.assertEqual(plain("ἦν. §1.7 προελθόντες").split(), ["ἦν.", "προελθόντες"])


if __name__ == "__main__":
    unittest.main()
