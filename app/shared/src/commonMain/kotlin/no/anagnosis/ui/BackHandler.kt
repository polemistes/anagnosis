package no.anagnosis.ui

import androidx.compose.runtime.Composable

/** Runs [onBack] when the platform's back gesture or button is used. */
@Composable
expect fun PlatformBackHandler(onBack: () -> Unit)
