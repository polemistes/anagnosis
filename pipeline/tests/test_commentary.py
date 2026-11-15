"""Jebb's commentary from Perseus (commentary.import_jebb_commentary): the spaces Perseus leaves out
at tag boundaries (a citation run together with its number or with the quotation after it)."""
import tempfile
import unittest
from pathlib import Path

from lxml import etree

from anagnosis_pipeline.commentary import _md_children, import_jebb_commentary


def md(xml: str) -> str:
    return _md_children(etree.fromstring(xml), False).strip()


class CitationSpaces(unittest.TestCase):
    def test_title_and_number(self):
        self.assertEqual(md('<p><bibl n="Hom. Il. 18.126"><title>Il.</title>18. 126</bibl>.</p>'), "*Il.* 18. 126.")
        self.assertEqual(md('<p><bibl n="Pind. O. 7">Pind. <title>O.</title>7. 54</bibl>, id.</p>'), "Pind. *O.* 7. 54, id.")

    def test_title_and_word_or_bracket(self):
        self.assertEqual(md("<p>Plut. <title>Mor.</title>p. 79 B</p>"), "Plut. *Mor.* p. 79 B")
        self.assertEqual(md("<p>the <title>O. C.</title>(1410) to</p>"), "the *O. C.* (1410) to")

    def test_citation_and_quotation(self):
        xml = ('<p>cp. <bibl n="Soph. Aj. 664">Soph. <title>Ai.</title>664</bibl>'
               '<quote lang="greek">h( brotw=n paroimi/a</quote>.</p>')
        self.assertEqual(md(xml), "cp. Soph. *Ai.* 664 ἡ βροτῶν παροιμία.")
        xml = ('<p>Cp. <bibl n="Soph. OC 1006"><title>O. C.</title>1006</bibl>'
               '<quote lang="greek">ei)/ tis gh=</quote>.</p>')
        self.assertEqual(md(xml), "Cp. *O. C.* 1006 εἴ τις γῆ.")

    def test_citation_and_following_text(self):
        self.assertEqual(md('<p>see <bibl n="Soph. Phil. 1157"><title>Ph.</title>1157.</bibl>A vase</p>'),
                         "see *Ph.* 1157. A vase")
        self.assertEqual(md('<p><bibl n="Soph. Trach. 542"><title>Tr.</title>542</bibl>(Deianeira speaks)</p>'),
                         "*Tr.* 542 (Deianeira speaks)")
        self.assertEqual(md('<p><bibl n="Aristot. Rh. 2.21">Rhet. 2. 21</bibl>§ 13.</p>'), "Rhet. 2. 21 § 13.")
        self.assertEqual(md('<p>cp. <bibl n="Soph. Ant. 1212">1212</bibl>f.: Thuc.</p>'), "cp. 1212 f.: Thuc.")

    def test_word_and_citation(self):
        self.assertEqual(md('<p>Cp. below<bibl n="Aesch. Ag. 876">Aesch. Ag., 876</bibl>.</p>'),
                         "Cp. below Aesch. Ag., 876.")

    def test_no_space_where_none_belongs(self):
        # before a stop, comma, colon, closing bracket or dash; between a citation and a digit
        self.assertEqual(md('<p>(<bibl n="Hes. Th. 311">Hes. Th. 311</bibl>), and <bibl n="x">Il. 8. 363</bibl>, '
                            '<bibl n="y"><title>Il.</title>20. 144</bibl>—148: <title>Trachiniae</title>):</p>'),
                         "(Hes. Th. 311), and Il. 8. 363, *Il.* 20. 144—148: *Trachiniae*):")
        self.assertEqual(md('<p><bibl n="Soph. Phil. 1111"><title>Ph.</title>111</bibl>1n.</p>'), "*Ph.* 1111n.")
        # inside a word: italics or a quotation that is part of a word stay joined
        self.assertEqual(md("<p>the <emph>marriage</emph>bed, <quote lang=\"greek\">ou)k</quote>, x</p>"),
                         "the *marriage*bed, οὐκ, x")
        # an elision mark after a citation (a Perseus mis-tagging) is not a word
        self.assertEqual(md('<p><bibl n="z">O. T., i</bibl>ʼx</p>'), "O. T., iʼx")

    def test_whole_file(self):
        xml = """<TEI.2><text><body><div1 type="commentary"><div2><head>1-48</head>
<p>Prologue.</p>
<div3 n="1" type="commLine"><p><lemma lang="greek">lo/gos</lemma>, as
<bibl n="Pind. O. 7">Pind. <title>O.</title>7. 54</bibl><quote lang="greek">a)nqrw/pwn palaiai\\ r(h/sies</quote>.</p></div3>
</div2></div1></body></text></TEI.2>"""
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "c.xml", Path(d) / "c.md"
            src.write_text(xml, encoding="utf-8")
            self.assertEqual(import_jebb_commentary(src, out, {"title": "t"}), 2)
            text = out.read_text(encoding="utf-8")
        self.assertIn("**λόγος**, as Pind. *O.* 7. 54 ἀνθρώπων παλαιαὶ ῥήσιες.", text)


class GapIsAnEllipsis(unittest.TestCase):
    """Perseus's Oedipus Tyrannus writes Jebb's "..." as <gap/>: kept as a spaced ellipsis."""

    def md(self, xml):
        from anagnosis_pipeline.commentary import _md
        return _md(etree.fromstring(xml), False)

    def test_between_words(self):
        self.assertEqual(self.md('<p><lemma lang="greek">duoi=n<gap/>a)pokri/nas kakoi=n</lemma> x</p>'),
                         "**δυοῖν … ἀποκρίνας κακοῖν** x\n\n")
        self.assertEqual(self.md('<p>The <foreign lang="greek">dra=sai<gap/>duoi=n,</foreign> is</p>'),
                         "The δρᾶσαι … δυοῖν, is\n\n")

    def test_no_space_before_a_stop_and_none_doubled(self):
        self.assertEqual(self.md('<p><foreign lang="greek">i)w\\<gap/>*zeu=,<gap/>po/rois</foreign></p>'),
                         "ἰὼ … Ζεῦ, … πόροις\n\n")
        self.assertEqual(self.md('<p><quote lang="greek">e)pei/ se <gap/> ste/rcas</quote></p>'),
                         "ἐπεί σε … στέρξας\n\n")


if __name__ == "__main__":
    unittest.main()
