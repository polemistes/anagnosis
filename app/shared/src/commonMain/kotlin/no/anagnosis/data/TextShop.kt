package no.anagnosis.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * The platform's store, through which the texts are bought inside the reader (Google Play on
 * Android). The shop's page and the front page only see this; the platform does the buying
 * and brings the bought texts onto the device.
 */
interface TextShop {
    val state: StateFlow<ShopState>

    /** Asks the store again for prices and purchases (when the app comes to the front). */
    fun refresh()

    /** Opens the store's payment sheet for a text. */
    fun buy(slug: String)

    /** Fetches a bought text again: after a failed download, or to confirm one on mobile data. */
    fun download(slug: String)
}

data class ShopState(
    /** The store answered; without it nothing can be bought, but bought texts stay readable. */
    val reachable: Boolean = false,
    /** Each text's price in the buyer's currency, as the store formats it, by slug. */
    val prices: Map<String, String> = emptyMap(),
    /** Why the store does not offer a text on sale here ("product not found"), by slug. */
    val missing: Map<String, String> = emptyMap(),
    /** The texts bought in the app, by slug. */
    val owned: Set<String> = emptySet(),
    /** Texts whose payment has been started but not completed (cash, bank transfer). */
    val pending: Set<String> = emptySet(),
    /** Bought texts on their way onto the device, by slug. */
    val downloads: Map<String, Download> = emptyMap(),
    /** Grows whenever a text arrives or what is owned changes, so the catalog is read again. */
    val revision: Int = 0,
)

class Download(val status: DownloadStatus, val percent: Int = 0)

enum class DownloadStatus { WAITING, DOWNLOADING, NEEDS_CONFIRMATION, FAILED }

/**
 * A text on sale in the reader: its slug (also the name of its asset pack), its product id in
 * the store (author, work and edition: sophocles_electra_jebb), and its version in this build.
 */
class OnSale(val slug: String, val productId: String, val version: String)

/** A shop that is never reachable: for a platform without a store. */
object NoTextShop : TextShop {
    override val state: StateFlow<ShopState> = MutableStateFlow(ShopState())
    override fun refresh() {}
    override fun buy(slug: String) {}
    override fun download(slug: String) {}
}

/** Which texts the reader shows and which it must fetch, from what is on the device and what is owned. */
object TextOwnership {
    /**
     * The texts to show: those bundled with the reader, those from installed text apps, and
     * those downloaded from the store that are still owned (a refunded text stays on the
     * device, hidden, and comes back without a download if it is bought again).
     */
    fun installed(bundled: Collection<String>, fromApps: Collection<String>, fromStore: Collection<String>, owned: Set<String>): List<String> =
        (bundled + fromApps + fromStore.filter { it in owned }).filter { it != "lexicon" }.distinct().sorted()

    /**
     * The owned texts to fetch from the store: those on sale (with a version in the catalog)
     * that are not on the device from the store in that version, unless a text app has
     * already brought them.
     */
    fun toFetch(owned: Set<String>, storeVersions: Map<String, String?>, catalogVersions: Map<String, String>, fromApps: Collection<String>): List<String> =
        owned.filter { slug ->
            val wanted = catalogVersions[slug] ?: return@filter false
            slug !in fromApps && storeVersions[slug] != wanted
        }.sorted()
}
