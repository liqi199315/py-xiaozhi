package com.xiaozhi.app.core.activation

import android.util.Log
import com.xiaozhi.app.core.config.AppConfig
import com.xiaozhi.app.core.identity.DeviceIdentity
import com.xiaozhi.app.core.ota.OtaClient
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import kotlin.coroutines.coroutineContext

class Activator(
    private val identity: DeviceIdentity
) {

    private val client: OkHttpClient = OkHttpClient.Builder()
        .callTimeout(AppConfig.HTTP_TIMEOUT_MS, TimeUnit.MILLISECONDS)
        .build()

    private val json = Json { ignoreUnknownKeys = true }

    @Serializable
    data class ActivatePayload(
        @Suppress("PropertyName")
        val Payload: PayloadBody
    ) {
        @Serializable
        data class PayloadBody(
            val algorithm: String,
            val serial_number: String,
            val challenge: String,
            val hmac: String
        )
    }

    suspend fun activate(challenge: String, code: String, activationUrl: String = "${AppConfig.OTA_BASE_URL}activate"): Boolean {
        val info = identity.getOrCreate()
        Log.i(AppConfig.LOG_TAG, "[激活] code=$code challenge=$challenge")

        val hmacSignature = hmacSha256(challenge, identity.hmacKeyBytes())
        val payload = ActivatePayload(
            Payload = ActivatePayload.PayloadBody(
                algorithm = "hmac-sha256",
                serial_number = info.serialNumber,
                challenge = challenge,
                hmac = hmacSignature
            )
        )

        val headers = mapOf(
            "Activation-Version" to AppConfig.ACTIVATION_HEADER_VERSION,
            "Device-Id" to info.deviceId,
            "Client-Id" to info.clientId,
            "Content-Type" to "application/json"
        )

        val body = json.encodeToString(ActivatePayload.serializer(), payload)
            .toRequestBody("application/json".toMediaType())

        repeat(60) { attempt ->
            if (!coroutineContext.isActive) return false
            Log.i(AppConfig.LOG_TAG, "[激活] 尝试 ${attempt + 1}/60 ...")

            val reqBuilder = Request.Builder()
                .url(activationUrl)
                .post(body)
            headers.forEach { (k, v) -> reqBuilder.addHeader(k, v) }

            val resp = client.newCall(reqBuilder.build()).execute()
            resp.use { r ->
                val codeResp = r.code
                val text = r.body?.string().orEmpty()
                Log.i(AppConfig.LOG_TAG, "[激活] HTTP $codeResp: $text")
                when (codeResp) {
                    200 -> {
                        identity.setActivated(true)
                        return true
                    }
                    202 -> {
                        delay(5000)
                    }
                    else -> {
                        delay(5000)
                    }
                }
            }
        }
        return false
    }

    private fun hmacSha256(data: String, key: ByteArray): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key, "HmacSHA256"))
        val result = mac.doFinal(data.toByteArray())
        return result.joinToString("") { "%02x".format(it) }
    }
}
