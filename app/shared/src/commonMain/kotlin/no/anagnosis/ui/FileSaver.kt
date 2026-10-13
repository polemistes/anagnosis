package no.anagnosis.ui

import androidx.compose.runtime.Composable

/**
 * A way to save a text file where the reader chooses, through the system's own file dialog
 * (no permission is needed). The returned function takes the suggested file name and the content.
 */
@Composable
expect fun rememberFileSaver(mimeType: String): (name: String, content: String) -> Unit
