import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.drama import (SIDGWICK_NOTE, bold_lemma, greek_speeches, note_heading, number_verses,
                                      perseus_map, perseus_play, place_notes, speech_segments)
from anagnosis_pipeline.drama_pages import abbreviation, match_speaker

TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><div type="edition">
<div type="textpart" subtype="episode">
<sp><speaker>Φύλαξ</speaker>
<l n="0"><hi rend="strong">Φύλαξ</hi></l>
<l n="1">θεοὺς μὲν αἰτῶ τῶνδʼ ἀπαλλαγὴν πόνων</l>
<l n="2"><del>ἀστέρας, ὅταν φθίνωσιν</del>.</l>
</sp>
</div>
<div type="textpart" subtype="choral">
<div type="textpart" subtype="strophe" n="1">
<sp><speaker>Χορός</speaker>
<l n="3">οἰωνῶν βασιλεὺς βασιλεῦσι νε-</l>
<l n="5">ῶν ὁ κελαινός<gap reason="lost"/></l>
<l n="6"><gap reason="lost"/></l>
</sp>
<sp><speaker>Χορός</speaker>
<l n="7">ἔτι ⟨γε⟩ λέγω</l>
</sp>
<sp><speaker>Κλυταιμήστρα</speaker>
<stage>ἔνδοθεν</stage>
<l n="7b">ἰώ.</l>
</sp>
</div></div>
</div></body></text></TEI>
"""


def tok(base, n=None):
    return {"base": base, "n": n or str(base)}


class NumberingTest(unittest.TestCase):
    def test_rule(self):
        toks = [tok(1), tok(1), tok(2), tok(2), tok(3), tok(4), tok(5)]
        verses = [[0, 1], [2], [3], [4, 5], [6]]
        got = [n for n, _f in number_verses(verses, toks)]
        # a second verse in Perseus line 2 gets a letter; a verse covering 3 and 4 is 3, and 4 is skipped
        self.assertEqual(got, ["1", "2", "2a", "3", "5"])
        flags = number_verses(verses, toks)[2][1]
        self.assertTrue(any(f.startswith("lettered") for f in flags))

    def test_perseus_letters_and_going_back(self):
        toks = [tok(15), tok(15, "15b"), tok(15, "15c"), tok(16), tok(14)]
        got = number_verses([[0], [1], [2], [3], [4]], toks)
        self.assertEqual([n for n, _f in got], ["15", "15a", "15b", "16", "16a"])
        self.assertTrue(any("go back" in f for f in got[4][1]))


class PerseusTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "play.xml"
        self.path.write_text(TEI, encoding="utf-8")
        self.p = perseus_play(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_tokens(self):
        t = self.p["tokens"]
        words = [x["t"] for x in t]
        self.assertEqual(words[:6], ["θεοὺς", "μὲν", "αἰτῶ", "τῶνδʼ", "ἀπαλλαγὴν", "πόνων"])
        self.assertIn("[ἀστέρας,", words)
        self.assertIn("φθίνωσιν].", words)
        # a word divided between verses is one word, on the first verse
        joined = next(x for x in t if x["t"] == "νεῶν")
        self.assertEqual(joined["n"], "3")
        self.assertEqual(t[words.index("ὁ")]["first"], True)
        # the display line n="0" is left out
        self.assertNotIn("Φύλαξ", words)

    def test_speakers_sections_gaps(self):
        t = self.p["tokens"]
        starts = [(x["t"], x["speaker"]) for x in t if x["newsp"]]
        # the chorus's second <sp> is not a new speech
        self.assertEqual(starts, [("θεοὺς", "Φύλαξ"), ("οἰωνῶν", "Χορός"), ("ἰώ.", "Κλυταιμήστρα")])
        self.assertEqual([s[2:] for s in self.p["sections"]], [("episode", ""), ("choral", ""), ("strophe", "1")])
        self.assertTrue(next(x for x in t if x["t"] == "κελαινός")["gap"])
        self.assertTrue(self.p["lines"][[l["n"] for l in self.p["lines"]].index("6")]["gap"])
        self.assertEqual(self.p["stages"], [(words_index(t, "λέγω"), "ἔνδοθεν")])
        self.assertEqual(t[-1]["base"], 7)

    def test_map(self):
        # the edition joins Perseus lines 1 and 2 into one verse, and divides line 3 in two
        lines = [("1", "θεοὺς μὲν αἰτῶ τῶνδʼ ἀπαλλαγὴν πόνων ἀστέρας, ὅταν φθίνωσιν."),
                 ("3", "οἰωνῶν βασιλεὺς"), ("3a", "βασιλεῦσι νεῶν ὁ κελαινός"), ("7", "ἔτι γε λέγω"), ("7a", "ἰώ.")]
        m = perseus_map(lines, self.p)
        ns = [l["n"] for l in self.p["lines"]]
        self.assertEqual(m[ns.index("1")], 0)
        self.assertEqual(m[ns.index("2")], 0)
        self.assertEqual(m[ns.index("5")], 2)
        self.assertEqual(m[ns.index("6")], 3)  # a lost verse goes with the next
        self.assertEqual(m[ns.index("7b")], 4)


def words_index(t, w):
    return [x["t"] for x in t].index(w)


class NotesTest(unittest.TestCase):
    def test_headings(self):
        self.assertEqual(note_heading("l. 1201. κυρεῖν λέγουσαν, ‘tell aright of.’", SIDGWICK_NOTE)[0], "1201")
        self.assertEqual(note_heading("ll. 1345-51. The second agon", SIDGWICK_NOTE)[0], "1345-1351")
        default = r"^(?:l{1,2}\.\s*)?(\d{1,4})(?:\s*[-–—]\s*(\d{1,4}))?(?:\s*f{1,2}\.|\s*sqq?\.)?[.,:]?(?=\s|$)"
        self.assertEqual(note_heading("215 f. ἀλλʼ ὦ", default)[0], "215")
        self.assertEqual(note_heading("779 ὁ δῆμος: as if", default)[0], "779")
        self.assertEqual(note_heading("1058, 1059 τί δαί;", default)[0], "1058-1059")
        self.assertIsNone(note_heading("The MSS. read", SIDGWICK_NOTE))
        self.assertIsNone(note_heading("1201 κυρεῖν", SIDGWICK_NOTE))

    def test_lemma(self):
        self.assertEqual(bold_lemma("κυρεῖν λέγουσαν, ‘tell aright of.’"), "**κυρεῖν λέγουσαν**, ‘tell aright of.’")
        self.assertEqual(bold_lemma("κρίσιν ποεῖν: not = κρίνειν"), "**κρίσιν ποεῖν**: not = κρίνειν")
        self.assertEqual(bold_lemma("ἁβρύνεται, ‘grows over nice.’"), "**ἁβρύνεται**, ‘grows over nice.’")
        self.assertEqual(bold_lemma("The vision of Thyestes’ children"), "The vision of Thyestes’ children")

    def test_place(self):
        notes = [("1", ["a"]), ("4", ["b"]), ("5-9", ["c"]), ("5-9", ["d"])]
        placed, problems = place_notes(notes, ["1", "2", "3", "5", "6", "8"])
        self.assertEqual(placed, [("1", ["a"]), ("3", ["b"]), ("5-8", ["c", "d"])])
        self.assertEqual(len(problems), 1)


class SpeechesTest(unittest.TestCase):
    def test_segments(self):
        items = [("@", "Ἀ", "")] + [("line", str(n), "λόγος " * 8) for n in (1, 2, 3)]
        items += [("@", "Β", "")] + [("line", str(n), "λόγος " * 8) for n in range(4, 30)]
        items += [("@", "Ἀ", "")] + [("line", str(n), "λόγος " * 8) for n in (30, 31)]
        grc = greek_speeches(items)
        long = " ".join(f"Sentence number {k} is here." for k in range(40))
        eng = [("ALPHA", "Short words here, of a few."), ("", "(He goes in.)"),
               ("BETA", long), ("ALPHA", "Two lines' worth.")]
        segs, problems = speech_segments(eng, grc, {"ALPHA": "Ἀ", "BETA": "Β"})
        self.assertEqual(segs[0][0], "1")
        self.assertIn("(He goes in.)", segs[0][2])
        self.assertEqual(segs[1][:2], ("4", "BETA"))
        self.assertGreaterEqual(len([s for s in segs if s[1] == ""]), 1)  # the long speech is cut
        self.assertEqual(segs[-1][:2], ("30", "ALPHA"))
        self.assertEqual(problems, [])


class AbbreviationTest(unittest.TestCase):
    def test_abbreviations(self):
        names = ["Φύλαξ", "Χορός", "Κλυταιμήστρα", "Κασάνδρα", "Ἀγαμέμνων", "Αἴγισθος"]
        self.assertEqual(abbreviation("ΚΛ."), "ΚΛ")
        self.assertEqual(abbreviation("XO."), "ΧΟ")
        self.assertIsNone(abbreviation("θεοὺς"))
        self.assertIsNone(abbreviation("Ὦ"))
        self.assertEqual(match_speaker("ΚΛ", names), "Κλυταιμήστρα")
        self.assertEqual(match_speaker("ΧΟ", names), "Χορός")
        self.assertEqual(match_speaker("ΑΓ", names), "Ἀγαμέμνων")
        self.assertEqual(match_speaker("ΑΙ", names), "Αἴγισθος")
        self.assertEqual(match_speaker("ΦΥΛΑΞ", names), "Φύλαξ")
        self.assertEqual(match_speaker("ΧΟ ΓΕ", ["Χορὸς γερόντων", "Χορὸς Γυναικῶν"]), "Χορὸς γερόντων")


class JebbSophocles(unittest.TestCase):
    def test_check_text_from_our_text_format(self):
        from anagnosis_pipeline.drama import textfile_play

        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "reference-grc.txt"
            p.write_text("# title: x\n\n== episode Prologue\n@ Δηιάνειρα\n1\tλόγος μέν ἐστʼ ἀρχαῖος\n"
                         "@ Ὕλλος\n2\tὡς οὐκ ἂν εὐδαί-\n3\tμων γένοιτο\n=== strophe 1\n3a\tτέλος\n", encoding="utf-8")
            pers = textfile_play(p)
        self.assertEqual([t["t"] for t in pers["tokens"]], ["λόγος", "μέν", "ἐστʼ", "ἀρχαῖος", "ὡς", "οὐκ", "ἂν", "εὐδαίμων", "γένοιτο", "τέλος"])
        self.assertEqual([l["n"] for l in pers["lines"]], ["1", "2", "3", "3a"])
        self.assertEqual(pers["sections"], [(0, 1, "episode", "Prologue"), (3, 2, "strophe", "1")])
        self.assertEqual(pers["speakers"], ["Δηιάνειρα", "Ὕλλος"])
        self.assertTrue(pers["tokens"][0]["newsp"] and pers["tokens"][4]["newsp"] and not pers["tokens"][1]["newsp"])
        self.assertEqual(pers["tokens"][7]["n"], "2")  # the divided word stands whole on the first verse
        self.assertEqual(pers["tokens"][9]["base"], 3)

    def test_apparatus_block_above_the_rule(self):
        from anagnosis_pipeline.drama_pages import _block_above_rule

        def line(y, size, n=3):
            return {"bbox": [200, y, 2200, y + 50], "x_size": size, "words": [{"text": "w"}] * n}

        head = [line(230, 80)]
        verses = [line(430 + 84 * k, 79) for k in range(10)]            # the last at 1186
        apparatus = [line(1330 + 54 * k, 50) for k in range(4)]         # a wider space above it
        commentary = [line(1800 + 54 * k, 52) for k in range(12)]
        lines = head + verses + apparatus + commentary
        self.assertEqual(_block_above_rule(lines, head, 1735), 1330)
        # a page whose verses run down to the rule: no apparatus
        self.assertIsNone(_block_above_rule(head + verses + commentary, head, 1735))


if __name__ == "__main__":
    unittest.main()


class RealignTest(unittest.TestCase):
    def test_refrain(self):
        from anagnosis_pipeline.drama_pages import realign
        from anagnosis_pipeline.gorgias_pages import align

        def w(s):
            return {"skel": s, "t": s}
        refrain = [f"r{k}" for k in range(10)]
        a = [f"a{k}" for k in range(20)]
        b = [f"b{k}" for k in range(20)]
        c = [f"c{k}" for k in range(40)]
        pers = [w(x) for x in refrain + a + b + refrain + c]
        # the print: the OCR garbled every second word of a and b, so the second refrain and c
        # make the longest block
        ocr = [w(x) for x in refrain + [x if k % 2 else x + "q" for k, x in enumerate(a + b)] + refrain + c]
        match = align(ocr, pers)
        realign(ocr, pers, match, run=10, reach=60)
        self.assertEqual(match[0], 0)          # the first refrain to the first
        self.assertEqual(match[50], 50)        # the second to the second
        self.assertEqual(match[21], 21)


class ItemNumberTest(unittest.TestCase):
    def test_bare_numbers(self):
        from anagnosis_pipeline.drama_pages import _item_number

        def w(text, x=100, conf=90):
            return {"text": text, "bbox": [x, 0, x + 40, 20], "conf": conf}

        self.assertTrue(_item_number(w("103.")))
        self.assertFalse(_item_number(w("215")))
        self.assertTrue(_item_number(w("215"), bare=True, right=1700))
        self.assertFalse(_item_number(w("215", x=1800), bare=True, right=1700))  # a margin number
        self.assertFalse(_item_number(w("5", conf=80), bare=True, right=1700))
