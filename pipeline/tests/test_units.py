"""Words the text prints apart and the treebank as one (αἵ θʼ for αἵθʼ): odyssey.align, units."""
import unittest

from anagnosis_pipeline.odyssey import align
from anagnosis_pipeline.textfmt import Document, Line


def word(i, form, lemma, postag, relation, head):
    return {"form": form, "lemma": lemma, "postag": postag, "relation": relation, "head": str(head), "sentence": "s1",
            "word_id": str(i), "is_word": True, "artificial": False}


TB = [word(1, "Μουσάων", "Μοῦσα", "n-p---fg-", "OBJ", 2), word(2, "ἀρχώμεθα", "ἄρχω", "v1ppsm---", "PRED", 0),
      word(3, "αἵθʼ", "ὅστε", "p-p---fn-", "SBJ", 5), word(4, "Ἑλικῶνος", "Ἑλικών", "n-s---mg-", "ATR", 6),
      word(5, "ἔχουσιν", "ἔχω", "v3ppia---", "ATR", 1), word(6, "ὄρος", "ὄρος", "n-s---na-", "OBJ", 5)]


def doc():
    d = Document(meta={})
    d.items += [Line("1", "Μουσάων ἀρχώμεθα,"), Line("2", "αἵ θʼ Ἑλικῶνος ἔχουσιν ὄρος")]
    return d


class Units(unittest.TestCase):
    def test_off_by_default(self):
        rows, _ = align(doc(), TB)
        by = {(r["line"], r["form"]): r for r in rows}
        self.assertEqual((by[("2", "αἵ")]["sentence"], by[("2", "θʼ")]["sentence"]), ("", ""))
        self.assertEqual(by[("2", "Ἑλικῶνος")]["word_id"], "4")

    def test_a_unit_on_the_tree_words_node(self):
        rows, _ = align(doc(), TB, keep_tb_form=True, units=True)
        by = {(r["line"], r["form"]): r for r in rows}
        first, second = by[("2", "αἵ")], by[("2", "θʼ")]
        # the first word carries the node; its lemma is left to the analyser (the tree's is ὅστε)
        self.assertEqual((first["sentence"], first["word_id"], first["relation"], first["head"]), ("s1", "3", "SBJ", "5"))
        self.assertEqual((first["lemma"], first["postag"], first["tb_form"]), ("", "p-p---fn-", "αἵθʼ"))
        # the second belongs to the same node: the sentence, the id written "=3", no relation of its own
        self.assertEqual((second["sentence"], second["word_id"], second["relation"], second["head"], second["lemma"]), ("s1", "=3", "", "", ""))
        # the words around are as before
        self.assertEqual([by[("2", f)]["word_id"] for f in ("Ἑλικῶνος", "ἔχουσιν", "ὄρος")], ["4", "5", "6"])
        self.assertEqual(by[("1", "ἀρχώμεθα")]["lemma"], "ἄρχω")

    def test_a_verse_at_another_place(self):
        # the trees' text has the verse "Ἑλικῶνος ἔχουσιν ὄρος" before "Μουσάων ἀρχώμεθα"; ours after
        tb = [word(1, "Ἑλικῶνος", "Ἑλικών", "n-s---mg-", "ATR", 3), word(2, "ἔχουσιν", "ἔχω", "v3ppia---", "PRED", 0),
              word(3, "ὄρος", "ὄρος", "n-s---na-", "OBJ", 2), word(4, "Μουσάων", "Μοῦσα", "n-p---fg-", "OBJ", 5),
              word(5, "ἀρχώμεθα", "ἄρχω", "v1ppsm---", "PRED", 0), word(6, "ἀείδειν", "ἀείδω", "v--pna---", "OBJ", 5)]
        d = Document(meta={})
        d.items += [Line("1", "Μουσάων ἀρχώμεθα ἀείδειν"), Line("2", "Ἑλικῶνος ἔχουσιν ὄρος")]
        rec = []
        rows, _ = align(d, tb, units=True, record=rec)
        self.assertEqual([(r["form"], r["word_id"]) for r in rows if r["line"] == "2"], [("Ἑλικῶνος", "1"), ("ἔχουσιν", "2"), ("ὄρος", "3")])
        self.assertEqual(rec, [])
        rows, _ = align(d, tb)
        self.assertEqual({r["word_id"] for r in rows if r["line"] == "2"} & {"1", "2", "3"} or {r["word_id"] for r in rows if r["line"] == "1"} & {"4", "5", "6"},
                         {r["word_id"] for r in rows if r["sentence"]})   # without the option only one of the two verses is linked

    def test_only_the_same_letters(self):
        d = Document(meta={})
        d.items += [Line("1", "Μουσάων ἀρχώμεθα,"), Line("2", "οἵ θʼ Ἑλικῶνος ἔχουσιν ὄρος")]
        rows, _ = align(d, TB, units=True)
        self.assertEqual([r["sentence"] for r in rows if r["form"] in ("οἵ", "θʼ")], ["", ""])


if __name__ == "__main__":
    unittest.main()


class TreesText(unittest.TestCase):
    """What each word is to the text the trees were made on (syntax_text.py)."""

    def rows(self):
        d = Document(meta={})
        d.items += [Line("1", "Μουσάων ἀρχώμεθα,"), Line("2", "αἵ θʼ [Ἑλικῶνος] ἔχουσι πέλωρ ὄρος"), Line("3", "νέος στίχος ὅλος")]
        rec = []
        rows, _ = align(d, TB, keep_tb_form=True, units=True, record=rec)
        return rows, rec

    def test_the_record(self):
        rows, rec = self.rows()
        got = {(r["line"], r["form"]): (r["kind"], r["tree_form"]) for r in rec}
        self.assertEqual(got[("2", "αἵ")], ("unit", "αἵθʼ"))
        self.assertEqual(got[("2", "θʼ")], ("unit", "αἵθʼ"))
        self.assertNotIn(("2", "Ἑλικῶνος"), got)                       # a bracket on the word is no other reading
        self.assertNotIn(("1", "Μουσάων"), got)                        # the tree's own word
        self.assertEqual({k: v[0] for k, v in got.items() if k[0] == "3"},
                         {("3", "νέος"): "absent", ("3", "στίχος"): "absent", ("3", "ὅλος"): "absent"})

    def test_decisions_runs_and_table(self):
        import sqlite3, tempfile
        from pathlib import Path
        from anagnosis_pipeline import syntax_text as S
        rec = [{"line": "2", "ord": 3, "form": "ἔχουσι", "kind": "reading", "tree_form": "ἔχουσιν", "tree_lemma": "ἔχω", "tree_postag": "v3ppia---", "sentence": "s1", "word_id": "5"},
               {"line": "2", "ord": 4, "form": "πέλωρ", "kind": "reading", "tree_form": "ὄρος", "tree_lemma": "ὄρος", "tree_postag": "n-s---na-", "sentence": "s1", "word_id": "6"},
               {"line": "3", "ord": 0, "form": "νέος", "kind": "absent", "tree_form": "", "tree_lemma": "", "sentence": "", "word_id": ""},
               {"line": "3", "ord": 1, "form": "στίχος", "kind": "absent", "tree_form": "", "tree_lemma": "", "sentence": "", "word_id": ""},
               {"line": "3", "ord": 2, "form": "ὅλος", "kind": "absent", "tree_form": "", "tree_lemma": "", "sentence": "", "word_id": ""}]
        rows = [{"line": "2", "ord": 3, "form": "ἔχουσι", "relation": "ATR", "head": "1", "sentence": "s1", "word_id": "5"},
                {"line": "2", "ord": 4, "form": "πέλωρ", "relation": "OBJ", "head": "5", "sentence": "s1", "word_id": "6"}]
        from anagnosis_pipeline import drama_fixes
        drama_fixes.TREE_READINGS["test-text"] = {"2 ἔχουσι": ("keep", "the same form"), "2 πέλωρ": ("drop", "another word in another role")}
        try:
            self.assertEqual(S.settle("test-text", rows, rec), [])
        finally:
            del drama_fixes.TREE_READINGS["test-text"]
        # in the same construction: the token carries the node itself
        self.assertEqual((rows[0]["sentence"], rows[0]["word_id"], rows[0]["relation"], rec[0]["same_construction"]), ("s1", "5", "ATR", "1"))
        # in another: the token keeps the sentence only; the record still names the tree word's node
        self.assertEqual((rows[1]["sentence"], rows[1]["word_id"], rows[1]["relation"], rows[1]["head"]), ("s1", "", "", ""))
        self.assertEqual((rec[1]["kind"], rec[1]["sentence"], rec[1]["word_id"], rec[1]["tree_form"], rec[1]["same_construction"]),
                         ("reading", "s1", "6", "ὄρος", "0"))
        self.assertEqual(S.settle("another-text", rows, rec[:1]), ["2 ἔχουσι"])                           # no decision: named
        self.assertEqual(S._runs([True, False, True, True, True]), [1, 0, 3, 3, 3])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "syntax-text.tsv"
            used = {("s1", str(i)) for i in (1, 2, 3, 5)}        # node 4 has no word of ours; node 6 is tied to πέλωρ by the record
            counts = S.write_record(path, rec, TB, used, {"2": 5, "3": 3})
            self.assertEqual(counts, {"reading": 2, "absent": 3, "unprinted": 1})
            got = S.read_record(path)
            self.assertEqual([r["extent"] for r in got], ["", "", "passage", "passage", "passage", "word"])
            self.assertEqual((got[-1]["kind"], got[-1]["word_id"], got[-1]["tree_form"]), ("unprinted", "4", "Ἑλικῶνος"))
            db = sqlite3.connect(":memory:")
            db.executescript("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT); CREATE TABLE lines (id INTEGER PRIMARY KEY, n TEXT);"
                             "CREATE TABLE tokens (id INTEGER PRIMARY KEY, line_id INTEGER, ord INTEGER);")
            db.executemany("INSERT INTO lines VALUES (?,?)", [(1, "2"), (2, "3")])
            db.executemany("INSERT INTO tokens VALUES (?,?,?)", [(10, 1, 3), (11, 1, 4), (12, 2, 0), (13, 2, 1), (14, 2, 2)])
            self.assertEqual(S.build_table(db, Path(d)), 6)
            self.assertEqual(db.execute("SELECT kind, token_id, sentence, word_id, tree_form, tree_postag, same_construction FROM syntax_text_words ORDER BY id").fetchall()[:2],
                             [("reading", 10, "s1", 5, "ἔχουσιν", "v3ppia---", 1), ("reading", 11, "s1", 6, "ὄρος", "n-s---na-", 0)])
            self.assertEqual(db.execute("SELECT value FROM meta WHERE key = 'syntax_text_words'").fetchone(), ("6",))
            # a text without the file gets no table
            db2 = sqlite3.connect(":memory:")
            self.assertEqual(S.build_table(db2, Path(d) / "none"), 0)
            self.assertEqual(db2.execute("SELECT count(*) FROM sqlite_master").fetchone(), (0,))
