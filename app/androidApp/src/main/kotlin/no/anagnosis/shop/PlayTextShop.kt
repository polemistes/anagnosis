package no.anagnosis.shop

import android.app.Activity
import android.content.Context
import com.google.android.play.core.assetpacks.AssetPackManagerFactory
import com.google.android.play.core.assetpacks.AssetPackState
import com.google.android.play.core.assetpacks.AssetPackStateUpdateListener
import com.google.android.play.core.assetpacks.model.AssetPackStatus
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import no.anagnosis.DriverFactory
import no.anagnosis.data.Download
import no.anagnosis.data.DownloadStatus
import no.anagnosis.data.OnSale
import no.anagnosis.data.ShopState
import no.anagnosis.data.TextOwnership
import no.anagnosis.data.TextShop
import java.util.concurrent.Executors

/**
 * The texts bought in the reader through Google Play: the payments go through [Billing], and a
 * bought text arrives as the on-demand asset pack of the same name (app/packs/<slug>), which
 * is copied in and then removed. What is owned is saved after every answer from the store, so
 * the texts stay readable offline. [onSale] holds the texts the catalog marks as on sale.
 */
class PlayTextShop(
    private val activity: Activity,
    private val driverFactory: DriverFactory,
    onSale: List<OnSale>,
    /**
     * The texts this build gives without a purchase (BuildConfig.GRANTED_TEXTS; empty unless the
     * build was asked for them on purpose). They are owned from the start, never bought, and
     * their packs are fetched like a bought text's.
     */
    granted: List<OnSale> = emptyList(),
    /**
     * The free texts: added by the user without payment ([add]) and fetched like a bought text;
     * never a product, never billing. What was added is kept in its own preferences, which are
     * backed up (res/xml/backup_rules.xml), so the texts come back after a reinstall.
     */
    free: List<OnSale> = emptyList(),
) : TextShop {
    /** The version of each text on sale, given or free in this build, by slug. */
    private val versions = (onSale + granted + free).associate { it.slug to it.version }
    private val productOf = onSale.associate { it.slug to it.productId }
    private val slugOf = onSale.associate { it.productId to it.slug }
    private val grantedSlugs = granted.map { it.slug }.toSet() - productOf.keys
    private val freeSlugs = free.map { it.slug }.toSet() - productOf.keys

    private val prefs = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private val addedPrefs = activity.getSharedPreferences(ADDED_PREFS, Context.MODE_PRIVATE)
    private fun added(): Set<String> = addedPrefs.getStringSet(ADDED, null).orEmpty().toSet()
    private val _state = MutableStateFlow(ShopState(
        owned = TextOwnership.owned(prefs.getStringSet(OWNED, null).orEmpty().toSet(), added(), freeSlugs, grantedSlugs)))
    override val state: StateFlow<ShopState> = _state.asStateFlow()

    private val billing = createBilling(activity.applicationContext) { bought ->
        if (bought == null) refresh() else takePurchases(bought, complete = false)
    }
    private val packs = AssetPackManagerFactory.getInstance(activity.applicationContext)
    private val packListener = AssetPackStateUpdateListener { onPackState(it) }
    /** Copies texts in one at a time, off the main thread. */
    private val installer = Executors.newSingleThreadExecutor()
    private val installing = HashSet<String>()

    init {
        packs.registerListener(packListener)
        // a given or added free text needs no answer from the store: fetch it now if it is not on the device
        if (grantedSlugs.isNotEmpty() || (added() intersect freeSlugs).isNotEmpty()) fetchMissing()
    }

    fun close() {
        packs.unregisterListener(packListener)
        billing.end()
        installer.shutdown()
    }

    override fun refresh() {
        billing.prices(productOf.values.toList()) { prices ->
            _state.update { s ->
                if (prices == null) s.copy(reachable = false)
                else s.copy(
                    reachable = true,
                    prices = prices.byId.mapNotNull { (id, price) -> slugOf[id]?.let { it to price } }.toMap(),
                    missing = prices.missing.mapNotNull { (id, why) -> slugOf[id]?.let { it to why } }.toMap(),
                )
            }
        }
        billing.purchases { bought -> if (bought != null) takePurchases(bought, complete = true) }
    }

    override fun buy(slug: String) {
        productOf[slug]?.let { billing.buy(activity, it) }
    }

    override fun add(slug: String) {
        if (slug !in freeSlugs) return
        addedPrefs.edit().putStringSet(ADDED, added() + slug).apply()
        _state.update { s -> if (slug in s.owned) s else s.copy(owned = s.owned + slug, revision = s.revision + 1) }
        fetch(listOf(slug))
    }

    override fun download(slug: String) {
        if (_state.value.downloads[slug]?.status == DownloadStatus.NEEDS_CONFIRMATION) {
            packs.showConfirmationDialog(activity)
        } else {
            fetch(listOf(slug))
        }
    }

    /**
     * Takes the store's purchases: the paid ones are owned (and acknowledged), the pending ones
     * shown as such. A [complete] list (every purchase of the account) replaces what was owned,
     * so a refunded text is no longer shown; a list of new purchases adds to it.
     */
    private fun takePurchases(bought: List<Bought>, complete: Boolean) {
        fun slugs(state: BoughtState) = bought.filter { it.state == state }.flatMap { it.productIds }.mapNotNull { slugOf[it] }.toSet()
        val paid = slugs(BoughtState.PURCHASED)
        val pending = slugs(BoughtState.PENDING)
        for (b in bought) if (b.state == BoughtState.PURCHASED && !b.acknowledged) billing.acknowledge(b.token)
        _state.update { s ->
            // the store's answer replaces what was bought; the added free texts and the given stay
            val owned = TextOwnership.owned(if (complete) paid else s.owned + paid, added(), freeSlugs, grantedSlugs)
            s.copy(
                owned = owned,
                pending = (if (complete) pending else s.pending - paid + pending),
                revision = if (owned != s.owned) s.revision + 1 else s.revision,
            )
        }
        // only what was bought is kept here: a given text is owned only in the build that gives it,
        // an added free text is kept with the added ones
        prefs.edit().putStringSet(OWNED, _state.value.owned - grantedSlugs - freeSlugs).apply()
        fetchMissing()
    }

    /** Fetches every owned text that is not on the device in the version of this build. */
    private fun fetchMissing() {
        val s = _state.value
        val missing = TextOwnership.toFetch(
            owned = s.owned,
            storeVersions = versions.keys.associateWith { driverFactory.packTextVersion(it) },
            catalogVersions = versions,
            fromApps = driverFactory.textsFromApps(),
        ).filter { s.downloads[it] == null || s.downloads[it]?.status == DownloadStatus.FAILED }
        if (missing.isNotEmpty()) fetch(missing)
    }

    private fun fetch(slugs: List<String>) {
        _state.update { s -> s.copy(downloads = s.downloads + slugs.associateWith { Download(DownloadStatus.WAITING) }) }
        packs.fetch(slugs)
            .addOnSuccessListener { states -> states.packStates().values.forEach(::onPackState) }
            .addOnFailureListener { setDownload(slugs, Download(DownloadStatus.FAILED)) }
    }

    private fun onPackState(st: AssetPackState) {
        val slug = st.name()
        if (slug !in versions) return
        when (st.status()) {
            AssetPackStatus.PENDING -> setDownload(listOf(slug), Download(DownloadStatus.WAITING))
            AssetPackStatus.DOWNLOADING -> {
                val total = st.totalBytesToDownload()
                setDownload(listOf(slug), Download(DownloadStatus.DOWNLOADING, if (total > 0) (st.bytesDownloaded() * 100 / total).toInt() else 0))
            }
            AssetPackStatus.TRANSFERRING -> setDownload(listOf(slug), Download(DownloadStatus.DOWNLOADING, st.transferProgressPercentage()))
            AssetPackStatus.WAITING_FOR_WIFI, AssetPackStatus.REQUIRES_USER_CONFIRMATION ->
                setDownload(listOf(slug), Download(DownloadStatus.NEEDS_CONFIRMATION))
            AssetPackStatus.COMPLETED -> install(slug)
            AssetPackStatus.FAILED, AssetPackStatus.CANCELED -> setDownload(listOf(slug), Download(DownloadStatus.FAILED))
            else -> {}  // NOT_INSTALLED once the pack has been removed after copying
        }
    }

    /** Copies a downloaded text in, then removes the pack so the text is not stored twice. */
    private fun install(slug: String) {
        synchronized(installing) { if (!installing.add(slug)) return }
        installer.execute {
            try {
                if (driverFactory.packTextVersion(slug) != versions[slug]) {
                    val location = packs.getPackLocation(slug)?.assetsPath() ?: error("$slug is not on the device")
                    driverFactory.installPackText(slug, location)
                    packs.removePack(slug)
                }
                _state.update { s -> s.copy(downloads = s.downloads - slug, revision = s.revision + 1) }
            } catch (e: Exception) {
                setDownload(listOf(slug), Download(DownloadStatus.FAILED))
            } finally {
                synchronized(installing) { installing.remove(slug) }
            }
        }
    }

    private fun setDownload(slugs: List<String>, d: Download) =
        _state.update { s -> s.copy(downloads = s.downloads + slugs.associateWith { d }) }

    private companion object {
        const val PREFS = "shop"
        const val OWNED = "owned"
        /** The free texts the user added (backed up: res/xml/backup_rules.xml). */
        const val ADDED_PREFS = "added_texts"
        const val ADDED = "added"
    }
}
