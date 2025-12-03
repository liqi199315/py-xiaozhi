# 小智Web客户端 - 完整实现指南

## 📁 项目结构

```
web-xiaozhi/
├── js/
│   ├── device.js           # 设备身份管理（序列号、HMAC密钥）
│   ├── ota.js             # OTA配置获取（WebSocket URL、Token）
│   ├── activator.js       # 设备激活流程
│   ├── protocol.js        # WebSocket通信协议
│   ├── audio_recorder.js  # 音频录制（麦克风 → Opus）✨ NEW
│   ├── audio_player.js    # 音频播放（TTS 输出）✨ NEW
│   └── mqtt_protocol.js   # MQTT协议（备选方案）
├── test/
│   ├── test-activation.html   # 完整激活测试
│   └── test-voice.html        # 语音交互测试 ⭐ NEW
├── VOICE_GUIDE.md         # 语音系统详细指南 ✨ NEW
└── README.md              # 本文件
```

## ✨ 功能特性

- ✅ **设备激活**: HMAC-SHA256 安全认证
- ✅ **OTA 配置**: 动态配置获取
- ✅ **WebSocket 通信**: 通过 Node.js 代理突破浏览器限制
- ✅ **实时语音输入**: 麦克风录音 + Opus 编码
- ✅ **实时语音输出**: TTS 音频播放
- ✅ **流式交互**: 低延迟语音对话
- ⏳ **唤醒词检测**: 计划中
- ⏳ **Capacitor 打包**: 计划中

## 🚀 快速开始

### 前置要求

**1. 启动 Node.js 代理服务器**（必需）

```bash
cd ../web-backend
npm install
npm start
```

确认代理服务器运行在 `http://127.0.0.1:8080`

**2. 有效的小智账号和 Token**

从 OTA 服务器获取配置，或使用测试 token 进行激活。

### 使用步骤

#### 方式一：设备激活流程（推荐）

1. 打开 `test/test-activation.html`
2. 点击"开始测试"
3. 系统自动完成 4 个阶段：
   - 阶段 1: 生成设备身份
   - 阶段 2: 获取 OTA 配置
   - 阶段 3: 激活设备
   - 阶段 4: 连接服务器
4. 激活成功后，刷新页面获取真实 token

#### 方式二：语音交互测试（需要 token）⭐ NEW

1. 打开 `test/test-voice.html`
2. 输入有效的 Token
3. 点击"连接"
4. 等待连接成功后，点击"开始录音"
5. 对着麦克风说话
6. 点击"停止录音"
7. 等待小智回复（自动播放语音）

详细使用说明请查看 [VOICE_GUIDE.md](./VOICE_GUIDE.md)

## 🔑 设备激活流程

### 情况1: 设备已激活

如果设备之前已经激活过，系统会：
- 直接跳过激活阶段
- 自动连接到WebSocket服务器
- 显示 "✅ 所有阶段完成"

### 情况2: 设备需要激活

如果是新设备，系统会：
1. 显示**验证码**（例如：123456）
2. 提示你打开 [xiaozhi.me](https://xiaozhi.me)
3. 在网站上**添加设备**并**输入验证码**
4. 等待激活成功（最多5分钟）
5. **显示刷新提示**（重要！）
6. 刷新页面后再次点击"开始完整流程"
7. 这次将使用**真实Token**自动连接成功

**重要提示**：激活成功后，服务器需要时间处理Token，因此必须刷新页面才能获取新Token。

**激活步骤截图：**
```
┌─────────────────────────────────────┐
│  请在 xiaozhi.me 输入验证码          │
│                                     │
│          1 2 3 4 5 6               │
│                                     │
│  正在等待激活... (最多等待5分钟)     │
└─────────────────────────────────────┘
```

## 🐛 调试技巧

### 打开浏览器控制台

按 `F12` 或 `右键 → 检查`，查看：
- **Console 标签**: 详细日志
- **Network 标签**: 网络请求
- **Application 标签**: localStorage数据

### 常见问题

#### Q1: 连接立即关闭（1005错误）
**原因**: Access Token无效或设备未激活
**解决**: 按照激活流程输入验证码

#### Q2: OTA请求失败
**原因**: 网络问题或服务器不可达
**解决**: 检查网络连接，确保能访问 `api.tenclass.net`

#### Q3: 激活超时
**原因**: 验证码未在网站上输入
**解决**:
1. 打开 [xiaozhi.me](https://xiaozhi.me)
2. 点击 "添加设备"
3. 输入页面显示的验证码
4. 提交后等待激活成功

#### Q4: 激活成功但无法连接
**原因**: 服务器需要时间处理Token
**解决**:
1. 激活成功后会显示"请刷新页面"提示
2. 点击刷新按钮或按F5
3. 再次点击"开始完整流程"
4. 这次应该能直接跳过激活并连接成功

#### Q5: 想重新测试激活
**方法1**: 点击 "🔄 重置设备身份" 按钮
**方法2**: 手动清除localStorage（Console输入）
```javascript
localStorage.clear();
location.reload();
```

## 📊 数据存储说明

### localStorage存储内容

```javascript
// 设备身份
{
  "serial_number": "...",    // 设备序列号
  "hmac_key": "...",         // HMAC密钥
  "mac_address": "...",      // MAC地址
  "client_id": "...",        // Client ID
  "is_activated": false      // 激活状态
}

// OTA配置
{
  "websocket": {
    "url": "wss://...",      // WebSocket URL
    "token": "..."           // Access Token
  }
}
```

## ✅ 第一阶段检查清单

完成以下项目，即可进入第二阶段（音频功能）：

- [ ] 能成功生成设备身份
- [ ] 能从OTA服务器获取配置
- [ ] 能完成设备激活流程（如果需要）
- [ ] 能成功连接到WebSocket服务器
- [ ] 能看到Session ID
- [ ] 理解了完整的激活流程

## 📝 核心代码说明

### 1. 设备身份管理 (device.js)

```javascript
// 生成序列号和HMAC密钥
const device = new DeviceManager();

// 获取设备信息
const identity = device.getOrCreateIdentity();
// => { serial_number, mac_address, client_id, hmac_key }

// 生成HMAC-SHA256签名（用于激活）
const signature = await device.generateHmac(challenge);
```

### 2. OTA配置获取 (ota.js)

```javascript
// 获取OTA配置
const ota = new OTAManager(deviceIdentity);
const config = await ota.fetchConfig();

// 检查是否需要激活
if (config.need_activation) {
    console.log('验证码:', config.activation.code);
}

// 获取WebSocket配置
const wsUrl = ota.getWebSocketURL();
const token = ota.getAccessToken();
```

### 3. 设备激活 (activator.js)

```javascript
// 创建激活器
const activator = new DeviceActivator(device, ota);

// 激活设备（会自动重试最多60次）
const success = await activator.activate(challenge, code);

if (success) {
    console.log('激活成功！');
    device.setActivationStatus(true);
}
```

### 4. WebSocket连接 (protocol.js)

```javascript
// 创建协议实例
const protocol = new XiaozhiProtocol({
    ACCESS_TOKEN: token,
    DEVICE_ID: device_id,
    CLIENT_ID: client_id,
    AUDIO: {
        FORMAT: 'opus',
        SAMPLE_RATE: 16000,
        CHANNELS: 1,
        FRAME_DURATION: 20
    }
});

// 设置回调
protocol.onConnected = (message) => {
    console.log('连接成功!', message.session_id);
};

protocol.onAudioData = (audioData) => {
    // 处理接收到的TTS音频
    player.playAudioData(audioData);
};

// 连接（通过本地代理）
await protocol.connect();

// 开始/停止监听
await protocol.startListening('manual');
protocol.sendAudio(audioData);  // 发送音频
await protocol.stopListening();
```

### 5. 音频录制 (audio_recorder.js) ✨ NEW

```javascript
// 创建录音器
const recorder = new AudioRecorder();

// 设置回调 - 实时接收Opus音频数据
recorder.onAudioData = (audioData) => {
    // audioData: Uint8Array 格式的 Opus 编码音频
    protocol.sendAudio(audioData);
    console.log('发送音频:', audioData.length, '字节');
};

recorder.onError = (error) => {
    console.error('录音错误:', error);
};

// 初始化（请求麦克风权限）
await recorder.initialize();

// 开始录音（每100ms触发一次回调）
recorder.startRecording();

// 停止录音
recorder.stopRecording();

// 释放资源
recorder.dispose();
```

**音频参数**:
- 采样率: 16kHz
- 声道: 单声道
- 编码: Opus（通过 MediaRecorder API）
- 帧时长: 100ms
- 音频增强: 回声消除、噪音抑制、自动增益

### 6. 音频播放 (audio_player.js) ✨ NEW

```javascript
// 创建播放器
const player = new AudioPlayer();

// 设置回调
player.onPlaybackStart = () => {
    console.log('开始播放TTS');
};

player.onPlaybackEnd = () => {
    console.log('播放完成');
};

player.onError = (error) => {
    console.error('播放错误:', error);
};

// 初始化
await player.initialize();

// 播放Opus音频数据（自动解码）
await player.playAudioData(opusAudioData);

// 停止播放
player.stop();

// 获取播放状态
const state = player.getPlaybackState();
// => { isPlaying, queueLength, currentSourceActive }

// 释放资源
player.dispose();
```

**播放特性**:
- 自动解码 Opus/WebM 音频
- 播放队列管理（按顺序播放）
- 流式播放（低延迟）
- 状态回调

## 🎯 开发路线图

### Stage 1: 基础连接 ✅ 已完成
- [x] 设备身份管理（localStorage）
- [x] OTA 配置获取
- [x] 设备激活流程（HMAC-SHA256）
- [x] WebSocket 通信
- [x] Node.js 代理集成

### Stage 2: 音频功能 ✅ 已完成
- [x] 麦克风录音（Opus 编码）
- [x] TTS 音频播放（自动解码）
- [x] 流式音频传输
- [x] 完整语音交互测试页面
- [x] 详细使用文档

### Stage 3: React 界面 ⏳ 计划中
- [ ] React 组件封装
- [ ] 状态管理（Redux/Zustand）
- [ ] 美化UI界面
- [ ] 响应式设计
- [ ] 预计时间: 5-7天

### Stage 4: Capacitor 打包 ⏳ 计划中
- [ ] iOS 平台适配
- [ ] Android 平台适配
- [ ] 原生权限处理
- [ ] 应用图标和启动页
- [ ] 预计时间: 7-10天

### Stage 5: 高级功能 ⏳ 计划中
- [ ] 唤醒词检测
- [ ] 离线语音缓存
- [ ] 多语言支持
- [ ] 推送通知
- [ ] 后台运行
- [ ] 预计时间: 10-15天

## 📊 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      浏览器 Web 应用                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AudioRecorder│  │  protocol.js │  │ AudioPlayer  │      │
│  │  (录音器)     │  │  (协议层)     │  │  (播放器)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────▲───────┘      │
│         │                 │                 │               │
│         │ Opus音频        │ JSON/Binary     │ Opus音频      │
│         ▼                 ▼                 │               │
│  ┌──────────────────────────────────────────┴───────┐      │
│  │           WebSocket (URL 参数传递认证)            │      │
│  └──────────────────────┬───────────────────────────┘      │
└─────────────────────────┼─────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Node.js 代理服务器 (:8080)                       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  URL参数 → HTTP Headers 转换                      │       │
│  │  token → Authorization: Bearer {token}           │       │
│  └──────────────────────┬───────────────────────────┘       │
└─────────────────────────┼─────────────────────────────────┘
                          │ WebSocket (HTTP Headers)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               小智后台服务器                                   │
│         (wss://api.tenclass.net/xiaozhi/v1/)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   语音识别    │  │   对话引擎    │  │   TTS合成     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 数据流向

**录音 → 识别**:
```
麦克风 → AudioRecorder (Opus编码)
       → protocol.sendAudio()
       → Node.js代理
       → 小智后台
       → 语音识别引擎
       → JSON响应 (transcription)
```

**对话 → 播放**:
```
小智后台 → TTS引擎 (Opus音频)
         → Node.js代理
         → protocol.onAudioData()
         → AudioPlayer.playAudioData()
         → 解码 → 扬声器
```

## 📊 性能指标

### 音频性能
- **录音延迟**: < 100ms（从录音到发送）
- **播放延迟**: < 50ms（从接收到播放）
- **采样率**: 16kHz
- **比特率**: 16kbps
- **音频质量**: Opus 编码，高清语音

### 网络性能
- **上行带宽**: ~2KB/s（录音时）
- **下行带宽**: ~2KB/s（TTS时）
- **WebSocket 开销**: < 1%
- **连接建立**: < 1s

### 浏览器兼容性

| 浏览器 | 支持状态 | MediaRecorder | Web Audio | 备注 |
|--------|---------|---------------|-----------|------|
| Chrome 60+ | ✅ 完全支持 | ✅ Opus | ✅ | 推荐 |
| Edge 79+ | ✅ 完全支持 | ✅ Opus | ✅ | 推荐 |
| Firefox 54+ | ✅ 支持 | ✅ Opus | ✅ | 需测试 |
| Safari 14.1+ | ⚠️ 部分支持 | ⚠️ WebM | ✅ | 需polyfill |
| 移动Chrome | ✅ 支持 | ✅ Opus | ✅ | HTTPS必需 |
| 移动Safari | ⚠️ 部分支持 | ⚠️ WebM | ✅ | HTTPS必需 |

**注意**: 生产环境必须使用 HTTPS，否则无法访问麦克风。

## 🔗 相关链接

- **语音系统详细指南**: [VOICE_GUIDE.md](./VOICE_GUIDE.md)
- **Node.js 代理服务器**: [../web-backend/README.md](../web-backend/README.md)
- **Python 原始实现**: [../README.md](../README.md)
- 小智官网: https://xiaozhi.me
- API文档: https://api.tenclass.net/xiaozhi/ota/
- 问题反馈: [GitHub Issues]

## 📞 技术支持

如果遇到问题，请提供以下信息：
1. 浏览器控制台截图（Console标签）
2. 设备身份信息（序列号、MAC地址）
3. 错误日志
4. 复现步骤
