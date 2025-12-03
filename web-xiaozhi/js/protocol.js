/**
 * 小智WebSocket协议实现 - 通过本地代理连接
 */
class XiaozhiProtocol {
    constructor(config) {
        this.config = config;
        this.ws = null;
        this.connected = false;
        this.sessionId = '';

        // 回调函数
        this.onConnected = null;
        this.onDisconnected = null;
        this.onJsonMessage = null;
        this.onAudioData = null;
        this.onError = null;
    }

    /**
     * 连接到服务器（通过本地代理）
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                // ===== 重要修改：连接到本地代理，而不是直接连接后台 =====
                // 构建本地代理 URL
                const proxyUrl = new URL('ws://127.0.0.1:8080/api/ws-proxy');

                // 通过 URL 参数传递认证信息
                if (this.config.ACCESS_TOKEN) {
                    proxyUrl.searchParams.set('token', this.config.ACCESS_TOKEN);
                }
                if (this.config.DEVICE_ID) {
                    proxyUrl.searchParams.set('device_id', this.config.DEVICE_ID);
                }
                if (this.config.CLIENT_ID) {
                    proxyUrl.searchParams.set('client_id', this.config.CLIENT_ID);
                }

                console.log('[协议] 通过本地代理连接:', proxyUrl.toString());
                console.log('[协议] 使用Token:', this.config.ACCESS_TOKEN);

                // 创建WebSocket连接（无需 Header）
                this.ws = new WebSocket(proxyUrl.toString());
                this.ws.binaryType = 'arraybuffer';  // 接收二进制数据

                // 连接超时处理
                const timeout = setTimeout(() => {
                    if (!this.connected) {
                        this.ws.close();
                        reject(new Error('连接超时'));
                    }
                }, 10000);

                // 连接打开
                this.ws.onopen = () => {
                    console.log('[协议] WebSocket已连接（通过代理）');
                    clearTimeout(timeout);

                    // 发送hello消息
                    this.sendHello()
                        .then(() => {
                            console.log('[协议] Hello消息已发送，等待服务器响应...');
                        })
                        .catch(err => {
                            console.error('[协议] 发送Hello失败:', err);
                            reject(err);
                        });
                };

                // 接收消息
                this.ws.onmessage = (event) => {
                    if (typeof event.data === 'string') {
                        // JSON消息
                        this.handleJsonMessage(event.data, resolve, reject);
                    } else {
                        // 二进制音频数据
                        this.handleAudioData(event.data);
                    }
                };

                // 连接关闭
                this.ws.onclose = (event) => {
                    console.log('[协议] 连接已关闭:', event.code, event.reason);
                    this.connected = false;
                    if (this.onDisconnected) {
                        this.onDisconnected(event.reason);
                    }
                };

                // 连接错误
                this.ws.onerror = (error) => {
                    console.error('[协议] WebSocket错误:', error);
                    clearTimeout(timeout);
                    this.connected = false;
                    if (this.onError) {
                        this.onError(error);
                    }
                    reject(error);
                };

            } catch (error) {
                console.error('[协议] 连接异常:', error);
                reject(error);
            }
        });
    }

    /**
     * 发送Hello消息
     */
    async sendHello() {
        const helloMessage = {
            type: 'hello',
            version: 1,
            features: {
                mcp: true
            },
            transport: 'websocket',
            audio_params: {
                format: this.config.AUDIO.FORMAT,
                sample_rate: this.config.AUDIO.SAMPLE_RATE,
                channels: this.config.AUDIO.CHANNELS,
                frame_duration: this.config.AUDIO.FRAME_DURATION
            }
        };

        console.log('[协议] 发送Hello:', helloMessage);
        return this.sendJson(helloMessage);
    }

    /**
     * 处理JSON消息
     */
    handleJsonMessage(data, resolve, reject) {
        try {
            const message = JSON.parse(data);
            console.log('[协议] 收到JSON消息:', message);

            // 处理服务器hello响应
            if (message.type === 'hello') {
                this.sessionId = message.session_id || '';
                this.connected = true;
                console.log('[协议] ✅ 连接成功! Session ID:', this.sessionId);

                if (this.onConnected) {
                    this.onConnected(message);
                }

                if (resolve) {
                    resolve(message);
                }
                return;
            }

            // 其他消息类型
            if (this.onJsonMessage) {
                this.onJsonMessage(message);
            }

        } catch (error) {
            console.error('[协议] JSON解析错误:', error);
            if (reject) {
                reject(error);
            }
        }
    }

    /**
     * 处理音频数据
     */
    handleAudioData(data) {
        console.log('[协议] 收到音频数据:', data.byteLength, '字节');
        if (this.onAudioData) {
            this.onAudioData(data);
        }
    }

    /**
     * 发送JSON消息
     */
    sendJson(data) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket未连接');
        }

        const jsonStr = JSON.stringify(data);
        this.ws.send(jsonStr);
        return Promise.resolve();
    }

    /**
     * 发送音频数据
     */
    sendAudio(audioData) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket未连接');
        }

        this.ws.send(audioData);
    }

    /**
     * 发送开始监听消息
     */
    async startListening(mode = 'manual') {
        const message = {
            session_id: this.sessionId,
            type: 'listen',
            state: 'start',
            mode: mode  // 'realtime' | 'auto' | 'manual'
        };

        console.log('[协议] 发送开始监听:', message);
        return this.sendJson(message);
    }

    /**
     * 发送停止监听消息
     */
    async stopListening() {
        const message = {
            session_id: this.sessionId,
            type: 'listen',
            state: 'stop'
        };

        console.log('[协议] 发送停止监听:', message);
        return this.sendJson(message);
    }

    /**
     * 断开连接
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }
}