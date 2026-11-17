"""The record of the trees' text made from a text's files (syntax_text.record_from_files) and
the checking pass over the kinds of difference (syntax_differences.py)."""
import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline import syntax_differences, syntax_text

HEAD = "line\tord\tform\tlemma\tpostag\trelation\thead\tsentence\tword_id"
TOKENS = [
    "1.1\t0\tκἀγὼ\tἐγώ\tp-s---mn-\tSBJ\t5\ts1\t2",          # the trees: "κ-" and "ἀγὼ"; it carries the second
    "1.1\t1\tμήτε\tμήτε\tc--------\t\t\t\t",                  # the trees: "-τε", "μή"; not linked
    "1.1\t2\tλέγω\tλέγω\tv1spia---\tPRED\t0\ts1\t5",
    "1.1\t3\tναυμαχίᾳ\tναυμαχία\tn-s---fn-\tADV\t5\ts1\t6",   # the trees: ναυμαχία, a nominative
    "1.1\t4\tνέος\tνέος\ta-s---mn-\t\t\t\t",                  # not in the trees' text
    "1.1\t5\tὁ\tὁ\tl-s---mn-\tATR\t9\ts1\t8",                 # the trees: "G?ὁ", a gap mark on it
    "1.1\t6\tλόγος\tλόγος\tn-s---mn-\tSBJ\t5\ts1\t9",         # the trees: λόγον
]
NODES = ["sentence\tword_id\tform\tlemma\tpostag\trelation\thead\tartificial",
         "s1\t1\tκ-\tκαί\tc--------\tCOORD\t0\t", "s1\t3\t-τε\tτε\tc--------\tCOORD\t0\t", "s1\t4\tμή\tμή\td--------\tAuxZ\t5\t",
         "s1\t7\tἐκεῖ\tἐκεῖ\td--------\tADV\t5\t", "s1\t10\t.\t.\tu--------\tAuxK\t0\t"]


def tree(i, form, lemma, postag, relation, head, word=True):
    return {"sentence": "s1", "word_id": str(i), "form": form, "lemma": lemma, "postag": postag, "relation": relation, "head": str(head),
            "is_word": word, "artificial": False}


TB = [tree(1, "κ-", "καί", "c--------", "COORD", 0), tree(2, "ἀγὼ", "ἐγώ", "p-s---mn-", "SBJ", 5),
      tree(3, "-τε", "τε", "c--------", "COORD", 0), tree(4, "μή", "μή", "d--------", "AuxZ", 5),
      tree(5, "λέγω", "λέγω", "v1spia---", "PRED", 0), tree(6, "ναυμαχία", "ναυμαχία", "n-s---fn-", "ADV", 5),
      tree(7, "ἐκεῖ", "ἐκεῖ", "d--------", "ADV", 5), tree(8, "G?ὁ", "ὁ", "l-s---mn-", "ATR", 9),
      tree(9, "λόγον", "λόγος", "n-s---ma-", "SBJ", 5), tree(10, ".", ".", "u--------", "AuxK", 0, word=False)]
HAND = {"1.1 ναυμαχίᾳ": ("ναυμαχία", "n-s---fd-")}


def work(d: str) -> Path:
    w = Path(d) / "text"
    w.mkdir()
    (w / "grc.txt").write_text("# title: T\n# lang: grc\n# syntax: manual\n\n== book 1\n1.1\tκἀγὼ μήτε λέγω ναυμαχίᾳ νέος, ὁ λόγος.\n", encoding="utf-8")
    (w / "tokens.tsv").write_text("\n".join([HEAD] + TOKENS) + "\n", encoding="utf-8")
    (w / "syntax-nodes.tsv").write_text("\n".join(NODES) + "\n", encoding="utf-8")
    return w


class FromFiles(unittest.TestCase):
    def run_it(self, w, **kw):
        return syntax_text.record_from_files(w, TB, "another text", hand=HAND, **kw)

    def test_the_record_and_the_token_lines(self):
        with tempfile.TemporaryDirectory() as d:
            w = work(d)
            out = self.run_it(w)
            rows = {r["form"] or r["tree_form"]: r for r in out["rows"]}
            tokens = (w / "tokens.tsv").read_text(encoding="utf-8").split("\n")
            # a word that carries one of the two words the trees write for it: a unit, the token as it was,
            # the other half still a node and no unprinted word
            self.assertEqual((rows["κἀγὼ"]["kind"], rows["κἀγὼ"]["tree_form"]), ("unit", "κ- ἀγὼ"))
            self.assertEqual(tokens[1], TOKENS[0])
            self.assertNotIn("κ-", rows)
            self.assertIn("s1\t1\tκ-", (w / "syntax-nodes.tsv").read_text(encoding="utf-8"))
            # our one word is two tree words, the enclitic first in the trees: both ids, the coordinator's syntax
            self.assertEqual(rows["μήτε"]["kind"], "unit")
            self.assertEqual(tokens[2], "1.1\t1\tμήτε\tμήτε\tc--------\tCOORD\t0\ts1\t3+4")
            self.assertNotIn("s1\t3\t", (w / "syntax-nodes.tsv").read_text(encoding="utf-8"))
            # an iota subscript is a letter: a reading, and the word gets its own analysis
            self.assertEqual((rows["ναυμαχίᾳ"]["kind"], rows["ναυμαχίᾳ"]["tree_form"]), ("reading", "ναυμαχία"))
            self.assertEqual(tokens[4], "1.1\t3\tναυμαχίᾳ\tναυμαχία\tn-s---fd-\tADV\t5\ts1\t6")
            self.assertEqual(rows["ναυμαχίᾳ"]["difference"], "form")
            # a word the trees' text has not: its sentence, no node
            self.assertEqual((rows["νέος"]["kind"], rows["νέος"]["sentence"]), ("absent", "s1"))
            self.assertEqual(tokens[5], "1.1\t4\tνέος\tνέος\ta-s---mn-\t\t\ts1\t")
            # a gap mark on the trees' word is no other reading; another form is; a tree word not printed
            self.assertNotIn("ὁ", rows)
            self.assertEqual((rows["λόγος"]["kind"], rows["λόγος"]["tree_form"]), ("reading", "λόγον"))
            self.assertEqual(rows["ἐκεῖ"]["kind"], "unprinted")
            self.assertEqual(out["kinds"], {"unit": 2, "reading": 2, "absent": 1, "unprinted": 1})
            self.assertIn("# syntax-text: another text", (w / "grc.txt").read_text(encoding="utf-8"))
            self.assertEqual(out["look"], [])

    def test_run_again_gives_the_same(self):
        with tempfile.TemporaryDirectory() as d:
            w = work(d)
            self.run_it(w)
            first = {p.name: p.read_text(encoding="utf-8") for p in w.iterdir()}
            out = self.run_it(w)
            self.assertEqual(out["changed tokens"], 0)
            self.assertEqual(first, {p.name: p.read_text(encoding="utf-8") for p in w.iterdir()})

    def test_dry_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            w = work(d)
            before = {p.name: p.read_text(encoding="utf-8") for p in w.iterdir()}
            out = self.run_it(w, write=False)
            self.assertEqual(before, {p.name: p.read_text(encoding="utf-8") for p in w.iterdir()})
            self.assertEqual(out["kinds"]["reading"], 2)

    def test_a_checked_difference_enters_where_the_words_are_the_same(self):
        with tempfile.TemporaryDirectory() as d:
            w = work(d)
            answers = {("1.1", 6): ("λόγος", "λόγον", "word"), ("1.1", 3): ("ναυμαχίᾳ", "ναυμαχίαν", "spelling")}
            out = self.run_it(w, answers=answers)
            got = {r["form"]: r["difference"] for r in out["rows"] if r["kind"] == "reading"}
            self.assertEqual(got, {"λόγος": "word", "ναυμαχίᾳ": "form"})  # the second answer was given for another tree word
            self.assertEqual(out["differences checked"], 1)

    def test_sentences_that_really_differ(self):
        rows = [{"kind": "reading", "difference": "spelling", "sentence": "a"}, {"kind": "reading", "difference": "form", "sentence": "b"},
                {"kind": "unit", "difference": "", "sentence": "c"}, {"kind": "absent", "difference": "", "sentence": "d"},
                {"kind": "unprinted", "difference": "", "sentence": "e"}, {"kind": "absent", "difference": "", "sentence": ""}]
        self.assertEqual(syntax_text.really_differing(rows), 3)
        # a sentence none of our words stands in is never shown
        self.assertEqual(syntax_text.really_differing(rows, [{"sentence": "b"}, {"sentence": "d"}, {"sentence": ""}]), 2)


class Differences(unittest.TestCase):
    def jobs(self, d):
        w = work(d)
        syntax_text.record_from_files(w, TB, "another text", hand=HAND)
        texts = Path(d)
        (texts / "text").rename(texts / "sample")
        jobs = texts / "jobs"
        done = syntax_differences.make_jobs(texts, ["sample"], jobs)
        return texts, jobs, done

    def test_jobs_check_and_answers(self):
        with tempfile.TemporaryDirectory() as d:
            texts, jobs, done = self.jobs(d)
            self.assertEqual(done, ["sample: 2 readings in 1 job files"])
            path = jobs / "sample-01.tsv"
            items = syntax_differences.read_job(path)
            self.assertEqual([(i["line"], i["ord"], i["form"], i["tree_form"], i["rule"]) for i in items],
                             [("1.1", 3, "ναυμαχίᾳ", "ναυμαχία", "form"), ("1.1", 6, "λόγος", "λόγον", "form")])
            self.assertIn("«ναυμαχίᾳ»", path.read_text(encoding="utf-8"))
            self.assertEqual(len(syntax_differences.check_job(path)), 2)          # not answered
            self.assertEqual(syntax_differences.answers("sample", jobs), {})      # a half-done file is not used
            text = path.read_text(encoding="utf-8").split("\n")
            arrows = [k for k, l in enumerate(text) if l.endswith("→ ")]
            text[arrows[0]] += "form"
            text[arrows[1]] += "word"                                             # changed without a reason
            path.write_text("\n".join(text), encoding="utf-8")
            self.assertEqual(len(syntax_differences.check_job(path)), 1)
            text[arrows[1]] += " another word in the trees' text"
            path.write_text("\n".join(text), encoding="utf-8")
            self.assertEqual(syntax_differences.check_job(path), [])
            self.assertEqual(syntax_differences.answers("sample", jobs),
                             {("1.1", 3): ("ναυμαχίᾳ", "ναυμαχία", "form"), ("1.1", 6): ("λόγος", "λόγον", "word")})
            # an existing file is never written again
            self.assertEqual(syntax_differences.make_jobs(texts, ["sample"], jobs), ["sample: job files exist already; none written"])

    def test_a_short_last_job_joins_the_one_before(self):
        self.assertEqual(syntax_differences.split(list(range(13)), 6), [[0, 1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11, 12]])
        self.assertEqual(syntax_differences.split(list(range(14)), 6), [[0, 1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11], [12, 13]])
        self.assertEqual(syntax_differences.split(list(range(4)), 6), [[0, 1, 2, 3]])

    def test_an_answer_that_is_no_kind(self):
        with tempfile.TemporaryDirectory() as d:
            _texts, jobs, _ = self.jobs(d)
            path = jobs / "sample-01.tsv"
            path.write_text(path.read_text(encoding="utf-8").replace("→ ", "→ same"), encoding="utf-8")
            self.assertTrue(all("not understood" in p for p in syntax_differences.check_job(path)))
            self.assertEqual(syntax_differences.answers("sample", jobs), {})


if __name__ == "__main__":
    unittest.main()
