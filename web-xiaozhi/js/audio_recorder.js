/**
 * 浏览器端音频录制器
 * 使用Web Audio API录制麦克风，并编码为Opus格式
 */
class AudioRecorder {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.sourceNode = null;
        this.processorNode = null;
        this.isRecording = false;

        // 音频参数（与小智后台一致）
        this.sampleRate = 16000;  // 16kHz
        this.channels = 1;         // 单声道
        this.bufferSize = 4096;    // 缓冲区大小

        // Opus编码器（需要引入opusjs或使用MediaRecorder）
        this.useMediaRecorder = true;  // 使用MediaRecorder API
        this.mediaRecorder = null;
        this.audioChunks = [];

        // 回调函数
        this.onAudioData = null;  // 音频数据回调
        this.onError = null;      // 错误回调
    }

    /**
     * 初始化音频录制
     */
    async initialize() {
        try {
            console.log('[录音] 初始化音频录制器...');

            // 请求麦克风权限
            const constraints = {
                audio: {
                    echoCancellation: true,  // 回声消除
                    noiseSuppression: true,  // 噪音抑制
                    autoGainControl: true,   // 自动增益
                    sampleRate: this.sampleRate,
                    channelCount: this.channels
                }
            };

            this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log('[录音] ✅ 麦克风权限已获取');

            if (this.useMediaRecorder) {
                // 使用MediaRecorder API（支持Opus编码）
                await this.initializeMediaRecorder();
            } else {
                // 使用Web Audio API（需要手动编码）
                await this.initializeWebAudio();
            }

            return true;
        } catch (error) {
            console.error('[录音] 初始化失败:', error);
            if (this.onError) {
                this.onError(error);
            }
            throw error;
        }
    }

    /**
     * 使用MediaRecorder初始化（推荐，浏览器原生Opus支持）
     */
    async initializeMediaRecorder() {
        try {
            // 检查浏览器支持的MIME类型
            const mimeTypes = [
                'audio/webm;codecs=opus',
                'audio/ogg;codecs=opus',
                'audio/webm'
            ];

            let mimeType = null;
            for (const type of mimeTypes) {
                if (MediaRecorder.isTypeSupported(type)) {
                    mimeType = type;
                    break;
                }
            }

            if (!mimeType) {
                throw new Error('浏览器不支持Opus编码');
            }

            console.log('[录音] 使用MIME类型:', mimeType);

            // 创建MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.mediaStream, {
                mimeType: mimeType,
                audioBitsPerSecond: 16000  // 16kbps
            });

            // 音频数据事件
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.audioChunks.push(event.data);

                    // 读取Blob数据并发送
                    event.data.arrayBuffer().then(buffer => {
                        if (this.onAudioData) {
                            this.onAudioData(new Uint8Array(buffer));
                        }
                    });
                }
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('[录音] MediaRecorder错误:', event.error);
                if (this.onError) {
                    this.onError(event.error);
                }
            };

            console.log('[录音] ✅ MediaRecorder已初始化');
        } catch (error) {
            console.error('[录音] MediaRecorder初始化失败:', error);
            throw error;
        }
    }

    /**
     * 使用Web Audio API初始化（需要手动Opus编码）
     */
    async initializeWebAudio() {
        try {
            // 创建AudioContext
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            this.audioContext = new AudioContextClass({
                sampleRate: this.sampleRate
            });

            // 创建音频源节点
            this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);

            // 创建ScriptProcessor节点（用于处理音频数据）
            this.processorNode = this.audioContext.createScriptProcessor(
                this.bufferSize,
                this.channels,
                this.channels
            );

            // 处理音频数据
            this.processorNode.onaudioprocess = (event) => {
                if (!this.isRecording) return;

                const inputBuffer = event.inputBuffer;
                const channelData = inputBuffer.getChannelData(0);

                // 转换为Int16（小智后台期望的格式）
                const int16Data = this.float32ToInt16(channelData);

                if (this.onAudioData) {
                    this.onAudioData(int16Data);
                }
            };

            console.log('[录音] ✅ Web Audio API已初始化');
        } catch (error) {
            console.error('[录音] Web Audio API初始化失败:', error);
            throw error;
        }
    }

    /**
     * 开始录音
     */
    startRecording() {
        if (this.isRecording) {
            console.warn('[录音] 已经在录音中');
            return;
        }

        console.log('[录音] 开始录音...');
        this.isRecording = true;
        this.audioChunks = [];

        if (this.useMediaRecorder && this.mediaRecorder) {
            // 使用MediaRecorder，每100ms触发一次dataavailable
            this.mediaRecorder.start(100);
        } else if (this.sourceNode && this.processorNode) {
            // 使用Web Audio API
            this.sourceNode.connect(this.processorNode);
            this.processorNode.connect(this.audioContext.destination);
        }

        console.log('[录音] ✅ 录音已开始');
    }

    /**
     * 停止录音
     */
    stopRecording() {
        if (!this.isRecording) {
            console.warn('[录音] 未在录音中');
            return;
        }

        console.log('[录音] 停止录音...');
        this.isRecording = false;

        if (this.useMediaRecorder && this.mediaRecorder) {
            this.mediaRecorder.stop();
        } else if (this.processorNode) {
            this.processorNode.disconnect();
            if (this.sourceNode) {
                this.sourceNode.disconnect();
            }
        }

        console.log('[录音] ✅ 录音已停止');
    }

    /**
     * 释放资源
     */
    dispose() {
        console.log('[录音] 释放资源...');

        this.stopRecording();

        if (this.mediaRecorder) {
            this.mediaRecorder = null;
        }

        if (this.processorNode) {
            this.processorNode.disconnect();
            this.processorNode = null;
        }

        if (this.sourceNode) {
            this.sourceNode.disconnect();
            this.sourceNode = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        console.log('[录音] ✅ 资源已释放');
    }

    /**
     * 将Float32转换为Int16
     */
    float32ToInt16(float32Array) {
        const int16Array = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16Array;
    }

    /**
     * 获取录音设备列表
     */
    static async getAudioDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            return audioInputs;
        } catch (error) {
            console.error('[录音] 获取设备列表失败:', error);
            return [];
        }
    }
}
