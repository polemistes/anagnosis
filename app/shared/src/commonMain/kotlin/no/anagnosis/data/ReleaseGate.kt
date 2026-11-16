package no.anagnosis.data

/**
 * Texts with a release date. A catalogue entry may carry `release` (YYYY-MM-DD): before that day,
 * by the device's local date, the text does not exist for the reader (not listed, not offered,
 * not searched, not fetched); from that day on it is offered like a text on sale, with its
 * product. A text without a release date is offered when it is marked for sale, as before. A
 * text this build gives without a purchase ([granted]) is shown whatever its date.
 */
object ReleaseGate {
    private val DATE = Regex("\\d{4}-\\d{2}-\\d{2}")

    /** Whether a text with this [release] value may be shown on [today] (both YYYY-MM-DD). */
    fun released(release: String, today: String): Boolean {
        val r = release.trim()
        if (r.isEmpty()) return true
        // a value that is not a date holds the text back; ISO dates compare as strings
        return DATE.matches(r) && DATE.matches(today) && r <= today
    }

    /** The texts of [entries] that do not exist for the user on [today]. */
    fun hidden(entries: List<CatalogEntry>, today: String, granted: Set<String>): Set<String> =
        entries.filter { it.slug !in granted && !released(it.release, today) }.map { it.slug }.toSet()

    /** Whether the shop offers [entry] on [today]: a released text with a release date, or one marked for sale. */
    fun offered(entry: CatalogEntry, today: String): Boolean =
        if (entry.release.isNotBlank()) released(entry.release, today) else entry.onGooglePlay
}
