# WebSocket 认证支持 - 修改指南

## 问题背景

浏览器的 WebSocket API 不支持自定义 Header，导致 Web 客户端无法像 Python 客户端那样通过 `Authorization` Header 传递 token。

## 解决方案

让后台 WebSocket 服务器同时支持两种认证方式：

1. **Header 方式**（用于 Python 客户端）
   ```
   Authorization: Bearer {token}
   Device-Id: {device_id}
   Client-Id: {client_id}
   ```

2. **URL 参数方式**（用于 Web 浏览器）
   ```
   wss://api.example.com/xiaozhi/v1/?token={token}&device_id={device_id}&client_id={client_id}
   ```

## 实现步骤

### 步骤 1: 使用认证辅助模块

我已经创建了 `src/protocols/websocket_auth_helper.py`，提供了：

- `extract_token_from_request(path, headers)` - 从请求中提取 token
- `validate_token(token, expected_token)` - 验证 token

### 步骤 2: 修改 WebSocket 服务器

你需要找到 WebSocket 服务器的连接处理代码，通常在以下位置之一：

1. `src/plugins/web_server.py` - 如果使用 aiohttp
2. 自定义的 WebSocket 服务器入口
3. 第三方框架的 WebSocket handler

#### 示例 1: 使用 websockets 库

如果你使用 `websockets` 库作为服务器：

```python
import asyncio
import websockets
from src.protocols.websocket_auth_helper import extract_token_from_request, validate_token
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def websocket_handler(websocket, path):
    """处理 WebSocket 连接"""
    
    # 1. 提取认证信息
    token, device_id, client_id = extract_token_from_request(
        path, 
        websocket.request_headers
    )
    
    # 2. 验证 token
    if not validate_token(token):
        logger.warning(f"认证失败，拒绝连接: device_id={device_id}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    logger.info(f"✅ 客户端认证成功: device_id={device_id}, client_id={client_id}")
    
    # 3. 处理正常的 WebSocket 通信
    try:
        async for message in websocket:
            # 处理消息...
            pass
    except websockets.ConnectionClosed:
        logger.info(f"客户端断开连接: {device_id}")

# 启动服务器
async def main():
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        logger.info("WebSocket 服务器启动在 ws://0.0.0.0:8765")
        await asyncio.Future()  # 永久运行

if __name__ == "__main__":
    asyncio.run(main())
```

#### 示例 2: 使用 aiohttp

如果你使用 `aiohttp` 框架：

```python
from aiohttp import web
import aiohttp
from src.protocols.websocket_auth_helper import extract_token_from_request, validate_token
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

async def websocket_handler(request):
    """处理 WebSocket 连接"""
    
    # 1. 提取认证信息
    token, device_id, client_id = extract_token_from_request(
        request.path_qs,  # 包含查询参数的完整路径
        dict(request.headers)
    )
    
    # 2. 验证 token
    if not validate_token(token):
        logger.warning(f"认证失败，拒绝连接: device_id={device_id}")
        return web.Response(status=401, text="Authentication failed")
    
    logger.info(f"✅ 客户端认证成功: device_id={device_id}, client_id={client_id}")
    
    # 3. 升级为 WebSocket
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # 4. 处理 WebSocket 消息
    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                # 处理文本消息
                pass
            elif msg.type == aiohttp.WSMsgType.BINARY:
                # 处理二进制消息
                pass
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f'WebSocket 错误: {ws.exception()}')
    finally:
        logger.info(f"客户端断开连接: {device_id}")
    
    return ws

# 创建应用
app = web.Application()
app.router.add_get('/xiaozhi/v1/', websocket_handler)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8765)
```

### 步骤 3: 测试认证

#### 测试 1: Python 客户端（Header 方式）

```python
import asyncio
import websockets

async def test_python_client():
    uri = "ws://localhost:8765/xiaozhi/v1/"
    headers = {
        "Authorization": "Bearer your-real-token-here",
        "Device-Id": "test-device-123",
        "Client-Id": "test-client-456"
    }
    
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        print("✅ Python 客户端连接成功")
        await websocket.send('{"type": "hello"}')
        response = await websocket.recv()
        print(f"收到响应: {response}")

asyncio.run(test_python_client())
```

#### 测试 2: Web 浏览器（URL 参数方式）

在浏览器控制台运行：

```javascript
const ws = new WebSocket('ws://localhost:8765/xiaozhi/v1/?token=your-real-token-here&device_id=test-device-123&client_id=test-client-456');

ws.onopen = () => {
    console.log('✅ Web 客户端连接成功');
    ws.send(JSON.stringify({ type: 'hello' }));
};

ws.onmessage = (event) => {
    console.log('收到响应:', event.data);
};

ws.onerror = (error) => {
    console.error('❌ 连接错误:', error);
};

ws.onclose = (event) => {
    console.log('连接关闭:', event.code, event.reason);
};
```

### 步骤 4: 更新 OTA 服务器

确保 OTA 服务器返回有效的 token：

检查 `src/core/ota.py` 第 214 行：

```python
# 修改前
token_value = websocket_info.get("token", "test-token") or "test-token"

# 修改后
token_value = websocket_info.get("token")
if not token_value or token_value == "test-token":
    self.logger.error("⚠️ OTA 响应中没有有效的 token!")
    self.logger.error("设备可能未正确激活，或后台服务器 token 生成失败")
    # 根据实际情况决定是否抛出异常
    # raise ValueError("无效的 WebSocket token")
```

## 调试技巧

### 1. 启用详细日志

在 WebSocket 服务器启动时：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 打印请求信息

```python
async def websocket_handler(websocket, path):
    logger.info(f"收到 WebSocket 连接请求:")
    logger.info(f"  Path: {path}")
    logger.info(f"  Headers: {dict(websocket.request_headers)}")
    # ... 继续处理
```

### 3. 检查 token 来源

```python
token, device_id, client_id = extract_token_from_request(path, headers)

if token:
    if '?' in path:
        logger.info("Token 来源: URL 参数（Web 客户端）")
    else:
        logger.info("Token 来源: Authorization Header（Python 客户端）")
```

## 安全建议

1. **使用 HTTPS/WSS**: 在生产环境必须使用加密连接
2. **Token 过期**: 实现 token 过期机制
3. **限流**: 防止暴力破解
4. **日志脱敏**: 不要在日志中完整记录 token

## 常见问题

### Q1: 浏览器显示 "连接被拒绝"

**检查项：**
- 后台服务器是否正在运行
- 端口是否正确
- 防火墙是否允许连接

### Q2: 连接后立即断开（1005/1008）

**可能原因：**
- Token 验证失败
- 查看服务器日志确认原因

### Q3: 仍然显示 "test-token"

**解决方法：**
1. 检查 OTA 服务器是否正确返回 token
2. 查看浏览器控制台的 OTA 响应
3. 确认设备已正确激活

## 总结

通过这个方案，你的后台服务器可以同时支持：
- ✅ Python 桌面客户端（Header 认证）
- ✅ Web 浏览器客户端（URL 参数认证）
- ✅ 移动端 WebView（URL 参数认证）
- ✅ 其他任何支持 WebSocket 的客户端

**下一步：** 找到你的 WebSocket 服务器代码，按照上述示例修改即可！
