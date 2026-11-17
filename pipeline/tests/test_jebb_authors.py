"""Places in Perseus's files of Jebb's commentaries where an author's name may have dropped out."""
import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline import jebb_authors as ja

XML = ('<div1 type="commentary"><p>Then in  <title>Phaedr.</title> 272 B, and  <bibl n="Eur. Andr. 733"> <title>Andr.</title> 733</bibl>; '
       'Eur. <bibl n="Eur. Hec. 5"><title>Hec.</title> 5</bibl>; cp.  <bibl n="Soph. Trach. 856"><title>Tr.</title> 856</bibl> '
       'and  <title>Il.</title> 4. 329; Cp. <bibl n="Plat. Rep. 367e"><title>Rep.</title> 367 E</bibl></p></div1>')


class Places(unittest.TestCase):
    def test_marks(self):
        marked = ja.mark_places(XML)
        self.assertEqual(marked.count(ja.MARK), 3)
        self.assertRegex(marked, rf"Then in +{ja.MARK} +<title>Phaedr\.")          # a bare title after a gap
        self.assertRegex(marked, rf"{ja.MARK} +<bibl n=\"Eur\. Andr\. 733\">")      # a citation that begins with its title
        self.assertIn("Eur. <bibl n=\"Eur. Hec. 5\">", marked)             # the author stands before it
        self.assertIn("cp.  <bibl n=\"Soph. Trach. 856\">", marked)        # Sophocles: Jebb names no author
        self.assertIn("and  <title>Il.</title>", marked)                   # nor for Homer
        self.assertRegex(marked, rf"Cp\. +{ja.MARK} +<bibl n=\"Plat\. Rep\. 367e\">")  # "Cp." is no author

    def test_checker(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "authors-01.tsv"
            path.write_text("# head\n\n== 1 · note 583 · leaves 180, 181\nThen in ⟦A⟧ *Phaedr.* 272 B\n→ Plat.\n\n"
                            "== 2 · note 4 · leaves 76, 77\nἄτερ: ⟦A⟧ *Th.* 683\n→ -\n\n"
                            "== 3 · note 9 · leaves 78, 79\nx ⟦A⟧ *Y.* 1\n→ \n\n"
                            "== 4 · note 9 · leaves 78, 79\nx ⟦A⟧ *Z.* 1\n→ see p. 3 (1)\n", encoding="utf-8")
            problems = ja.check_job(path)
            self.assertEqual(len(problems), 2)
            self.assertIn("not answered", problems[0])
            self.assertIn("not understood", problems[1])
            self.assertEqual([it["answer"] for it in ja.read_job(path)], ["Plat.", "-", "", "see p. 3 (1)"])


if __name__ == "__main__":
    unittest.main()
