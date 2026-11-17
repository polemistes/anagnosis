package no.anagnosis.data

/**
 * A lemma as the text spells it, capital or small letter, decides what the word sheet shows of
 * it (the author's rule, 2026-11-17): a name does not take a common word's short definition or
 * dictionary entry (Πῶλος, the speaker Polus, is not πῶλος "a foal"; Ἰωνία is not ἰωνιά
 * "violet-bed"), nor a common word a name's.
 */
object LemmaSpelling {
    /**
     * The text database's meta key: its short definitions of lemmas written with a capital stand
     * under the lemma itself (NFC, the capital kept, no homograph digit); those of lemmas written
     * small under the lower-case lemma key, as before. Packs without it keep only the lower-case key.
     */
    const val BY_SPELLING_META = "short_definitions_by_spelling"

    /** Whether a lemma (or headword) begins with a capital: its first letter, the homograph digit taken off. */
    fun isCapitalised(lemma: String): Boolean =
        splitHomograph(lemma).first.firstOrNull { it.isLetter() }?.let { it.isUpperCase() || it.isTitleCase() } == true

    /**
     * The key a token's short definition is looked up by: in a text keyed by spelling, a lemma
     * with a capital by its own spelling and by nothing else (no row there means no short
     * definition, never the common word's under the lower-case key); otherwise the lemma key.
     */
    fun shortDefinitionKey(lemma: String, lemmaKey: String, bySpelling: Boolean): String =
        if (bySpelling && isCapitalised(lemma)) splitHomograph(lemma).first else lemmaKey

    /**
     * Of the dictionary entries found only by the loose key (accents, breathings and capitals
     * ignored), those a lemma may be given: a lemma with a capital only headwords that begin
     * with a capital themselves (none: no dictionary entry); a lemma written small all of them.
     */
    fun <T> looseMatches(lemma: String, entries: List<T>, headword: (T) -> String): List<T> =
        if (!isCapitalised(lemma)) entries else entries.filter { isCapitalised(headword(it)) }
}
