import unittest
from io import BytesIO

from lxml import etree

from anagnosis_pipeline.nt_syntax import convert_sentence


def sentence(xml: str):
    """A MACULA-style sentence from a compact notation: <w id="n…" class lemma mood role>form</w>."""
    return etree.parse(BytesIO(xml.encode("utf-8"))).getroot()


def tree(sent):
    s = convert_sentence(sentence(sent))
    by_id = {n.id: n for n in s.nodes + s.extra}
    for marks in s.punct_after.values():
        for p in marks:
            if p.id in s.used_punct:
                by_id[p.id] = p
    return {n.form: (n.rel, by_id[n.head].form if n.head else "ROOT") for n in by_id.values()}


class NtSyntaxTest(unittest.TestCase):
    def test_clause_with_object_and_subordinate_clause(self):
        # λέγω ὅτι ὁ ἀνὴρ ἥκει: the ὅτι clause is the object of λέγω
        t = tree("""<sentence><p/>
          <wg class="cl" rule="V-O">
            <w xml:id="n40001001001" class="verb" lemma="λέγω" mood="indicative" role="v" after=" ">λέγω</w>
            <wg class="cl" rule="sub-CL" role="o">
              <w xml:id="n40001001002" class="conj" lemma="ὅτι" after=" ">ὅτι</w>
              <wg class="cl" rule="S-V">
                <wg class="np" rule="DetNP" role="s">
                  <w xml:id="n40001001003" class="det" lemma="ὁ" after=" ">ὁ</w>
                  <w xml:id="n40001001004" class="noun" lemma="ἀνήρ" after=" ">ἀνὴρ</w>
                </wg>
                <w xml:id="n40001001005" class="verb" lemma="ἥκω" mood="indicative" role="v" after=".">ἥκει</w>
              </wg>
            </wg>
          </wg></sentence>""")
        self.assertEqual(t["λέγω"], ("PRED", "ROOT"))
        self.assertEqual(t["ὅτι"], ("AuxC", "λέγω"))
        self.assertEqual(t["ἥκει"], ("OBJ", "ὅτι"))
        self.assertEqual(t["ἀνὴρ"], ("SBJ", "ἥκει"))
        self.assertEqual(t["ὁ"], ("ATR", "ἀνὴρ"))

    def test_preposition_heads_its_phrase_and_negation_joins_the_verb(self):
        # οὐκ ἦλθεν εἰς τὴν πόλιν
        t = tree("""<sentence><p/>
          <wg class="cl" rule="ADV-V-ADV">
            <w xml:id="n40001001001" class="adv" lemma="οὐ" role="adv" after=" ">οὐκ</w>
            <w xml:id="n40001001002" class="verb" lemma="ἔρχομαι" mood="indicative" role="v" after=" ">ἦλθεν</w>
            <wg class="pp" rule="PrepNp" role="adv">
              <w xml:id="n40001001003" class="prep" lemma="εἰς" after=" ">εἰς</w>
              <wg class="np" rule="DetNP">
                <w xml:id="n40001001004" class="det" lemma="ὁ" after=" ">τὴν</w>
                <w xml:id="n40001001005" class="noun" lemma="πόλις" after=".">πόλιν</w>
              </wg>
            </wg>
          </wg></sentence>""")
        self.assertEqual(t["οὐκ"], ("AuxZ", "ἦλθεν"))
        self.assertEqual(t["εἰς"], ("AuxP", "ἦλθεν"))
        self.assertEqual(t["πόλιν"], ("ADV", "εἰς"))

    def test_coordinated_clauses_hang_on_their_conjunction(self):
        # ἦλθε καὶ εἶδε, with a particle δέ connecting the sentence to the one before
        t = tree("""<sentence><p/>
          <wg class="cl" rule="Conj-CL">
            <w xml:id="n40001001002" class="conj" lemma="δέ" after=" ">δὲ</w>
            <wg class="cl" rule="CLaCL">
              <w xml:id="n40001001001" class="verb" lemma="ἔρχομαι" mood="indicative" role="v" rule="v2cl" after=" ">ἦλθε</w>
              <wg type="group">
                <w xml:id="n40001001003" class="conj" lemma="καί" after=" ">καὶ</w>
                <w xml:id="n40001001004" class="verb" lemma="ὁράω" mood="indicative" role="v" rule="v2cl" after=".">εἶδε</w>
              </wg>
            </wg>
          </wg></sentence>""")
        self.assertEqual(t["καὶ"], ("COORD", "ROOT"))
        self.assertEqual(t["ἦλθε"], ("PRED_CO", "καὶ"))
        self.assertEqual(t["εἶδε"], ("PRED_CO", "καὶ"))
        self.assertEqual(t["δὲ"], ("AuxY", "καὶ"))

    def test_verbless_clause_gets_an_understood_verb_and_asyndeton_its_comma(self):
        # μακάριοι οἱ πτωχοί, καλὸς ὁ λόγος: two verbless clauses coordinated by the comma
        t = tree("""<sentence><p/>
          <wg class="cl" rule="ClCl">
            <wg class="cl" rule="P-S" predication="verbless">
              <w xml:id="n40001001001" class="adj" lemma="μακάριος" role="p" after=" ">μακάριοι</w>
              <wg class="np" rule="DetNP" role="s">
                <w xml:id="n40001001002" class="det" lemma="ὁ" after=" ">οἱ</w>
                <w xml:id="n40001001003" class="adj" lemma="πτωχός" after=", ">πτωχοί</w>
              </wg>
            </wg>
            <wg class="cl" rule="P-S" predication="verbless">
              <w xml:id="n40001001004" class="adj" lemma="καλός" role="p" after=" ">καλὸς</w>
              <wg class="np" rule="DetNP" role="s">
                <w xml:id="n40001001005" class="det" lemma="ὁ" after=" ">ὁ</w>
                <w xml:id="n40001001006" class="noun" lemma="λόγος" after=".">λόγος</w>
              </wg>
            </wg>
          </wg></sentence>""")
        self.assertEqual(t[","], ("COORD", "ROOT"))
        self.assertEqual(t["μακάριοι"][0], "PNOM")
        self.assertEqual(t["πτωχοί"][0], "SBJ")
        self.assertEqual(t["λόγος"][0], "SBJ")
        heads = {t["μακάριοι"][1], t["πτωχοί"][1], t["καλὸς"][1], t["λόγος"][1]}
        self.assertEqual(heads, {"[0]"})

    def test_periphrasis_and_circumstantial_participle(self):
        # ἐλθὼν ἦν διδάσκων: the participle διδάσκων heads, ἦν is its auxiliary, ἐλθών modifies it
        t = tree("""<sentence><p/>
          <wg class="cl" rule="ADV-VC-P">
            <w xml:id="n40001001001" class="verb" lemma="ἔρχομαι" mood="participle" role="v" rule="v2cl" after=" ">ἐλθὼν</w>
            <w xml:id="n40001001002" class="verb" lemma="εἰμί" mood="indicative" role="vc" after=" ">ἦν</w>
            <w xml:id="n40001001003" class="verb" lemma="διδάσκω" mood="participle" role="p" after=".">διδάσκων</w>
          </wg></sentence>""")
        self.assertEqual(t["διδάσκων"], ("PRED", "ROOT"))
        self.assertEqual(t["ἦν"], ("AuxV", "διδάσκων"))
        self.assertEqual(t["ἐλθὼν"], ("ADV", "διδάσκων"))


if __name__ == "__main__":
    unittest.main()
