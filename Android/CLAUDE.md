# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Android 原生应用,用于 EShowcaseAI 语音交互系统。应用完成了从设备激活到 WebSocket 实时语音交互的完整链路,支持 Opus 音频编解码和 Live2D 虚拟形象渲染。

**包名变更**: 项目正在从 `com.xiaozhi.app` 迁移到 `com.eshowcaseai.app`。

## 常用开发命令

### 构建和运行
```bash
# 使用 Android Studio 打开项目
# File > Open > 选择 Android 目录

# 命令行构建 (在项目根目录)
./gradlew build

# 构建 Debug APK
./gradlew assembleDebug

# 构建 Release APK
./gradlew assembleRelease

# 安装到设备
./gradlew installDebug

# 运行测试
./gradlew test

# 运行 Android 测试
./gradlew connectedAndroidTest

# 清理构建
./gradlew clean
```

### Lint 和代码检查
```bash
# 运行 Lint 检查
./gradlew lint

# Kotlin 代码格式检查 (如果配置)
./gradlew ktlintCheck

# 查看依赖
./gradlew app:dependencies
```

## 核心架构

### 分层架构
```
app/
├── core/                     # 核心业务逻辑层
│   ├── config/              # 配置管理 (AppConfig)
│   ├── identity/            # 设备身份管理 (DeviceIdentity)
│   ├── ota/                 # OTA 配置获取 (OtaClient)
│   ├── activation/          # 设备激活流程 (Activator)
│   ├── ws/                  # WebSocket 连接 (EShowcaseAIWebSocket)
│   ├── audio/               # 音频管线 (AudioPipeline, AudioConfig)
│   └── live2d/              # Live2D 渲染 (Live2DView, LipSyncController)
├── ui/                      # UI 层
│   ├── HomeFragment         # 主页面
│   ├── ConversationFragment # 对话页面
│   ├── ActivationFragment   # 激活页面
│   └── widget/              # 自定义控件
├── viewmodel/               # ViewModel 层
│   └── BootstrapViewModel   # 核心业务协调器
└── MainActivity             # 主 Activity
```

### 启动流程 (Bootstrap Flow)

```
1. DeviceIdentity.getOrCreate()
   └─> 生成或读取设备身份: serial_number, hmac_key, device_id, client_id

2. OtaClient.fetchConfig()
   └─> POST https://api.tenclass.net/EShowcaseAI/ota/
       ├─> 返回 activation (需要激活)
       └─> 返回 websocket.url + websocket.token

3. Activator.activate() [如果需要激活]
   └─> 计算 HMAC-SHA256(challenge, hmac_key)
       └─> 轮询 POST /activate (最多 60 次,每次间隔 5 秒)
           ├─> 200 OK → 激活成功
           ├─> 202 Accepted → 继续轮询
           └─> 其他 → 重试

4. EShowcaseAIWebSocket.connect()
   └─> WebSocket 连接 + Bearer Token 认证
       └─> 发送 Hello 消息
           └─> 接收 session_id
               └─> 启动心跳 (每 25 秒)

5. 语音交互
   ├─> AudioPipeline.startCapture() → 录音 + Opus 编码 → WS 发送
   └─> WS 接收 Opus 数据 → AudioPipeline.play() → 解码播放
```

### 关键组件说明

**BootstrapViewModel**:
- 应用的核心协调器,管理整个初始化和交互生命周期
- 协调 OTA、激活、WebSocket 连接和音频管线
- 处理 WebSocket 消息路由和状态管理
- 实现自动重连机制

**AudioPipeline**:
- 封装音频采集、编码、解码、播放的完整管线
- 使用 MediaCodec 进行 Opus 编解码 (48kHz)
- 实现数字增益控制 (4倍放大) 和音频缓冲区管理
- 支持播放状态监听和超时检测

**DeviceIdentity**:
- 负责设备唯一标识的生成和持久化
- 使用 SharedPreferences 存储
- 提供 HMAC-SHA256 密钥管理

**WebSocket 协议**:
- 握手: `{"type":"hello","version":1,...}`
- 开始监听: `{"type":"listen","state":"start","session_id":"..."}`
- 文本检测: `{"type":"listen","state":"detect","text":"...","session_id":"..."}`
- 停止监听: `{"type":"listen","state":"stop","session_id":"..."}`
- 心跳: `{"type":"status","state":"idle","session_id":"..."}`
- 音频: 二进制 Opus 帧

## 关键配置 (AppConfig.kt)

```kotlin
OTA_BASE_URL = "https://api.tenclass.net/EShowcaseAI/ota/"
DEFAULT_WS_URL = "wss://api.tenclass.net/EShowcaseAI/v1/"
APP_VERSION = "2.0.3"
APP_NAME = "eshowcaseai"
ACTIVATION_VERSION = "v2"
```

## 依赖管理

### 核心依赖
- **OkHttp 4.12.0**: HTTP/WebSocket 客户端
- **Kotlinx Coroutines 1.8.1**: 异步编程
- **Kotlinx Serialization JSON 1.6.3**: JSON 序列化
- **Live2D Cubism Core**: 虚拟形象渲染 (libs/Live2DCubismCore.aar)
- **AndroidX**: 核心库、AppCompat、Material Design、Fragment、Lifecycle

### 最低要求
- minSdk: 24 (Android 7.0)
- targetSdk: 34 (Android 14)
- compileSdk: 34
- Kotlin: 1.9.24
- JVM Target: 17

## 开发注意事项

### 权限要求
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.INTERNET" />
```
录音权限在运行时动态申请 (MainActivity)。

### 音频配置限制
- 采样率: 16000 Hz
- 声道: 单声道 (Mono)
- 帧时长: 20ms
- 编码: Opus (需要 Android 10+ 或设备支持)
- 播放采样率: 48000 Hz (Opus 标准)

### WebSocket 重连策略
- 连接失败或异常关闭: 3 秒后自动重连
- 正常关闭 (code 1000): 不重连
- Session 失效: 触发完整 bootstrap 流程

### 激活流程注意
- 验证码显示在 UI 上,用户需手动输入到后台系统
- 激活过程最多轮询 60 次 (5 分钟)
- 激活成功后需要重新获取 OTA 配置获取最新 token

### 调试日志
- 所有组件使用统一的日志标签: `EShowcaseAI`
- WebSocket 消息完整记录在 logcat 和 UI 日志叠加层
- 音频包发送每 100 帧打印一次统计

## 已知问题

1. **包名迁移中**: 从 `com.xiaozhi.app` 到 `com.eshowcaseai.app`,可能存在历史遗留引用
2. **Opus 编解码兼容性**: Android 10 以下设备可能不支持硬件 Opus 编解码
3. **音频增益**: 当前硬编码 4 倍增益,可能需要根据设备调整
4. **Live2D 集成**: 当前 Live2DView 和 LipSyncController 实现待完善

## 测试建议

### 单元测试
- DeviceIdentity 的身份生成和持久化逻辑
- OtaClient 的请求构造和响应解析
- Activator 的 HMAC-SHA256 计算

### 集成测试
- OTA → 激活 → WebSocket 完整流程
- WebSocket 重连机制
- 音频编解码管线

### 手动测试检查项
- [ ] 首次启动生成设备身份
- [ ] 激活码正确显示
- [ ] 激活成功后自动连接
- [ ] 语音录音和播放正常
- [ ] 断网重连功能
- [ ] Session 失效后重新初始化
- [ ] 录音权限被拒绝的情况

## 相关资源

- API 端点: `https://api.tenclass.net/EShowcaseAI/`
- 协议版本: v2 (Activation), v1 (WebSocket)
- 音频格式: Opus 16kHz Mono 20ms frames
