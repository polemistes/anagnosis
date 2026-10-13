package no.anagnosis.shop

import android.content.Context

/** Google Play Billing; a debug build may use a fake instead (src/debug). */
fun createBilling(context: Context, onUpdate: (List<Bought>?) -> Unit): Billing = PlayBilling(context, onUpdate)
