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

    def test_only_the_same_letters(self):
        d = Document(meta={})
        d.items += [Line("1", "Μουσάων ἀρχώμεθα,"), Line("2", "οἵ θʼ Ἑλικῶνος ἔχουσιν ὄρος")]
        rows, _ = align(d, TB, units=True)
        self.assertEqual([r["sentence"] for r in rows if r["form"] in ("οἵ", "θʼ")], ["", ""])


if __name__ == "__main__":
    unittest.main()
