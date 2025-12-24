package com.eshowcaseai.app.core.identity

import android.content.Context
import android.util.Base64
import java.security.SecureRandom
import java.util.UUID

/**
 * 设备身份管理：生成并持久化序列号、HMAC 密钥、device_id、client_id、激活状态。
 * 首次生成后应保持稳定，避免频繁更换导致服务器视为新设备。
 */
class DeviceIdentity(private val context: Context) {

    companion object {
        private const val PREF_NAME = "EShowcaseAI_identity"
        private const val KEY_SERIAL = "serial_number"
        private const val KEY_HMAC = "hmac_key"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_CLIENT_ID = "client_id"
        private const val KEY_ACTIVATED = "is_activated"
    }

    data class Info(
        val serialNumber: String,
        val hmacKeyHex: String,
        val deviceId: String,
        val clientId: String,
        val isActivated: Boolean
    )

    private val prefs by lazy {
        context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
    }

    fun getOrCreate(): Info {
        val serial = prefs.getString(KEY_SERIAL, null) ?: generateSerial().also {
            prefs.edit().putString(KEY_SERIAL, it).apply()
        }
        val hmac = prefs.getString(KEY_HMAC, null) ?: generateHmacKey().also {
            prefs.edit().putString(KEY_HMAC, it).apply()
        }
        val deviceId = prefs.getString(KEY_DEVICE_ID, null) ?: generateMacLikeId().also {
            prefs.edit().putString(KEY_DEVICE_ID, it).apply()
        }
        val clientId = prefs.getString(KEY_CLIENT_ID, null) ?: UUID.randomUUID().toString().also {
            prefs.edit().putString(KEY_CLIENT_ID, it).apply()
        }
        val activated = prefs.getBoolean(KEY_ACTIVATED, false)
        return Info(serial, hmac, deviceId, clientId, activated)
    }

    fun setActivated(value: Boolean) {
        prefs.edit().putBoolean(KEY_ACTIVATED, value).apply()
    }

    fun reset() {
        prefs.edit().clear().apply()
    }

    private fun generateSerial(): String = UUID.randomUUID().toString().replace("-", "")

    private fun generateHmacKey(): String {
        val random = SecureRandom()
        val bytes = ByteArray(32)
        random.nextBytes(bytes)
        return bytes.joinToString("") { "%02x".format(it) }
    }

    private fun generateMacLikeId(): String {
        val random = SecureRandom()
        val bytes = ByteArray(6)
        random.nextBytes(bytes)
        return bytes.joinToString(":") { "%02x".format(it) }
    }

    fun hmacKeyBytes(): ByteArray {
        val hex = getOrCreate().hmacKeyHex
        val len = hex.length
        val data = ByteArray(len / 2)
        var i = 0
        while (i < len) {
            data[i / 2] = ((Character.digit(hex[i], 16) shl 4) + Character.digit(hex[i + 1], 16)).toByte()
            i += 2
        }
        return data
    }

    fun base64HmacKey(): String = Base64.encodeToString(hmacKeyBytes(), Base64.NO_WRAP)
}
