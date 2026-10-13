package no.anagnosis.ui

import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext

@Composable
actual fun rememberFileSaver(mimeType: String): (name: String, content: String) -> Unit {
    val context = LocalContext.current
    // the content waits here while the file dialog is open
    var pending by remember { mutableStateOf<String?>(null) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument(mimeType)) { uri ->
        val content = pending
        pending = null
        if (uri == null || content == null) return@rememberLauncherForActivityResult
        val saved = try {
            context.contentResolver.openOutputStream(uri, "wt")?.use { it.write(content.toByteArray(Charsets.UTF_8)) } != null
        } catch (e: Exception) {
            false
        }
        Toast.makeText(context, if (saved) "Notes exported" else "The notes could not be saved there", Toast.LENGTH_SHORT).show()
    }
    return remember(launcher) { { name, content -> pending = content; launcher.launch(name) } }
}
