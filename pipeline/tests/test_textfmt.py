import unittest

from anagnosis_pipeline.textfmt import Line, Section, Speaker, Stage, parse, serialize

SAMPLE = """# title: Ἀντιγόνη
# lang: grc

== episode
@ Ἀντιγόνη
1\tὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα,
2\tἆρʼ οἶσθʼ ὅ τι Ζεὺς τῶν ἀπʼ Οἰδίπου κακῶν

== choral
=== strophe 1
@ Χορός
!\tEnter the Chorus.
100\tἀκτὶς ἀελίου,
161b\tκοινῷ κηρύγματι πέμψας,
"""


class TextFormatTest(unittest.TestCase):
    def test_parse(self):
        doc = parse(SAMPLE)
        self.assertEqual(doc.meta, {"title": "Ἀντιγόνη", "lang": "grc"})
        self.assertEqual(doc.items[0], Section(1, "episode", ""))
        self.assertEqual(doc.items[1], Speaker("Ἀντιγόνη"))
        self.assertEqual(doc.items[2], Line("1", "ὦ κοινὸν αὐτάδελφον Ἰσμήνης κάρα,"))
        self.assertEqual(doc.items[5], Section(2, "strophe", "1"))
        self.assertEqual(doc.items[7], Stage("Enter the Chorus."))
        self.assertEqual(doc.lines[-1].sort_key, (161, "b"))

    def test_round_trip(self):
        doc = parse(SAMPLE)
        self.assertEqual(parse(serialize(doc)), doc)

    def test_bad_line(self):
        with self.assertRaises(ValueError):
            parse("1 no tab here")

    def test_header_after_content(self):
        with self.assertRaises(ValueError):
            parse("1\tfoo\n# title: x")


if __name__ == "__main__":
    unittest.main()
