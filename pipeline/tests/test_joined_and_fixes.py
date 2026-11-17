"""The half a joined word follows (import_perseus.joined_main, syntax_text.mend_joined), the
digamma of the Odyssey commentary, and the fix tables over an imported commentary."""
import contextlib
import io
import unittest

from anagnosis_pipeline import syntax_text
from anagnosis_pipeline.commentary import apply_fixes
from anagnosis_pipeline.import_perseus import joined_main
from anagnosis_pipeline.odyssey import digamma


def w(i, form, relation, head):
    return {"sentence": "s", "word_id": str(i), "form": form, "lemma": form, "postag": "", "relation": relation, "head": str(head)}


def tree(*words):
    return {("s", x["word_id"]): x for x in words}


class Joined(unittest.TestCase):
    def test_the_part_another_part_hangs_on(self):
        ou, de = w(5, "οὐ", "AuxZ", 8), w(6, "δὲ", "MWE", 5)          # GLAUx: the δέ of οὐδέ tied to its οὐ
        self.assertIs(joined_main([ou, de], tree(ou, de, w(8, "ἔφη", "PRED", 0))), ou)
        ei, te = w(7, "εἴ", "MWE", 8), w(8, "τε", "COORD", 3)
        self.assertIs(joined_main([ei, te], tree(ei, te)), te)

    def test_the_part_above_through_another_word(self):
        # οὔτε: the οὔ an AuxZ on a member of the coordination that the τε heads
        ou, te, member = w(19, "οὔ", "AuxZ", 21), w(20, "τε", "AuxY", 28), w(21, "ἔργῳ", "ADV_CO", 20)
        self.assertIs(joined_main([ou, te], tree(ou, te, member, w(28, "ἔβλαψα", "PRED", 0))), te)
        self.assertIs(joined_main([ou, te]), ou)                        # without the tree only the parts' own heads are seen

    def test_neither_above_the_other(self):
        ou, te = w(1, "οὔ", "AuxZ", 5), w(2, "τε", "COORD", 9)         # the part that is no mere particle
        self.assertIs(joined_main([ou, te], tree(ou, te, w(5, "x", "OBJ", 7), w(9, "y", "PRED", 0))), te)

    def test_mending_the_older_merges_words(self):
        ou, de, verb = w(5, "οὐ", "AuxZ", 8), w(6, "δὲ", "MWE", 5), w(8, "ἔφη", "PRED", 0)
        ou2, te2, member = w(19, "οὔ", "AuxZ", 21), w(20, "τε", "AuxY", 28), w(21, "ἔργῳ", "ADV_CO", 20)
        by_id = tree(ou, de, verb, ou2, te2, member, w(28, "ἔβλαψα", "PRED", 0))
        rows = [{"line": "1", "form": "οὐδὲ", "relation": "MWE", "head": "5", "sentence": "s", "word_id": "5+6"},     # hangs on itself
                {"line": "2", "form": "οὔτε", "relation": "AuxZ", "head": "21", "sentence": "s", "word_id": "19+20"},  # on a word under it
                {"line": "3", "form": "ἔφη", "relation": "PRED", "head": "0", "sentence": "s", "word_id": "8"}]
        done = syntax_text.mend_joined(rows, by_id)
        self.assertEqual(len(done), 2)
        self.assertEqual([(r["relation"], r["head"]) for r in rows], [("AuxZ", "8"), ("AuxY", "28"), ("PRED", "0")])
        self.assertEqual(syntax_text.mend_joined(rows, by_id), [])      # a second time nothing


class Digamma(unittest.TestCase):
    def test_a_v_that_touches_greek(self):
        self.assertEqual(digamma("instead of κλέvος, ῥέvοντας; (vάστυ); root vελ; ἀvώς"), "instead of κλέϝος, ῥέϝοντας; (ϝάστυ); root ϝελ; ἀϝώς")
        self.assertEqual(digamma("does not invariably take the *v. Cp."), "does not invariably take the Ϝ. Cp.")

    def test_latin_is_left(self):
        for s in ("Lat. *via*, and", "the v. l. δώμασιν", "Lat. *vă*(*d*)*s*", "*vivid* form", "root *vas*, which"):
            self.assertEqual(digamma(s), s)


class Fixes(unittest.TestCase):
    def test_applied_and_reported(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            got = apply_fixes("**αυ[?]τό**: draws", [("**αυ[?]τό**", "**αὐτό**"), ("not there", "x")], "notes.md")
        self.assertEqual(got, "**αὐτό**: draws")
        self.assertIn("notes.md: fix not applied, not found: not there", out.getvalue())


if __name__ == "__main__":
    unittest.main()
