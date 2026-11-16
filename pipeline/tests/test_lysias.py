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
        for t in ("I", "II.", "XXXIV", "ΧΙΙ", "X1", "ΙΠ", "ΧΧῚΙ", "ΧΧΧΙΙΠ", "ὟΥΙ", "ΧΙΝ"):
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

    def test_known_misreadings_are_no_residuals(self):
        from anagnosis_pipeline.hude_pages import known_misreading

        self.assertTrue(known_misreading({"kind": "punctuation", "text": "διοικοῦσα·", "ocr": "διοικοῦσαʼ"}))
        self.assertTrue(known_misreading({"kind": "word", "text": "δʼ", "ocr": "ὃ"}))
        self.assertTrue(known_misreading({"kind": "bracket", "text": "⟨οὐκ⟩", "ocr": "(οὐκ)"}))
        self.assertFalse(known_misreading({"kind": "punctuation", "text": "ἐκέλευον,", "ocr": "ἐκέλευον"}))
        self.assertFalse(known_misreading({"kind": "punctuation", "text": "εἶναι·", "ocr": "εἶναι."}))
        self.assertFalse(known_misreading({"kind": "bracket", "text": "οὐκ", "ocr": "(οὐκ)"}))

    def test_plain(self):
        self.assertEqual(plain("[label] ΜΑΡΤΥΡΕΣ."), "ΜΑΡΤΥΡΕΣ.")
        self.assertEqual(plain("ταύτης. §1.44 οὐδεμίαν γὰρ").split(), ["ταύτης.", "οὐδεμίαν", "γὰρ"])

    def test_quotes_and_elision(self):
        # ’ closes a quotation that ‘ opened, also on a later line; otherwise it is a wrong elision sign
        r, open_ = quote_remarks("ἀπιέναι, ‘ἵνα σύ γε’ ἔφη ‘πειρᾷς ἐνταῦθα", False)
        self.assertEqual((r, open_), ([], True))
        r, open_ = quote_remarks("εἷλκες αὐτήν.’ κἀγὼ μὲν ἐγέλων, ἀλλʼ οὕτως", open_)
        self.assertEqual((r, open_), ([], False))
        r, open_ = quote_remarks("ἀλλ’ ἐν ἁπάσῃ", False)
        self.assertEqual(len(r), 1)
        r, _ = quote_remarks("παρ᾽ ὑμῖν", False)
        self.assertEqual(len(r), 1)
        # a second ‘ inside an open quotation (Hude at 1.16) leaves one quotation open, closed by one ’
        r, open_ = quote_remarks("‘μηδεμιᾷ πολυπραγμοσύνῃ πεύσει. ‘ἔστι δʼ’ ἔφη ‘Ἐρατοσθένης ἔχει.’ ταῦτα", False)
        self.assertEqual((r, open_), ([], False))


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

    def test_misprints(self):
        from anagnosis_pipeline import hude_merge

        old = dict(hude_merge.MISPRINTS)
        olda = dict(hude_merge.APPARATUS_MISPRINTS)
        try:
            hude_merge.MISPRINTS["t"] = [("40.2", "μικρὰς", "μακρὰς"), ("40.4", "ἀκηκόατε· καί", "ἀκηκόατε, καὶ"), ("40.9", "x", "y")]
            problems: list[str] = []
            notes = hude_merge.correct_misprints("t", self.text, problems)
            self.assertEqual(notes, [(0, "μακρὰς: Hude prints μικρὰς, a misprint; corrected in this edition."),
                                     (2, "ἀκηκόατε, καὶ: Hude prints ἀκηκόατε· καί, a misprint; corrected in this edition.")])
            self.assertEqual(self.text["units"][0]["words"][-2][0], "μακρὰς")
            self.assertIn("ἀκηκόατε, καὶ", " ".join(w for w, _k in self.text["units"][2]["words"]))
            self.assertEqual(len(problems), 1)
            hude_merge.APPARATUS_MISPRINTS["t"] = [("40.2", "μακρὰς", "μακράς"), ("40.2", "nothing", "x")]
            problems = []
            self.assertEqual(hude_merge.correct_apparatus("t", self.pages, problems), 1)
            self.assertEqual(self.pages["p-0040"]["apparatus"][2][1],
                             "μικρὰς Xᶜ: μακράς C H [μακράς: Hude's apparatus prints μακρὰς, a misprint; corrected in this edition.]")
            self.assertEqual(len(problems), 1)
        finally:
            hude_merge.MISPRINTS.clear(); hude_merge.MISPRINTS.update(old)
            hude_merge.APPARATUS_MISPRINTS.clear(); hude_merge.APPARATUS_MISPRINTS.update(olda)

    def test_heading_at_a_speechs_end(self):
        # the documents read after a speech's last words: a heading before the next speech's title
        batch = BATCH.replace("40.6\tἀκούετε, ὦ ἄνδρες, ὅτι κελεύει.\n", "40.6\tἀκούετε, ὦ ἄνδρες, ὅτι κελεύει.\n40.7\t[label] ΝΟΜΟΙ. ΟΡΚΟΙ.\n")
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "batch-01.md").write_text(batch, encoding="utf-8")
            text = assemble(read_batches(Path(t)), INDEX)
        self.assertEqual(text["problems"], [])
        self.assertEqual([(u["n"], u.get("after")) for u in text["units"] if u.get("after")], [("1.3b", ["ΝΟΜΟΙ. ΟΡΚΟΙ."])])


if __name__ == "__main__":
    unittest.main()


class Commentaries(unittest.TestCase):
    def test_entries(self):
        from anagnosis_pipeline.drama import LYSIAS_GILLIES, LYSIAS_NOTES

        # one commentary to a speech: Adams 8, Morgan 3, Shuckburgh 8; Gillies's six speeches
        by = {}
        for speech, row in LYSIAS_NOTES.items():
            by.setdefault(row[0], []).append(speech)
        self.assertEqual(sorted(by["adams"]), [12, 16, 19, 22, 24, 25, 32, 34])
        self.assertEqual(sorted(by["morgan"]), [7, 23, 31])
        self.assertEqual(sorted(by["shuckburgh"]), [5, 9, 10, 13, 14, 17, 28, 30])
        self.assertEqual(sorted(LYSIAS_GILLIES), [1, 3, 4, 21, 26, 34])
        p = PLAYS["lysias-12"]
        self.assertEqual((p.notes_layout, p.last_note, p.route), ("college", 100, "hude-notes"))
        self.assertEqual(PLAYS["lysias-10"].notes_layout, "back")
        self.assertTrue(PLAYS["lysias-10"].notes_text_leaves)
        self.assertTrue(PLAYS["lysias-07"].intro_foot_columns and not PLAYS["lysias-12"].intro_foot_columns)
        self.assertTrue(PLAYS["lysias-gillies-04"].long_s)
        # the new options are off for every other entry
        for slug, play in PLAYS.items():
            if not slug.startswith("lysias-"):
                self.assertEqual((play.long_s, play.intro_foot_columns, play.last_note, play.unhide if slug != "lysias" else ()),
                                 (False, False, 0, ()), slug)
                self.assertNotIn(play.notes_layout, ("college", "back"), slug)

    def test_college_lemma(self):
        from anagnosis_pipeline.drama_prose import college_lemma, split_lemmas

        self.assertEqual(college_lemma("κινδυνεύειν ἐδόκει, ὡς... ὑπάρχοντος : it seemed"),
                         "**κινδυνεύειν ἐδόκει, ὡς . . . ὑπάρχοντος**: it seemed")
        self.assertEqual(college_lemma("βαδίζειν : to go on"), "**βαδίζειν**: to go on")
        self.assertEqual(college_lemma("ἥκω κτλ.: note the short"), "**ἥκω κτλ.**: note the short")
        self.assertEqual(college_lemma("κινδυνεύειν is usually"), "**κινδυνεύειν** is usually")   # no colon: as Jebb's
        self.assertEqual(split_lemmas("σιγᾶν: Lysias would.—ὡς ἥξων ἐκεῖσε : on the", first=True, lemma=college_lemma),
                         ["**σιγᾶν**: Lysias would.", "**ὡς ἥξων ἐκεῖσε**: on the"])

    def test_long_s(self):
        from anagnosis_pipeline.drama_prose import long_s

        english = {"should", "possession", "himself", "of", "defence", "said", "first", "same", "fame", "self-defence"}
        for read, want in (("fhould", "should"), ("ſhould", "should"), ("poffeffion", "possession"), ("himfelf,", "himself,"),
                           ("of", "of"), ("defence", "defence"), ("faid", "said"), ("firft", "first"), ("fame", "fame"),
                           ("Athenians!", "Athenians!"), ("xyzf", "xyzf"), ("poffeflion", "possession"), ("{aid", "said")):
            self.assertEqual(long_s(read, english), want, read)

    def test_own_oration(self):
        from anagnosis_pipeline.drama_prose import _own_oration

        def line(y, text):
            return {"bbox": [100, y, 900, y + 40], "words": [{"text": w} for w in text.split()]}

        play = PLAYS["lysias-10"]           # Shuckburgh's ORATION IV. [10.]: notes on leaves 258-268
        first, last = play.leaves("notes")[0], play.leaves("notes")[-1]
        page = [line(100, "the end of the notes on the speech before"), line(300, "ORATION IV. [10.]"), line(400, "This speech was"),
                line(500, "4. κελεύοντος on his demand")]
        self.assertEqual([" ".join(w["text"] for w in l["words"])[:9] for l in _own_oration(play, first, page)],
                         ["ORATION I", "This spee", "4. κελεύο"])
        end = [line(100, "210. the last note"), line(300, "ORATION V. [12]."), line(400, "the next speech's introduction")]
        self.assertEqual(len(_own_oration(play, last, end)), 1)
        self.assertEqual(len(_own_oration(play, first + 2, page[2:])), 2)   # a middle page: all of it


class NotesPlacement(unittest.TestCase):
    SECTIONS = {"12.12": "ἐπιτυγχάνει μηλόβιός τε καὶ μνησιθείδης ἐκ τοῦ ἐργαστηρίου ἀπιόντες".split(),
                "12.13": "πείσων δὲ προσελθὼν σιγᾶν μοι παρεκελεύετο καὶ θαρρεῖν ὡς ἥξων ἐκεῖσε κινδυνεύειν ἐδόκει ὡς τοῦ γε ἀποθανεῖν ὑπάρχοντος ἤδη".split(),
                "12.14": "καλέσας δὲ δάμνιππον λέγω πρὸς αὐτὸν τάδε ἀδικῶ δʼ οὐδέν".split()}

    def setUp(self):
        from anagnosis_pipeline.drama import skel

        self.sections = {k: [skel(w) for w in v] for k, v in self.SECTIONS.items()}

    def test_lemma_parts(self):
        from anagnosis_pipeline.hude_notes import lemma_parts

        self.assertEqual(lemma_parts("**κινδυνεύειν ἐδόκει, ὡς . . . ὑπάρχοντος**: it seemed"),
                         [["κινδυνευειν", "εδοκει", "ωσ"], ["υπαρχοντοσ"]])
        self.assertEqual(lemma_parts("**ἥκω κτλ.**: note"), [["ηκω"]])
        self.assertEqual(lemma_parts("A note without a lemma."), [])
        self.assertEqual(lemma_parts("**Wakefield** reads"), [])

    def test_place(self):
        from anagnosis_pipeline.hude_notes import place

        # in the section named; in the one beside it (the editions divide the sections otherwise);
        # not in Hude's text at all (another reading): it stays where the commentator puts it
        self.assertEqual(place(12, [13], "**σιγᾶν**: Lysias would have us suspect", self.sections), ("12.13", "lemma"))
        self.assertEqual(place(12, [13], "**κινδυνεύειν ἐδόκει, ὡς . . . ὑπάρχοντος**: it seemed", self.sections), ("12.13", "lemma"))
        self.assertEqual(place(12, [13], "**Δάμνιππον**: this is all that we know", self.sections), ("12.14", "near"))
        self.assertEqual(place(12, [13], "**πείσας**: so the MSS.", self.sections), ("12.13", "miss"))
        self.assertEqual(place(12, [13], "See Crit. Note.", self.sections), ("12.13", "none"))
        # Shuckburgh's line holds the end of one section and the start of the next: both are tried
        self.assertEqual(place(12, [12, 13], "**θαρρεῖν**: to be of good cheer", self.sections), ("12.13", "lemma"))
        # a section number beyond the speech's last is brought back to it
        self.assertEqual(place(12, [40], "No lemma here.", self.sections)[0], "12.14")

    def test_split_notes(self):
        from anagnosis_pipeline.hude_notes import line_sections, split_notes

        intro, notes = split_notes(["# Introduction", "This speech was delivered", "in 384.", "## 4", "**κελεύοντος** ‘on his demand.’",
                                    "## 6-8", "**συμβολαίων** ‘business’", "**ἐνόμιζον** ‘I used to think.’"])
        self.assertEqual(intro, ["This speech was delivered", "in 384."])
        self.assertEqual(notes, [("4", ["**κελεύοντος** ‘on his demand.’"]), ("6-8", ["**συμβολαίων** ‘business’", "**ἐνόμιζον** ‘I used to think.’"])])
        lines = {5: [1, 1, 1], 6: [1, 2, 2, 2], 9: [3]}
        self.assertEqual(line_sections(lines, 6), [2, 1])
        self.assertEqual(line_sections(lines, 5, 6), [1, 2])
        self.assertEqual(line_sections(lines, 7), [2, 1])     # a line not in the map: the nearest before
        self.assertEqual(line_sections({}, 7), [])


class WordsAndTranslation(unittest.TestCase):
    def test_syntax_by_speech(self):
        from anagnosis_pipeline.hude_merge import NO_SYNTAX, SPEECH_NAMES, syntax_kind

        self.assertEqual([k for k in range(1, 35) if syntax_kind(k) == "manual"], [1, 14, 15, 23, 24])
        self.assertEqual([k for k in range(1, 35) if syntax_kind(k) == "none"], [12, 13, 19])
        self.assertEqual(sum(1 for k in range(1, 35) if syntax_kind(k) == "automatic"), 26)
        self.assertEqual(sorted(SPEECH_NAMES), list(range(1, 35)))
        self.assertEqual(NO_SYNTAX, {12, 13, 19})

    def test_vocatives(self):
        from anagnosis_pipeline.hude_merge import vocatives
        table = {"ἄνδρες": [("ἄνδρες", "ἀνήρ", "n-p---mn-", "m"), ("ἄνδρες", "ἀνήρ", "n-p---mv-", "m")],
                 "δικασταί": [("δικασταί", "δικαστής", "n-p---mn-", "m"), ("δικασταί", "δικαστής", "n-p---mv-", "m")],
                 "ἡγοῦμαι": [("ἡγοῦμαι", "ἡγέομαι", "v1spie---", "m")]}
        rows = [{"form": f, "lemma": l, "postag": t} for f, l, t in (
            ("ἄνδρες", "ἀνήρ", "n-p---mn-"), ("ὦ", "ὦ", "i--------"), ("ἄνδρες", "ἀνήρ", "n-p---mn-"),
            ("δικασταί", "δικαστής", "n-p---mn-"), ("ἡγοῦμαι", "ἡγέομαι", "v1spie---"))]
        self.assertEqual(vocatives(rows, lambda f: table.get(f, [])), 2)
        self.assertEqual([r["postag"] for r in rows], ["n-p---mn-", "i--------", "n-p---mv-", "n-p---mv-", "v1spie---"])

    def test_relatives_and_articles(self):
        from anagnosis_pipeline.hude_merge import relatives_and_articles
        rows = [{"form": f, "lemma": l, "postag": t, "sentence": sent} for f, l, t, sent in (
            ("ὃ", "ὁ", "p-s---mn-", ""), ("οὐκ", "οὐ", "d--------", ""), ("ὅ", "ὁ", "p-s---mn-", ""), ("τι", "τις", "p-s---na-", ""),
            ("ἥ", "ὅς", "p-s---fn-", ""), ("τε", "τε", "g--------", ""), ("ὃ", "ὁ", "p-s---mn-", "1.5"), ("καὶ", "καί", "c--------", ""))]
        self.assertEqual(relatives_and_articles(rows), 3)
        self.assertEqual([(r["lemma"], r["postag"]) for r in rows if r["form"] in ("ὃ", "ὅ", "ἥ")],
                         [("ὅς", "p-s---na-"), ("ὅς", "p-s---na-"), ("ὁ", "l-s---fn-"), ("ὁ", "p-s---mn-")])  # the trees' word is left

    def test_english_stops(self):
        from anagnosis_pipeline.hude_notes import english_stops as f
        self.assertEqual(f("we had not settled our differences ; and though it be so : he said, why ? Athenians !"),
                         "we had not settled our differences; and though it be so: he said, why? Athenians!")
        self.assertEqual(f("(as he says) ; *so* : and “thus” ?"), "(as he says); *so*: and “thus”?")
        # after a Greek word ; may be the Greek question mark: untouched, as are · and a ; that stands close
        self.assertEqual(f("he asks τί δέ ; and goes on"), "he asks τί δέ ; and goes on")
        self.assertEqual(f("τί δέ; πῶς · οὕτως ·"), "τί δέ; πῶς · οὕτως ·")
        # a colon is no Greek stop: after a lemma it loses its space, between Greek words it stays
        self.assertEqual(f("**κινδυνεύειν** : *to run a risk*"), "**κινδυνεύειν**: *to run a risk*")
        self.assertEqual(f("αἰνέσαι : ἐπαινέσαι"), "αἰνέσαι : ἐπαινέσαι")
        # an elision typed with the closing quotation mark becomes the Greek's own apostrophe
        self.assertEqual(f("ὁ δ’ ἔφασκεν and **κᾆτ’**: after; but ‘ἐς τὰς χύτρας’ (cf. Ar.)"),
                         "ὁ δʼ ἔφασκεν and **κᾆτʼ**: after; but ‘ἐς τὰς χύτρας’ (cf. Ar.)")
        # nothing else moves: a time, a ratio, a stop already close
        self.assertEqual(f("at 3:15; so: yes"), "at 3:15; so: yes")

    def test_checked_analyses(self):
        import tempfile
        from anagnosis_pipeline import hude_analyses as H
        self.assertEqual(H.describe("v3saia---"), "verb, 3rd singular aorist indicative active")
        self.assertEqual(H.describe("v-sapamn-"), "verb, aorist participle active, singular masculine nominative")
        self.assertEqual(H.describe("n-p---mv-"), "noun, plural masculine vocative")
        # the same reading for a learner: gender, part of speech, middle or passive do not count; case does
        self.assertEqual(H.signature("οὗτος", "p-p---ng-", {}), H.signature("οὗτος", "a-p---mg-", {}))
        self.assertEqual(H.signature("γίγνομαι", "v--anm---", {}), H.signature("γίγνομαι", "v--ane---", {}))
        self.assertNotEqual(H.signature("ὁ", "l-s---na-", {}), H.signature("ὁ", "l-s---nn-", {}))
        words = [{"line": "12.1", "ord": k, "form": f, "now": ("", ""), "readings": r} for k, (f, r) in enumerate((
            ("τὸ", [("ὁ", "l-s---na-"), ("ὁ", "l-s---nn-")]), ("πλῆθος", []), ("ἀξιῶ", [("ἄξιος", "a-d---nn-"), ("ἀξιόω", "v1spia---")]),
            ("δοκεῖ", [("δοκέω", "v3spia---"), ("δοκέω", "v2spie---")])))]
        text = H.job_text(1, 12, words, {"12.1": "τὸ πλῆθος ἀξιῶ δοκεῖ"})
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "job-01.tsv"
            f.write_text(text, encoding="utf-8")
            self.assertEqual(len(H.check_job(f)), 3)   # three words, none answered
            self.assertEqual(H.answers(Path(d)), {})   # a half-done file gives nothing to the merge
            lines = text.splitlines()
            items = [i for i, l in enumerate(lines) if l.endswith("→ ")]
            lines[items[0]] += "2"
            lines[items[1]] += "other: ἀξιόω v1spia--- the verb, not the adjective"
            lines[items[2]] += "? either person fits"
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertEqual(H.check_job(f), [])
            self.assertEqual(H.answers(Path(d)), {("12.1", 0): ("τὸ", "ὁ", "l-s---nn-"), ("12.1", 2): ("ἀξιῶ", "ἀξιόω", "v1spia---")})
            lines[items[0]] = lines[items[0]][:-1] + "5"
            lines[items[1]] = lines[items[1]].split("→")[0] + "→ other: ἀξιόω"
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.assertEqual(len(H.check_job(f)), 2)
            (Path(d) / "job-91.tsv").write_text(text.replace("→ ", "→ 1"), encoding="utf-8")
            self.assertEqual(H.answers(Path(d)), {})   # the control jobs never reach the merge
        self.assertEqual(H._frame("12.1:0\tx\ty\t→ 2\n"), H._frame("12.1:0\tx\ty\t→ \n"))

    def test_footnote_over_a_page(self):
        from anagnosis_pipeline.hude_notes import join_footnotes
        got = join_footnotes(["Text.¹", "[Note: ¹ Lysias had three brothers, Pole-]", "More text.", "[Note: marchus, Euthydemus, and Brachyllus.]",
                              "[Note: A second paragraph of the same note.]", "[Note: ² Another note,]", "[Note: ³ and a marked one.]"])
        self.assertEqual(got, ["Text.¹", "[Note: ¹ Lysias had three brothers, Polemarchus, Euthydemus, and Brachyllus.]", "More text.",
                               "[Note: A second paragraph of the same note.]", "[Note: ² Another note,]", "[Note: ³ and a marked one.]"])

    def test_gillies_marks(self):
        from anagnosis_pipeline.hude_merge import _batch_text, gillies_segments
        paras = ["# An Oration", "§1 It is wonderful, O Senators! he should pretend. §3 But granting I was his enemy.",
                 "[Note: a A note.]", "He goes on without a mark.", "§5 Another paragraph."]
        segs, wrong = gillies_segments(paras)
        self.assertEqual(wrong, [])
        self.assertEqual([n for n, _ in segs], [1, 3, 5])
        self.assertEqual(segs[0][1], "It is wonderful, O Senators! he should pretend.")
        self.assertEqual(segs[1][1], "But granting I was his enemy.\n\nHe goes on without a mark.")
        # the marks must rise; text before the first mark has no place
        self.assertEqual(len(gillies_segments(["Unplaced.", "§4 One.", "§4 Two.", "§2 Three."])[1]), 3)
        # the alignment pass may add marks and nothing else: the flags and notes do not count
        was = "=== p-0607\nIt is wonderful. But granting.\n--- notes\nnone\n"
        now = "=== p-0607\n§1 It is wonderful. §3 But granting.\n--- notes\nplaced by the alignment pass\n"
        self.assertEqual(_batch_text(was), _batch_text(now))
        self.assertNotEqual(_batch_text(was), _batch_text(now.replace("wonderful", "wonderfull")))

    def test_compound_verbs(self):
        from anagnosis_pipeline.hude_merge import _join_prefix, compound_analysis

        self.assertEqual([_join_prefix(a, b) for a, b in (("κατα", "ἕζομαι"), ("ἀπο", "ἄγω"), ("συν", "λέγω"), ("ἐκ", "ἐλαύνω"),
                                                          ("ἐν", "βάλλω"), ("περι", "ὁράω"), ("ἀπο", "γράφω"), ("ἀπο", "ἵημι"))],
                         ["καθέζομαι", "ἀπάγω", "συλλέγω", "ἐξελαύνω", "ἐμβάλλω", "περιοράω", "ἀπογράφω", "ἀφίημι"])
        forms = {"εχορηγησε": [("ἐχορήγησε", "χορηγέω", "v3saia---")], "ιεναι": [("ἱέναι", "ἵημι", "v--pna---"), ("ἰέναι", "εἶμι", "v--pna---")],
                 "εγραψασ": [("ἔγραψας", "γράφω", "v2saia---")]}
        import unicodedata

        def analyse(form):
            key = "".join(c for c in unicodedata.normalize("NFD", form.lower()) if not unicodedata.combining(c)).replace("ς", "σ")
            return forms.get(key, [])

        known = lambda lemma: lemma in ("καταχορηγέω", "ἄπειμι", "ἀφίημι", "ἀπογράφω", "προσαπογράφω")  # noqa: E731
        self.assertEqual(compound_analysis("κατεχορήγησε", analyse, known), ("καταχορηγέω", "v3saia---"))
        self.assertEqual(compound_analysis("ἀπέγραψας", analyse, known), ("ἀπογράφω", "v2saia---"))
        self.assertEqual(compound_analysis("προσαπέγραψας", analyse, known), ("προσαπογράφω", "v2saia---"))
        # the prefix shows the stem's breathing: ἀφ- before ἱέναι, ἀπ- before ἰέναι
        self.assertEqual(compound_analysis("ἀφιέναι", analyse, known), ("ἀφίημι", "v--pna---"))
        # (ἄπειμι draws its accent back: the joined ἀπεῖμι is in no dictionary, so nothing is offered,
        # and above all not ἀφίημι; such a word goes to the hand table)
        self.assertIsNone(compound_analysis("ἀπιέναι", analyse, known))
        self.assertIsNone(compound_analysis("κατεχορήγησε", analyse, lambda lemma: False))
        self.assertIsNone(compound_analysis("λόγος", analyse, known))

    def test_names_have_hudes_letters(self):
        from anagnosis_pipeline.hude_merge import SPEECH_NAMES, _letters

        self.assertEqual(_letters(SPEECH_NAMES[16][0]), _letters("ΕΝ ΒΟΥΛΗΙ ΜΑΝΤΙΘΕΩΙ ΔΟΚΙΜΑΖΟΜΕΝΩΙ ΑΠΟΛΟΓΙΑ"))
        self.assertEqual(_letters(SPEECH_NAMES[27][0]), _letters("ΚΑΤΑ ΕΠΙΚΡΑΤΟΥΣ ΚΑΙ ΤΩΝ ΣΥΜΠΡΕ- ΣΒΕΥΤΩΝ ΕΠΙΛΟΓΟΣ [ΩΣ ΘΕΟΔΩΡΟΣ]"))
        self.assertEqual(_letters(SPEECH_NAMES[4][0]), _letters("ΠΕΡΙ ΤΡΑΥΜΑΤΟΣ ΕΚ ΠΡΟΝΟΙΑΣ, ΥΠΕΡ ΟΥ ΚΑΙ ΠΡΟΣ ΟΝ ⟨ΑΔΗΛΟΝ⟩"))

    def test_translation_1898(self):
        from anagnosis_pipeline.hude_merge import translation_1898

        text = ("front matter\n\nORATION II.\n\nFUNERAL ORATION.\n\n\n1. If I thought it possible, in 12 days. 2. And though\nmy words "
                "relate.\n\n3. First, then, _I_ will review.\n\nWITNESSES.\n\n5. The Amazons were once.\n\n\n\nORATION V.\n\nCALLIAS.\n\n"
                "1. If Callias were contending.\n\n*** END OF THE PROJECT GUTENBERG EBOOK ***\n1. licence\n")
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "pg.txt"
            p.write_text(text, encoding="utf-8")
            got, problems = translation_1898(p)
        self.assertEqual(problems, [])
        self.assertEqual(got[2], [(1, "If I thought it possible, in 12 days."), (2, "And though my words relate."),
                                  (3, "First, then, *I* will review. WITNESSES."), (5, "The Amazons were once.")])
        self.assertEqual(got[5], [(1, "If Callias were contending.")])
