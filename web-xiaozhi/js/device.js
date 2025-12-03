/**
 * 设备身份管理 - 管理序列号、HMAC密钥、MAC地址
 */
class DeviceIdentity {
    constructor() {
        this.STORAGE_KEY = 'xiaozhi_device_identity';
        this.identity = this.loadIdentity();
    }

    /**
     * 从localStorage加载设备身份
     */
    loadIdentity() {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        if (stored) {
            try {
                return JSON.parse(stored);
            } catch (e) {
                console.error('加载设备身份失败:', e);
            }
        }

        // 如果没有存储的身份，创建新的
        return this.createNewIdentity();
    }

    /**
     * 创建新的设备身份
     */
    createNewIdentity() {
        const identity = {
            serial_number: this.generateSerialNumber(),
            hmac_key: this.generateHmacKey(),
            mac_address: this.generateMacAddress(),
            client_id: this.generateUUID(),
            is_activated: false,
            created_at: new Date().toISOString()
        };

        this.saveIdentity(identity);
        return identity;
    }

    /**
     * 保存设备身份到localStorage
     */
    saveIdentity(identity) {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(identity));
            this.identity = identity;
        } catch (e) {
            console.error('保存设备身份失败:', e);
        }
    }

    /**
     * 生成序列号（16字节随机hex）
     */
    generateSerialNumber() {
        const bytes = new Uint8Array(16);
        crypto.getRandomValues(bytes);
        return Array.from(bytes)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    /**
     * 生成HMAC密钥（32字节随机hex）
     */
    generateHmacKey() {
        const bytes = new Uint8Array(32);
        crypto.getRandomValues(bytes);
        return Array.from(bytes)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    /**
     * 生成MAC地址（基于浏览器指纹）
     */
    generateMacAddress() {
        // 使用浏览器特征生成稳定的MAC地址
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            screen.width,
            screen.height,
            new Date().getTimezoneOffset()
        ].join('|');

        // 简单hash生成12位hex
        let hash = 0;
        for (let i = 0; i < fingerprint.length; i++) {
            hash = ((hash << 5) - hash) + fingerprint.charCodeAt(i);
            hash = hash & hash;
        }

        // 转换为MAC地址格式
        const hex = Math.abs(hash).toString(16).padStart(12, '0');
        return hex.match(/.{2}/g).join(':').substring(0, 17);
    }

    /**
     * 生成UUID v4
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * 使用HMAC-SHA256生成签名
     */
    async generateHmac(challenge) {
        try {
            // 将hex字符串转换为Uint8Array
            const keyBytes = this.hexToBytes(this.identity.hmac_key);
            const messageBytes = new TextEncoder().encode(challenge);

            // 导入密钥
            const cryptoKey = await crypto.subtle.importKey(
                'raw',
                keyBytes,
                { name: 'HMAC', hash: 'SHA-256' },
                false,
                ['sign']
            );

            // 生成签名
            const signature = await crypto.subtle.sign(
                'HMAC',
                cryptoKey,
                messageBytes
            );

            // 转换为hex字符串
            return this.bytesToHex(new Uint8Array(signature));

        } catch (error) {
            console.error('生成HMAC签名失败:', error);
            throw error;
        }
    }

    /**
     * hex字符串转Uint8Array
     */
    hexToBytes(hex) {
        const bytes = new Uint8Array(hex.length / 2);
        for (let i = 0; i < hex.length; i += 2) {
            bytes[i / 2] = parseInt(hex.substr(i, 2), 16);
        }
        return bytes;
    }

    /**
     * Uint8Array转hex字符串
     */
    bytesToHex(bytes) {
        return Array.from(bytes)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    /**
     * 获取设备信息
     */
    getDeviceInfo() {
        return {
            serial_number: this.identity.serial_number,
            mac_address: this.identity.mac_address,
            device_id: this.identity.mac_address,  // 使用MAC作为device_id
            client_id: this.identity.client_id,
            is_activated: this.identity.is_activated
        };
    }

    /**
     * 设置激活状态
     */
    setActivationStatus(activated) {
        this.identity.is_activated = activated;
        this.saveIdentity(this.identity);
    }

    /**
     * 检查是否已激活
     */
    isActivated() {
        return this.identity.is_activated || false;
    }

    /**
     * 重置设备身份（用于测试）
     */
    reset() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.identity = this.createNewIdentity();
    }
}
