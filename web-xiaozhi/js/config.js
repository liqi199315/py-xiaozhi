// 配置管理
const CONFIG = {
    // 从你的Python config.json获取这些值
    WEBSOCKET_URL: 'ws://127.0.0.1:8080/api/ws-proxy',  // 本地代理地址
    ACCESS_TOKEN: '622121be-663d-44d7-b65a-8763f4502e2c',  // 真实Token（从 Python config.json）
    DEVICE_ID: '58:11:22:b7:26:42',                        // 设备ID
    CLIENT_ID: '975b0760-e76d-4571-be81-362c7cd35fde',     // 客户端ID
    
    ACTIVATION_VERSION: "v2",
    // 音频参数（与Python保持一致）
    AUDIO: {
        FORMAT: 'opus',
        SAMPLE_RATE: 16000,
        CHANNELS: 1,
        FRAME_DURATION: 20
    }
};