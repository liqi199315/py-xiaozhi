/**
 * 小智MQTT协议实现（使用MQTT over WebSocket）
 * 需要引入 Paho MQTT JavaScript 客户端
 */
class XiaozhiMQTTProtocol {
    constructor(config) {
        this.config = config;
        this.client = null;
        this.connected = false;
        this.sessionId = '';

        // UDP配置（浏览器不支持UDP，音频数据通过MQTT发送）
        this.audioSequence = 0;

        // 回调函数
        this.onConnected = null;
        this.onDisconnected = null;
        this.onJsonMessage = null;
        this.onAudioData = null;
        this.onError = null;
    }

    /**
     * 连接到MQTT服务器
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                // 检查Paho库是否加载
                if (typeof Paho === 'undefined' || typeof Paho.MQTT === 'undefined') {
                    reject(new Error('Paho MQTT库未加载，请在HTML中引入: <script src="https://unpkg.com/paho-mqtt@1.1.0/paho-mqtt.js"></script>'));
                    return;
                }

                console.log('[MQTT] 开始连接...');
                console.log('[MQTT] Endpoint:', this.config.MQTT_ENDPOINT);
                console.log('[MQTT] Client ID:', this.config.MQTT_CLIENT_ID);

                // 解析endpoint
                const host = this.config.MQTT_ENDPOINT;
                const port = 8084; // MQTT over WebSocket 默认端口
                const path = '/mqtt'; // WebSocket 路径
                const useSSL = true; // 使用 wss://

                // 创建MQTT客户端
                this.client = new Paho.MQTT.Client(
                    host,
                    port,
                    path,
                    this.config.MQTT_CLIENT_ID
                );

                // 设置回调
                this.client.onConnectionLost = (response) => {
                    console.log('[MQTT] 连接断开:', response.errorMessage);
                    this.connected = false;
                    if (this.onDisconnected) {
                        this.onDisconnected(response.errorMessage);
                    }
                };

                this.client.onMessageArrived = (message) => {
                    this.handleMessage(message);
                };

                // 连接选项
                const connectOptions = {
                    userName: this.config.MQTT_USERNAME,
                    password: this.config.MQTT_PASSWORD,
                    useSSL: useSSL,
                    timeout: 10,
                    keepAliveInterval: 60,
                    cleanSession: true,
                    onSuccess: () => {
                        console.log('[MQTT] 连接成功');
                        this.connected = true;

                        // 订阅服务器消息主题（如果有）
                        if (this.config.MQTT_SUBSCRIBE_TOPIC &&
                            this.config.MQTT_SUBSCRIBE_TOPIC !== 'null') {
                            this.client.subscribe(this.config.MQTT_SUBSCRIBE_TOPIC);
                            console.log('[MQTT] 已订阅主题:', this.config.MQTT_SUBSCRIBE_TOPIC);
                        }

                        // 发送hello消息
                        this.sendHello()
                            .then(() => {
                                console.log('[MQTT] Hello消息已发送');
                            })
                            .catch(err => {
                                console.error('[MQTT] 发送Hello失败:', err);
                                reject(err);
                            });
                    },
                    onFailure: (error) => {
                        console.error('[MQTT] 连接失败:', error.errorMessage);
                        this.connected = false;
                        reject(new Error(`MQTT连接失败: ${error.errorMessage}`));
                    }
                };

                // 发起连接
                this.client.connect(connectOptions);

            } catch (error) {
                console.error('[MQTT] 连接异常:', error);
                reject(error);
            }
        });
    }

    /**
     * 处理接收到的消息
     */
    handleMessage(message) {
        try {
            const payload = message.payloadString;
            console.log('[MQTT] 收到消息:', payload);

            // 尝试解析JSON
            try {
                const data = JSON.parse(payload);
                this.handleJsonMessage(data);
            } catch (e) {
                console.warn('[MQTT] 收到非JSON消息:', payload);
            }
        } catch (error) {
            console.error('[MQTT] 处理消息失败:', error);
        }
    }

    /**
     * 处理JSON消息
     */
    handleJsonMessage(data) {
        console.log('[MQTT] JSON消息:', data);

        // 处理hello响应
        if (data.type === 'hello') {
            this.sessionId = data.session_id || '';
            console.log('[MQTT] ✅ Hello响应已收到, Session ID:', this.sessionId);

            if (this.onConnected) {
                this.onConnected(data);
            }
            return;
        }

        // 其他JSON消息
        if (this.onJsonMessage) {
            this.onJsonMessage(data);
        }
    }

    /**
     * 发送Hello消息
     */
    async sendHello() {
        const hello = {
            type: 'hello',
            version: 1,
            features: {
                mcp: true
            },
            transport: 'mqtt',
            audio_params: {
                format: this.config.AUDIO?.FORMAT || 'opus',
                sample_rate: this.config.AUDIO?.SAMPLE_RATE || 16000,
                channels: this.config.AUDIO?.CHANNELS || 1,
                frame_duration: this.config.AUDIO?.FRAME_DURATION || 20
            }
        };

        console.log('[MQTT] 发送Hello:', hello);
        await this.sendJson(hello);
    }

    /**
     * 发送JSON消息
     */
    async sendJson(data) {
        if (!this.connected) {
            throw new Error('MQTT未连接');
        }

        const payload = JSON.stringify(data);
        const message = new Paho.MQTT.Message(payload);
        message.destinationName = this.config.MQTT_PUBLISH_TOPIC;
        message.qos = 0;

        console.log('[MQTT] 发送消息到主题:', this.config.MQTT_PUBLISH_TOPIC);
        this.client.send(message);
    }

    /**
     * 发送音频数据
     * 注意：浏览器不支持UDP，音频通过MQTT发送（Base64编码）
     */
    async sendAudio(audioData) {
        if (!this.connected) {
            throw new Error('MQTT未连接');
        }

        // 将音频数据转换为Base64
        const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioData)));

        const audioMessage = {
            type: 'audio',
            sequence: this.audioSequence++,
            data: base64Audio,
            format: 'opus'
        };

        await this.sendJson(audioMessage);
    }

    /**
     * 断开连接
     */
    async disconnect() {
        if (this.client && this.connected) {
            console.log('[MQTT] 正在断开连接...');
            this.client.disconnect();
            this.connected = false;
        }
    }
}
