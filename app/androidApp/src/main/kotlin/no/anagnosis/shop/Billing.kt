package no.anagnosis.shop

import android.app.Activity

/**
 * The store's payments, as the shop needs them: Google Play Billing in the app, a fake on an
 * emulator without the Play Store (debug builds only, see BillingFactory). Callbacks may come on
 * any thread.
 */
interface Billing {
    /** The products' prices in the buyer's currency; null when the store cannot be reached. */
    fun prices(ids: List<String>, done: (Prices?) -> Unit)

    /** Every one-time purchase of the account; null when the store cannot be reached. */
    fun purchases(done: (List<Bought>?) -> Unit)

    /** Opens the payment sheet; the outcome comes to the listener the billing was made with. */
    fun buy(activity: Activity, id: String)

    /** Tells the store the product has been handed over; unacknowledged purchases are refunded after three days. */
    fun acknowledge(token: String)

    fun end()
}

/**
 * The store's answer about the products: the price of each it offers, by product id, and the
 * reason for each it does not offer ("product not found"), so the shop can say why.
 */
class Prices(val byId: Map<String, String>, val missing: Map<String, String> = emptyMap())

/** One purchase: its products, whether it is paid or still pending, and its token. */
class Bought(
    val productIds: List<String>,
    val state: BoughtState,
    val acknowledged: Boolean,
    val token: String,
)

enum class BoughtState { PURCHASED, PENDING, OTHER }
