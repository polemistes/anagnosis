import unittest

from anagnosis_pipeline import greek
from anagnosis_pipeline.import_perseus import align_tokens
from anagnosis_pipeline.textfmt import Document, Line


def tb(form, lemma, line, postag="x--------"):
    return {
        "sentence": "1", "word_id": "1", "line": line, "form": form, "lemma": lemma,
        "postag": postag, "head": "0", "relation": "", "is_word": greek.is_word(form),
    }


class AlignTest(unittest.TestCase):
    def test_tokenize(self):
        toks = [t for t, _, _ in greek.tokenize("ἆρʼ οἶσθʼ ὅ τι, ʼφάπτουσα;")]
        self.assertEqual(toks, ["ἆρʼ", "οἶσθʼ", "ὅ", "τι", ",", "ʼφάπτουσα", ";"])

    def test_simple_and_merged(self):
        doc = Document(items=[Line("5", "οὔτʼ αἰσχρὸν οὔτʼ ἄτιμόν ἐσθʼ"), Line("6", "τῶν σῶν")])
        words = [
            tb("οὔ", "οὔτε", "5"), tb("τ̓", "τε", "5"), tb("αἰσχρὸν", "αἰσχρός", "5"),
            tb("οὔ", "οὔτε", "5"), tb("τ̓", "τε", "5"), tb("ἄτιμόν", "ἄτιμος", "5"),
            tb("ἐσθ̓", "εἰμί", "5"), tb(",", ",", "5"), tb("τῶν", "ὁ", "6"), tb("σῶν", "σός", "6"),
        ]
        rows, warnings = align_tokens(doc, words)
        self.assertEqual(warnings, [])
        self.assertEqual([r["lemma"] for r in rows], ["οὔτε", "αἰσχρός", "οὔτε", "ἄτιμος", "εἰμί", "ὁ", "σός"])
        self.assertEqual(rows[0]["form"], "οὔτʼ")  # text form wins over the treebank's

    def test_line_drift_is_ignored(self):
        doc = Document(items=[Line("117", "στὰς δʼ ὑπὲρ"), Line("118", "λόγχαις στόμα")])
        words = [tb("στὰς", "ἵστημι", "118"), tb("δ̓", "δέ", "118"), tb("ὑπὲρ", "ὑπέρ", "118"),
                 tb("λόγχαις", "λόγχη", "119"), tb("στόμα", "στόμα", "119")]
        rows, warnings = align_tokens(doc, words)
        self.assertEqual(warnings, [])
        self.assertEqual([r["line"] for r in rows], ["117", "117", "117", "118", "118"])

    def test_unmatched_is_reported(self):
        doc = Document(items=[Line("1", "ἄλφα βῆτα γάμμα δέλτα ἔψιλον")])
        words = [tb("ἄλφα", "ἄλφα", "1"), tb("ζῆτα", "ζῆτα", "1"), tb("γάμμα", "γάμμα", "1"),
                 tb("δέλτα", "δέλτα", "1"), tb("ἔψιλον", "ἔψιλον", "1")]
        rows, warnings = align_tokens(doc, words)
        self.assertEqual(len(warnings), 1)
        self.assertIn("paired", warnings[0])
        self.assertEqual(rows[1]["lemma"], "ζῆτα")  # paired positionally, flagged for review


if __name__ == "__main__":
    unittest.main()
