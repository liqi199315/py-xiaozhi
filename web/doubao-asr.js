// ==================================================
// 豆包流式语音识别模块 (Doubao ASR)
// 独立的前端模块，替换浏览器原生 SpeechRecognition
// ==================================================

class DoubaoASR {
    constructor(serverBase) {
        this.serverBase = serverBase;
        this.ws = null;
        this.recorder = null;
        this.stream = null;
        this.enabled = true;  // 默认启用
        this.SAMPLE_RATE = 16000;
        this.isRecording = false;

        // 回调函数
        this.onPartialResult = null;  // 中间结果回调
        this.onFinalResult = null;    // 最终结果回调
        this.onError = null;           // 错误回调
    }

    async connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return true;
        }

        try {
            const doubaoUrl = `${this.serverBase.replace(/^http/, 'ws')}/api/doubao-asr`;
            console.log('[豆包ASR] 正在连接:', doubaoUrl);

            this.ws = new WebSocket(doubaoUrl);
            this.ws.binaryType = 'arraybuffer';

            return new Promise((resolve, reject) => {
                this.ws.onopen = () => {
                    console.log('[豆包ASR] WebSocket 已连接');
                };

                this.ws.onmessage = (event) => {
                    try {
                        const msg = JSON.parse(event.data);
                        console.log('[豆包ASR] 收到消息:', msg);

                        if (msg.type === 'ready') {
                            console.log('[豆包ASR] 服务已准备好');
                            resolve(true);
                        } else if (msg.type === 'partial') {
                            // 中间结果
                            if (this.onPartialResult) {
                                this.onPartialResult(msg.text);
                            }
                        } else if (msg.type === 'complete') {
                            // 最终结果
                            console.log('[豆包ASR] 最终文本:', msg.text);
                            if (this.onFinalResult) {
                                this.onFinalResult(msg.text);
                            }
                        } else if (msg.type === 'error') {
                            console.error('[豆包ASR] 错误:', msg.message);
                            if (this.onError) {
                                this.onError(msg.message);
                            }
                        }
                    } catch (e) {
                        console.error('[豆包ASR] 解析消息失败:', e);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('[豆包ASR] WebSocket 错误:', error);
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('[豆包ASR] WebSocket 已关闭');
                    this.ws = null;
                };

                // 10秒超时
                setTimeout(() => reject(new Error('连接超时')), 10000);
            });
        } catch (e) {
            console.error('[豆包ASR] 连接失败:', e);
            return false;
        }
    }

    async start() {
        if (this.isRecording) {
            console.warn('[豆包ASR] 已经在录音中');
            return false;
        }

        try {
            // 1. 获取麦克风权限
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: this.SAMPLE_RATE,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            });

            console.log('[豆包ASR] 已获取麦克风');

            // 2. 连接豆包服务
            if (!await this.connect()) {
                throw new Error('无法连接到豆包服务');
            }

            // 3. 创建 MediaRecorder
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : 'audio/webm';

            this.recorder = new MediaRecorder(this.stream, {
                mimeType: mimeType,
                audioBitsPerSecond: 16000
            });

            // 4. 处理音频数据
            this.recorder.ondataavailable = (event) => {
                if (event.data.size > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(event.data);
                    console.log('[豆包ASR] 发送音频块:', event.data.size, '字节');
                }
            };

            this.recorder.onstop = () => {
                console.log('[豆包ASR] 录音已停止');
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'stop' }));
                }
                this.isRecording = false;
            };

            // 5. 开始录音 (每 200ms 发送一次数据)
            this.recorder.start(200);
            this.isRecording = true;
            console.log('[豆包ASR] 开始录音');
            return true;

        } catch (e) {
            console.error('[豆包ASR] 启动录音失败:', e);
            // 调用错误回调
            if (this.onError) {
                this.onError('启动录音失败: ' + e.message);
            }
            this.stop();
            return false;
        }
    }

    stop() {
        console.log('[豆包ASR] 停止录音');

        if (this.recorder && this.recorder.state !== 'inactive') {
            this.recorder.stop();
        }
        this.recorder = null;

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        this.isRecording = false;
    }

    close() {
        this.stop();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// 导出为全局变量
window.DoubaoASR = DoubaoASR;
