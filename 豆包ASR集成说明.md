# 豆包语音识别集成说明

## 📋 已完成的修改

### 1. 后端修改

#### ✅ 已创建: `src/audio_processing/doubao_asr.py`
- 封装了完整的豆包 ASR 协议
- 支持流式音频识别
- 包含二进制打包、GZIP压缩等功能

#### ✅ 已修改: `src/plugins/web_server.py`
- 添加了新的 WebSocket 端点: `/api/doubao-asr`
- 处理浏览器发来的音频流
- 调用豆包 API 识别后将文本发送给 AI

#### ✅ 已创建: `web/doubao-asr.js`
- 独立的前端 JavaScript 模块
- 封装录音和 WebSocket 通信逻辑

---

## 🔧 前端集成步骤

### 方法 1: 修改 index2.html (推荐)

在 `index2.html` 中进行以下修改:

#### 1. 在 `<head>` 部分添加新脚本 (第615行左右，在 Live2D 脚本之后):

```html
<!-- 豆包语音识别模块 -->
<script src="./doubao-asr.js"></script>
```

#### 2. 在 JavaScript 部分初始化豆包 ASR (第840行左右，loadConfig 函数之后):

```javascript
// 豆包 ASR 实例
let doubaoASR = null;
let useDoubao = true;  // 设为 true 使用豆包，false 使用浏览器原生

const initDoubaoASR = () => {
    if (doubaoASR) return;
    
    doubaoASR = new DoubaoASR(serverBase);
    
    // 设置回调
    doubaoASR.onPartialResult = (text) => {
        showMessage(`识别中: ${text}`);
    };
    
    doubaoASR.onFinalResult = (text) => {
        showMessage(`USER: ${text}`);
        // 文本已在后端发送给 AI，这里无需再发送
    };
    
    doubaoASR.onError = (error) => {
        showMessage(`ASR错误: ${error}`);
    };
};
```

#### 3. 修改语音按钮的 handleStartSpeaking 函数 (约第1329行):

在函数开头添加豆包分支:

```javascript
const handleStartSpeaking = async (e) => {
    if (e.cancelable) e.preventDefault();
    
    // 【新增】豆包 ASR 分支
    if (useDoubao) {
        isPressing = true;
        ui.btnSpeak.classList.add('active');
        
        initDoubaoASR();
        await unlockAudioContext();
        await connectWs();
        sendHelloIfNeeded();
        
        updateStatus(true, 'listening');
        const started = await doubaoASR.start();
        if (!started) {
            ui.btnSpeak.classList.remove('active');
            isPressing = false;
        }
        return;
    }
    
    // 原有的浏览器语音识别代码...
```

#### 4. 修改 handleStopSpeaking 函数 (约第1382行):

在函数开头添加:

```javascript
const handleStopSpeaking = (e) => {
    if (e && e.cancelable) e.preventDefault();
    
    // 【新增】豆包 ASR 分支
    if (useDoubao && doubaoASR) {
        isPressing = false;
        ui.btnSpeak.classList.remove('active');
        doubaoASR.stop();
        updateStatus(true, 'idle');
        return;
    }
    
    // 原有代码...
```

---

### 方法 2: 创建新文件 index3.html

如果不想修改 index2.html，可以：

```bash
# 复制文件
copy web\index2.html web\index3.html
```

然后在 index3.html 中按照上述方法 1 进行修改。

---

## 🔑 配置豆包凭证

### 方式 1: 环境变量 (推荐用于生产)

```bash
# Windows
set DOUBAO_APP_KEY=2785683478
set DOUBAO_ACCESS_KEY=OHl7yBW1VI5M9f4oI26RDU-3xPtkAGZp

# Linux/Mac
export DOUBAO_APP_KEY=2785683478
export DOUBAO_ACCESS_KEY=OHl7yBW1VI5M9f4oI26RDU-3xPtkAGZp
```

### 方式 2: 修改代码 (已硬编码，可直接使用)

在 `src/plugins/web_server.py` 第 473 行已经硬编码了你的凭证:

```python
app_key = os.getenv("DOUBAO_APP_KEY", "2785683478")
access_key = os.getenv("DOUBAO_ACCESS_KEY", "OHl7yBW1VI5M9f4oI26RDU-3xPtkAGZp")
```

---

## 🚀 启动测试

1. 启动 Python 后端:
```bash
python main_web.py --skip-activation
```

2. 打开浏览器访问:
```
http://127.0.0.1:8080/index2.html
```

3. 按住"HOLD TO SPEAK"按钮说话

4. 查看控制台日志，应该会看到:
```
[豆包ASR] 正在连接: ws://127.0.0.1:8080/api/doubao-asr
[豆包ASR] WebSocket 已连接
[豆包ASR] 服务已准备好
[豆包ASR] 开始录音
[豆包ASR] 发送音频块: XXX 字节
[豆包ASR] 识别结果: 你好
[豆包ASR] 最终文本: 你好世界
```

---

## 🎯 主要改动总结

### 后端改动:
1. ✅ 创建 `src/audio_processing/doubao_asr.py` - 豆包协议处理
2. ✅ 修改 `src/plugins/web_server.py` - 添加 `/api/doubao-asr` 端点
3. ✅ 硬编码了你的豆包凭证（可通过环境变量覆盖）

### 前端改动:
1. ✅ 创建 `web/doubao-asr.js` - 独立JS模块
2. ⏳ 需要修改 `index2.html` - 集成豆包模块（见上述步骤）

### 数据流:
```
前端录音 (MediaRecorder)
    ↓
WebSocket: /api/doubao-asr
    ↓
Python后端 (web_server.py)
    ↓
豆包ASR服务 (wss://openspeech.bytedance.com)
    ↓
识别结果返回
    ↓
发送给AI系统 (protocol.send_wake_word_detected)
```

---

## ❓ 使用说明

### 切换识别方式

在 JavaScript 代码中设置:
```javascript
let useDoubao = true;   // 使用豆包识别
let useDoubao = false;  // 使用浏览器原生识别
```

### 支持的平台

- ✅ 所有支持 MediaRecorder 的浏览器
- ✅ 安卓平板/手机
- ✅ iOS (Safari 14.5+)
- ✅ Windows/Mac 桌面浏览器

---

## 🐛 调试

### 后端日志
```bash
tail -f logs/xiaozhi.log
# 查找 [豆包ASR] 标签
```

### 前端控制台
按 F12 打开开发者工具，查看 Console 标签页，筛选 "[豆包ASR]"

---

## 📝 注意事项

1. **音频格式**: 豆包要求 16kHz, 16bit, 单声道 PCM
   - 前端使用 MediaRecorder 录制 WebM/Opus
   - 后端接收后需要转换格式（待实现）

2. **网络延迟**: WebSocket 通信会有延迟，建议在局域网测试

3. **并发限制**: 豆包 API 有并发限制，注意不要同时开启多个录音

4. **安全性**: 凭证已硬编码，生产环境建议使用环境变量

---

如有问题，请查看日志文件或控制台输出。
