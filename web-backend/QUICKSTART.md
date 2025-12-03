# 小智 Web 客户端 - Node.js 代理版本

## 🎉 完成！

我已经为你创建了一个完整的 **Node.js WebSocket 代理服务器**！

## 📁 创建的文件

```
web-backend/
├── server.js           # 主服务器文件
├── package.json        # Node.js 项目配置
├── .env.example        # 环境变量示例
├── .gitignore         # Git 忽略文件
├── README.md          # 详细文档
├── start.bat          # Windows 启动脚本
└── start.sh           # Linux/Mac 启动脚本
```

## 🚀 快速开始（3 步）

### 步骤 1: 安装 Node.js（如果还没有）

访问 https://nodejs.org/ 下载并安装 LTS 版本

### 步骤 2: 启动代理服务器

**Windows**:
```bash
cd web-backend
start.bat
```

**Linux/Mac**:
```bash
cd web-backend
chmod +x start.sh
./start.sh
```

或者手动启动：
```bash
cd web-backend
npm install    # 首次运行
npm start      # 启动服务器
```

### 步骤 3: 测试连接

打开浏览器访问: **http://localhost:8080**

你会看到一个状态页面，显示：
- ✅ 服务运行中
- 当前连接数
- WebSocket 端点信息

## ✅ 与 web-xiaozhi 前端集成

前端代码已经准备好了，只需确保连接到 Node.js 代理：

```javascript
// web-xiaozhi/js/protocol.js
const proxyUrl = new URL('ws://127.0.0.1:8080/api/ws-proxy');
proxyUrl.searchParams.set('token', this.config.ACCESS_TOKEN);
// ...
```

## 📊 架构对比

### Python 版本 vs Node.js 版本

| 特性 | Python 版本 | Node.js 版本 |
|------|-------------|--------------|
| 语言 | Python 3.8+ | Node.js 14+ |
| 依赖 | aiohttp, websockets | express, ws |
| 启动方式 | `python main_web.py` | `npm start` |
| 性能 | ⚡ 高 | ⚡⚡ 非常高 |
| 部署 | 需要 Python 环境 | 需要 Node.js 环境 |
| 日志 | 详细 | 详细 |
| 并发 |  异步IO | 事件循环 |

### 选择建议

- **如果你熟悉 Python** → 使用 Python 版本（已实现在 `src/plugins/web_server.py`）
- **如果你熟悉 Node.js** → 使用 Node.js 版本（`web-backend/`）
- **如果要独立部署** → Node.js 版本更轻量
- **如果要集成到现有项目** → 看项目技术栈

## 🔧 详细配置

### 1. 修改端口

编辑 `web-backend/.env`:
```bash
PORT=3000  # 使用端口 3000
```

###  2. 修改后台地址

如果要连接本地开发服务器：
```bash
# .env
BACKEND_WS_URL=ws://localhost:8765/xiaozhi/v1/
```

### 3. 生产部署

使用 PM2:
```bash
npm install -g pm2
pm2 start server.js --name xiaozhi-proxy
pm2 save
```

或使用 Docker:
```bash
docker build -t xiaozhi-proxy .
docker run -p 8080:8080 xiaozhi-proxy
```

## 🐛 故障排查

### 问题 1: Node.js 未安装

**错误**: `'node' 不是内部或外部命令`

**解决**: 安装 Node.js from https://nodejs.org/

### 问题 2: 端口被占用

**错误**: `EADDRINUSE: address already in use :::8080`

**解决**:
```bash
# 杀掉占用端口的进程，或使用其他端口
PORT=3000 npm start
```

### 问题 3: npm install 失败

**解决**:
```bash
# 清除缓存
npm cache clean --force

# 使用国内镜像
npm install --registry=https://registry.npmmirror.com
```

## 🎯 测试

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

在浏览器控制台：
```javascript
const ws = new WebSocket('ws://localhost:8080/api/ws-proxy?token=YOUR_TOKEN');
ws.onopen = () => console.log('✅ 连接成功');
ws.onmessage = (e) => console.log('📥 收到:', e.data);
```

## 📝 日志示例

服务器运行时的日志：
```
🚀 小智 WebSocket 代理服务器
================================

✅ 服务器已启动
   - HTTP:      http://localhost:8080
   - WebSocket: ws://localhost:8080/api/ws-proxy

[abc123] 📥 新连接请求
  - Device ID: web-client
  - Client ID: web-client
[abc123] 🔌 连接后台: wss://api.tenclass.net/xiaozhi/v1/
[abc123] ✅ 已连接到后台服务器
[abc123] 📤 客户端→后台: {"type":"hello"...
[abc123] 📥 后台→客户端: {"type":"hello","session_id":"xyz"...
```

## 🎨 未来扩展（可选）

如果你想添加 Vue 或 React 前端：

### Vue 版本
```bash
cd web-backend
npm install vue@next @vitejs/plugin-vue vite
# 然后创建 Vue 组件
```

### React 版本
```bash
cd web-backend
npx create-react-app client
# 或使用 Vite
npm create vite@latest client -- --template react
```

我可以帮你创建完整的 Vue 或 React 版本，如果需要的话！

## 📚 相关文档

- **Node.js 文档**: `web-backend/README.md`
- **原 Python 版本**: `WEB_PROXY_IMPLEMENTATION.md`
- **故障排查**: `web-xiaozhi/TROUBLESHOOTING.md`

## 🎊 总结

现在你有**两个选择**：

1. **Python 版本** (已实现)
   - 位置: `src/plugins/web_server.py`
   - 启动: `python main_web.py --web-port 8080`
   
2. **Node.js 版本** (新建)
   - 位置: `web-backend/`
   - 启动: `cd web-backend && npm start`

**两者功能完全相同**，选择你熟悉的即可！

---

**立即开始**:
```bash
cd web-backend
start.bat
```

然后访问 http://localhost:8080 查看状态！🚀
