# 🐛 错误 1005: 后台认证失败

## 问题描述

你看到的错误：
```
[vmzqkb] 🔌 后台断开: 1005
```

这表示**小智后台服务器拒绝了连接**，通常是因为 **Token 认证失败**。

---

## ✅ 解决方案

### 方案 1: 获取有效的 Token（推荐）

#### 步骤 1: 检查设备是否已激活

Token 无效通常是因为设备未激活。需要先激活设备。

#### 步骤 2: 运行 py-xiaozhi 获取 Token

```bash
# 启动 py-xiaozhi（会自动激活并获取 token）
cd py-xiaozhi
python main_web.py --skip-activation
```

#### 步骤 3: 从配置文件获取 Token

激活成功后，查看配置文件：

```bash
# 打开配置文件
notepad config\config.json

# 或在 Linux/Mac
cat config/config.json
```

找到这一行：
```json
{
  "SYSTEM_OPTIONS": {
    "NETWORK": {
      "WEBSOCKET_ACCESS_TOKEN": "YOUR_REAL_TOKEN_HERE"
    }
  }
}
```

复制这个 token 值！

---

### 方案 2: 手动激活设备

如果你还没有激活设备，需要先获取激活码：

#### 步骤 1: 运行激活流程

```bash
cd py-xiaozhi
python main.py
```

或者查看 `web-xiaozhi` 的激活流程。

#### 步骤 2: 在网站输入验证码

1. 访问 https://xiaozhi.me/
2. 输入显示的验证码
3. 等待激活成功

激活成功后，配置文件会自动更新 token。

---

### 方案 3: 使用测试环境（仅开发）

如果你只是想测试代理功能，可以：

#### 修改后台 URL 为本地测试服务器

编辑 `web-backend/.env`：

```bash
# 连接到本地测试服务器（如果有）
BACKEND_WS_URL=ws://localhost:8765/xiaozhi/v1/

# 或者其他测试服务器
BACKEND_WS_URL=ws://192.168.1.100:8765/xiaozhi/v1/
```

然后重启代理服务器：
```bash
npm start
```

---

## 🔍 诊断步骤

### 检查 1: Token 是否为 "test-token"

如果你看到服务器日志：
```
[vmzqkb] ⚠️  使用测试 token，可能导致后台认证失败
```

说明你使用的是无效的测试 token，需要获取真实 token。

### 检查 2: 查看完整的服务器日志

服务器日志应该显示：
```
[xxx] 📥 新连接请求
  - Device ID: web-test-device
  - Client ID: web-test-client
[xxx] 🔌 连接后台: wss://api.tenclass.net/xiaozhi/v1/
[xxx] ✅ 已连接到后台服务器
[xxx] 🔌 后台断开: 1005
[xxx] ⚠️  后台连接被拒绝（可能是 token 认证失败）
```

最后一行确认是认证失败。

### 检查 3: 测试 Token 有效性

你可以用这个简单的 Node.js 脚本测试 token：

创建 `test-token.js`:
```javascript
const WebSocket = require('ws');

const token = 'YOUR_TOKEN_HERE'; // 替换为你的 token
const url = 'wss://api.tenclass.net/xiaozhi/v1/';

const ws = new WebSocket(url, {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Protocol-Version': '1',
        'Device-Id': 'test-device',
        'Client-Id': 'test-client'
    }
});

ws.on('open', () => {
    console.log('✅ Token 有效！连接成功！');
    ws.close();
});

ws.on('error', (err) => {
    console.error('❌ 连接失败:', err.message);
});

ws.on('close', (code, reason) => {
    if (code === 1005) {
        console.error('❌ Token 无效或认证失败');
    } else {
        console.log(`连接关闭: ${code} ${reason}`);
    }
});
```

运行测试：
```bash
cd web-backend
node test-token.js
```

---

## 📝 常见问题

### Q1: 我有 token，但还是 1005 错误

**可能原因**：
1. Token 已过期
2. Token 格式不正确（有空格或换行）
3. 后台服务器配置变更

**解决**：
1. 重新激活设备获取新 token
2. 检查 token 字符串（去掉首尾空格）
3. 联系后台管理员确认

### Q2: 设备已激活但没有 token

**解决**：
查看 `config/config.json`，如果 `WEBSOCKET_ACCESS_TOKEN` 为空或为 "test-token"，说明配置有问题。

尝试重新运行：
```bash
python main.py
```

让它重新获取配置。

### Q3: 如何知道 token 是否有效？

有效的 token 通常：
- 长度 > 20 字符
- 不是 "test-token"
- 包含随机字符和数字

无效的 token：
- 是 "test-token"
- 是 null 或空字符串
- 过短（< 10 字符）

---

## ✅ 修复步骤总结

1. **🔄 重启代理服务器**（已修复 bug）
   ```bash
   cd web-backend
   npm start
   ```

2. **🔑 获取真实 Token**
   ```bash
   # 方法 A: 从配置文件
   cat config/config.json
   
   # 方法 B: 运行 py-xiaozhi
   python main_web.py
   ```

3. **🧪 重新测试**
   - 访问 http://localhost:8080/test.html
   - 粘贴真实 token
   - 点击连接

4. **✅ 期望结果**
   ```
   ✅ 代理连接成功！
   ✅ 服务器握手成功！
   🟢 已连接
   Session ID: xxx-xxx-xxx
   ```

---

## 🆘 还是不行？

如果按照上述步骤还是失败，请提供以下信息：

1. **配置文件内容**（隐藏敏感信息）：
   ```json
   "WEBSOCKET_ACCESS_TOKEN": "xxx...xxx"  // 前后几位
   ```

2. **服务器完整日志**：
   ```
   [xxx] 📥 新连接请求
   ...
   [xxx] 🔌 后台断开: 1005
   ```

3. **你使用的 token 长度**：
   - 字符数量
   - 是否包含特殊字符

我会继续帮你调试！🚀

---

**下一步**: 重启服务器后，用真实 token 重新测试！
