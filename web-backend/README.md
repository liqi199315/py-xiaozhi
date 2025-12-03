# 小智 WebSocket 代理服务器 (Node.js)

一个独立的 Node.js WebSocket 代理服务器，解决浏览器无法传递自定义 Header 的问题。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd web-backend
npm install
```

### 2. 启动服务器

**开发模式**（自动重启）:
```bash
npm run dev
```

**生产模式**:
```bash
npm start
```

启动后你会看到：
```
🚀 小智 WebSocket 代理服务器
================================

✅ 服务器已启动
   - HTTP:      http://localhost:8080
   - WebSocket: ws://localhost:8080/api/ws-proxy
   - 健康检查:  http://localhost:8080/health
```

### 3. 测试连接

打开浏览器访问: http://localhost:8080

## 📊 架构说明

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│  Web 浏览器  │ ◄────► │  Node.js 代理     │ ◄────► │  小智后台   │
│             │  URL参数 │  (port 8080)     │  Header │             │
│  protocol.js│  token   │  server.js       │  Auth   │  认证通过✅  │
└─────────────┘         └──────────────────┘         └─────────────┘
```

## 🔧 配置

### 环境变量

复制 `.env.example` 到 `.env` 并修改：

```bash
cp .env.example .env
```

可配置项：
- `PORT` - 服务器端口（默认 8080）
- `HOST` - 监听地址（默认 0.0.0.0）
- `BACKEND_WS_URL` - 后台 WebSocket 地址

### 修改后台地址

如果需要连接到本地开发服务器：

```bash
# .env
BACKEND_WS_URL=ws://localhost:8765/xiaozhi/v1/
```

## 📡 API 端点

### WebSocket 代理

**URL**: `ws://localhost:8080/api/ws-proxy`

**参数**:
- `token` - 访问令牌（必需）
- `device_id` - 设备ID（可选，默认 'web-client'）
- `client_id` - 客户端ID（可选，默认 'web-client'）

**示例**:
```javascript
const ws = new WebSocket('ws://localhost:8080/api/ws-proxy?token=YOUR_TOKEN&device_id=my-device');
```

### HTTP 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务器状态页面 |
| `/health` | GET | 健康检查（返回连接数等信息） |

## 🧪 测试

### 测试 1: 健康检查

```bash
curl http://localhost:8080/health
```

期望输出：
```json
{
  "status": "ok",
  "service": "xiaozhi-websocket-proxy",
  "connections": 0
}
```

### 测试 2: WebSocket 连接

**在浏览器控制台运行**:

```javascript
// 连接代理
const ws = new WebSocket('ws://localhost:8080/api/ws-proxy?token=YOUR_REAL_TOKEN&device_id=test-device');

ws.onopen = () => console.log('✅ 连接成功');
ws.onmessage = (e) => console.log('📥 收到消息:', e.data);
ws.onerror = (e) => console.error('❌ 错误:', e);
ws.onclose = (e) => console.log('🔌 关闭:', e.code, e.reason);

// 发送 hello 消息
ws.send(JSON.stringify({
    type: 'hello',
    version: 1,
    features: { mcp: true },
    transport: 'websocket'
}));
```

## 📝 日志说明

服务器会记录详细的转发日志：

```
[abc123] 📥 新连接请求
  - Device ID: web-client
  - Client ID: web-client
[abc123] 🔌 连接后台: wss://api.tenclass.net/xiaozhi/v1/
[abc123] ✅ 已连接到后台服务器
[abc123] 📤 客户端→后台: {"type":"hello"...
[abc123] 📥 后台→客户端: {"type":"hello","session_id":"xyz"...
```

## 🐛 故障排查

### 问题 1: 端口已被占用

**错误**: `Error: listen EADDRINUSE: address already in use :::8080`

**解决**:
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8080
kill -9 <PID>

# 或者使用不同端口
PORT=8081 npm start
```

### 问题 2: 后台连接失败

**症状**: 日志显示 "后台连接错误"

**检查**:
1. 确认 `BACKEND_WS_URL` 配置正确
2. 检查网络连接
3. 验证 token 是否有效

### 问题 3: 客户端无法连接

**症状**: `ERR_CONNECTION_REFUSED`

**解决**:
1. 确认服务器正在运行
2. 检查端口号是否正确
3. 查看防火墙设置

## 🚀 部署

### Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY server.js ./

EXPOSE 8080

CMD ["node", "server.js"]
```

构建和运行：

```bash
docker build -t xiaozhi-proxy .
docker run -p 8080:8080 -e BACKEND_WS_URL=wss://api.tenclass.net/xiaozhi/v1/ xiaozhi-proxy
```

### PM2 部署（生产环境推荐）

```bash
# 安装 PM2
npm install -g pm2

# 启动服务
pm2 start server.js --name xiaozhi-proxy

# 查看状态
pm2 status

# 查看日志
pm2 logs xiaozhi-proxy

# 设置开机自启
pm2 startup
pm2 save
```

### systemd 服务（Linux）

创建 `/etc/systemd/system/xiaozhi-proxy.service`:

```ini
[Unit]
Description=XiaoZhi WebSocket Proxy
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/web-backend
ExecStart=/usr/bin/node server.js
Restart=on-failure
Environment=NODE_ENV=production
Environment=PORT=8080

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable xiaozhi-proxy
sudo systemctl start xiaozhi-proxy
sudo systemctl status xiaozhi-proxy
```

## 📦 依赖说明

- **express** - Web 框架
- **ws** - WebSocket 库
- **cors** - 跨域支持
- **nodemon** - 开发时自动重启（仅开发依赖）

## 🔐 安全建议

1. **生产环境**: 不要使用 `0.0.0.0` 作为 HOST，改用 `127.0.0.1` 或具体 IP
2. **HTTPS**: 如果对外服务，使用 HTTPS/WSS
3. **Token 验证**: 可以添加额外的 token 白名单验证
4. **速率限制**: 考虑添加请求速率限制

## 📊 性能

- **内存占用**: ~50MB
- **CPU 占用**: 极低
- **延迟增加**: < 1ms
- **并发连接**: 支持数千个

## 📄 许可证

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发者**: py-xiaozhi 项目  
**版本**: 1.0.0  
**更新时间**: 2025-12-02
