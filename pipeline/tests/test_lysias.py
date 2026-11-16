import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.drama import PLAYS
from anagnosis_pipeline.hude_merge import assemble, place_apparatus, speech_title
from anagnosis_pipeline.hude_pages import (APP_KEY, KEY, _clusters, apparatus_top, batch_lines, bracket_flags, head_bottom, is_caps,
                                           is_numeral, label_form, left_out, mend, number_lines, plain, quote_remarks, read_batches,
                                           transposed)
from anagnosis_pipeline.lucian_pages import perseus_prose

# a speech of the Perseus Lysias: sections without a book, a heading at the head of a section, a quotation
TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="edition">
<div type="textpart" subtype="section" n="1"><p>περὶ πολλοῦ ἄν, <q>ἵνα σύ γε</q> ἔφη <q>πειρᾷς αὐτήν.</q> καὶ τοῦτ’ ἔστιν</p></div>
<div type="textpart" subtype="section" n="2"><p rend="align(center)"><label>Μάρτυρες<note>μάρτυρες add. Markland</note></label></p>
<p>τῶν μὲν μαρτύρων <add>τὸν</add> <gap reason="lost"/> ἀκηκόατε</p></div>
</div></body></text></TEI>
"""


class CheckText(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "grc.xml"
        self.path.write_text(TEI, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_speech_as_a_book(self):
        toks, notes = perseus_prose(self.path, book="12", quotes=True, headings=True)
        self.assertEqual([t["sec"] for t in toks if t["newsec"]], ["12.1", "12.2"])
        # the quotation in Hude's single marks, the closing mark not taken for an elision
        self.assertEqual([t["t"] for t in toks][3:10], ["‘ἵνα", "σύ", "γε’", "ἔφη", "‘πειρᾷς", "αὐτήν.’", "καὶ"])
        self.assertEqual(toks[10]["t"], "τοῦτʼ")
        # the heading is a word of its own; the section begins at the first word after it
        head = next(t for t in toks if t.get("heading"))
        self.assertEqual((head["t"], head["newsec"]), ("Μάρτυρες", False))
        self.assertEqual(next(t for t in toks if t["newsec"] and t["sec"] == "12.2")["t"], "τῶν")
        self.assertEqual([n["text"] for n in notes], ["μάρτυρες add. Markland"])
        self.assertIn("⟨τὸν⟩", [t["t"] for t in toks])
        self.assertTrue(next(t for t in toks if t["t"] == "⟨τὸν⟩")["gap"])

    def test_defaults_unchanged(self):
        # without the options (the True Story): no quotation marks, the heading's words plain words
        toks, _notes = perseus_prose(self.path)
        self.assertEqual([t["t"] for t in toks][3:6], ["ἵνα", "σύ", "γε"])
        self.assertFalse(any(t.get("heading") for t in toks))
        self.assertEqual(toks[0]["sec"], ".1")


class Page(unittest.TestCase):
    def test_numeral_and_capitals(self):
        for t in ("I", "II.", "XXXIV", "ΧΙΙ", "X1"):
            self.assertTrue(is_numeral(t), t)
        for t in ("ΜΑΡΤΥΡΕΣ", "καὶ", "23", "ΥΠΕΡ ΤΟΥ", ""):
            self.assertFalse(is_numeral(t), t)
        from anagnosis_pipeline.hude_pages import to_roman

        self.assertEqual([to_roman(n) for n in (1, 4, 9, 14, 19, 24, 29, 34)], ["I", "IV", "IX", "XIV", "XIX", "XXIV", "XXIX", "XXXIV"])
        self.assertTrue(is_caps("ΜΑΡΤΥΡΕΣ."))
        self.assertTrue(is_caps("ὙΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥ͂Σ ΦΟΝΟΥ͂"))
        self.assertFalse(is_caps("Περὶ πολλοῦ ἂν ποιησαίμην"))
        self.assertFalse(is_caps("ΚΑΙ"))  # too short to tell

    def test_label_form(self):
        self.assertEqual(label_form("Μάρτυρες"), "ΜΑΡΤΥΡΕΣ")
        self.assertEqual(label_form("ὙΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥ͂Σ ΦΟΝΟΥ͂."), "ΥΠΕΡ ΤΟΥ ΕΡΑΤΟΣΘΕΝΟΥΣ ΦΟΝΟΥ")
        self.assertEqual(label_form("Ψήφισμα."), "ΨΗΦΙΣΜΑ")

    def test_clusters(self):
        rows = [0, 0, 5, 6, 0, 7, 0, 0, 0, 0, 4, 4, 0]
        self.assertEqual(_clusters(rows, gap=2, low=1), [(2, 6), (10, 12)])
        self.assertEqual(_clusters(rows, gap=1, low=1), [(2, 4), (5, 6), (10, 12)])
        self.assertEqual(_clusters([0, 0], gap=2, low=1), [])

    def test_number_lines(self):
        # a speech's first page: the numeral and title are not counted; a line the check text
        # lacks is kept (the hypothesis); a heading inside the speech is counted
        def line(leaf, kind="text", ocr="λόγος τις ἐνταῦθα", caps=False, centred=False, start=False):
            return {"leaf": leaf, "kind": kind, "ocr": ocr, "caps": caps, "centred": centred, "start_page": start}

        lines = [line(40, "title", "XXXIV", start=True), line(40, "title", "ΠΕΡΙ ΤΟΥ ΜΗ ΚΑΤΑΛΥΣΑΙ", start=True),
                 line(40, ocr="Τοῦ δήμου κατελθόντος ἐκ Πειραιῶς", start=True),
                 line(40, start=True), line(40, ocr="ΜΑΡΤΥΡΕΣ.", caps=True, centred=True, start=True), line(40, start=True),
                 line(41, ocr="; ."), line(41), line(41, ocr="ΝΟΜΟΣ.", caps=True, centred=True)]
        pers = [{"line": 3, "sec": "34.1", "newsec": True}, {"line": 3, "sec": "34.1", "newsec": False},
                {"line": 4, "sec": "34.1", "newsec": False, "heading": True},
                {"line": 5, "sec": "34.2", "newsec": True}, {"line": 7, "sec": "34.2", "newsec": False}]
        got = number_lines(lines, pers)
        self.assertEqual([(L["n"], L["kind"]) for L in got],
                         [("[title]", "title"), ("[title]", "title"), ("40.1", "hypothesis"), ("40.2", "text"), ("40.3", "label"),
                          ("40.4", "text"), ("41.1", "text"), ("41.2", "label")])
        self.assertEqual(got[3]["starts"], [(0, "34.1")])
        self.assertTrue(got[7]["flags"])   # a heading the check text does not have
        self.assertFalse(got[4]["flags"])

    def test_batch_lines(self):
        Ls = [{"n": "[title]", "text": "II", "para": False}, {"n": "30.1", "text": "§2.1 Εἰ μὲν", "para": True},
              {"n": "30.2", "text": "[label] ΜΑΡΤΥΡΕΣ.", "para": False}]
        self.assertEqual(batch_lines(Ls), ["[title]\tII", "¶", "30.1\t§2.1 Εἰ μὲν", "30.2\t[label] ΜΑΡΤΥΡΕΣ."])

    def test_only_hude(self):
        # Hude's page shares the Oxford options with Murray's (tests/test_murray_layout.py) but
        # prints no metrical labels; the route is this text's alone
        self.assertEqual([s for s, p in PLAYS.items() if p.route == "hude"], ["lysias"])
        p = PLAYS["lysias"]
        self.assertTrue(p.foot_signature and p.app_pitch_cut and p.app_bare_numbers)
        self.assertFalse(p.metre_labels)
        self.assertEqual(p.verse_size_q, 0.75)


def ocr_line(y, text="λόγος τις ἐνταῦθα κεῖται καλῶς", x0=200, x1=1900, h=68, size=66, conf=95):
    words = [{"text": w, "bbox": [x0, y, x1, y + h], "conf": conf} for w in text.split()]
    return {"bbox": [x0, y, x1, y + h], "words": words, "x_size": size}


class Layout(unittest.TestCase):
    W, H = 2300, 3600

    def test_running_head(self):
        # the head is the topmost print of a page; a speech's first page has none (its number stands lower)
        page = [ocr_line(230, "[92] ΛΥΣΙΟΥ", x0=120, x1=1200, conf=20), ocr_line(236, "[I", x0=1900, x1=2000, conf=0), ocr_line(320)]
        self.assertEqual(head_bottom(page, self.H), 236 + 68)
        first = [ocr_line(700, "II", x0=1100, x1=1180), ocr_line(830, "ΕΠΙΤΑΦΙΟΣ", x0=900, x1=1400), ocr_line(1000)]
        self.assertIsNone(head_bottom(first, self.H))
        # rows of accents read apart (thin, tiny type) are not print
        self.assertEqual(head_bottom([ocr_line(100, "᾽ Ν ΄", h=24, size=25)] + page, self.H), 236 + 68)

    def test_apparatus_by_pitch(self):
        text = [ocr_line(320 + 85 * k) for k in range(20)]                      # the last text line at 1935
        app = [ocr_line(2075 + 57 * k, "3 εἴητε marg. Ald. : εἰ ἦτε", h=56, size=52) for k in range(4)]
        top, bottom = apparatus_top(text + app, self.W, self.H, 300)
        self.assertTrue(1935 + 68 < top < 2075)
        self.assertTrue(bottom >= 2075 + 57 * 3 + 56)
        # the last line of the text sized as small as the apparatus stays text: it stands a line and a half above
        text[-1]["x_size"] = 52
        self.assertTrue(apparatus_top(text + app, self.W, self.H, 300)[0] > 1935 + 68)
        # Tesseract's uneven boxes inside the apparatus do not end it
        app[1]["bbox"][1] += 30
        app[1]["bbox"][3] += 40
        self.assertTrue(apparatus_top(text + app, self.W, self.H, 300)[0] < 2075)

    def test_apparatus_of_one_line_or_none(self):
        text = [ocr_line(320 + 85 * k) for k in range(6)]                       # the end of a speech
        self.assertEqual(apparatus_top(text, self.W, self.H, 300), (None, None))
        one = ocr_line(320 + 85 * 5 + 140, "1 λειτ. λελειτ. L", x0=900, x1=1300, h=44, size=44)
        top, _bottom = apparatus_top(text + [one], self.W, self.H, 300)
        self.assertTrue(320 + 85 * 5 + 68 < top < one["bbox"][1])
        # a library's stamp under the apparatus is passed over
        stamp = ocr_line(3300, "ετ. ΜιοΕ", x0=1500, x1=1900, h=72, size=69)
        self.assertEqual(apparatus_top(text + [one, stamp], self.W, self.H, 300)[0], top)


class Matching(unittest.TestCase):
    @staticmethod
    def toks(words, **more):
        from anagnosis_pipeline.drama import skel

        return [{"t": w, "skel": skel(w), "sec": "1.1", "newsec": False, **more} for w in words.split()]

    def test_delta_and_run_on_words(self):
        pers = self.toks("οὗτος δʼ ἦν ὑπὸ τῶν παρόντων")
        ocr = self.toks("οὗτος ὃ ἦν ὑπὸτῶν παρόντων")
        match = [0, None, 2, 3, None, 4]
        for t, sim in zip(pers, (1.0, 0.0, 1.0, 0.6, 0.0, 1.0)):
            t["sim"] = sim
        mend(ocr, pers, match)
        self.assertEqual(match, [0, 1, 2, 3, 3, 4])
        self.assertEqual([t["sim"] for t in pers], [1.0] * 6)

    def test_left_out(self):
        pers = self.toks("α β γ δ ε ζ η θ ι κ λ μ ν ξ")
        pers[3]["newsec"], pers[3]["sec"] = True, "1.2"
        match = [0, 1] + [None] * 9 + [2, 3, 4]
        left_out(pers, match)
        self.assertEqual([bool(t.get("left_out")) for t in pers], [False] * 2 + [True] * 9 + [False] * 3)
        self.assertEqual(pers[2]["left_out_run"], (9, "γ δ ε ζ", "ι κ λ", ["1.2"]))
        short = self.toks("α β γ δ")
        left_out(short, [0, None, None, 1])
        self.assertFalse(any(t.get("left_out") for t in short))

    def test_transposed(self):
        import random

        rnd = random.Random(1)
        words = ["".join(rnd.choice("αβγδεζηθικλμνξοπρστυφχψω") for _ in range(6)) for _ in range(80)]
        a, b, c, d = words[:20], words[20:40], words[40:60], words[60:]
        pers = self.toks(" ".join(a + b + c + d))            # the check text: A B C D
        ocr = self.toks(" ".join(a + c + b + d))             # the print:      A C B D
        match = list(range(20)) + [None] * 20 + list(range(20, 40)) + list(range(60, 80))
        self.assertEqual(transposed(ocr, pers, match), [(20, 40, 60)])   # B is to stand before D
        self.assertEqual(transposed(ocr, pers, list(range(80))), [])

    def test_brackets(self):
        # Tesseract reads ⟨ ⟩ as ( ): no flag; a bracket inside a word is a misread letter
        self.assertEqual(bracket_flags("κατεστήσαμεν ⟨ἐν⟩ τῇ ἐρήμῃ", "κατεστήσαμεν (ἐν) τῇ ἐρημῇῃ"), [])
        self.assertEqual(bracket_flags("εἰς Πειραιᾶ, οὗτος", "εἰς Τ]ειραιᾶ, οὗτος"), [])
        self.assertEqual(len(bracket_flags("τῶν πολεμίων ἦσαν", "τῶν (πολεμίων) ἦσαν")), 1)
        self.assertEqual(len(bracket_flags("καὶ ⟨τὸν⟩ ἄνδρα", "καὶ τὸν ἄνδρα")), 1)
        self.assertEqual(len(bracket_flags("φειδωλὸς καὶ ἀκριβῶς", "φειδωλὸς [ἀγαθὴ] καὶ ἀκριβῶς")), 1)
        self.assertEqual(len(bracket_flags("φειδωλὸς [ἀγαθὴ] καὶ", "φειδωλὸς ἀγαθὴ καὶ")), 1)
        self.assertEqual(bracket_flags("φειδωλὸς [ἀγαθὴ] καὶ", "φειδωλὸς [ἀγαθὴ] καὶ"), [])


class Checker(unittest.TestCase):
    def test_keys(self):
        self.assertTrue(KEY.match("28.5"))
        self.assertFalse(KEY.match("[title]"))
        for n, groups in (("3", ("3", None, None)), ("22-23", ("22", "23", None)), ("8, 9", ("8", None, "9")), ("-", (None, None, None))):
            self.assertEqual(APP_KEY.match(n).groups(), groups)
        for n in ("3/4", "3 sq.", "a", ""):
            self.assertIsNone(APP_KEY.match(n))

    def test_plain(self):
        self.assertEqual(plain("[label] ΜΑΡΤΥΡΕΣ."), "ΜΑΡΤΥΡΕΣ.")
        self.assertEqual(plain("ταύτης. §1.44 οὐδεμίαν γὰρ").split(), ["ταύτης.", "οὐδεμίαν", "γὰρ"])

    def test_quotes_and_elision(self):
        # ’ closes a quotation that ‘ opened, also on a later line; otherwise it is a wrong elision sign
        r, open_ = quote_remarks("ἀπιέναι, ‘ἵνα σύ γε’ ἔφη ‘πειρᾷς ἐνταῦθα", 0)
        self.assertEqual((r, open_), ([], 1))
        r, open_ = quote_remarks("εἷλκες αὐτήν.’ κἀγὼ μὲν ἐγέλων, ἀλλʼ οὕτως", open_)
        self.assertEqual((r, open_), ([], 0))
        r, open_ = quote_remarks("ἀλλ’ ἐν ἁπάσῃ", 0)
        self.assertEqual(len(r), 1)
        r, _ = quote_remarks("παρ᾽ ὑμῖν", 0)
        self.assertEqual(len(r), 1)


BATCH = """=== p-0040
--- text
[title]	I
[title]	ΥΠΕΡ ΤΟΥ ΦΟΝΟΥ
[title]	ΑΠΟΛΟΓΙΑ
¶
40.1	§1.1 Περὶ πολλοῦ ἂν ποιησαίμην, τὴν γνώμην τὴν ἐμὴν
40.2	μικρὰς ἡγοῖσθε. §1.2 καὶ ταῦτα μάρτυρες.
40.3	[label] ΜΑΡΤΥΡΕΣ.
¶
40.4	§1.3 Τῶν μὲν μαρτύρων ἀκηκόατε· καί μοι ἀνάγνωθι.
40.5	[label] ΝΟΜΟΣ.
40.6	ἀκούετε, ὦ ἄνδρες, ὅτι κελεύει.
--- apparatus
-	Λυσίου ἀπολογία F
1	alt. τὴν del. Emperius
2	μικρὰς Xᶜ: μακρὰς C H
2	ταῦτα] ταὐτὰ Reiske
4	ἀκηκόατε] ἠκούσατε Cobet
4	lacunam statuit Schenkl
5	νόμος om. C
--- notes

=== p-0041
--- text
[title]	II
[title]	ΕΠΙΤΑΦΙΟΣ
[title]	ΥΠΟΘΕΣΙΣ ΔΙΟΝΥΣΙΟΥ.
41.1	[hypothesis] Τοῦ δήμου κατελθόντος
¶
41.2	§2.1 Εἰ μὲν ἡγούμην οἷόν τε εἶναι
--- apparatus
2	ἡγοῦμαι C: ἡγούμην X
--- notes
"""
INDEX = [{"stem": "p-0040", "leaf": 40}, {"stem": "p-0041", "leaf": 41}]


class Merge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        (Path(self.tmp.name) / "batch-01.md").write_text(BATCH, encoding="utf-8")
        self.pages = read_batches(Path(self.tmp.name))
        self.text = assemble(self.pages, INDEX)

    def tearDown(self):
        self.tmp.cleanup()

    def test_units(self):
        units = self.text["units"]
        self.assertEqual(self.text["problems"], [])
        self.assertEqual([u["n"] for u in units], ["1.1", "1.2", "1.3", "1.3b", "2.0", "2.1"])
        self.assertEqual([u["para"] for u in units], [True, False, True, False, True, True])
        # the headings stand before the part they are printed before
        self.assertEqual([u["before"] for u in units], [[], [], ["ΜΑΡΤΥΡΕΣ."], ["ΝΟΜΟΣ."], [], []])
        self.assertEqual(" ".join(w for w, _k in units[1]["words"]), "καὶ ταῦτα μάρτυρες.")
        self.assertEqual(" ".join(w for w, _k in units[3]["words"]), "ἀκούετε, ὦ ἄνδρες, ὅτι κελεύει.")
        self.assertEqual(self.text["lines"]["40.3"], [])
        self.assertEqual(self.text["lines"]["40.2"][2], (1, 0, "καὶ"))

    def test_titles(self):
        self.assertEqual(self.text["titles"], {1: ["I", "ΥΠΕΡ ΤΟΥ ΦΟΝΟΥ", "ΑΠΟΛΟΓΙΑ"], 2: ["II", "ΕΠΙΤΑΦΙΟΣ", "ΥΠΟΘΕΣΙΣ ΔΙΟΝΥΣΙΟΥ."]})
        self.assertEqual(speech_title(self.text["titles"][1]), ("I", "ΥΠΕΡ ΤΟΥ ΦΟΝΟΥ ΑΠΟΛΟΓΙΑ"))
        self.assertEqual(speech_title(self.text["titles"][2]), ("II", "ΕΠΙΤΑΦΙΟΣ"))

    def test_apparatus(self):
        placed, misses, problems = place_apparatus(self.pages, INDEX, self.text)
        self.assertEqual(problems, [])
        units = self.text["units"]
        got = [(units[u]["n"], item) for u, item in placed]
        self.assertEqual(got, [
            ("1.1", "Λυσίου ἀπολογία F"),              # a note on the title: the page's first section
            ("1.1", "alt. τὴν del. Emperius"),
            ("1.1", "μικρὰς Xᶜ: μακρὰς C H"),          # line 2 holds two sections: the lemma decides
            ("1.2", "ταῦτα] ταὐτὰ Reiske"),
            ("1.3", "ἀκηκόατε] ἠκούσατε Cobet"),
            ("1.3", "lacunam statuit Schenkl"),
            ("1.3b", "νόμος om. C"),                   # an item on a heading's line: the part after it
            ("2.1", "ἡγοῦμαι C: ἡγούμην X"),
        ])
        # the last item's first reading is not in the text, a later one is: the text may have slipped
        self.assertEqual([m.split(":")[0] for m in misses if m.startswith("SERIOUS")], ["SERIOUS 41.2"])
        self.assertFalse([m for m in misses if "40.1" in m or "40.2" in m])

    def test_misprint_table_is_keyed_by_line(self):
        from anagnosis_pipeline import hude_merge

        old = dict(hude_merge.MISPRINTS)
        try:
            hude_merge.MISPRINTS["t"] = {"40.2": ("μικρὰς", "μακρὰς"), "40.9": ("x", "y")}
            problems: list[str] = []
            notes = hude_merge.correct_misprints("t", self.text, problems)
            self.assertEqual(notes, [(0, "μακρὰς: Hude prints μικρὰς, a misprint; corrected in this edition.")])
            self.assertEqual(self.text["units"][0]["words"][-2][0], "μακρὰς")
            self.assertEqual(len(problems), 1)
        finally:
            hude_merge.MISPRINTS.clear()
            hude_merge.MISPRINTS.update(old)


if __name__ == "__main__":
    unittest.main()
