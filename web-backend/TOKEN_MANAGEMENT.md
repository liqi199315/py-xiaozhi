# 🔑 Token 管理指南

## ✅ 当前状态

恭喜！你已经成功连接到小智后台了！🎉

当前使用的配置：
- **Token**: `622121be-663d-44d7-b65a-8763f4502e2c`
- **Device ID**: `58:11:22:b7:26:42`  
- **Client ID**: `975b0760-e76d-4571-be81-362c7cd35fde`

---

## 🕐 Token 会失效吗？

**是的**，Token 可能会失效，原因包括：

1. **时间过期** - Token 有有效期（通常几天到几周）
2. **设备重新激活** - 重新激活设备会生成新 token
3. **后台更新** - 后台服务器配置变更

**症状**：
- WebSocket 连接返回 1005 错误
- 日志显示 "后台连接被拒绝"

---

## 🔄 Token 更新方法

### 方法 1: 从日志文件获取（推荐）

当 py-xiaozhi 运行时，token 会被记录到日志中。

#### 步骤：

```bash
# 1. 运行 py-xiaozhi
cd c:\Users\Administrator\Desktop\project-active\py-xiaozhi
python main_web.py

# 2. 查看日志文件，搜索 token
type logs\app.log | findstr "token"

# 3. 复制新的 token 值
# 示例输出：
#   "token": "新的-token-值-在这里"

# 4. 更新测试页面
# 打开 http://localhost:8080/test.html
# 粘贴新 token 到输入框

# 5. 或者更新配置文件
python update_token.py  # 使用之前创建的脚本
```

### 方法 2: 从配置文件读取

```bash
# 查看当前 token
type config\config.json | findstr WEBSOCKET_ACCESS_TOKEN

# 复制 token 值到测试页面
```

### 方法 3: 自动同步（最方便）

创建一个自动同步脚本：

**`sync-token.bat`**:
```batch
@echo off
echo 🔄 同步 Token...

REM 从 config.json 提取 token
python -c "import json; data=json.load(open('config/config.json')); print(data['SYSTEM_OPTIONS']['NETWORK']['WEBSOCKET_ACCESS_TOKEN'])" > temp_token.txt

set /p NEW_TOKEN=<temp_token.txt
del temp_token.txt

echo.
echo 当前 Token: %NEW_TOKEN%
echo.
echo ✅ Token 已读取
echo.
echo 💡 提示：
echo 1. 在测试页面使用此 token
echo 2. 或者重新访问 http://localhost:8080/test.html
echo.

pause
```

---

## 🛠️ 永久配置方法

如果不想每次都手动更新，可以：

### 方案 A: 修改测试页面从配置读取

创建一个 API 端点读取配置：

**修改 `server.js`** 添加：

```javascript
// 读取 token 的 API
app.get('/api/config', (req, res) => {
    try {
        const config = require('../config/config.json');
        res.json({
            token: config.SYSTEM_OPTIONS.NETWORK.WEBSOCKET_ACCESS_TOKEN,
            device_id: config.SYSTEM_OPTIONS.DEVICE_ID,
            client_id: config.SYSTEM_OPTIONS.CLIENT_ID
        });
    } catch (error) {
        res.status(500).json({ error: 'Failed to read config' });
    }
});
```

然后测试页面可以自动获取：

```javascript
// 在测试页面加载时
async function loadConfig() {
    const res = await fetch('/api/config');
    const config = await res.json();
    document.getElementById('token').value = config.token;
    document.getElementById('deviceId').value = config.device_id;
    document.getElementById('clientId').value = config.client_id;
}
window.onload = loadConfig;
```

### 方案 B: 使用定时任务自动更新

创建一个监控脚本，当检测到配置文件变化时自动重启服务器（需要 nodemon）。

---

## 📝 快速更新步骤

**当 token 失效时**：

1. **获取新 token**:
   ```bash
   # 运行 Python 版本
   python main_web.py
   
   # 或者查看日志
   type logs\app.log | findstr "token" | findstr "622"
   ```

2. **更新方式**（选一种）:
   
   **A. 更新测试页面**（临时）:
   - 访问 http://localhost:8080/test.html
   - 粘贴新 token
   - 点击连接

   **B. 更新配置文件**（永久）:
   ```bash
   # 运行更新脚本
   python update_token.py
   
   # 然后刷新测试页面
   ```

   **C. 更新测试页面默认值**（推荐）:
   ```bash
   # 编辑 test.html，修改这一行：
   <input type="text" id="token" value="新的token">
   
   # 不需要重启服务器，刷新页面即可
   ```

---

## 💡 最佳实践

1. **记录 token 来源**
   - 如果 token 来自 OTA 服务器，记录获取时间
   - 如果来自配置文件，定期检查

2. **监控连接状态**
   - 如果出现 1005 错误，说明 token 可能失效
   - 及时更新

3. **保持 py-xiaozhi 运行**
   - py-xiaozhi 会自动维护 token
   - 定期运行可以获取最新 token

4. **备份配置**
   - 定期备份 `config/config.json`
   - 包含 token 和其他重要配置

---

## 🎯 推荐方案

**对于开发测试**：
- 使用测试页面手动输入 token（最灵活）

**对于长期使用**：
- 添加 `/api/config` 端点自动读取配置（最方便）
- 或者使用环境变量管理（最专业）

---

## ❓ 常见问题

### Q1: Token 多久会失效？

通常几天到几周，具体取决于后台配置。如果每天都运行 py-xiaozhi，token 会自动刷新。

### Q2: 失效了怎么知道？

连接时会看到 1005 错误，日志显示"后台连接被拒绝"。

### Q3: 可以一直用同一个 token 吗？

不建议。最好定期从 py-xiaozhi 获取最新 token，确保连接稳定。

---

**现在你已经成功连接了！** 🎊

如果将来 token 失效，按照上面的方法更新即可。

需要我帮你实现自动读取配置的功能吗？
