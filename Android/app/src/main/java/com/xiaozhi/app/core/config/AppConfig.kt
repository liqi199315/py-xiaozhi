package com.xiaozhi.app.core.config

object AppConfig {
    // OTA
    const val OTA_BASE_URL = "https://api.tenclass.net/xiaozhi/ota/"
    const val APP_VERSION = "2.0.3"
    const val APP_NAME = "xiaozhi"
    const val BOARD_TYPE = "Desktop"

    // WebSocket
    const val DEFAULT_WS_URL = "wss://api.tenclass.net/xiaozhi/v1/"

    // 超时
    const val HTTP_TIMEOUT_MS = 15000L

    // 日志标签前缀
    const val LOG_TAG = "Xiaozhi"

    // 协议版本对齐
    const val ACTIVATION_VERSION = "v2"
    const val ACTIVATION_HEADER_VERSION = "2"
}
