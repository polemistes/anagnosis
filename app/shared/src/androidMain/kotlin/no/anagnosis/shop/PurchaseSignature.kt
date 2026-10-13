package no.anagnosis.shop

import java.security.KeyFactory
import java.security.PublicKey
import java.security.Signature
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

/**
 * Checks that a purchase really comes from Google Play: Play signs each purchase's JSON with the
 * app's private key, and the reader checks the signature with the public half, the licence key
 * from Play Console (Monetize with Play › Monetization setup). The key is public; it is not a
 * secret.
 */
object PurchaseSignature {
    /** The reader's licence key in Play Console (no.anagnosis.reader), base64. */
    const val PLAY_KEY =
        "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuk5TjdtEDBo3VJYv/T4LjkS1hqXKY6Hg47NK/pcIa9VEqh2pqLtD6SrHh6DlG+0Fli4JiFlZ" +
            "SYaWyUhrMS5uyH/dUhatwasXUIEd6EEESElMXyVCeRLnk+oL0vkxM5XH0Ec9JWddrYFVtjVpeP8Wk76/e9SUPMrOO0nScJ5CQAoSdZ5mJPPuNPMBJZb+" +
            "W9cCjWDz2kcOBRe9Zg2qR+W+1JnJOli5xPSUvG1znZPN+egKS6t3pUCrvYASVcmjo//xKkBw553XE4EDvLpiRrNyXDsK/ay559u50BzOjpgvTSXGC42X" +
            "GFa0gYxjInZRy54rWi5plW0D22aVEKJUdkxvnQIDAQAB"

    private val playKey: PublicKey by lazy { publicKey(PLAY_KEY) }

    fun publicKey(base64: String): PublicKey =
        KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(Base64.getDecoder().decode(base64)))

    /** Whether [signature] (base64) is Google Play's signature of [json] (a purchase's original JSON). */
    fun isValid(json: String, signature: String, key: PublicKey = playKey): Boolean = try {
        Signature.getInstance("SHA1withRSA").run {
            initVerify(key)
            update(json.toByteArray(Charsets.UTF_8))
            verify(Base64.getDecoder().decode(signature))
        }
    } catch (e: Exception) {
        false
    }
}
