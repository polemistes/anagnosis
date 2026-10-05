package no.anagnosis.oedipuscoloneus

import android.app.Activity
import android.app.AlertDialog
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Bundle

/**
 * This app only carries the Oedipus at Colonus for the Anagnosis reader. Opened, it opens the reader at
 * the Oedipus at Colonus; without the reader installed, it says so and offers the way to Google Play.
 */
class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val reader = packageManager.getLaunchIntentForPackage(READER)
        if (reader != null) {
            reader.putExtra("open_text", TEXT)
            reader.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            startActivity(reader)
            finish()
            return
        }
        AlertDialog.Builder(this)
            .setTitle("Oedipus at Colonus")
            .setMessage(
                "This app adds Sophocles' Oedipus at Colonus to Anagnosis, the ancient Greek reader. " +
                    "Install Anagnosis from Google Play, and the Oedipus at Colonus appears in its library.",
            )
            .setPositiveButton("Get Anagnosis") { _, _ -> openStore(); finish() }
            .setNegativeButton("Close") { _, _ -> finish() }
            .setOnCancelListener { finish() }
            .show()
    }

    private fun openStore() {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$READER")))
        } catch (e: ActivityNotFoundException) {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=$READER")))
        }
    }

    companion object {
        const val READER = "no.anagnosis.reader"
        const val TEXT = "oedipuscoloneus"
    }
}
