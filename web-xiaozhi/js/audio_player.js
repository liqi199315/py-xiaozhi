/**
 * 浏览器端音频播放器
 * 用于播放从小智后台接收的Opus音频流
 */
class AudioPlayer {
    constructor() {
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.currentSourceNode = null;

        // 音频参数（与小智后台一致）
        this.sampleRate = 16000;  // 16kHz
        this.channels = 1;         // 单声道

        // 回调函数
        this.onPlaybackStart = null;
        this.onPlaybackEnd = null;
        this.onError = null;
    }

    /**
     * 初始化音频播放器
     */
    async initialize() {
        try {
            console.log('[播放] 初始化音频播放器...');

            // 创建AudioContext
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            this.audioContext = new AudioContextClass({
                sampleRate: this.sampleRate
            });

            console.log('[播放] ✅ AudioContext已创建');
            console.log('[播放] 采样率:', this.audioContext.sampleRate);

            return true;
        } catch (error) {
            console.error('[播放] 初始化失败:', error);
            if (this.onError) {
                this.onError(error);
            }
            throw error;
        }
    }

    /**
     * 解码Opus音频数据
     * 浏览器的AudioContext原生支持解码Opus/WebM格式
     */
    async decodeAudioData(opusData) {
        try {
            // 如果数据是Uint8Array，转换为ArrayBuffer
            const arrayBuffer = opusData instanceof ArrayBuffer
                ? opusData
                : opusData.buffer.slice(opusData.byteOffset, opusData.byteOffset + opusData.byteLength);

            // 使用AudioContext解码音频数据
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);

            console.log('[播放] ✅ 音频解码成功:', {
                duration: audioBuffer.duration.toFixed(2) + 's',
                sampleRate: audioBuffer.sampleRate,
                channels: audioBuffer.numberOfChannels,
                length: audioBuffer.length
            });

            return audioBuffer;
        } catch (error) {
            console.error('[播放] 音频解码失败:', error);
            throw error;
        }
    }

    /**
     * 播放音频数据
     */
    async playAudioData(opusData) {
        try {
            // 解码音频数据
            const audioBuffer = await this.decodeAudioData(opusData);

            // 添加到播放队列
            this.audioQueue.push(audioBuffer);

            // 如果当前没有在播放，开始播放
            if (!this.isPlaying) {
                await this.processQueue();
            }

            return true;
        } catch (error) {
            console.error('[播放] 播放失败:', error);
            if (this.onError) {
                this.onError(error);
            }
            return false;
        }
    }

    /**
     * 处理播放队列
     */
    async processQueue() {
        if (this.isPlaying || this.audioQueue.length === 0) {
            return;
        }

        this.isPlaying = true;
        console.log('[播放] 开始播放队列，剩余片段:', this.audioQueue.length);

        if (this.onPlaybackStart) {
            this.onPlaybackStart();
        }

        while (this.audioQueue.length > 0) {
            const audioBuffer = this.audioQueue.shift();
            await this.playBuffer(audioBuffer);
        }

        this.isPlaying = false;
        console.log('[播放] 播放队列完成');

        if (this.onPlaybackEnd) {
            this.onPlaybackEnd();
        }
    }

    /**
     * 播放单个AudioBuffer
     */
    playBuffer(audioBuffer) {
        return new Promise((resolve) => {
            try {
                // 创建音频源节点
                const sourceNode = this.audioContext.createBufferSource();
                sourceNode.buffer = audioBuffer;

                // 连接到输出
                sourceNode.connect(this.audioContext.destination);

                // 播放结束回调
                sourceNode.onended = () => {
                    console.log('[播放] 音频片段播放完成');
                    this.currentSourceNode = null;
                    resolve();
                };

                // 开始播放
                sourceNode.start(0);
                this.currentSourceNode = sourceNode;

                console.log('[播放] ▶️ 正在播放，时长:', audioBuffer.duration.toFixed(2) + 's');
            } catch (error) {
                console.error('[播放] 播放Buffer失败:', error);
                resolve();
            }
        });
    }

    /**
     * 停止当前播放
     */
    stop() {
        console.log('[播放] 停止播放...');

        // 停止当前播放
        if (this.currentSourceNode) {
            try {
                this.currentSourceNode.stop();
            } catch (error) {
                console.warn('[播放] 停止播放时出错:', error);
            }
            this.currentSourceNode = null;
        }

        // 清空队列
        this.audioQueue = [];
        this.isPlaying = false;

        console.log('[播放] ✅ 播放已停止');
    }

    /**
     * 获取音量（当前播放状态）
     */
    getVolume() {
        if (this.audioContext) {
            return this.audioContext.destination.volume || 1.0;
        }
        return 1.0;
    }

    /**
     * 设置音量
     */
    setVolume(volume) {
        if (this.audioContext && this.audioContext.destination) {
            // Web Audio API中destination没有volume属性
            // 需要使用GainNode来控制音量
            console.log('[播放] 设置音量:', volume);
            // TODO: 实现音量控制
        }
    }

    /**
     * 获取播放状态
     */
    getPlaybackState() {
        return {
            isPlaying: this.isPlaying,
            queueLength: this.audioQueue.length,
            currentSourceActive: this.currentSourceNode !== null
        };
    }

    /**
     * 释放资源
     */
    dispose() {
        console.log('[播放] 释放资源...');

        this.stop();

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        console.log('[播放] ✅ 资源已释放');
    }
}
