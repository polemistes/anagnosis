package no.anagnosis.data

import no.anagnosis.db.Sentence_nodes
import no.anagnosis.db.Tokens
import kotlin.test.Test
import kotlin.test.assertEquals

class SimpleSyntaxTest {
    private var nextId = 1L

    private fun token(wordId: String, form: String, relation: String?, head: Long?, postag: String = "n-s---fn-", lemma: String = form) =
        Tokens(nextId++, 1, 0, 0, 0, form, lemma, lemma, postag, relation, head, "s1", wordId)

    private fun node(wordId: Long, form: String, relation: String, head: Long, artificial: Boolean = false) =
        Sentence_nodes(nextId++, 1, "s1", wordId, form, null, if (artificial) "" else "u--------", relation, head, if (artificial) 1 else 0)

    private fun render(tokens: List<Tokens>, extra: List<Sentence_nodes> = emptyList()) =
        SimpleSyntax.render(Syntax.build("s1", tokens, extra)).trimEnd().lines()

    private fun words(tokens: List<Tokens>, extra: List<Sentence_nodes> = emptyList()) =
        SimpleSyntax.words(SimpleSyntax.outline(Syntax.build("s1", tokens, extra))).map { it.form }

    @Test
    fun aSubordinateClauseIsIndentedUnderItsVerbWithItsConjunction() {
        // λέγω ὅτι ὁ ἀνὴρ ἥκει . : the ὅτι clause is the object of λέγω
        val tokens = listOf(
            token("1", "λέγω", "PRED", 0, "v1spia---"),
            token("2", "ὅτι", "AuxC", 1, "c--------"),
            token("3", "ὁ", "ATR", 4, "l-s---mn-"),
            token("4", "ἀνὴρ", "SBJ", 5, "n-s---mn-", "ἀνήρ"),
            token("5", "ἥκει", "OBJ", 2, "v3spia---", "ἥκω"),
        )
        assertEquals(
            listOf(
                "— main clause",
                "    λέγω ⟨main verb⟩",
                "    — ὅτι clause (that, because) · object of λέγω",
                "        ὅτι",
                "        ὁ ἀνὴρ ⟨subject⟩",
                "        ἥκει ⟨verb⟩",
            ),
            render(tokens, listOf(node(6, ".", "AuxK", 0))),
        )
    }

    @Test
    fun aPrepositionStaysWithItsNounAndNegationWithTheVerb() {
        // οὐκ ἦλθεν εἰς τὴν πόλιν
        val tokens = listOf(
            token("1", "οὐκ", "AuxZ", 2, "d--------", "οὐ"),
            token("2", "ἦλθεν", "PRED", 0, "v3saia---", "ἔρχομαι"),
            token("3", "εἰς", "AuxP", 2, "r--------"),
            token("4", "τὴν", "ATR", 5, "l-s---fa-", "ὁ"),
            token("5", "πόλιν", "ADV", 3, "n-s---fa-", "πόλις"),
        )
        assertEquals(listOf("— main clause", "    οὐκ ἦλθεν ⟨main verb⟩", "    εἰς τὴν πόλιν ⟨adverbial⟩"), render(tokens))
    }

    @Test
    fun coordinatedClausesEachGetTheirConnector() {
        // ἦλθε καὶ εἶδε: two main clauses; καί goes with the second
        val tokens = listOf(
            token("1", "ἦλθε", "PRED_CO", 2, "v3saia---", "ἔρχομαι"),
            token("2", "καὶ", "COORD", 0, "c--------", "καί"),
            token("3", "εἶδε", "PRED_CO", 2, "v3saia---", "ὁράω"),
        )
        assertEquals(listOf("— main clause", "    ἦλθε ⟨main verb⟩", "— main clause", "    καὶ", "    εἶδε ⟨main verb⟩"), render(tokens))
    }

    @Test
    fun aShortClauseInsideAnotherIsOneLineWhereItStands() {
        // εἰ βούλει , λέγε : the if-clause precedes, and being short is one line
        val tokens = listOf(
            token("1", "εἰ", "AuxC", 4, "c--------"),
            token("2", "βούλει", "ADV", 1, "v2spie---", "βούλομαι"),
            token("4", "λέγε", "PRED", 0, "v2spma---", "λέγω"),
        )
        assertEquals(
            listOf("— main clause", "    εἰ βούλει ⟨εἰ clause (if, whether) · modifies λέγε⟩", "    λέγε ⟨main verb · imperative⟩"),
            render(tokens, listOf(node(3, ",", "AuxX", 4))),
        )
    }

    @Test
    fun everyWordAppearsOnceAndAnOmittedVerbIsShown() {
        // [0] PRED with a subject and a predicate noun; a comma on it is not shown
        val tokens = listOf(
            token("1", "σοφὸς", "PNOM", 3, "a-s---mn-", "σοφός"),
            token("2", "ὁ", "SBJ", 3, "p-s---mn-", "ὁ"),
        )
        val extra = listOf(node(3, "[0]", "PRED", 0, artificial = true), node(4, ",", "AuxX", 3))
        // the omitted verb stands by its first dependent, not at the end where the treebank keeps it
        assertEquals(listOf("σοφὸς", "[0]", "ὁ"), words(tokens, extra))
        assertEquals(
            listOf("— main clause, verb understood", "    σοφὸς ⟨predicate⟩", "    […] ⟨verb understood⟩", "    ὁ ⟨subject⟩"),
            render(tokens, extra),
        )
    }

    @Test
    fun coordinatedPrepositionalPhrasesAreOnePhrase() {
        // μήθʼ ὑπὸ κυνῶν μήθʼ ὑπʼ οἰωνῶν ὀλέσθαι: the members sit under prepositions, as the treebank does it
        val tokens = listOf(
            token("1", "μήθʼ", "AuxY", 5, "c--------", "μήτε"),
            token("2", "ὑπὸ", "AuxP", 5, "r--------", "ὑπό"),
            token("3", "κυνῶν", "OBJ_CO", 2, "n-p---mg-", "κύων"),
            token("5", "μήθʼ", "COORD", 8, "c--------", "μήτε"),
            token("6", "ὑπʼ", "AuxP", 5, "r--------", "ὑπό"),
            token("7", "οἰωνῶν", "OBJ_CO", 6, "n-p---mg-", "οἰωνός"),
            token("8", "ὀλέσθαι", "PRED", 0, "v--anm---", "ὄλλυμι"),
        )
        assertEquals(listOf("— main clause", "    μήθʼ ὑπὸ κυνῶν μήθʼ ὑπʼ οἰωνῶν ⟨adverbial⟩", "    ὀλέσθαι ⟨infinitive⟩"), render(tokens))
    }

    @Test
    fun aNounsCaseNamesItsConstruction() {
        // δίδωσι τῷ ἀνδρὶ τὸν ἵππον: a dative object is marked, an accusative one is simply the object
        val tokens = listOf(
            token("1", "δίδωσι", "PRED", 0, "v3spia---", "δίδωμι"),
            token("2", "τῷ", "ATR", 3, "l-s---md-", "ὁ"),
            token("3", "ἀνδρὶ", "OBJ", 1, "n-s---md-", "ἀνήρ"),
            token("4", "τὸν", "ATR", 5, "l-s---ma-", "ὁ"),
            token("5", "ἵππον", "OBJ", 1, "n-s---ma-", "ἵππος"),
        )
        assertEquals(listOf("— main clause", "    δίδωσι ⟨main verb⟩", "    τῷ ἀνδρὶ ⟨object · dat.⟩", "    τὸν ἵππον ⟨object⟩"), render(tokens))
    }

    @Test
    fun noWordIsEverLost() {
        // a coordinator with no marked members and an odd shape: whatever the rules make of it, every word shows
        val tokens = listOf(
            token("1", "καὶ", "COORD", 0, "c--------", "καί"),
            token("2", "νῦν", "ADV", 1, "d--------"),
            token("3", "λέγω", "ADV", 1, "v1spia---"),
            token("4", "σοι", "OBJ", 3, "p-s---md-", "σύ"),
        )
        val words = words(tokens)
        assertEquals(setOf("καὶ", "νῦν", "λέγω", "σοι"), words.toSet())
        assertEquals(4, words.size)
    }
}
