package com.eshowcaseai.app.core.ota

import android.util.Log
import com.eshowcaseai.app.core.config.AppConfig
import com.eshowcaseai.app.core.identity.DeviceIdentity
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class OtaClient(
    private val identity: DeviceIdentity
    ) {

    private val client: OkHttpClient = OkHttpClient.Builder()
        .callTimeout(AppConfig.HTTP_TIMEOUT_MS, TimeUnit.MILLISECONDS)
        .build()

    private val json = Json { ignoreUnknownKeys = true }

    @Serializable
    data class OtaRequest(
        val application: Application,
        val board: Board
    ) {
        @Serializable
        data class Application(
            val version: String,
            @SerialName("elf_sha256") val elfSha256: String
        )
        @Serializable
        data class Board(
            val type: String,
            val name: String,
            val ip: String,
            val mac: String
        )
    }

    @Serializable
    data class OtaResponse(
        val websocket: WebsocketConfig? = null,
        val mqtt: Map<String, String>? = null,
        val activation: ActivationInfo? = null
    ) {
        @Serializable
        data class WebsocketConfig(
            val url: String,
            val token: String
        )
        @Serializable
        data class ActivationInfo(
            val code: String,
            val challenge: String,
            val message: String? = null
        )
    }

    fun buildRequestPayload(): OtaRequest {
        val info = identity.getOrCreate()
        return OtaRequest(
            application = OtaRequest.Application(
                version = AppConfig.APP_VERSION,
                elfSha256 = info.hmacKeyHex
            ),
            board = OtaRequest.Board(
                type = AppConfig.BOARD_TYPE,
                name = AppConfig.APP_NAME,
                ip = "0.0.0.0",
                mac = info.deviceId
            )
        )
    }

    fun buildHeaders(): Map<String, String> {
        val info = identity.getOrCreate()
        val headers = mutableMapOf(
            "Device-Id" to info.deviceId,
            "Client-Id" to info.clientId,
            "Content-Type" to "application/json",
            "User-Agent" to "${AppConfig.BOARD_TYPE}/${AppConfig.APP_NAME}-${AppConfig.APP_VERSION}",
            "Accept-Language" to "zh-CN"
        )
        if (AppConfig.ACTIVATION_VERSION == "v2") {
            headers["Activation-Version"] = AppConfig.APP_VERSION
        }
        return headers
    }

    /**
     * TODO: 实现实际的 HTTP 调用并返回解析后的 OtaResponse。
     * 目前仅打印构造的请求，方便后续补全。
     */
    fun fetchConfigMock(): OtaResponse? {
        val payload = buildRequestPayload()
        Log.i(AppConfig.LOG_TAG, "[OTA] Mock payload: $payload")
        Log.i(AppConfig.LOG_TAG, "[OTA] Mock headers: ${buildHeaders()}")
        return null
    }

    fun fetchConfig(): OtaResponse? {
        val payload = buildRequestPayload()
        val jsonBody = json.encodeToString(OtaRequest.serializer(), payload)
        val body = jsonBody.toRequestBody("application/json".toMediaType())

        val requestBuilder = Request.Builder()
            .url(AppConfig.OTA_BASE_URL)
            .post(body)
        buildHeaders().forEach { (k, v) -> requestBuilder.addHeader(k, v) }

        val request = requestBuilder.build()
        client.newCall(request).execute().use { resp ->
            if (!resp.isSuccessful) {
                Log.e(AppConfig.LOG_TAG, "[OTA] HTTP error: ${resp.code}")
                return null
            }
            val content = resp.body?.string().orEmpty()
            Log.i(AppConfig.LOG_TAG, "[OTA] Response: $content")
            return runCatching {
                json.decodeFromString(OtaResponse.serializer(), content)
            }.onFailure {
                Log.e(AppConfig.LOG_TAG, "[OTA] Parse failed", it)
            }.getOrNull()
        }
    }
}
