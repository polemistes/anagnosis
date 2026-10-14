package no.anagnosis.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import no.anagnosis.data.CatalogEntry
import no.anagnosis.data.DownloadStatus
import no.anagnosis.data.ShopState

/**
 * The shop: the texts on sale in the reader, in the order of their authors, with what each
 * comes with, and the way to buy it through the platform's store. A text the store does not
 * offer (not yet on sale there) is left out while the store can be reached; without the store,
 * the texts are listed with nothing to press.
 */
@Composable
fun AvailableTextsScreen(
    catalog: List<CatalogEntry>,
    shop: ShopState,
    onBuy: (String) -> Unit,
    onDownload: (String) -> Unit,
    onOpen: (String) -> Unit,
    onBack: () -> Unit,
) {
    val offered = catalog.filter { e ->
        e.onGooglePlay && (!shop.reachable || e.slug in shop.prices || e.slug in shop.owned || e.installed)
    }
    Column(
        Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 24.dp, vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
    Column(Modifier.widthIn(max = CONTENT_MAX_WIDTH).fillMaxWidth()) {
        TextButton(onClick = onBack) { Text("‹ Back") }
        Spacer(Modifier.height(8.dp))
        Text("Available texts", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Each text is bought once, here in Anagnosis, through Google Play, and it comes back on a new phone with " +
                "the same Google account. After you buy a text, it is downloaded and appears in your list of texts on " +
                "the front page; this can take some minutes.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        if (!shop.reachable) {
            Spacer(Modifier.height(8.dp))
            Text(
                "Google Play cannot be reached just now. Buying a text needs Google Play and an internet connection; " +
                    "the texts you have are not affected.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
            )
        }
        Spacer(Modifier.height(16.dp))
        // in the order of their authors, each named in its title ("Antigone by Sophocles")
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            for (entry in byAuthor(offered).flatMap { it.second }) {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text(fullTitle(entry), style = MaterialTheme.typography.titleLarge)
                        Spacer(Modifier.height(8.dp))
                        Detail("Editor", entry.editor)
                        Detail("Critical apparatus", entry.apparatus)
                        Detail("Translation", entry.translation)
                        Detail("Commentary", entry.commentary)
                        Detail("Syntax", entry.syntax)
                        Detail("Extra dictionaries", entry.dictionaries)
                        Spacer(Modifier.height(8.dp))
                        Purchase(entry, shop, onBuy, onDownload, onOpen)
                    }
                }
            }
        }
        // texts on sale here that the store does not offer just now, and the store's reason
        val missing = catalog.filter { it.onGooglePlay && it.slug in shop.missing && it !in offered }
        if (shop.reachable && missing.isNotEmpty()) {
            Spacer(Modifier.height(16.dp))
            Text(
                "Not offered by Google Play just now: " +
                    missing.joinToString("; ") { "${it.titleEn.ifEmpty { it.title }} (${shop.missing.getValue(it.slug)})" } + ".",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Spacer(Modifier.height(24.dp))
    }
    }
}

/** A card's last row: where the text stands with the buyer, and what can be done about it. */
@Composable
private fun Purchase(entry: CatalogEntry, shop: ShopState, onBuy: (String) -> Unit, onDownload: (String) -> Unit, onOpen: (String) -> Unit) {
    val slug = entry.slug
    val download = shop.downloads[slug]
    @Composable
    fun Status(text: String, color: Color = MaterialTheme.colorScheme.onSurfaceVariant) =
        Text(text, style = MaterialTheme.typography.labelLarge, color = color)
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        when {
            entry.installed -> {
                Status("Owned", MaterialTheme.colorScheme.primary)
                Spacer(Modifier.weight(1f))
                OutlinedButton(onClick = { onOpen(slug) }) { Text("Open") }
            }
            download?.status == DownloadStatus.WAITING || download?.status == DownloadStatus.DOWNLOADING -> {
                Column(Modifier.fillMaxWidth()) {
                    Status(if (download.status == DownloadStatus.DOWNLOADING && download.percent > 0) "Downloading · ${download.percent} %" else "Downloading")
                    Spacer(Modifier.height(8.dp))
                    if (download.status == DownloadStatus.DOWNLOADING) {
                        LinearProgressIndicator(progress = { download.percent / 100f }, modifier = Modifier.fillMaxWidth())
                    } else {
                        LinearProgressIndicator(Modifier.fillMaxWidth())
                    }
                }
            }
            download?.status == DownloadStatus.NEEDS_CONFIRMATION -> {
                Status("Waiting for Wi-Fi")
                Spacer(Modifier.weight(1f))
                Button(onClick = { onDownload(slug) }) { Text("Download now") }
            }
            download?.status == DownloadStatus.FAILED -> {
                Status("Download failed", MaterialTheme.colorScheme.error)
                Spacer(Modifier.weight(1f))
                Button(onClick = { onDownload(slug) }) { Text("Try again") }
            }
            slug in shop.owned -> {
                Status("Owned", MaterialTheme.colorScheme.primary)
                Spacer(Modifier.weight(1f))
                Button(onClick = { onDownload(slug) }) { Text("Download") }
            }
            slug in shop.pending -> Status("Payment pending")
            shop.reachable && slug in shop.prices -> {
                Spacer(Modifier.weight(1f))
                Button(onClick = { onBuy(slug) }) { Text("Buy · ${shop.prices.getValue(slug)}") }
            }
        }
    }
}

/** One thing a text comes with, as "Label: what"; nothing when it does not have it. */
@Composable
private fun Detail(label: String, value: String) {
    if (value.isEmpty()) return
    Text(
        buildAnnotatedString {
            withStyle(SpanStyle(fontWeight = FontWeight.SemiBold)) { append("$label: ") }
            append(value)
        },
        style = MaterialTheme.typography.bodyMedium,
        modifier = Modifier.padding(vertical = 2.dp),
    )
}
