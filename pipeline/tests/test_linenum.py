import unittest

from anagnosis_pipeline.linenum import complete, parts
from anagnosis_pipeline.textfmt import parse


class LineNumberTest(unittest.TestCase):
    def test_plain_and_book_numbers(self):
        self.assertEqual(parts("161b"), (161, "b"))
        self.assertEqual(parts("1.12"), (1012, ""))
        self.assertEqual(parts("16.101"), (16101, ""))
        self.assertEqual(parts("1.93a"), (1093, "a"))
        with self.assertRaises(ValueError):
            parts("1.x")

    def test_stephanus_lines(self):
        self.assertEqual(parts("172a1"), (172001, ""))
        self.assertEqual(parts("172b3"), (172103, ""))
        self.assertLess(parts("172e12")[0], parts("173a1")[0])
        doc = parse("172a1\t{ΑΠΟΛ.} Δοκῶ μοι\n172a2\tεἶναι.\n")
        self.assertEqual([l.n for l in doc.lines], ["172a1", "172a2"])

    def test_speaker_label_is_not_a_word(self):
        from anagnosis_pipeline import greek
        self.assertEqual([w for w, _s, _e in greek.words("{ΑΠΟΛ.} Δοκῶ μοι")], ["Δοκῶ", "μοι"])

    def test_short_range_end_takes_the_book(self):
        self.assertEqual(complete("7", "1.5"), "1.7")
        self.assertEqual(complete("2.3", "1.5"), "2.3")
        self.assertEqual(complete("7", "5"), "7")

    def test_short_range_end_takes_the_stephanus_page(self):
        self.assertEqual(complete("5", "172a3"), "172a5")
        self.assertEqual(complete("b2", "172a3"), "172b2")
        self.assertEqual(complete("173a1", "172e4"), "173a1")

    def test_text_format_accepts_book_lines(self):
        doc = parse("== book 1\n1.1\tἄνδρα μοι ἔννεπε\n1.2\tπλάγχθη\n")
        self.assertEqual([l.n for l in doc.lines], ["1.1", "1.2"])
        self.assertLess(doc.lines[0].sort_key, doc.lines[1].sort_key)

    def test_verses(self):
        self.assertEqual(parts("1.5.3"), (1005003, ""))
        self.assertEqual(parts("27.22.21"), (27022021, ""))
        self.assertEqual(parts("5.20.28b"), (5020028, "b"))
        self.assertLess(parts("1.28.20")[0], parts("2.1.1")[0])
        self.assertEqual(complete("7", "1.5.3"), "1.5.7")
        self.assertEqual(complete("6.2", "1.5.3"), "1.6.2")
        doc = parse("== book Matthew\n1.1.1\tΒίβλος γενέσεως\n1.1.2\tἈβραὰμ ἐγέννησεν\n1.1.2b\tἸσαὰκ δὲ\n")
        self.assertEqual([l.n for l in doc.lines], ["1.1.1", "1.1.2", "1.1.2b"])
        self.assertLess(doc.lines[1].sort_key, doc.lines[2].sort_key)


if __name__ == "__main__":
    unittest.main()
