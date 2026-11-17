package no.anagnosis.ui

import androidx.compose.runtime.Composable

/** A brief notice that shows for a moment and goes by itself (on Android a toast). */
@Composable
expect fun rememberShortNotice(): (String) -> Unit
