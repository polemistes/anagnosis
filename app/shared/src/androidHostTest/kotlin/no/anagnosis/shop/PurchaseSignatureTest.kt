package no.anagnosis.shop

import java.security.KeyPairGenerator
import java.security.Signature
import java.util.Base64
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class PurchaseSignatureTest {
    private val pair = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.generateKeyPair()
    private val json = """{"orderId":"GPA.1234","productId":"sophocles_antigone_jebb","purchaseState":0}"""

    private fun sign(data: String): String = Base64.getEncoder().encodeToString(
        Signature.getInstance("SHA1withRSA").run { initSign(pair.private); update(data.toByteArray()); sign() },
    )

    @Test
    fun aSignedPurchaseIsAccepted() = assertTrue(PurchaseSignature.isValid(json, sign(json), pair.public))

    @Test
    fun aChangedPurchaseIsRefused() =
        assertFalse(PurchaseSignature.isValid(json.replace("antigone", "electra"), sign(json), pair.public))

    @Test
    fun rubbishIsRefused() {
        assertFalse(PurchaseSignature.isValid(json, "not base64!", pair.public))
        assertFalse(PurchaseSignature.isValid(json, "", pair.public))
    }

    @Test
    fun theReadersKeyIsARsaKey() = assertEquals("RSA", PurchaseSignature.publicKey(PurchaseSignature.PLAY_KEY).algorithm)
}
