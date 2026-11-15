import unittest
import unicodedata

from anagnosis_pipeline.greek import betacode_to_unicode, length_signs_over


def marks(s: str) -> list[str]:
    return [hex(ord(c)) for c in unicodedata.normalize("NFD", s) if unicodedata.combining(c)]


class VowelLengthTest(unittest.TestCase):
    """Betacode ^ and _ become a breve and a macron over their vowel, as in print."""

    def test_short_and_long_vowels_get_their_mark(self):
        self.assertEqual(betacode_to_unicode("pa^ra/"), "πᾰρά")
        self.assertEqual(betacode_to_unicode("i_"), "ῑ")
        self.assertEqual(betacode_to_unicode("[a^g]"), "[ᾰγ]")
        self.assertEqual(betacode_to_unicode("ba_sei=mai"), "βᾱσεῖμαι")

    def test_the_mark_stands_first_over_the_letter(self):
        # before the breathing and the accent, whatever its place in the Betacode
        self.assertEqual(marks(betacode_to_unicode("a^)/kouon"))[:3], ["0x306", "0x313", "0x301"])
        self.assertEqual(marks(betacode_to_unicode("polu^/-gonon")), ["0x306", "0x301"])
        self.assertEqual(marks(betacode_to_unicode("*)a_")), ["0x304", "0x313"])

    def test_words_without_length_marks_are_unchanged(self):
        self.assertEqual(betacode_to_unicode("e)/rxomai"), "ἔρχομαι")
        self.assertEqual(betacode_to_unicode("lo/gos"), "λόγος")

    def test_a_mark_that_follows_no_vowel_is_left_alone(self):
        # metrical schemes in English text, and a dash after a consonant
        self.assertIn("^", betacode_to_unicode("^ ^"))
        self.assertTrue(betacode_to_unicode("q_").endswith("—"))


class LengthSignsTest(unittest.TestCase):
    """˘ and ¯ written beside a vowel (Perseus's &breve; &macr;) go over it; free signs stay."""

    def test_a_sign_after_a_vowel_is_its_length_mark(self):
        self.assertEqual(marks(length_signs_over("γενύ¯ων")), ["0x304", "0x301"])
        self.assertEqual(length_signs_over("(α˘)"), "(ᾰ)")
        self.assertEqual(length_signs_over("Πάνδι¯α"), "Πάνδῑα")
        self.assertEqual(length_signs_over("aera¯"), "aerā")

    def test_free_signs_and_schemes_are_left(self):
        for s in ("¯¯ ˘˘", "¯˘˘¯", "only of ˘: see", "ἐστι ¯˘˘¯", "α¯˘˘¯", "ν¯"):
            self.assertEqual(length_signs_over(s), s)


if __name__ == "__main__":
    unittest.main()
