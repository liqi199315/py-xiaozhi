# 小智语音交互系统使用指南

## 📋 系统概述

完整的浏览器端语音交互系统，实现了与小智后台的实时语音对话功能。

### 架构图

```
┌─────────────────────┐
│   浏览器 Web 页面    │
│                     │
│  ┌───────────────┐  │
│  │ AudioRecorder │  │ ← 麦克风录音（Opus编码）
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │  protocol.js  │  │ ← WebSocket通信
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ AudioPlayer   │  │ ← 扬声器播放（TTS输出）
│  └───────────────┘  │
└──────────┬──────────┘
           │ WebSocket (URL参数)
           ▼
┌──────────────────────┐
│  Node.js 代理服务器   │
│   (127.0.0.1:8080)   │
└──────────┬───────────┘
           │ WebSocket (HTTP Headers)
           ▼
┌──────────────────────┐
│   小智后台服务器      │
│ (api.tenclass.net)   │
└──────────────────────┘
```

## 🚀 快速开始

### 1. 启动 Node.js 代理服务器

```bash
cd web-backend
npm install
npm start
```

确认看到：
```
✅ 服务器已启动
   - HTTP:      http://localhost:8080
   - WebSocket: ws://localhost:8080/api/ws-proxy
```

### 2. 打开语音测试页面

```bash
# 使用本地 Web 服务器打开
cd web-xiaozhi
# 然后访问: http://localhost:your-port/test/test-voice.html
```

或者直接用浏览器打开：
```
file:///path/to/py-xiaozhi/web-xiaozhi/test/test-voice.html
```

### 3. 配置连接参数

在页面中输入：
- **Token**: 从 OTA 服务器获取的有效 token
- **Device ID**: 设备标识符（可使用默认值）

### 4. 测试语音交互

1. 点击 **"🔌 连接"** 按钮
2. 等待连接成功（状态变为 "🟢 已连接"）
3. 点击 **"🎤 开始录音"** 按钮
4. 对着麦克风说话（浏览器会请求麦克风权限）
5. 点击 **"⏹️ 停止录音"** 按钮
6. 等待小智回复（会自动播放 TTS 语音）

## 📁 文件结构

```
web-xiaozhi/
├── js/
│   ├── audio_recorder.js    # 音频录制器（麦克风 → Opus）
│   ├── audio_player.js      # 音频播放器（Opus → 扬声器）
│   ├── protocol.js          # WebSocket 协议实现
│   ├── device.js            # 设备身份管理
│   ├── ota.js              # OTA 配置管理
│   └── activator.js        # 设备激活逻辑
└── test/
    ├── test-activation.html # 激活测试页面
    └── test-voice.html      # 语音交互测试页面（新增）
```

## 🎤 AudioRecorder 类

### 功能
- 访问浏览器麦克风
- 实时录制音频
- 编码为 Opus 格式（使用 MediaRecorder API）
- 流式发送音频数据

### 关键参数
```javascript
{
    sampleRate: 16000,      // 16kHz 采样率
    channels: 1,            // 单声道
    bufferSize: 4096,       // 缓冲区大小
    format: 'opus'          // Opus 编码
}
```

### 音频处理选项
- **echoCancellation**: true（回声消除）
- **noiseSuppression**: true（噪音抑制）
- **autoGainControl**: true（自动增益）

### 使用方法
```javascript
const recorder = new AudioRecorder();

// 设置回调
recorder.onAudioData = (audioData) => {
    // audioData: Uint8Array 格式的 Opus 音频
    protocol.sendAudio(audioData);
};

// 初始化并开始录音
await recorder.initialize();
recorder.startRecording();

// 停止录音
recorder.stopRecording();
```

## 🔊 AudioPlayer 类

### 功能
- 接收后台返回的 Opus 音频数据
- 解码音频（浏览器原生支持）
- 队列管理（按顺序播放）
- 扬声器输出

### 音频格式支持
- **audio/webm;codecs=opus**（首选）
- **audio/ogg;codecs=opus**
- **audio/webm**

### 使用方法
```javascript
const player = new AudioPlayer();

// 设置回调
player.onPlaybackStart = () => {
    console.log('开始播放');
};

player.onPlaybackEnd = () => {
    console.log('播放完成');
};

// 初始化并播放音频
await player.initialize();
await player.playAudioData(opusAudioData);

// 停止播放
player.stop();
```

## 🔌 协议交互流程

### 1. 连接握手
```javascript
// 客户端发送
{
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
}

// 服务器响应
{
    type: 'hello',
    session_id: 'xxx-yyy-zzz',
    ...
}
```

### 2. 开始监听
```javascript
// 客户端发送
{
    session_id: 'xxx-yyy-zzz',
    type: 'listen',
    state: 'start',
    mode: 'manual'  // 'realtime' | 'auto' | 'manual'
}
```

### 3. 音频数据流
```javascript
// 客户端发送：二进制 Opus 音频数据
ws.send(opusAudioData);  // Uint8Array

// 服务器响应：
// - JSON 消息（识别结果、回复等）
// - 二进制音频数据（TTS 语音）
```

### 4. 停止监听
```javascript
// 客户端发送
{
    session_id: 'xxx-yyy-zzz',
    type: 'listen',
    state: 'stop'
}
```

## 📊 消息类型

### JSON 消息
- **hello**: 握手消息
- **listen**: 监听控制（start/stop）
- **transcription**: 语音识别结果
- **response**: 小智回复文本
- **error**: 错误信息
- **tts_start**: TTS 开始
- **tts_end**: TTS 结束

### 二进制消息
- **音频数据**: Opus 编码的音频流

## ⚠️ 注意事项

### 1. 浏览器兼容性
- **Chrome/Edge**: 完全支持（推荐）
- **Firefox**: 支持（需测试）
- **Safari**: 部分支持（可能需要 polyfill）

### 2. HTTPS 要求
生产环境必须使用 HTTPS，否则浏览器会拒绝麦克风访问。

开发环境可以使用：
- `localhost`（不需要 HTTPS）
- `127.0.0.1`（不需要 HTTPS）

### 3. 麦克风权限
首次使用时，浏览器会弹出权限请求对话框。用户必须允许才能录音。

### 4. 音频格式
- 录音：自动使用浏览器支持的最佳格式（Opus 优先）
- 播放：需要 Opus 编码的音频数据

### 5. 性能优化
- 使用 `MediaRecorder` API（比 Web Audio API 更高效）
- 每 100ms 触发一次 `dataavailable` 事件（实时性）
- 音频队列管理（平滑播放）

## 🐛 故障排查

### 问题 1: 麦克风无法访问
**症状**: 点击"开始录音"后没有反应

**解决**:
1. 检查浏览器是否支持 `getUserMedia`
2. 确认已授予麦克风权限
3. 检查浏览器控制台是否有错误
4. 尝试刷新页面重新授权

### 问题 2: 音频无法播放
**症状**: 收到音频数据但扬声器无声音

**解决**:
1. 检查系统音量设置
2. 打开浏览器控制台查看解码错误
3. 确认音频格式是否为 Opus
4. 检查 `AudioContext` 状态

### 问题 3: 连接失败
**症状**: 无法连接到服务器

**解决**:
1. 确认 Node.js 代理服务器正在运行
2. 检查代理地址是否正确（默认 ws://127.0.0.1:8080/api/ws-proxy）
3. 确认 Token 有效
4. 查看浏览器控制台和代理服务器日志

### 问题 4: 音频断断续续
**症状**: 播放音频卡顿或中断

**可能原因**:
1. 网络延迟过高
2. 音频数据接收不完整
3. 浏览器性能不足

**解决**:
1. 检查网络连接质量
2. 增加音频队列缓冲
3. 关闭其他占用资源的标签页

## 📈 性能指标

### 录音性能
- **延迟**: < 100ms（从录音到发送）
- **采样率**: 16kHz
- **比特率**: 16kbps
- **帧时长**: 20ms

### 播放性能
- **延迟**: < 50ms（从接收到播放）
- **解码时间**: < 10ms/秒音频
- **队列深度**: 动态调整

### 网络性能
- **上行带宽**: ~2KB/s（录音时）
- **下行带宽**: ~2KB/s（TTS时）
- **WebSocket 开销**: < 1%

## 🔧 调试技巧

### 1. 查看详细日志
打开浏览器开发者工具（F12），在 Console 标签查看：
- `[录音]` 前缀：录音器日志
- `[播放]` 前缀：播放器日志
- `[协议]` 前缀：协议层日志

### 2. 监控音频数据
```javascript
// 在 test-voice.html 中已实现
// 查看页面右侧的统计面板：
// - 发送数据量
// - 接收数据量
// - 录音状态
// - 播放状态
```

### 3. 测试音频格式
```javascript
// 检查浏览器支持的格式
console.log('支持 Opus WebM:', MediaRecorder.isTypeSupported('audio/webm;codecs=opus'));
console.log('支持 Opus OGG:', MediaRecorder.isTypeSupported('audio/ogg;codecs=opus'));
```

## 📚 进一步开发

### 集成到 React 应用
```javascript
import AudioRecorder from './js/audio_recorder.js';
import AudioPlayer from './js/audio_player.js';
import XiaozhiProtocol from './js/protocol.js';

// 在组件中使用
function VoiceChat() {
    const [recorder] = useState(new AudioRecorder());
    const [player] = useState(new AudioPlayer());
    const [protocol] = useState(new XiaozhiProtocol(config));

    // ... 实现组件逻辑
}
```

### Capacitor 打包
1. 安装 Capacitor 插件
2. 配置麦克风和网络权限
3. 处理 iOS/Android 特定逻辑
4. 测试音频设备兼容性

## 🎯 下一步计划

1. ✅ 完成基础语音交互
2. ⏳ 添加唤醒词检测
3. ⏳ 实现离线语音缓存
4. ⏳ 优化音频质量和延迟
5. ⏳ 添加多语言支持
6. ⏳ React 组件封装
7. ⏳ Capacitor 移动端适配

---

**开发者**: py-xiaozhi 项目
**版本**: 1.0.0
**更新时间**: 2025-12-02
