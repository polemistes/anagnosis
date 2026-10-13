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
import no.anagnosis.data.ShopState
import no.anagnosis.data.TextOwnership
import no.anagnosis.data.TextShop
import no.anagnosis.data.productId
import no.anagnosis.data.slugOfProduct
import java.util.concurrent.Executors

/**
 * The texts bought in the reader through Google Play: the payments go through [Billing], and a
 * bought text arrives as the on-demand asset pack of the same name (app/packs/<slug>), which
 * is copied in and then removed. What is owned is saved after every answer from the store, so
 * the texts stay readable offline. [onSale] holds the slugs and versions of the texts the
 * catalog marks as on sale.
 */
class PlayTextShop(
    private val activity: Activity,
    private val driverFactory: DriverFactory,
    private val onSale: Map<String, String>,
) : TextShop {
    private val prefs = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private val _state = MutableStateFlow(ShopState(owned = prefs.getStringSet(OWNED, null).orEmpty().toSet()))
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
    }

    fun close() {
        packs.unregisterListener(packListener)
        billing.end()
        installer.shutdown()
    }

    override fun refresh() {
        billing.prices(onSale.keys.map(::productId)) { prices ->
            _state.update { s ->
                if (prices == null) s.copy(reachable = false)
                else s.copy(reachable = true, prices = prices.mapNotNull { (id, price) -> slugOfProduct(id)?.let { it to price } }.toMap())
            }
        }
        billing.purchases { bought -> if (bought != null) takePurchases(bought, complete = true) }
    }

    override fun buy(slug: String) = billing.buy(activity, productId(slug))

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
        fun slugs(state: BoughtState) = bought.filter { it.state == state }.flatMap { it.productIds }.mapNotNull(::slugOfProduct).toSet()
        val paid = slugs(BoughtState.PURCHASED)
        val pending = slugs(BoughtState.PENDING)
        for (b in bought) if (b.state == BoughtState.PURCHASED && !b.acknowledged) billing.acknowledge(b.token)
        _state.update { s ->
            val owned = if (complete) paid else s.owned + paid
            s.copy(
                owned = owned,
                pending = (if (complete) pending else s.pending - paid + pending),
                revision = if (owned != s.owned) s.revision + 1 else s.revision,
            )
        }
        prefs.edit().putStringSet(OWNED, _state.value.owned).apply()
        fetchMissing()
    }

    /** Fetches every owned text that is not on the device in the version of this build. */
    private fun fetchMissing() {
        val s = _state.value
        val missing = TextOwnership.toFetch(
            owned = s.owned,
            storeVersions = onSale.keys.associateWith { driverFactory.packTextVersion(it) },
            catalogVersions = onSale,
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
        if (slug !in onSale) return
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
                if (driverFactory.packTextVersion(slug) != onSale[slug]) {
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
    }
}
