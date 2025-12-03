/**
 * 设备激活管理器
 */
class DeviceActivator {
    constructor(deviceIdentity, otaManager) {
        this.device = deviceIdentity;
        this.ota = otaManager;
        this.OTA_BASE_URL = 'https://api.tenclass.net/xiaozhi/ota/';
        this.isActivating = false;
        this.activationTask = null;
    }

    /**
     * 处理激活流程
     */
    async activate(challenge, code) {
        try {
            console.log('[激活] 开始激活流程...');
            console.log('[激活] Challenge:', challenge);
            console.log('[激活] 验证码:', code);

            const deviceInfo = this.device.getDeviceInfo();

            // 生成HMAC签名
            const hmacSignature = await this.device.generateHmac(challenge);
            console.log('[激活] HMAC签名:', hmacSignature);

            // 构建激活请求payload
            const payload = {
                Payload: {
                    algorithm: 'hmac-sha256',
                    serial_number: deviceInfo.serial_number,
                    challenge: challenge,
                    hmac: hmacSignature
                }
            };

            // 构建请求headers
            const headers = {
                'Activation-Version': '2',
                'Device-Id': deviceInfo.device_id,
                'Client-Id': deviceInfo.client_id,
                'Content-Type': 'application/json'
            };

            const activateUrl = `${this.OTA_BASE_URL}activate`;
            console.log('[激活] 激活URL:', activateUrl);
            console.log('[激活] 请求Headers:', headers);
            console.log('[激活] 请求Payload:', payload);

            // 重试激活（最多60次，每次间隔5秒）
            const maxRetries = 60;
            const retryInterval = 5000;

            for (let attempt = 0; attempt < maxRetries; attempt++) {
                console.log(`[激活] 尝试激活 (${attempt + 1}/${maxRetries})...`);

                try {
                    const response = await fetch(activateUrl, {
                        method: 'POST',
                        headers: headers,
                        body: JSON.stringify(payload)
                    });

                    const responseText = await response.text();
                    console.log(`[激活] HTTP ${response.status}:`, responseText);

                    // 200 - 激活成功
                    if (response.status === 200) {
                        console.log('[激活] ✅ 设备激活成功!');
                        this.device.setActivationStatus(true);
                        return true;
                    }

                    // 202 - 等待用户输入验证码
                    if (response.status === 202) {
                        console.log('[激活] 等待用户输入验证码...');
                        await this.sleep(retryInterval);
                        continue;
                    }

                    // 其他错误
                    try {
                        const errorData = JSON.parse(responseText);
                        const errorMsg = errorData.error || `未知错误 (状态码: ${response.status})`;
                        console.warn(`[激活] 服务器返回: ${errorMsg}`);

                        // Device not found - 继续等待
                        if (errorMsg.includes('Device not found')) {
                            if ((attempt + 1) % 5 === 0) {
                                console.warn('[激活] 提示: 如果错误持续出现，可能需要在网站上刷新页面获取新验证码');
                            }
                        }
                    } catch (e) {
                        console.warn(`[激活] 服务器返回错误 (状态码: ${response.status})`);
                    }

                    await this.sleep(retryInterval);

                } catch (error) {
                    console.warn(`[激活] 请求失败: ${error.message}，重试中...`);
                    await this.sleep(retryInterval);
                }
            }

            // 达到最大重试次数
            console.error('[激活] ❌ 激活失败，达到最大重试次数');
            return false;

        } catch (error) {
            console.error('[激活] 激活异常:', error);
            return false;
        }
    }

    /**
     * 自动激活流程
     */
    async autoActivate(onProgress) {
        try {
            this.isActivating = true;

            // 步骤1: 获取OTA配置
            onProgress && onProgress('获取OTA配置...');
            const config = await this.ota.fetchConfig('v2');

            // 检查是否需要激活
            if (!config.need_activation) {
                console.log('[激活] 设备已激活，无需激活');
                this.device.setActivationStatus(true);
                return {
                    success: true,
                    need_activation: false,
                    message: '设备已激活'
                };
            }

            // 步骤2: 显示验证码
            const activation = config.activation;
            const code = activation.code;
            const challenge = activation.challenge;
            const message = activation.message || '请在xiaozhi.me输入验证码';

            console.log('[激活] 激活信息:');
            console.log('  - 提示:', message);
            console.log('  - 验证码:', code);
            console.log('  - Challenge:', challenge);

            onProgress && onProgress(`请在网站输入验证码: ${code}`);

            // 步骤3: 开始激活
            onProgress && onProgress('正在激活...');
            const success = await this.activate(challenge, code);

            if (success) {
                // 激活成功后重新获取配置
                onProgress && onProgress('激活成功，重新获取配置...');
                const newConfig = await this.ota.fetchConfig('v2');
                this.ota.saveConfig(newConfig);

                return {
                    success: true,
                    need_activation: false,
                    message: '激活成功',
                    config: newConfig
                };
            } else {
                return {
                    success: false,
                    need_activation: true,
                    message: '激活失败',
                    code: code,
                    challenge: challenge
                };
            }

        } catch (error) {
            console.error('[激活] 自动激活异常:', error);
            return {
                success: false,
                error: error.message
            };
        } finally {
            this.isActivating = false;
        }
    }

    /**
     * 取消激活
     */
    cancelActivation() {
        this.isActivating = false;
        if (this.activationTask) {
            console.log('[激活] 取消激活任务');
            this.activationTask = null;
        }
    }

    /**
     * 睡眠函数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
