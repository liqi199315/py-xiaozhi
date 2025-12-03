const express = require('express');
const { WebSocketServer, WebSocket } = require('ws');
const http = require('http');
const https = require('https');
const cors = require('cors');
const path = require('path');

// 配置
const PORT = process.env.PORT || 8080;
const HOST = process.env.HOST || '0.0.0.0';

// 创建 Express 应用
const app = express();
app.use(cors());
app.use(express.json());

// 静态文件服务（提供 test.html 等文件）
app.use(express.static(path.join(__dirname)));

// 创建 HTTP 服务器
const server = http.createServer(app);

// 创建 WebSocket 服务器
const wss = new WebSocketServer({
    server,
    path: '/api/ws-proxy'
});

console.log('🚀 小智 WebSocket 代理服务器');
console.log('================================');

// 健康检查端点
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'xiaozhi-websocket-proxy',
        connections: wss.clients.size
    });
});

// 主页
app.get('/', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>小智 WebSocket 代理</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                .info { background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0; }
                .endpoint { background: #e8f4f8; padding: 10px; border-left: 4px solid #2196F3; margin: 10px 0; }
                code { background: #272822; color: #f8f8f2; padding: 2px 6px; border-radius: 3px; }
                .status { color: green; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>🚀 小智 WebSocket 代理服务器</h1>
            <div class="info">
                <p><span class="status">✅ 服务运行中</span></p>
                <p>当前连接数: <strong id="connections">0</strong></p>
            </div>
            
            <h2>WebSocket 端点</h2>
            <div class="endpoint">
                <p><strong>URL:</strong> <code>ws://localhost:${PORT}/api/ws-proxy</code></p>
                <p><strong>参数:</strong></p>
                <ul>
                    <li><code>token</code> - 访问令牌（必需）</li>
                    <li><code>device_id</code> - 设备ID（可选）</li>
                    <li><code>client_id</code> - 客户端ID（可选）</li>
                </ul>
                <p><strong>示例:</strong></p>
                <code>ws://localhost:${PORT}/api/ws-proxy?token=YOUR_TOKEN&device_id=web-client</code>
            </div>

            <h2>HTTP API</h2>
            <div class="endpoint">
                <p><code>GET /health</code> - 健康检查</p>
                <p><code>GET /</code> - 此页面</p>
            </div>

            <script>
                setInterval(async () => {
                    const res = await fetch('/health');
                    const data = await res.json();
                    document.getElementById('connections').textContent = data.connections;
                }, 2000);
            </script>
        </body>
        </html>
    `);
});

// WebSocket 连接处理
wss.on('connection', async (clientWs, request) => {
    const clientId = Math.random().toString(36).substring(7);

    try {
        // 解析 URL 参数
        const url = new URL(request.url, `http://${request.headers.host}`);
        const token = url.searchParams.get('token') || url.searchParams.get('access_token');
        const deviceId = url.searchParams.get('device_id') || 'web-client';
        const clientIdParam = url.searchParams.get('client_id') || 'web-client';

        console.log(`\n[${clientId}] 📥 新连接请求`);
        console.log(`  - Device ID: ${deviceId}`);
        console.log(`  - Client ID: ${clientIdParam}`);

        // 验证 token
        if (!token) {
            console.log(`[${clientId}] ❌ 缺少 token，拒绝连接`);
            clientWs.close(1008, 'Missing token parameter');
            return;
        }

        if (token === 'test-token') {
            console.log(`[${clientId}] ⚠️  使用测试 token，可能导致后台认证失败`);
        }

        // 获取后台服务器 URL（从环境变量或使用默认值）
        const backendUrl = process.env.BACKEND_WS_URL || 'wss://api.tenclass.net/xiaozhi/v1/';

        console.log(`[${clientId}] 🔌 连接后台: ${backendUrl}`);

        // 连接到后台服务器
        const backendWs = new WebSocket(backendUrl, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Protocol-Version': '1',
                'Device-Id': deviceId,
                'Client-Id': clientIdParam
            },
            // 关键配置
            perMessageDeflate: false,  // 禁用压缩
            rejectUnauthorized: false  // 开发时可以忽略证书验证
        });

        // 后台连接成功
        backendWs.on('open', () => {
            console.log(`[${clientId}] ✅ 已连接到后台服务器`);
        });

        // 客户端 -> 后台
        clientWs.on('message', (data, isBinary) => {
            if (backendWs.readyState === WebSocket.OPEN) {
                if (isBinary) {
                    console.log(`[${clientId}] 📤 客户端→后台: ${data.length} 字节`);
                } else {
                    const preview = data.toString().substring(0, 100);
                    console.log(`[${clientId}] 📤 客户端→后台: ${preview}${data.length > 100 ? '...' : ''}`);
                }
                backendWs.send(data, { binary: isBinary });
            }
        });

        // 后台 -> 客户端
        backendWs.on('message', (data, isBinary) => {
            if (clientWs.readyState === WebSocket.OPEN) {
                if (isBinary) {
                    console.log(`[${clientId}] 📥 后台→客户端: ${data.length} 字节`);
                } else {
                    const preview = data.toString().substring(0, 100);
                    console.log(`[${clientId}] 📥 后台→客户端: ${preview}${data.length > 100 ? '...' : ''}`);
                }
                clientWs.send(data, { binary: isBinary });
            }
        });

        // 错误处理
        clientWs.on('error', (error) => {
            console.log(`[${clientId}] ❌ 客户端错误:`, error.message);
        });

        backendWs.on('error', (error) => {
            console.log(`[${clientId}] ❌ 后台连接错误:`, error.message);
            if (clientWs.readyState === WebSocket.OPEN) {
                clientWs.close(1011, `Backend error: ${error.message}`);
            }
        });

        // 关闭处理
        clientWs.on('close', (code, reason) => {
            console.log(`[${clientId}] 🔌 客户端断开: ${code} ${reason}`);
            if (backendWs.readyState === WebSocket.OPEN || backendWs.readyState === WebSocket.CONNECTING) {
                backendWs.close();
            }
        });

        backendWs.on('close', (code, reason) => {
            console.log(`[${clientId}] 🔌 后台断开: ${code} ${reason}`);

            // WebSocket 规范中的保留状态码不能主动使用
            // 1004, 1005, 1006, 1015 都是保留的，不能作为 close() 的参数
            let closeCode = 1011; // 默认使用 1011（服务器错误）
            let closeReason = 'Backend closed';

            if (code === 1005) {
                // 1005 表示没有收到状态码（通常是认证失败）
                console.log(`[${clientId}] ⚠️  后台连接被拒绝（可能是 token 认证失败）`);
                closeCode = 1008; // 策略违反（认证失败）
                closeReason = 'Backend authentication failed';
            } else if (code === 1006) {
                // 1006 表示连接异常关闭，不能直接传递，使用 1011
                console.log(`[${clientId}] ⚠️  后台连接异常关闭`);
                closeCode = 1011; // 内部错误
                closeReason = 'Backend connection closed abnormally';
            } else if ([1004, 1015].includes(code)) {
                // 其他保留状态码，使用 1011
                closeCode = 1011;
                closeReason = 'Backend connection error';
            } else if (code === 1000) {
                // 正常关闭
                closeCode = 1000;
                closeReason = 'Normal closure';
            } else if (code >= 1000 && code < 5000 && ![1004, 1005, 1006, 1015].includes(code)) {
                // 其他有效的状态码可以直接使用
                closeCode = code;
                closeReason = reason ? reason.toString() : 'Backend closed';
            }

            if (clientWs.readyState === WebSocket.OPEN) {
                try {
                    clientWs.close(closeCode, closeReason);
                    console.log(`[${clientId}] 📤 已向客户端发送关闭: ${closeCode} ${closeReason}`);
                } catch (err) {
                    console.error(`[${clientId}] ❌ 关闭客户端连接失败:`, err.message);
                    // 强制关闭
                    clientWs.terminate();
                }
            }
        });

    } catch (error) {
        console.error(`[${clientId}] ❌ 处理连接失败:`, error);
        if (clientWs.readyState === WebSocket.OPEN) {
            clientWs.close(1011, 'Proxy error');
        }
    }
});

// 启动服务器
server.listen(PORT, HOST, () => {
    console.log(`\n✅ 服务器已启动`);
    console.log(`   - HTTP:      http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`);
    console.log(`   - WebSocket: ws://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/api/ws-proxy`);
    console.log(`   - 健康检查:  http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/health`);
    console.log('\n按 Ctrl+C 停止服务器\n');
});

// 优雅关闭
process.on('SIGTERM', () => {
    console.log('\n📴 收到 SIGTERM 信号，正在关闭服务器...');
    server.close(() => {
        console.log('✅ 服务器已关闭');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('\n📴 收到 SIGINT 信号，正在关闭服务器...');
    server.close(() => {
        console.log('✅ 服务器已关闭');
        process.exit(0);
    });
});
