# Web 小智激活和连接问题排查指南

## 问题症状
- 无法激活设备
- Token 显示为 "test-token"
- WebSocket 连接失败，错误代码 1005

## 问题原因

### 1. WebSocket 1005 错误
错误代码 1005 通常表示：
- 服务器拒绝连接
- 认证失败（Token 无效）
- 设备未正确激活

### 2. Token 问题
如果看到 `"test-token"`，说明：
- 设备可能未被服务器正确激活
- OTA 服务器返回的 token 为空或无效
- 系统使用了默认的测试 token

## 排查步骤

### 步骤 1: 检查浏览器控制台
1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 查看以下关键信息：
   - `[OTA] 服务器返回:` - 查看 OTA 响应
   - `[激活]` 相关的日志
   - `[协议] 使用Token:` - 确认正在使用的 token

### 步骤 2: 检查 OTA 响应
查看控制台中的 OTA 响应，特别注意：

```javascript
[OTA] 服务器返回: {
  "websocket": {
    "url": "wss://api.tenclass.net/xiaozhi/v1/",
    "token": "xxx"  // ← 这里应该是真实的 token，不应该是 "test-token"
  },
  "activation": {  // ← 如果有这个字段，说明需要激活
    "code": "123456",
    "challenge": "xxx"
  }
}
```

### 步骤 3: 激活流程检查

#### 如果看到 `activation` 字段：
1. 复制显示的验证码（如 123456）
2. 访问 https://xiaozhi.me/
3. 在网站上输入验证码
4. 等待激活成功

#### 如果没有 `activation` 字段但 token 是 "test-token"：
这说明服务器认为设备已激活，但返回的 token 无效。可能的原因：
1. **后台服务器配置问题**：检查后台服务器是否正确运行
2. **设备未在系统中注册**：需要在后台系统中注册设备
3. **Token 生成失败**：后台服务器 token 生成逻辑有问题

### 步骤 4: 重置设备身份
如果上述步骤都无法解决，尝试重置设备身份：

1. 在浏览器控制台运行：
```javascript
localStorage.removeItem('xiaozhi_device_identity');
localStorage.removeItem('xiaozhi_ota_config');
location.reload();
```

2. 刷新页面后重新激活

## 后台服务器检查

### 检查项 1: OTA 服务器是否正常运行
```bash
curl -X POST http://127.0.0.1:8002/xiaozhi/ota/ \
  -H "Content-Type: application/json" \
  -H "Device-Id: test-device" \
  -H "Client-Id: test-client" \
  -d '{
    "application": {"version": "2.0.3"},
    "board": {"type": "Desktop", "name": "xiaozhi"}
  }'
```

期望返回包含 `websocket` 和可能的 `activation` 字段。

### 检查项 2: WebSocket 服务器是否正常运行
确认 WebSocket 服务器在正确的地址和端口上运行。

### 检查项 3: 检查后台日志
查看后台服务器日志，看是否有：
- 设备激活请求
- Token 生成记录
- WebSocket 连接拒绝的原因

## 配置文件检查

### test/index.html (line 70-71)
确认 token 值：
```html
<input type="text" id="token" value="your-token1" placeholder="token" disabled>
```

这个值只是**测试页面显示用**，实际使用的 token 来自 OTA 响应。

### web-xiaozhi/js/config.js
确认配置：
```javascript
const CONFIG = {
    WEBSOCKET_URL: 'wss://api.tenclass.net/xiaozhi/v1/',
    ACCESS_TOKEN: 'test-token',  // ← 这是默认值
    DEVICE_ID: '58:11:22:b7:26:42',
    CLIENT_ID: '975b0760-e76d-4571-be81-362c7cd35fde',
    ACTIVATION_VERSION: "v2",
    // ...
};
```

**注意**：`config.js` 中的 `ACCESS_TOKEN` 只是备用值，实际应该从 OTA 服务器动态获取。

## 常见解决方案

### 方案 1: 确保使用本地 OTA 服务器
如果你在测试本地后台，需要修改 OTA URL：

在 `web-xiaozhi/js/ota.js` 或相应配置中：
```javascript
this.OTA_URL = 'http://127.0.0.1:8002/xiaozhi/ota/';  // 本地服务器
```

在 `test/index.html` 中：
```html
<input type="text" id="otaUrl" value="http://127.0.0.1:8002/xiaozhi/ota/" />
```

### 方案 2: 检查后台 Token 配置
在后台 Python 代码中，确保正确生成和返回 token：

```python
# src/core/ota.py 第 214 行
# 问题代码：
token_value = websocket_info.get("token", "test-token") or "test-token"

# 如果 token 为空，应该记录日志：
if not websocket_info.get("token"):
    self.logger.warning("⚠️ OTA 响应中没有 token，使用默认值")
    self.logger.warning("这可能表示设备未正确激活或后台配置错误")
```

### 方案 3: 检查 WebSocket 认证方式
浏览器 WebSocket 不支持自定义 Header，所以：

**Python 客户端** (`websocket_protocol.py` line 52-57):
```python
self.HEADERS = {
    "Authorization": f"Bearer {access_token}",  # ← 使用 Header
    "Protocol-Version": "1",
    "Device-Id": device_id,
    "Client-Id": client_id,
}
```

**Web 客户端** (`protocol.js` line 29-42):
```javascript
// 浏览器不支持自定义 Header，使用 URL 参数
url.searchParams.set('token', this.config.ACCESS_TOKEN);
url.searchParams.set('access_token', this.config.ACCESS_TOKEN);
url.searchParams.set('device_id', this.config.DEVICE_ID);
url.searchParams.set('client_id', this.config.CLIENT_ID);
```

**确保后台服务器支持两种认证方式**：
1. 从 `Authorization` Header 读取 token
2. 从 URL 参数 `?token=xxx` 或 `?access_token=xxx` 读取 token

## 调试技巧

### 1. 启用详细日志
在浏览器控制台运行：
```javascript
localStorage.setItem('debug', 'true');
```

### 2. 手动测试 WebSocket 连接
```javascript
// 使用真实的 token 测试
const ws = new WebSocket('wss://api.tenclass.net/xiaozhi/v1/?token=YOUR_REAL_TOKEN&device_id=YOUR_DEVICE_ID&client_id=YOUR_CLIENT_ID');

ws.onopen = () => console.log('✅ 连接成功');
ws.onerror = (e) => console.error('❌ 连接错误:', e);
ws.onclose = (e) => console.log('连接关闭:', e.code, e.reason);
ws.onmessage = (e) => console.log('收到消息:', e.data);

// 发送 hello
ws.send(JSON.stringify({
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
}));
```

### 3. 检查网络请求
在开发者工具的 Network 标签中：
1. 查看 OTA 请求的响应
2. 查看 WebSocket 连接的握手过程
3. 检查是否有 CORS 错误

## 总结

最可能的原因是：
1. **设备未正确激活** - 需要在 https://xiaozhi.me/ 输入验证码
2. **后台服务器未正确配置** - 检查后台 token 生成逻辑
3. **认证方式不匹配** - 确保后台支持 URL 参数认证

按照以上步骤逐一排查，应该能够解决问题。
