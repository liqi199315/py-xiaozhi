# 测试 Token 的步骤

## 🧪 测试你的 Token

我创建了一个测试脚本来直接连接小智后台，验证 token 是否有效。

### 运行测试

```bash
cd web-backend

# 替换 YOUR_TOKEN 为你的真实 token
node test-direct-connection.js YOUR_TOKEN
```

### 期望结果

#### ✅ 如果 Token 有效

你会看到：
```
🧪 测试直接连接小智后台

Token: xxxxxxxxxx...
Device ID: test-device
Client ID: test-client

连接: wss://api.tenclass.net/xiaozhi/v1/

✅ WebSocket 连接成功！

📤 发送 hello 消息...
Hello 消息已发送

📥 收到消息:
{
  "type": "hello",
  "session_id": "xxx-xxx-xxx",
  ...
}

🎉 认证成功！Session ID: xxx-xxx-xxx

🔌 连接已关闭
Code: 1000
Reason: 
```

#### ❌ 如果 Token 无效

你会看到：
```
🧪 测试直接连接小智后台
...
✅ WebSocket 连接成功！
📤 发送 hello 消息...

🔌 连接已关闭
Code: 1005
Reason: 

⚠️  错误 1005 通常表示:
1. Token 无效或过期
2. Token 格式不正确
3. 设备未激活

💡 建议: 检查你的 token 是否正确
```

---

## 🔍 可能的问题

### 问题 1: ws 库的 headers 支持

Node.js 的 `ws` 库在某些情况下可能不正确发送自定义 headers。

让我检查一下我们使用的方式是否正确...

**Python 使用**:
```python
self.websocket = await websockets.connect(
    uri=self.WEBSOCKET_URL,
    additional_headers=self.HEADERS,  # ← headers 传递方式
    ...
)
```

**Node.js 使用**:
```javascript
const backendWs = new WebSocket(backendUrl, {
    headers: {  // ← 这个方式在某些版本可能不工作
        'Authorization': `Bearer ${token}`,
        ...
    }
});
```

### 问题 2: ws 库版本

检查你的 ws 库版本：
```bash
cd web-backend
npm list ws
```

如果版本 < 8.0.0，可能需要升级：
```bash
npm install ws@latest
```

### 问题 3: 协议版本

检查 Python 代码中的头部：
```python
self.HEADERS = {
    "Authorization": f"Bearer {access_token}",
    "Protocol-Version": "1",
    "Device-Id": device_id,
    "Client-Id": client_id,
}
```

我们的 Node.js 代码也是一样的，所以应该没问题。

---

## 📝 下一步

请执行以下操作：

### 1. 获取你的真实 token

```bash
# 查看配置文件
cd ..
cat config/config.json | grep WEBSOCKET_ACCESS_TOKEN

# 或者在 Windows
type config\config.json | findstr WEBSOCKET_ACCESS_TOKEN
```

### 2. 运行测试脚本

```bash
cd web-backend

# 使用你的真实 token
node test-direct-connection.js "你的token在这里"
```

### 3. 告诉我结果

告诉我：
- ✅ 测试成功（看到 session_id）
- ❌ 测试失败（看到 1005 错误）

---

## 💡 如果测试脚本也是 1005

这说明问题不在代理，而是：

1. **Token 本身无效**
   - 需要重新激活设备
   - 或者从正确运行的 py-xiaozhi 获取

2. **后台服务器配置变更**
   - 可能需要额外的认证参数
   - 联系后台管理员确认

3. **网络问题**
   - 防火墙阻止
   - 代理设置

---

请先运行测试脚本，告诉我结果！🔬
