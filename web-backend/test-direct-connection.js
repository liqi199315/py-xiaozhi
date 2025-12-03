// 测试脚本：直接连接小智后台验证 headers
const WebSocket = require('ws');

const token = process.argv[2] || 'test-token';
const deviceId = 'test-device';
const clientId = 'test-client';

console.log('🧪 测试直接连接小智后台\n');
console.log(`Token: ${token.substring(0, 10)}...`);
console.log(`Device ID: ${deviceId}`);
console.log(`Client ID: ${clientId}\n`);

const url = 'wss://api.tenclass.net/xiaozhi/v1/';

console.log(`连接: ${url}\n`);

const ws = new WebSocket(url, {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Protocol-Version': '1',
        'Device-Id': deviceId,
        'Client-Id': clientId
    },
    rejectUnauthorized: false
});

ws.on('open', () => {
    console.log('✅ WebSocket 连接成功！\n');
    console.log('📤 发送 hello 消息...');

    const hello = {
        type: 'hello',
        version: 1,
        features: { mcp: true },
        transport: 'websocket',
        audio_params: {
            format: 'opus',
            sample_rate: 16000,
            channels: 1,
            frame_duration: 20
        }
    };

    ws.send(JSON.stringify(hello));
    console.log('Hello 消息已发送\n');
});

ws.on('message', (data) => {
    console.log('📥 收到消息:');
    try {
        const msg = JSON.parse(data.toString());
        console.log(JSON.stringify(msg, null, 2));

        if (msg.type === 'hello' && msg.session_id) {
            console.log(`\n🎉 认证成功！Session ID: ${msg.session_id}`);
            ws.close();
        }
    } catch (e) {
        console.log(data.toString());
    }
});

ws.on('error', (error) => {
    console.error('❌ 错误:', error.message);
});

ws.on('close', (code, reason) => {
    console.log(`\n🔌 连接已关闭`);
    console.log(`Code: ${code}`);
    console.log(`Reason: ${reason.toString()}`);

    if (code === 1005) {
        console.log('\n⚠️  错误 1005 通常表示:');
        console.log('1. Token 无效或过期');
        console.log('2. Token 格式不正确');
        console.log('3. 设备未激活');
        console.log('\n💡 建议: 检查你的 token 是否正确');
    }

    process.exit(code === 1000 ? 0 : 1);
});

// 超时检查
setTimeout(() => {
    if (ws.readyState !== WebSocket.OPEN) {
        console.log('\n⏱️  连接超时');
        ws.close();
    }
}, 10000);
