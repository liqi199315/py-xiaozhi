package com.xiaozhi.app.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.xiaozhi.app.core.activation.Activator
import com.xiaozhi.app.core.audio.AudioPipeline
import com.xiaozhi.app.core.identity.DeviceIdentity
import com.xiaozhi.app.core.ota.OtaClient
import com.xiaozhi.app.core.ws.XiaozhiWebSocket
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener

class BootstrapViewModel(app: Application) : AndroidViewModel(app) {

    private val identity = DeviceIdentity(app)
    private val otaClient = OtaClient(identity)
    private val activator = Activator(identity)
    private val ws = XiaozhiWebSocket()

    private val _uiState = MutableLiveData("準備就緒")
    val uiState: LiveData<String> = _uiState

    private val _logText = MutableLiveData("調試輸出：")
    val logText: LiveData<String> = _logText

    private val _activationCode = MutableLiveData<String?>(null)
    val activationCode: LiveData<String?> = _activationCode

    private val _isListening = MutableLiveData(false)
    val isListening: LiveData<Boolean> = _isListening

    private val _aiResponse = MutableLiveData<String>("")
    val aiResponse: LiveData<String> = _aiResponse

    private val _isSpeaking = MutableLiveData(false)
    val isSpeaking: LiveData<Boolean> = _isSpeaking

    private val _isBootstrapping = MutableLiveData(false)
    val isBootstrapping: LiveData<Boolean> = _isBootstrapping

    private val _currentSentence = MutableLiveData("")
    val currentSentence: LiveData<String> = _currentSentence

    private val _isReady = MutableLiveData(false)
    val isReady: LiveData<Boolean> = _isReady

    private var sessionId: String? = null

    private val audioPipeline = AudioPipeline(
        onAudioCaptured = { data -> ws.sendBinaryAudio(data) },
        onPlaybackStateChanged = { speaking -> _isSpeaking.postValue(speaking) }
    )

    fun sendText(text: String) {
        val sid = sessionId
        if (sid == null) {
            appendLog("尚未連接，正在嘗試連接...")
            bootstrap()
            return
        }
        ws.sendText(sid, text)
        appendLog("發送文字: $text")
    }

    fun startListening() {
        val sid = sessionId ?: return
        if (_isListening.value == true) return
        
        ws.sendListenStart(sid)
        audioPipeline.startCapture()
        appendLog("開始對話")
        _isListening.postValue(true)
    }

    fun stopListening() {
        val sid = sessionId ?: return
        if (_isListening.value != true) return

        ws.sendListenStop(sid)
        audioPipeline.stopCapture()
        appendLog("停止對話")
        _isListening.postValue(false)
    }

    fun toggleListen() {
        val sid = sessionId
        if (sid == null) {
            appendLog("尚未连接，正在尝试连接...")
            bootstrap()
            return
        }

        if (_isListening.value == true) {
            stopListening()
        } else {
            startListening()
        }
    }

    fun bootstrap() {
        if (_isBootstrapping.value == true) return
        
        viewModelScope.launch {
            _isBootstrapping.postValue(true)
            _activationCode.postValue(null)
            appendLog("開始引導")
            val info = identity.getOrCreate()
            appendLog("deviceId=${info.deviceId} clientId=${info.clientId} activated=${info.isActivated}")

            val ota = withContext(Dispatchers.IO) { otaClient.fetchConfig() }
            if (ota == null) {
                _uiState.postValue("OTA 請求失敗")
                return@launch
            }

            if (!info.isActivated && ota.activation != null) {
                val act = ota.activation
                appendLog("需要激活: code=${act.code} message=${act.message ?: ""}")
                _activationCode.postValue(act.code)
                
                try {
                    val ok = withContext(Dispatchers.IO) {
                        activator.activate(act.challenge, act.code)
                    }
                    if (!ok) {
                        _uiState.postValue("激活失敗")
                        _isBootstrapping.postValue(false)
                        return@launch
                    }
                    appendLog("激活成功")
                    _activationCode.postValue(null)
                } catch (e: Exception) {
                    android.util.Log.e("Xiaozhi", "激活异常", e)
                    appendLog("激活异常: ${e.message}")
                    _uiState.postValue("激活出错")
                    _isBootstrapping.postValue(false)
                    return@launch
                }
            }

            // 激活后或已激活，再次获取配置以确保拿到最新的 token
            val ota2 = withContext(Dispatchers.IO) { otaClient.fetchConfig() }
            val wsConfig = ota2?.websocket ?: ota.websocket
            if (wsConfig == null) {
                _uiState.postValue("未獲取到 WebSocket 配置")
                return@launch
            }

            val params = XiaozhiWebSocket.Params(
                url = wsConfig.url,
                token = wsConfig.token,
                deviceId = info.deviceId,
                clientId = info.clientId
            )

            ws.connect(params, object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    appendLog("WS 已連接")
                    _uiState.postValue("WS 已連接")
                    val helloMsg = XiaozhiWebSocket.Hello()
                    val jsonStr = Json { encodeDefaults = true }.encodeToString(XiaozhiWebSocket.Hello.serializer(), helloMsg)
                    appendLog("WS -> $jsonStr")
                    ws.sendHello()
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    android.util.Log.i("Xiaozhi", "[WS] <- $text")
                    appendLog("WS <- $text")
                    try {
                        val json = Json { ignoreUnknownKeys = true }
                        val element = json.parseToJsonElement(text)
                        val jsonObject = element.jsonObject
                        
                        // 尝试多种可能的路径获取 session_id
                        val sid = jsonObject["session_id"]?.jsonPrimitive?.content
                            ?: jsonObject["payload"]?.jsonObject?.get("session_id")?.jsonPrimitive?.content
                            ?: jsonObject["data"]?.jsonObject?.get("session_id")?.jsonPrimitive?.content

                        if (sid != null) {
                            if (sid != sessionId) {
                                sessionId = sid
                                android.util.Log.i("Xiaozhi", "✅ 已就緒 (SessionId: $sid)")
                                appendLog("✅ 已就緒 (SessionId: $sid)")
                                _uiState.postValue("WS 已連接 (已就緒)")
                                _isReady.postValue(true)
                            }
                        }
                        val type = jsonObject["type"]?.jsonPrimitive?.content
                        if (type == "tts" || type == "stt") {
                            val textMsg = jsonObject["text"]?.jsonPrimitive?.content
                            if (textMsg != null) {
                                val currentHistory = _aiResponse.value ?: ""
                                val newMsg = if (type == "stt") "我: $textMsg" else "AI: $textMsg"
                                _aiResponse.postValue("$currentHistory\n$newMsg".trim())
                                _currentSentence.postValue(textMsg)
                            }
                        }
                    } catch (e: Exception) {
                        android.util.Log.e("Xiaozhi", "解析失敗: ${e.message}")
                        appendLog("解析失敗: ${e.message}")
                    }
                }

                override fun onMessage(webSocket: WebSocket, bytes: okio.ByteString) {
                    audioPipeline.play(bytes.toByteArray())
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    appendLog("WS 失敗: ${t.message}")
                    _isListening.postValue(false)
                    _isReady.postValue(false)
                    audioPipeline.stopCapture()
                }

                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    appendLog("WS 已關閉: $code $reason")
                    _isListening.postValue(false)
                    _isReady.postValue(false)
                    audioPipeline.stopCapture()
                }
            })

            _uiState.postValue("WS 連接中...")
            _isBootstrapping.postValue(false)
        }
    }

    override fun onCleared() {
        super.onCleared()
        ws.close()
        _isReady.postValue(false)
        audioPipeline.release()
    }

    fun isActivated(): Boolean {
        return identity.getOrCreate().isActivated
    }

    private fun appendLog(msg: String) {
        val current = _logText.value ?: ""
        _logText.postValue("$current\n$msg")
    }
}
