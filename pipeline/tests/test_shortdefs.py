"""The short definition of a lemma is Logeion's own entry for that word, or none
(texts/README.md, "Short definitions"): no entry of another word is taken."""
import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline import build

LIST = """Ὅμηρος\tHomer
ὅμηρος\ta hostage
φείδων\tan oil-can
Θούριος\tof Thurii
Ζεύς\tZeus
θνῄσκω\tto die
κάλως\ta reefing rope
Οἶον\tOeum
ποτε\tever, sometime
πότε\twhen?
ἦμος\tat which time
ἄϊδρις\tunknowing
ἐϋπλόκαμος\tfair-haired
ὁ\tthe
ἔρως\tlove
περ\tprecisely
δέ\tbut
"""


class ShortDefinitions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "logeion-shortdefs.txt").write_text(LIST, encoding="utf-8")
            cls.exact, cls.loose = build.load_logeion_shortdefs(Path(d))

    def r(self, lemma, capital_in_text=False):
        return build.resolve_short_definition(lemma, self.exact, self.loose, capital_in_text)

    def test_the_word_as_spelt(self):
        self.assertEqual(self.r("Ὅμηρος"), "Homer")
        self.assertEqual(self.r("ὅμηρος"), "a hostage")
        self.assertEqual(self.r("ἔρως"), "love")

    def test_a_name_never_takes_a_common_words_definition(self):
        self.assertIsNone(self.r("Φείδων"))
        self.assertIsNone(self.r("Ἔρως"))

    def test_a_small_lemma_takes_a_name_only_where_the_text_prints_a_capital(self):
        self.assertEqual(self.r("ζεύς", True), "Zeus")
        self.assertIsNone(self.r("ζεύς"))
        self.assertIsNone(self.r("θούριος"))            # "impetuous" in the Ajax, not "of Thurii"
        self.assertEqual(self.r("ὅμηρος", True), "Homer")      # the name first, where every word has the capital
        self.assertEqual(self.r("ὅμηρος"), "a hostage")

    def test_the_same_word_otherwise_written(self):
        self.assertEqual(self.r("θνήσκω"), "to die")           # iota subscript
        self.assertEqual(self.r("ἄιδρις"), "unknowing")        # diaeresis
        self.assertEqual(self.r("εὐπλόκαμος"), "fair-haired")  # ἐϋ- for εὐ-
        self.assertEqual(self.r("ἐυπλόκαμος"), "fair-haired")  # the same without the diaeresis
        self.assertEqual(self.r("ποτέ"), "ever, sometime")     # the enclitic, not πότε
        self.assertEqual(self.r("πέρ"), "precisely")
        self.assertEqual(self.r("δὲ"), "but")                  # a grave for an acute

    def test_another_accent_or_breathing_is_another_word(self):
        self.assertIsNone(self.r("καλῶς"))   # not κάλως, a reefing rope
        self.assertIsNone(self.r("οἷον"))    # not Οἶον, Oeum
        self.assertIsNone(self.r("ἡμός"))    # not ἦμος
        self.assertIsNone(self.r("ὅ"))       # not the article

    def test_the_headword_a_lemma_is_listed_under(self):
        a = lambda lemma, headword: build.alias_short_definition(lemma, headword, self.exact, self.loose)
        self.assertEqual(a("θνήσκομαι", "θνῄσκω"), "to die")
        self.assertEqual(a("Ὁμηρίδης", "ὅμηρος"), "Homer")   # a name under a name
        self.assertEqual(a("ὁμηρεύω", "ὅμηρος"), "a hostage")
        self.assertIsNone(a("Φειδώ", "φείδων"))               # never a common word's definition for a name

    def test_a_name_and_a_common_word_in_one_text(self):
        import sqlite3
        db = sqlite3.connect(":memory:")
        db.executescript("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);"
                         "CREATE TABLE tokens (form TEXT, lemma TEXT);"
                         "CREATE TABLE short_definitions (lemma_key TEXT PRIMARY KEY, source TEXT, definition TEXT);")
        db.executemany("INSERT INTO tokens VALUES (?, ?)", [
            ("Ὅμηρος", "Ὅμηρος"), ("ὁμήρους", "ὅμηρος"),      # the poet and the hostages: two rows
            ("Διὸς", "Ζεύς"),                                  # a name alone: also under the small key, for older readers
            ("Φείδωνα", "Φείδων"), ("ἔρωτι", "ἔρως"), ("Ἔρως", "Ἔρως")])
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "logeion-shortdefs.txt").write_text(LIST, encoding="utf-8")
            build.build_short_definitions(db, Path(d), {}, {})
        rows = dict(db.execute("SELECT lemma_key, definition FROM short_definitions"))
        flag = db.execute("SELECT value FROM meta WHERE key = 'short_definitions_by_spelling'").fetchone()
        db.close()
        self.assertEqual(rows, {"Ὅμηρος": "Homer", "ὅμηρος": "a hostage", "Ζεύς": "Zeus", "ζεύς": "Zeus", "ἔρως": "love"})
        self.assertEqual(flag, ("1",))

    def test_a_line_break_in_a_document(self):
        self.assertEqual(build.md_to_html("904 first verse\\\n914 second verse"), "<p>904 first verse<br>914 second verse</p>")
        self.assertEqual(build.md_to_html("one line\nwrapped"), "<p>one line wrapped</p>")

    def test_words_printed_with_a_capital(self):
        rows = [("Διὸς", "ζεύς"), ("Ζεῦ", "ζεύς"), ("θούριος", "θούριος"), ("Δῆλον", "δῆλος"), ("δῆλον", "δῆλος")]
        self.assertEqual(build.capitalised_lemmas(rows), {"ζεύς"})
        self.assertEqual(build.capitalised_lemmas([("Πῶλε", "πῶλος"), ("Πῶλος", "Πῶλος"), ("πώλους", "Πῶλος")]), {"πῶλος"})


if __name__ == "__main__":
    unittest.main()
