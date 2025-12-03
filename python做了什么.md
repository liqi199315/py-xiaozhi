• src/core/ota.py + src/core/system_initializer.py: 启动时先向 OTA 接口 https://api.tenclass.net/xiaozhi/ota/ 上报设备指纹（MAC/机器码、版本等），拿回 WebSocket/MQTT 地址和 token；如返回 activation 数据则认为服务器侧未激活。
• src/utils/device_activator.py: 针对 v2 激活，调用 OTA_VERSION_URL/activate（默认 https://api.tenclass.net/xiaozhi/ota/activate），用本机 HMAC 对 challenge 签名并附带验证码；成功后把“已激活”写入本地。
• src/protocols/websocket_protocol.py：用 OTA 写入的 WEBSOCKET_URL 和 WEBSOCKET_ACCESS_TOKEN 建立到小智后台的 WebSocket，Authorization 走 Bearer {token}，同时带 Device-Id/Client-Id 头。握手发送 hello（音频参数：opus/16kHz/1ch/20-60ms 帧），随后：
  ◦ 文本 JSON：listen/start/stop、wake_word、iot 等指令；处理后台 tts start/stop 来驱动状态。
  ◦ 二进制：后台返回的 TTS 音频流（Opus）；本地录音/播放插件负责编码解码。
  ◦ 断线重连/心跳监测等。
• src/plugins/web_server.py：在本地起 aiohttp 服务（默认 127.0.0.1:8080），提供 REST 控制（开始/停止监听、文本输入、abort 等）+ SSE 状态推送，并实现 /api/ws-proxy：把浏览器的 WS（URL 参数传 token/device/client）转发成带自定义 Header 的 WS 到小智后台，双向转发文本与音频。
• web-xiaozhi/js/protocol.js 等前端脚本：浏览器端通过 ws://<host>:8080/api/ws-proxy?token=... 连接代理，发送 hello、listen/start/stop，并用 MediaRecorder 采集 Opus 音频流式发送；audio_player.js 负责播放后台返回的 Opus。
Web 前端做流式语音、后台上服务器的可行性

• 已有 Python 端 WebSocket 代理和前端实现，天然支持“浏览器录音→WS 代理→小智后台”以及“TTS 流→浏览器播放”的全链路，逻辑完整可用。
• 部署要点：在服务器上跑 python main_web.py --web-host 0.0.0.0 --web-port <端口>（或等价脚本），先通过 CLI 激活拿到有效 token/设备 ID；用静态站点或 python -m http.server 发布 web-xiaozhi 前端，并把前端里的代理地址指向服务器（需 HTTPS 才能取麦克风，建议在前面挂 Nginx/证书，把 WS 升级为 WSS）。
• 注意：浏览器不能自定义 Header，所以必须走 /api/ws-proxy；保证服务器能直连官方 WSS（或你的自建后端），并开放代理端口给前端访问。
如果需要，我可以整理一份最小部署清单（配置文件需要改哪些字段、前端需要改的代理 URL、Nginx 示例）。