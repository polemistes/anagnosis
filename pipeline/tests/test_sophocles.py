import unittest

from lxml import etree

from anagnosis_pipeline.commentary import _md, _txt
from anagnosis_pipeline.sophocles import _printed, apply_text_check, perseus_anchors
from anagnosis_pipeline.sophocles_pages import bold_lemmas
from anagnosis_pipeline.textfmt import Document, Line


def doc_of(*lines: tuple[str, str]) -> Document:
    doc = Document(meta={})
    for n, text in lines:
        doc.items.append(Line(n, text))
    return doc


class TextCheck(unittest.TestCase):
    def test_difference_found_by_its_words_near_a_shifted_number(self):
        # the transcriber numbered by the print, one higher than this import
        doc = doc_of(("10", "ἀλλʼ ὦ φίλαι"), ("11", "τίς ἐστιν οὗτος;"), ("12", "ὦ τέκνον, εἰ σοί"))
        _, _, warnings = apply_text_check(doc, [], [("12", False, "οὗτος;", "οὗτος.")], set())
        self.assertEqual(warnings, [])
        self.assertEqual(doc.lines[1].text, "τίς ἐστιν οὗτος.")

    def test_reference_text_decides_between_lines_with_the_same_words(self):
        doc = doc_of(("1", "ὦ παῖ, λέγε."), ("2", "ὦ παῖ, σίγα."))
        reference = {"5": "ὦ παῖ, σίγα."}
        apply_text_check(doc, [], [("5", False, "ὦ παῖ,", "ὦ παῖ")], set(), reference)
        self.assertEqual([l.text for l in doc.lines], ["ὦ παῖ, λέγε.", "ὦ παῖ σίγα."])

    def test_inserted_line_follows_the_reference_line(self):
        doc = doc_of(("554", "ἐν τῷ φρονεῖν γὰρ μηδὲν ἥδιστος βίος,"), ("555", "ἕως τὸ χαίρειν"))
        reference = {"554": "ἐν τῷ φρονεῖν γὰρ μηδὲν ἥδιστος βίος,"}
        apply_text_check(doc, [], [("554", True, "", "[τὸ μὴ φρονεῖν γὰρ κάρτʼ ἀνώδυνον κακόν,]")], set(), reference)
        self.assertEqual(doc.lines[1].text, "[τὸ μὴ φρονεῖν γὰρ κάρτʼ ἀνώδυνον κακόν,]")

    def test_printed_conventions(self):
        self.assertEqual(_printed("*τοιοῖσδ’ <γὰρ>"), "τοιοῖσδʼ ⟨γὰρ⟩")
        self.assertEqual(_printed("* * * μή"), "* * * μή")

    def test_perseus_anchor_kept_only_far_from_printed_numbers(self):
        doc = doc_of(*[(str(n), "λόγος") for n in range(1, 41)])
        lines = doc.lines
        stated = {id(lines[4]): "5", id(lines[34]): "35"}
        printed = {9: "10"}
        self.assertEqual(perseus_anchors(lines, stated, printed), {34: "35"})


    def test_lyric_pass_splits_and_joins_verses(self):
        doc = doc_of(("1", "ἰὼ πόροι ἁλίρροθοι πάραλά τʼ ἄντρα"), ("2", "καὶ νέμος"), ("3", "ἐπάκτιον,"))
        lyrics = [("1", False, "ἁλίρροθοι πάραλά", "ἁλίρροθοι | πάραλά"),
                  ("3", False, "ἐπάκτιον,", ""), ("2", False, "καὶ νέμος", "καὶ νέμος ἐπάκτιον,")]
        _, _, warnings = apply_text_check(doc, [], [], set(), None, lyrics)
        self.assertEqual(warnings, [])
        self.assertEqual([l.text for l in doc.lines],
                         ["ἰὼ πόροι ἁλίρροθοι", "πάραλά τʼ ἄντρα", "καὶ νέμος ἐπάκτιον,"])


class Commentary(unittest.TestCase):
    def test_english_aside_inside_greek_quotation(self):
        x = '<p><quote lang="greek">e)/stai <note place="inline" lang="en">(we shall hear of him)</note> a)namixqh/setai</quote></p>'
        self.assertEqual(" ".join(_md(etree.fromstring(x), False).split()), "ἔσται (we shall hear of him) ἀναμιχθήσεται")

    def test_parentheses_and_elisions_in_betacode(self):
        self.assertEqual(_txt("kai\\ a)\\n xrh/sima (o)/nta) e)reuna=|", True), "καὶ ἂν χρήσιμα (ὄντα) ἐρευνᾷ")
        self.assertEqual(_txt("e)ntau=q) h)\\ )gw/", True), "ἐνταῦθʼ ἢ ʼγώ")
        self.assertEqual(_txt("w)= xqo/ni) *(ermh=", True), "ὦ χθόνιʼ Ἑρμῆ")
        self.assertEqual(_txt("ka)gw/ tou)/noma prou)/sthn", True), "κἀγώ τοὔνομα προὔστην")

    def test_parenthesis_opened_in_english_closed_in_greek(self):
        x = '<p>wore garlands (<quote lang="greek">e)stefanwme/noi)</quote>, and</p>'
        self.assertEqual(_md(etree.fromstring(x), False).strip(), "wore garlands (ἐστεφανωμένοι), and")


class Lemmas(unittest.TestCase):
    def test_lemma_does_not_run_over_a_full_stop(self):
        self.assertEqual(bold_lemmas("Nauck, s. v. ὑπόβλητον. σαυτοῦ] σεαυτοῦ L."),
                         "Nauck, s. v. ὑπόβλητον. **σαυτοῦ**] σεαυτοῦ L.")


if __name__ == "__main__":
    unittest.main()
