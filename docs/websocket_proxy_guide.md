# 方案 2: 使用 Web Server Plugin 做 WebSocket 代理

## 方案概述

利用项目现有的 `src/plugins/web_server.py`，添加一个 WebSocket 代理端点，
让 Web 客户端连接到本地代理，由代理转发到后台服务器。

## 架构图

```
Web 浏览器 <--WebSocket(无需Header)--> Web Server Plugin <--WebSocket(带Header)--> 后台服务器
   (前端)                                  (本地代理)                            (xiaozhi 服务器)
```

## 优点

- ✅ 不需要修改后台服务器
- ✅ 利用现有代码结构
- ✅ 可以在代理层做额外的处理（如日志、监控）
- ✅ 方便调试和测试

## 缺点

- ⚠️ 增加了一层代理，略微增加延迟
- ⚠️ 需要维护代理逻辑

## 实现代码

### 修改 `src/plugins/web_server.py`

添加 WebSocket 代理端点：

```python
import asyncio
import websockets
from aiohttp import web, WSMsgType
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class WebServerPlugin(Plugin):
    """Web服务器插件 - 扩展 WebSocket 代理功能"""
    
    # ... 现有代码 ...
    
    async def _handle_websocket_proxy(self, request: web.Request) -> web.WebSocketResponse:
        """
        WebSocket 代理端点
        
        浏览器连接到这个端点，代理会转发到真实的后台服务器
        URL: /api/ws-proxy?token=xxx&device_id=xxx&client_id=xxx
        """
        # 1. 从 URL 参数获取认证信息
        query = request.query
        token = query.get('token') or query.get('access_token')
        device_id = query.get('device_id')
        client_id = query.get('client_id')
        
        if not token:
            logger.warning("WebSocket 代理: 缺少 token")
            return web.json_response({'error': '缺少 token'}, status=401)
        
        logger.info(f"WebSocket 代理连接请求: device_id={device_id}")
        
        # 2. 准备客户端 WebSocket
        client_ws = web.WebSocketResponse()
        await client_ws.prepare(request)
        
        # 3. 连接到后台服务器
        backend_url = self.app.config.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_URL")
        
        # 构建 Headers（Python 客户端方式）
        headers = {
            "Authorization": f"Bearer {token}",
            "Protocol-Version": "1",
            "Device-Id": device_id or "",
            "Client-Id": client_id or "",
        }
        
        try:
            # 连接到后台
            logger.info(f"代理连接后台: {backend_url}")
            
            # 判断是否使用 SSL
            ssl_context = None
            if backend_url.startswith("wss://"):
                import ssl
                ssl_context = ssl._create_unverified_context()
            
            async with websockets.connect(
                backend_url,
                extra_headers=headers,
                ssl=ssl_context
            ) as backend_ws:
                logger.info("✅ 代理已连接到后台服务器")
                
                # 4. 双向转发消息
                await self._proxy_messages(client_ws, backend_ws, device_id)
                
        except Exception as e:
            logger.error(f"代理连接后台失败: {e}")
            await client_ws.close(code=1011, reason=f"Backend connection failed: {str(e)}")
        
        return client_ws
    
    async def _proxy_messages(
        self, 
        client_ws: web.WebSocketResponse, 
        backend_ws: websockets.WebSocketClientProtocol,
        device_id: str
    ):
        """双向转发消息"""
        
        async def forward_client_to_backend():
            """客户端 -> 后台"""
            try:
                async for msg in client_ws:
                    if msg.type == WSMsgType.TEXT:
                        logger.debug(f"[{device_id}] 客户端->后台: {msg.data[:100]}...")
                        await backend_ws.send(msg.data)
                    elif msg.type == WSMsgType.BINARY:
                        logger.debug(f"[{device_id}] 客户端->后台: {len(msg.data)} 字节")
                        await backend_ws.send(msg.data)
                    elif msg.type == WSMsgType.ERROR:
                        logger.error(f"[{device_id}] 客户端 WebSocket 错误")
                        break
            except Exception as e:
                logger.error(f"[{device_id}] 客户端->后台转发错误: {e}")
        
        async def forward_backend_to_client():
            """后台 -> 客户端"""
            try:
                async for msg in backend_ws:
                    if isinstance(msg, str):
                        logger.debug(f"[{device_id}] 后台->客户端: {msg[:100]}...")
                        await client_ws.send_str(msg)
                    elif isinstance(msg, bytes):
                        logger.debug(f"[{device_id}] 后台->客户端: {len(msg)} 字节")
                        await client_ws.send_bytes(msg)
            except Exception as e:
                logger.error(f"[{device_id}] 后台->客户端转发错误: {e}")
        
        # 同时运行两个转发任务
        await asyncio.gather(
            forward_client_to_backend(),
            forward_backend_to_client(),
            return_exceptions=True
        )
        
        logger.info(f"[{device_id}] WebSocket 代理连接关闭")
    
    async def on_load(self):
        """插件加载时注册路由"""
        # ... 现有路由 ...
        
        # 添加 WebSocket 代理路由
        self._aiohttp_app.router.add_get('/api/ws-proxy', self._handle_websocket_proxy)
        logger.info("WebSocket 代理端点已注册: /api/ws-proxy")
```

### 修改前端代码

修改 `web-xiaozhi/js/protocol.js`:

```javascript
/**
 * 连接到服务器（使用代理）
 */
async connect() {
    return new Promise((resolve, reject) => {
        try {
            // 连接到本地代理，而不是直接连接后台
            const proxyUrl = new URL('ws://127.0.0.1:8080/api/ws-proxy');
            
            // 通过 URL 参数传递认证信息
            if (this.config.ACCESS_TOKEN) {
                proxyUrl.searchParams.set('token', this.config.ACCESS_TOKEN);
            }
            if (this.config.DEVICE_ID) {
                proxyUrl.searchParams.set('device_id', this.config.DEVICE_ID);
            }
            if (this.config.CLIENT_ID) {
                proxyUrl.searchParams.set('client_id', this.config.CLIENT_ID);
            }
            
            console.log('[协议] 通过代理连接:', proxyUrl.toString());
            
            // 创建 WebSocket 连接（无需 Header）
            this.ws = new WebSocket(proxyUrl.toString());
            this.ws.binaryType = 'arraybuffer';
            
            // ... 其余代码保持不变 ...
        }
    });
}
```

## 使用方法

1. **启动应用**: 确保 Web Server Plugin 已启用
   ```bash
   python main_web.py --web-port 8080
   ```

2. **前端配置**: 修改前端代码使用代理 URL

3. **测试**: 在浏览器中测试连接

## 调试

启用代理日志：

```python
# 在 web_server.py 中
logger.setLevel(logging.DEBUG)  # 显示详细的转发日志
```

查看日志输出：
```
[INFO] WebSocket 代理连接请求: device_id=test-device
[INFO] 代理连接后台: wss://api.tenclass.net/xiaozhi/v1/
[INFO] ✅ 代理已连接到后台服务器
[DEBUG] [test-device] 客户端->后台: {"type":"hello"...
[DEBUG] [test-device] 后台->客户端: {"type":"hello"...
```

## 与方案 1 的对比

| 特性 | 方案 1（修改后台） | 方案 2（本地代理） |
|------|-------------------|-------------------|
| 改动后台 | ✅ 需要 | ❌ 不需要 |
| 延迟 | ⚡ 低 | 🐌 稍高 |
| 调试难度 | 简单 | 中等 |
| 维护成本 | 低 | 中等 |
| 适用场景 | 有后台控制权 | 无后台控制权 |

## 建议

- 如果你有后台服务器的控制权 → **选方案 1**
- 如果你只能修改客户端 → **选方案 2**
