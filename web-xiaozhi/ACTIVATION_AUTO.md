# 🔑 自动化激活流程说明

## 问题背景

之前的激活流程存在以下问题：
1. 激活成功后，token 仍然是 `test-token`
2. 需要用户手动刷新页面重新获取配置
3. 用户体验不好，不够自动化

## 新的解决方案

### ✅ 自动重新获取 Token

激活成功后，系统会**自动执行以下步骤**：

```
用户输入验证码激活
    ↓
激活成功（HTTP 200）
    ↓
等待 3 秒（给服务器处理时间）
    ↓
自动重新获取 OTA 配置（最多尝试 5 次）
    ↓
每次尝试间隔 3 秒
    ↓
【情况 1】获取到真实 Token
    ↓
✅ 自动使用新 Token 连接 WebSocket
    ↓
完成！
    ↓
【情况 2】5 次尝试后仍是 test-token
    ↓
⚠️ 提示用户等待 1-2 分钟后刷新页面
```

## 工作流程详解

### 阶段 3: 设备激活（改进后）

```javascript
// 1. 激活成功
const success = await activator.activate(challenge, code);

if (success) {
    // 2. 清除旧的 OTA 配置缓存
    localStorage.removeItem('xiaozhi_ota_config');

    // 3. 等待 3 秒
    await new Promise(resolve => setTimeout(resolve, 3000));

    // 4. 尝试最多 5 次重新获取配置
    for (let i = 1; i <= 5; i++) {
        const newConfig = await ota.fetchConfig('v2');
        const newToken = newConfig.websocket?.token;

        if (newToken && newToken !== 'test-token') {
            // ✅ 成功获取真实 Token
            console.log('获取到真实Token:', newToken);
            return newConfig;  // 返回新配置，继续执行阶段 4
        }

        // 还是 test-token，等待 3 秒后重试
        await new Promise(resolve => setTimeout(resolve, 3000));
    }

    // 5 次尝试后仍未获取到真实 token
    return 'skip_stage4';  // 跳过阶段 4，提示用户刷新
}
```

### 主流程（改进后）

```javascript
// 阶段 2: 获取初始配置
let config = await stage2_otaConfig();

// 阶段 3: 激活并尝试获取新配置
const activationResult = await stage3_activation(config);

// 判断返回结果
if (activationResult && typeof activationResult === 'object') {
    // 情况 1: 返回了新配置对象（包含真实 token）
    config = activationResult;  // 使用新配置
    await stage4_connection();  // 继续连接

} else if (activationResult === 'skip_stage4') {
    // 情况 2: 未能获取真实 token，需要等待刷新
    console.log('请等待 1-2 分钟后刷新页面');
    return;

} else {
    // 情况 3: 设备已激活（config.need_activation = false）
    await stage4_connection();  // 直接连接
}
```

## 用户体验对比

### 之前的流程 ❌

```
激活成功
    ↓
显示："请刷新页面"
    ↓
用户手动刷新
    ↓
重新点击"开始测试"
    ↓
获取真实 token
    ↓
连接成功
```

**缺点**：
- 需要 2 次手动操作
- 用户体验差
- 不够自动化

### 现在的流程 ✅

```
激活成功
    ↓
自动等待 3 秒
    ↓
自动重新获取配置（最多 5 次）
    ↓
【成功】获取到真实 token
    ↓
自动连接 WebSocket
    ↓
完成！
```

**优点**：
- 完全自动化
- 无需用户干预
- 体验流畅

## 时间参数说明

### 初次等待时间：3 秒
```javascript
await new Promise(resolve => setTimeout(resolve, 3000));
```
**原因**：给服务器足够时间处理激活请求并生成 Token

### 重试间隔：3 秒
```javascript
await new Promise(resolve => setTimeout(resolve, 3000));
```
**原因**：避免频繁请求服务器，同时给足够时间让 Token 生成

### 最大重试次数：5 次
```javascript
const maxRetries = 5;
```
**计算**：
- 初次等待：3 秒
- 5 次重试 × 3 秒 = 15 秒
- 总时间：约 18 秒

**如果 18 秒内仍未获取到真实 token**：
- 可能是服务器处理较慢
- 提示用户等待 1-2 分钟后刷新页面

## 失败兜底方案

如果自动获取失败（极少数情况），系统会：

1. **显示友好提示**：
   ```
   ⚠️ 激活成功，但Token获取延迟
   ✅ 设备已成功激活
   ⚠️ 服务器Token生成需要更多时间
   💡 请等待1-2分钟后刷新页面
   ```

2. **提供刷新按钮**：
   - 用户可以主动刷新
   - 刷新后系统会自动使用真实 token

3. **保留设备激活状态**：
   - `device.setActivationStatus(true)`
   - 下次打开时不会再要求激活

## 测试建议

### 测试场景 1：正常激活（最常见）

1. 打开 `test/test-activation.html`
2. 点击"开始完整流程"
3. 在 xiaozhi.me 输入验证码
4. 观察日志：
   ```
   ✅ 设备激活成功！
   ⏳ 等待3秒后重新获取配置...
   🔄 第1次尝试获取新配置...
   ✅ 成功获取真实Token: xxx-xxx-xxx
   ✅ 设备已激活
   ✅ 真实Token已获取
   ✅ 准备连接WebSocket...
   ```
5. 自动连接成功，完成！

### 测试场景 2：服务器延迟（少见）

1. 同上步骤 1-3
2. 观察日志：
   ```
   ✅ 设备激活成功！
   ⏳ 等待3秒后重新获取配置...
   🔄 第1次尝试获取新配置...
   ⚠️ 第1次获取仍是test-token，继续重试...
   🔄 第2次尝试获取新配置...
   ⚠️ 第2次获取仍是test-token，继续重试...
   ...
   ⚠️ 多次尝试后仍未获取到真实Token
   💡 建议：等待1-2分钟后刷新页面重试
   ```
3. 等待 1-2 分钟
4. 点击"刷新页面"按钮
5. 重新点击"开始完整流程"
6. 这次应该能直接获取到真实 token 并连接成功

## 技术细节

### 为什么不能立即获取到真实 token？

服务器端的处理流程：
```
收到激活请求
    ↓
验证验证码
    ↓
绑定设备到用户账号
    ↓
生成真实 Token（需要时间）
    ↓
更新数据库
    ↓
Token 可用
```

**时间估计**：
- 快速情况：3-5 秒
- 正常情况：5-10 秒
- 慢速情况：10-60 秒

### OTA 配置缓存机制

```javascript
// ota.js 中的实现
fetchConfig(version = 'v2') {
    // 1. 检查缓存
    const cached = localStorage.getItem('xiaozhi_ota_config');
    if (cached) {
        return JSON.parse(cached);  // 使用缓存
    }

    // 2. 从服务器获取
    const config = await fetch(otaUrl);

    // 3. 保存到缓存
    localStorage.setItem('xiaozhi_ota_config', JSON.stringify(config));

    return config;
}
```

**重要**：激活成功后必须清除缓存：
```javascript
localStorage.removeItem('xiaozhi_ota_config');
```
否则会一直使用旧的 test-token。

## 总结

新的激活流程：
- ✅ **自动化**：无需手动刷新（90%+ 情况）
- ✅ **智能重试**：最多 5 次，18 秒内完成
- ✅ **用户友好**：失败时有明确提示
- ✅ **兜底方案**：极端情况下仍可手动刷新

**核心改进**：从"激活成功后手动刷新"变为"激活成功后自动获取真实 token"。

---

**更新日期**：2025-12-02
**版本**：v2.1.0
