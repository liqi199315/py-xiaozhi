# xiaozhi-android 脚手架

这个目录是为“小智”原生 Android 客户端准备的 Kotlin 脚手架。目标：在不依赖 Python 代理的情况下，直接完成 OTA 配置获取 → 设备激活 → WebSocket 语音交互的全链路。

## 架构概览（按功能层）
- **core/config**：统一常量与环境配置（OTA / WS 基地址、应用版本、默认超时等）。
- **core/identity**：设备身份生成与持久化（serial_number、hmac_key、device_id、client_id、激活状态）。
- **core/ota**：向 OTA 服务器拉取配置，判断是否需要激活，并解析 websocket.url 与 websocket.token。
- **core/activation**：基于 OTA 返回的 challenge 与验证码，计算 HMAC-SHA256，轮询 `.../activate` 完成绑定。
- **core/ws**：WebSocket 会话（握手 hello、listen start/stop、JSON 收发、二进制 Opus 收发、断线重连策略）。
- **core/audio**：音频采集/播放与 Opus 编解码（占位，后续接入 Concentus 或 NDK Opus）。
- **ui**：最小的 `MainActivity`，后续扩展为连接、激活、语音控制的界面。

## 代码骨架与文件
- `app/build.gradle.kts`：应用模块配置，依赖 OkHttp、Coroutines、Serialization。
- `core/config/AppConfig.kt`：基础常量，集中管理。
- `core/identity/DeviceIdentity.kt`：生成/读取设备身份，K/V 存储。
- `core/ota/OtaClient.kt`：拉取 OTA 配置，解析需要激活的场景。
- `core/activation/Activator.kt`：激活流程骨架（计算 HMAC，轮询 activate 接口）。
- `core/ws/XiaozhiWebSocket.kt`：WebSocket 连接与握手的最小实现（待接入音频）。
- `core/audio/AudioConfig.kt`、`AudioPipeline.kt`：音频参数与后续管线占位。
- `MainActivity.kt`：简单 UI 骨架，后续接入激活与连接按钮。

## 开发顺序建议（对新手友好）
1) **跑通工程**：用 Android Studio 打开 `Android` 目录，Sync Gradle，确认编译通过（当前 UI 极简）。
2) **设备身份**：完善 `DeviceIdentity`，确保持久化、重置能力。
3) **OTA 获取**：实现 `OtaClient.fetchConfig`，打印返回的 websocket/activation 信息。
4) **激活流程**：在 `Activator` 补充 HMAC-SHA256、轮询逻辑；UI 上显示验证码与状态。
5) **WebSocket 握手**：用 OTA 拿到的真实 token 与 url，完成 hello → listen start/stop。
6) **音频管线**：接入录音/播放与 Opus 编解码（推荐 Concentus 纯 Java 版，先做本地回环测试）。
7) **体验优化**：断线重连、日志、错误提示、权限处理（录音、网络）。

## 运行提示
- 直接用 Android Studio 打开 `Android` 目录即可；顶层 Gradle 已配置插件仓库与依赖源。
- 真实联调需要可用的 `device_id/client_id/serial/hmac_key` 和有效账号。可参考 `config/efuse.json` 的形态将身份初始化到设备侧。
- 后续接入音频与激活时，务必在 UI 上展示验证码与状态，避免“无提示卡死”。

## 下一步
- 补全 `OtaClient` HTTP 请求与 JSON 解析。
- 补全 `Activator` 的 HMAC 与轮询。
- 为 `XiaozhiWebSocket` 增加监听控制（listen start/stop）与二进制音频收发。
- 接入音频管线与 Opus。
