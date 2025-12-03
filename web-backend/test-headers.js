// 测试 WebSocket 库的 headers 支持
const WebSocket = require('ws');
const https = require('https');

const token = process.argv[2] || '622121be-663d-44d7-b65a-8763f4502e2c';

console.log('🧪 测试不同的 header 发送方式\n');

// 方法 1: 直接在构造函数中传 headers（可能不工作）
console.log('方法 1: 直接传 headers...');
const ws1 = new WebSocket('wss://api.tenclass.net/xiaozhi/v1/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Protocol-Version': '1',
        'Device-Id': '58:11:22:b7:26:42',
        'Client-Id': '975b0760-e76d-4571-be81-362c7cd35fde'
    }
});

ws1.on('open', () => {
    console.log('✅方法 1 连接成功！');
    ws1.close();

    // 尝试方法 2
    tryMethod2();
});

ws1.on('close', (code) => {
    if (code === 1005) {
        console.log('❌方法 1 失败 (1005)\n');
        // 尝试方法 2
        tryMethod2();
    }
});

ws1.on('error', (err) => {
    console.error('❌方法 1 错误:', err.message);
});

function tryMethod2() {
    console.log('方法 2: 使用 perMessageDeflate: false...');

    const ws2 = new WebSocket('wss://api.tenclass.net/xiaozhi/v1/', {
        perMessageDeflate: false,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Protocol-Version': '1',
            'Device-Id': '58:11:22:b7:26:42',
            'Client-Id': '975b0760-e76d-4571-be81-362c7cd35fde'
        }
    });

    ws2.on('open', () => {
        console.log('✅方法 2 连接成功！');

        // 发送 hello
        const hello = {
            type: 'hello',
            version: 1,
            features: { mcp: true },
            transport: 'websocket'
        };
        ws2.send(JSON.stringify(hello));
    });

    ws2.on('message', (data) => {
        console.log('📥 收到消息:', data.toString());
        ws2.close();
    });

    ws2.on('close', (code) => {
        if (code === 1005) {
            console.log('❌方法 2 也失败 (1005)\n');

            console.log('💡 可能的原因:');
            console.log('1. ws 库不支持在 wss:// 连接中传递自定义 headers');
            console.log('2. 需要使用其他库（如 websocket）');
            console.log('3. 或者后台服务器不接受来自 Node.js 客户端的连接');
        } else {
            console.log(`方法 2 关闭: ${code}`);
        }

        process.exit(code === 1000 ? 0 : 1);
    });

    ws2.on('error', (err) => {
        console.error('❌方法 2 错误:', err.message);
    });
}

setTimeout(() => {
    console.log('\n⏱️  测试超时');
    process.exit(1);
}, 15000);
