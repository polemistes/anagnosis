import tempfile
import unittest
from pathlib import Path

from anagnosis_pipeline.woodhouse import (
    apply_corrections, apply_lsj_forms, apply_rules, english_key, entries, read_corrections, read_rules, render_entry, render_line,
)

DSL = """Abandon
\t[b]v. trans.[/b]
\t[i]Quit:[/i] [c brown]P.[/c] and [c brown]V.[/c] λείπειν, κ[c blue]α[/c]τ[c blue]α[/c]λείπειν, [c blue]ἀ[/c]πολείπειν.
\t[i]Abandon to slavery:[/i] εἰς δουλείαν προέσθαι ([c brown]Dem.[/c] 102).
\t[i]They abandoned themselves to their fate:[/i] [c brown]P.[/c] προΐεντο σφᾶς αὐτοὺς ἐν τῷ κινδύνῳ ([c brown]Thuc.[/c] 2, 51).
\t[i]See[/i] ([c brown]Eur.[/c], [i]I.
\tT.[/i] 287).

Late
\t[b]adv.[/b]
\t[i]As late us possible:[/i] [c brown]P.[/c] ὠς ὀψιαίτατα.
""".split("\n")


class WoodhouseTest(unittest.TestCase):
    def test_entries_join_lines_left_open(self):
        es = entries(DSL)
        self.assertEqual([e.headword for e in es], ["Abandon", "Late"])
        self.assertEqual(es[0].lines[-1][1], "[i]See[/i] ([c brown]Eur.[/c], [i]I. T.[/i] 287).")

    def test_render(self):
        html = render_entry(entries(DSL)[0])
        self.assertTrue(html.startswith('<p class="head"><b class="orth">Abandon</b>, <span class="gram">v. trans.</span></p>'))
        # length marks are marks again, before the breathing
        self.assertIn('<span class="tr">κᾰτᾰλείπειν</span>', html)
        self.assertIn('<span class="tr">ᾰ̓πολείπειν</span>', html)
        self.assertIn('<span class="usg">P.</span> and <span class="usg">V.</span>', html)
        # three words are a rendering; a quotation of more stays plain
        self.assertIn('<span class="tr">εἰς δουλείαν προέσθαι</span>', html)
        self.assertIn("προΐεντο σφᾶς αὐτοὺς ἐν τῷ κινδύνῳ (", html)
        self.assertNotIn('<span class="tr">προΐεντο', html)

    def test_articles_and_brackets_are_not_renderings(self):
        self.assertEqual(render_line("λείπειν, ἡ, (τινά)"), '<span class="tr">λείπειν</span>, ἡ, (τινά)')

    def test_corrections_and_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "corrections-01.tsv").write_text("# a comment\n11\tus\tas\t500\t\n11\tὠς\tὡς\t500\t\n", encoding="utf-8")
            (d / "global.tsv").write_text("ὀψιαίτατα\tὀψιαίτατα\tnothing to change\n\\[c brown\\]P\\.\\[/c\\] ὡς\t[c brown]P.[/c]  ὡς\tdouble space\n", encoding="utf-8")
            lines = apply_rules(apply_corrections(DSL, read_corrections(d)), read_rules(d))
        self.assertEqual(lines[10], "\t[i]As late as possible:[/i] [c brown]P.[/c]  ὡς ὀψιαίτατα.")

    def test_a_correction_that_does_not_apply_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "corrections-01.tsv").write_text("11\tnot there\tx\t500\t\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                apply_corrections(DSL, read_corrections(d))

    def test_lsj_forms(self):
        forms = {"βλαβή": "βλάβη", "ὁδάξ": "ὀδάξ", "ἀλάζων": "ἀλαζών"}
        lines = ["\tP. βλ[c blue]α[/c]βή, ἡ.", "\tὁδάξ ἐσθίειν, ἀλάζων.", "\tἀβλαβή"]
        self.assertEqual(apply_lsj_forms(lines, forms), ["\tP. βλ[c blue]ά[/c]βη, ἡ.", "\tὀδὰξ ἐσθίειν, ἀλαζών.", "\tἀβλαβή"])

    def test_english_key(self):
        self.assertEqual(english_key("Advised, Be"), "advised be")
        self.assertEqual(english_key("Ædile"), "aedile")


if __name__ == "__main__":
    unittest.main()
