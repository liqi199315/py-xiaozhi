/**
 * OTA配置管理 - 从服务器获取WebSocket URL和Token
 */
class OTAManager {
    constructor(deviceIdentity) {
        this.device = deviceIdentity;
        this.config = null;
        this.OTA_URL = 'https://api.tenclass.net/xiaozhi/ota/';
        this.APP_VERSION = '2.0.3';
        this.APP_NAME = 'xiaozhi';  // ← 改为与Python项目一致
        this.BOARD_TYPE = 'Desktop';  // ← 改为Desktop，模拟桌面客户端
    }

    /**
     * 获取本机IP地址（Web环境使用占位符）
     */
    async getLocalIP() {
        try {
            // Web环境无法直接获取本地IP，使用占位符
            return '0.0.0.0';
        } catch (e) {
            return '0.0.0.0';
        }
    }

    /**
     * 构建OTA请求payload
     */
    async buildPayload() {
        const deviceInfo = this.device.getDeviceInfo();
        const localIP = await this.getLocalIP();

        return {
            application: {
                version: this.APP_VERSION,
                elf_sha256: deviceInfo.serial_number  // Web版本使用序列号
            },
            board: {
                type: this.BOARD_TYPE,
                name: this.APP_NAME,
                ip: localIP,
                mac: deviceInfo.mac_address
            }
        };
    }

    /**
     * 构建OTA请求headers
     */
    buildHeaders(activationVersion = 'v2') {
        const deviceInfo = this.device.getDeviceInfo();

        const headers = {
            'Device-Id': deviceInfo.device_id,
            'Client-Id': deviceInfo.client_id,
            'Content-Type': 'application/json',
            'User-Agent': `${this.BOARD_TYPE}/${this.APP_NAME}-${this.APP_VERSION}`,
            'Accept-Language': 'zh-CN'
        };

        // v2协议添加激活版本头
        if (activationVersion === 'v2') {
            headers['Activation-Version'] = this.APP_VERSION;
            console.log('[OTA] v2协议：添加Activation-Version头部');
        }

        return headers;
    }

    /**
     * 获取OTA配置
     */
    async fetchConfig(activationVersion = 'v2') {
        try {
            console.log('[OTA] 正在获取配置...');
            console.log('[OTA] OTA URL:', this.OTA_URL);

            const headers = this.buildHeaders(activationVersion);
            const payload = await this.buildPayload();

            console.log('[OTA] 请求Headers:', headers);
            console.log('[OTA] 请求Payload:', payload);

            const response = await fetch(this.OTA_URL, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`OTA服务器错误: HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('[OTA] 服务器返回:', data);
            console.log('[OTA] 完整响应:', JSON.stringify(data, null, 2));

            this.config = data;
            return this.parseConfig(data);

        } catch (error) {
            console.error('[OTA] 获取配置失败:', error);
            throw error;
        }
    }

    /**
     * 解析OTA配置
     */
    parseConfig(data) {
        const result = {
            websocket: null,
            mqtt: null,
            activation: null,
            need_activation: false
        };

        // 解析WebSocket配置
        if (data.websocket) {
            const token = data.websocket.token;

            // 检查token有效性
            if (!token || token === 'test-token') {
                console.warn('[OTA] ⚠️ WebSocket token无效或为默认值!');
                console.warn('[OTA] 这通常意味着设备未正确激活');
                console.warn('[OTA] 建议: 点击"重置设备身份"重新激活');
            }

            result.websocket = {
                url: data.websocket.url,
                token: token || 'test-token'
            };
            console.log('[OTA] WebSocket配置:', result.websocket);
        }

        // 解析MQTT配置
        if (data.mqtt) {
            result.mqtt = data.mqtt;
            console.log('[OTA] MQTT配置已获取');
        }

        // 检查是否需要激活
        if (data.activation) {
            result.activation = data.activation;
            result.need_activation = true;
            console.log('[OTA] 检测到激活信息，设备需要激活');
            console.log('[OTA] 验证码:', data.activation.code);
            console.log('[OTA] Challenge:', data.activation.challenge);
        } else {
            console.log('[OTA] 未检测到激活信息，设备已激活');
        }

        return result;
    }

    /**
     * 保存配置到localStorage
     */
    saveConfig(config) {
        try {
            // 更新内存中的配置
            this.config = config;

            // 保存到localStorage
            localStorage.setItem('xiaozhi_ota_config', JSON.stringify(config));
            console.log('[OTA] 配置已保存到localStorage');
            console.log('[OTA] 新Token:', config.websocket?.token);
        } catch (e) {
            console.error('[OTA] 保存配置失败:', e);
        }
    }

    /**
     * 从localStorage加载配置
     */
    loadConfig() {
        try {
            const stored = localStorage.getItem('xiaozhi_ota_config');
            if (stored) {
                this.config = JSON.parse(stored);
                console.log('[OTA] 从localStorage加载配置成功');
                return this.config;
            }
        } catch (e) {
            console.error('[OTA] 加载配置失败:', e);
        }
        return null;
    }

    /**
     * 获取WebSocket URL
     */
    getWebSocketURL() {
        return this.config?.websocket?.url || null;
    }

    /**
     * 获取WebSocket Token
     */
    getWebSocketToken() {
        return this.config?.websocket?.token || null;
    }

    /**
     * 获取激活信息
     */
    getActivationInfo() {
        return this.config?.activation || null;
    }
}
