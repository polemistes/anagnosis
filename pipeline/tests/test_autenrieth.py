import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.autenrieth import also_headwords, entries_from, parse_autenrieth, read_batches, render, second_headwords, sort_key

BATCH = """=== a-0037
--- head
ἁμαρτέω | ἀμείβω
--- left
+ *to hit*, τινός, Ε 287.
**ἁμαρτῇ**, **ἁμαρτῆ** (ἅμα): *at once, together.*
1. **ἀ-μέρδω** (μέρος): *deprive*, τινός, θ 64.
--- right
+ *dreadful;* voc., ρ 219.
**ἀμείβω**: I. act., *change;* —II. mid., *answer*, Α 604, 605.
--- notes
nothing
"""


class AutenriethTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "batch-000.md").write_text(BATCH, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_continuations_join_the_entry_before(self):
        entries = entries_from(read_batches(self.dir))
        self.assertEqual([(h, n) for h, n, _t in entries], [("ἁμαρτῇ", 0), ("ἀ-μέρδω", 1), ("ἀμείβω", 0)])
        self.assertTrue(entries[1][2].endswith("θ 64. *dreadful;* voc., ρ 219."))

    def test_render_marks_meanings_references_and_senses(self):
        html = render("**ἀμείβω**: I. act., *change;* —II. mid., *answer*, Α 604, 605.")
        self.assertIn('<b class="orth">ἀμείβω</b>', html)
        self.assertIn('<i class="tr">change;</i>', html)
        self.assertIn('<span class="bibl">Α 604, 605</span>', html)
        self.assertIn('<p class="sense"><b>II.</b> mid.', html)

    def test_second_headword_and_homograph(self):
        self.assertEqual(also_headwords("**ἁμαρτῇ**, **ἁμαρτῆ** (ἅμα): *at once*"), ["ἁμαρτῆ"])
        entries = parse_autenrieth(self.dir)
        self.assertEqual([e.headword for e in entries], ["ἁμαρτῇ", "ἀμέρδω", "ἀμείβω"])
        self.assertEqual(entries[1].homograph, 1)
        self.assertEqual([(k, e.headword) for k, e in second_headwords(self.dir, entries)], [("ἁμαρτῆ", "ἁμαρτῇ")])

    def test_sort_key_ignores_diacritics_hyphens_and_final_sigma(self):
        self.assertEqual(sort_key("Ἀ-μείλικτος"), "αμειλικτοσ")


if __name__ == "__main__":
    unittest.main()
