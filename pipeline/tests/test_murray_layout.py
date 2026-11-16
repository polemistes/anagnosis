"""Murray's Oxford text: the printer's signature at the foot of a page is not apparatus
(drama_pages._signature, Play.foot_signature)."""
import unittest

from anagnosis_pipeline.drama import PLAYS
from anagnosis_pipeline.drama_pages import METRE_LABEL, _signature

W, H = 1683, 2732


def line(texts, x0, y0):
    words = [{"text": t, "bbox": [x0 + 60 * i, y0, x0 + 60 * i + 50, y0 + 30], "conf": 90} for i, t in enumerate(texts)]
    return {"bbox": [x0, y0, x0 + 60 * len(texts), y0 + 30], "words": words, "x_size": 38.0}


class Signature(unittest.TestCase):
    def test_signatures(self):
        self.assertTrue(_signature(line(["ΕΥΚ.", "1.", "6"], 251, 2377), W, H))   # "EUR. I. 6" as Tesseract reads it
        self.assertTrue(_signature(line(["ΕΚ.", "1.", "10"], 251, 2500), W, H))
        self.assertTrue(_signature(line(["88"], 1318, 2384), W, H))               # "8*" alone at the right
        self.assertTrue(_signature(line(["8:"], 1300, 2375), W, H))
        self.assertTrue(_signature(line(["ΤῈ"], 1305, 2396), W, H))              # "7*"
        sig = line(["ΕὥΕ.Ὶ1:", "8"], 222, 2370)
        sig["words"][1]["bbox"] = [1300, 2370, 1330, 2399]
        self.assertTrue(_signature(sig, W, H))                                   # "EUR. I. 8"

    def test_not_signatures(self):
        self.assertFalse(_signature(line(["74.", "30"], 160, 2329), W, H))        # the end of an apparatus item
        self.assertFalse(_signature(line(["45"], 160, 2329), W, H))               # a number at the left
        self.assertFalse(_signature(line(["88"], 1318, 1200), W, H))              # high on the page
        self.assertFalse(_signature(line(["ΕΥΚ.", "1.", "6", "λόγος]", "x"], 251, 2377), W, H))

    def test_only_murray(self):
        # the options for Murray's page are on for the plays read from his Oxford text, and for
        # no other play (Hude's Lysias, another Oxford text of the same years, shares the page's
        # options but not the metrical labels: tests/test_lysias.py)
        murray = {slug for slug, play in PLAYS.items() if play.app_editor == "murray"}
        self.assertLessEqual({"medea", "alcestis"}, murray)
        for slug in murray:
            self.assertTrue(PLAYS[slug].foot_signature, slug)
            self.assertEqual(PLAYS[slug].verse_size_q, 0.75, slug)
            self.assertTrue(PLAYS[slug].app_pitch_cut, slug)
            self.assertTrue(PLAYS[slug].metre_labels, slug)
        for slug, play in PLAYS.items():
            if slug not in murray and play.route != "hude":
                self.assertFalse(play.foot_signature, slug)
                self.assertEqual(play.verse_size_q, 0.5, slug)
                self.assertFalse(play.app_pitch_cut, slug)
                self.assertFalse(play.metre_labels, slug)


class MetreLabel(unittest.TestCase):
    def test_label_at_the_end_only(self):
        self.assertEqual(METRE_LABEL.sub("", "ὦ πατρίς, ὦ δώματα, μὴ [στρ."), "ὦ πατρίς, ὦ δώματα, μὴ ")
        self.assertEqual(METRE_LABEL.sub("", "στέργοι δέ με σωφροσύνα, [ἀντ."), "στέργοι δέ με σωφροσύνα, ")
        self.assertEqual(METRE_LABEL.sub("", "[νὼ μανεῖσαν ἐκ θεῶν"), "[νὼ μανεῖσαν ἐκ θεῶν")


if __name__ == "__main__":
    unittest.main()
