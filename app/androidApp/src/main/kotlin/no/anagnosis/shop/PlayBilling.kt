package no.anagnosis.shop

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClient.BillingResponseCode
import com.android.billingclient.api.BillingClient.ProductType
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import com.android.billingclient.api.UnfetchedProduct

/**
 * Google Play Billing. [onUpdate] receives the purchases made through [buy] (and pending ones
 * that complete later), or null when the store's answer calls for asking it again (a product
 * already owned).
 */
class PlayBilling(context: Context, private val onUpdate: (List<Bought>?) -> Unit) : Billing {
    private val client = BillingClient.newBuilder(context)
        .setListener { result, purchases ->
            when (result.responseCode) {
                BillingResponseCode.OK -> onUpdate(purchases.orEmpty().map(::bought))
                BillingResponseCode.ITEM_ALREADY_OWNED -> onUpdate(null)
                else -> {}  // cancelled by the buyer, or an error the payment sheet has shown
            }
        }
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
        .enableAutoServiceReconnection()
        .build()

    /** The products as the store last described them, for opening the payment sheet. */
    private val details = HashMap<String, ProductDetails>()

    private val waiting = mutableListOf<(Boolean) -> Unit>()
    private var connecting = false

    /** Runs [action] once connected to the store, with false when the store cannot be reached. */
    private fun whenReady(action: (Boolean) -> Unit) {
        if (client.isReady) return action(true)
        val start = synchronized(this) {
            waiting += action
            !connecting.also { connecting = true }
        }
        if (start) client.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                val ok = result.responseCode == BillingResponseCode.OK
                val run = synchronized(this@PlayBilling) {
                    connecting = false
                    waiting.toList().also { waiting.clear() }
                }
                run.forEach { it(ok) }
            }

            // reconnecting is left to the client (enableAutoServiceReconnection)
            override fun onBillingServiceDisconnected() {}
        })
    }

    override fun prices(ids: List<String>, done: (Prices?) -> Unit) = whenReady { ok ->
        if (!ok || ids.isEmpty()) return@whenReady done(if (ok) Prices(emptyMap()) else null)
        val params = QueryProductDetailsParams.newBuilder().setProductList(
            ids.map { QueryProductDetailsParams.Product.newBuilder().setProductId(it).setProductType(ProductType.INAPP).build() },
        ).build()
        client.queryProductDetailsAsync(params) { result, found ->
            if (result.responseCode != BillingResponseCode.OK) return@queryProductDetailsAsync done(null)
            val prices = HashMap<String, String>()
            val missing = HashMap<String, String>()
            for (d in found.productDetailsList) {
                val price = offer(d)?.formattedPrice
                if (price == null) {
                    missing[d.productId] = "no purchase option"
                    continue
                }
                synchronized(details) { details[d.productId] = d }
                prices[d.productId] = price
            }
            for (u in found.unfetchedProductList) {
                missing[u.productId] = when (u.statusCode) {
                    UnfetchedProduct.StatusCode.PRODUCT_NOT_FOUND -> "product not found"
                    UnfetchedProduct.StatusCode.NO_ELIGIBLE_OFFER -> "no purchase option for this account or country"
                    UnfetchedProduct.StatusCode.INVALID_PRODUCT_ID_FORMAT -> "product id not accepted"
                    else -> "reason not given"
                }
            }
            done(Prices(prices, missing))
        }
    }

    override fun purchases(done: (List<Bought>?) -> Unit) = whenReady { ok ->
        if (!ok) return@whenReady done(null)
        client.queryPurchasesAsync(QueryPurchasesParams.newBuilder().setProductType(ProductType.INAPP).build()) { result, list ->
            done(if (result.responseCode == BillingResponseCode.OK) list.map(::bought) else null)
        }
    }

    override fun buy(activity: Activity, id: String) = whenReady { ok ->
        val d = synchronized(details) { details[id] } ?: return@whenReady
        if (!ok) return@whenReady
        val product = BillingFlowParams.ProductDetailsParams.newBuilder().setProductDetails(d)
        offer(d)?.offerToken?.let { product.setOfferToken(it) }
        val params = BillingFlowParams.newBuilder().setProductDetailsParamsList(listOf(product.build())).build()
        activity.runOnUiThread { client.launchBillingFlow(activity, params) }
    }

    override fun acknowledge(token: String) = whenReady { ok ->
        if (ok) client.acknowledgePurchase(AcknowledgePurchaseParams.newBuilder().setPurchaseToken(token).build()) {}
    }

    override fun end() = client.endConnection()

    /**
     * The purchase option a text is sold with. A product may have several, and
     * oneTimePurchaseOfferDetails gives only the one marked backwards compatible in Play Console,
     * so the list is asked first.
     */
    private fun offer(d: ProductDetails): ProductDetails.OneTimePurchaseOfferDetails? =
        d.oneTimePurchaseOfferDetailsList?.firstOrNull() ?: d.oneTimePurchaseOfferDetails

    /** A purchase whose signature is not Google Play's counts for nothing. */
    private fun bought(p: Purchase) = Bought(
        productIds = p.products,
        state = when {
            !PurchaseSignature.isValid(p.originalJson, p.signature) -> BoughtState.OTHER
            p.purchaseState == Purchase.PurchaseState.PURCHASED -> BoughtState.PURCHASED
            p.purchaseState == Purchase.PurchaseState.PENDING -> BoughtState.PENDING
            else -> BoughtState.OTHER
        },
        acknowledged = p.isAcknowledged,
        token = p.purchaseToken,
    )
}
