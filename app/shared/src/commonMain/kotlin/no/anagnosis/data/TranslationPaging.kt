package no.anagnosis.data

import no.anagnosis.db.Translation_segments

/** How the translation is laid beside the Greek pages. */
object TranslationPaging {
    /**
     * The passage of the translation that covers the line [nInt] without beginning at it (a
     * section the translator renders together with the one before), or null. The last such
     * passage when several do (a speech's own segment over the rest).
     */
    fun covering(segments: List<Translation_segments>, nInt: Long): Translation_segments? =
        segments.lastOrNull { it.kind != "stage" && it.from_n_int < nInt && it.to_n_int >= nInt }
}
