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


if __name__ == "__main__":
    unittest.main()
