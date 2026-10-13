package no.anagnosis.shop

import android.app.Activity
import android.content.Context
import android.os.Build

/**
 * Google Play Billing on a phone; on the emulator, whose images without the Play Store still
 * carry a stub of it, a fake that sells every text at once for nothing, so the shop can be tried
 * out. Debug builds only.
 */
fun createBilling(context: Context, onUpdate: (List<Bought>?) -> Unit): Billing =
    if (Build.HARDWARE in setOf("ranchu", "goldfish")) FakeBilling(context, onUpdate) else PlayBilling(context, onUpdate)

/**
 * Keeps its purchases in the preferences file fake_billing. To take a purchase back:
 * `adb shell run-as no.anagnosis.reader rm shared_prefs/fake_billing.xml`, then restart the app.
 */
private class FakeBilling(context: Context, private val onUpdate: (List<Bought>?) -> Unit) : Billing {
    private val prefs = context.getSharedPreferences("fake_billing", Context.MODE_PRIVATE)

    private fun bought(id: String) = Bought(listOf(id), BoughtState.PURCHASED, acknowledged = true, token = "fake-$id")

    override fun prices(ids: List<String>, done: (Map<String, String>?) -> Unit) = done(ids.associateWith { "€3.00" })

    override fun purchases(done: (List<Bought>?) -> Unit) =
        done(prefs.getStringSet("bought", null).orEmpty().map(::bought))

    override fun buy(activity: Activity, id: String) {
        prefs.edit().putStringSet("bought", prefs.getStringSet("bought", null).orEmpty() + id).apply()
        onUpdate(listOf(bought(id)))
    }

    override fun acknowledge(token: String) {}

    override fun end() {}
}
