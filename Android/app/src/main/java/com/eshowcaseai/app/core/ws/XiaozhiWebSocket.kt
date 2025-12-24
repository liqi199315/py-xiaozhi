package com.eshowcaseai.app.core.ws

import android.util.Log
import com.eshowcaseai.app.core.config.AppConfig
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.ByteString
import okio.ByteString.Companion.toByteString
import java.util.concurrent.TimeUnit

class EShowcaseAIWebSocket {

    data class Params(
        val url: String,
        val token: String,
        val deviceId: String,
        val clientId: String
    )

    @Serializable
    data class Hello(
        val type: String = "hello",
        val version: Int = 1,
        val transport: String = "websocket",
        val features: Features = Features(),
        val audio_params: AudioParams = AudioParams()
    ) {
        @Serializable
        data class Features(val mcp: Boolean = true)
        @Serializable
        data class AudioParams(
            val format: String = "opus",
            val sample_rate: Int = com.eshowcaseai.app.core.audio.AudioConfig.SAMPLE_RATE,
            val channels: Int = com.eshowcaseai.app.core.audio.AudioConfig.CHANNELS,
            val frame_duration: Int = com.eshowcaseai.app.core.audio.AudioConfig.FRAME_DURATION_MS
        )
    }

    private val json = Json { 
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    private val client = OkHttpClient.Builder()
        .pingInterval(20, TimeUnit.SECONDS)
        .build()

    private var socket: WebSocket? = null

    fun connect(params: Params, listener: WebSocketListener) {
        val reqBuilder = Request.Builder()
            .url(params.url)
            .addHeader("Authorization", "Bearer ${params.token}")
            .addHeader("Protocol-Version", "1")
            .addHeader("Device-Id", params.deviceId)
            .addHeader("Client-Id", params.clientId)

        socket = client.newWebSocket(reqBuilder.build(), listener)
    }

    fun sendHello() {
        val msg = json.encodeToString(Hello.serializer(), Hello())
        val sent = socket?.send(msg) ?: false
        if (!sent) {
            Log.e(AppConfig.LOG_TAG, "[WS] 发送 Hello 失败: Socket 未连接")
        } else {
            Log.i(AppConfig.LOG_TAG, "[WS] -> hello")
        }
    }

    fun sendListenStart(sessionId: String, mode: String = "manual") {
        val payload = """
            {"session_id":"$sessionId","type":"listen","state":"start","mode":"$mode"}
        """.trimIndent()
        socket?.send(payload)
    }

    fun sendListenStop(sessionId: String) {
        val payload = """{"session_id":"$sessionId","type":"listen","state":"stop"}"""
        socket?.send(payload)
    }

    fun sendText(sessionId: String, text: String) {
        val payload = """
            {"session_id":"$sessionId","type":"listen","state":"detect","text":"$text"}
        """.trimIndent()
        val sent = socket?.send(payload) ?: false
        if (!sent) {
            Log.e(AppConfig.LOG_TAG, "[WS] 发送失败: Socket 未连接或已关闭")
        } else {
            Log.i(AppConfig.LOG_TAG, "[WS] -> text: $text")
        }
    }

    fun sendHeartbeat(sessionId: String) {
        val payload = """{"session_id":"$sessionId","type":"status","state":"idle"}"""
        socket?.send(payload)
    }

    private var binaryCount = 0
    fun sendBinaryAudio(data: ByteArray) {
        socket?.send(data.toByteString(0, data.size))
        binaryCount++
        if (binaryCount % 100 == 0) {
            Log.d(AppConfig.LOG_TAG, "[WS] 已发送 $binaryCount 个音频包")
        }
    }

    fun close() {
        binaryCount = 0
        socket?.close(1000, "client close")
        socket = null
    }
}
