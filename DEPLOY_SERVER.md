# 服务器部署指南

本文档介绍如何在Ubuntu服务器（无GUI环境）中部署py-xiaozhi项目。

## 📋 前提条件

- Ubuntu 18.04+ / Debian 10+ 或其他Linux发行版
- Python 3.9 - 3.12
- 音频设备（或虚拟音频设备）
- 稳定的网络连接

## 🚀 快速部署

### 1. 上传项目到服务器

```bash
# 使用git克隆
git clone https://github.com/huangjunsen0406/py-xiaozhi.git
cd py-xiaozhi

# 或通过scp上传已有项目
# scp -r /path/to/py-xiaozhi user@server:/path/to/destination
```

### 2. 安装依赖

```bash
# 更新系统包
sudo apt update

# 安装系统依赖
sudo apt install -y python3 python3-pip portaudio19-dev

# 安装Python依赖
pip3 install -r requirements.txt
```

### 3. 使用部署脚本启动

```bash
# 添加执行权限
chmod +x deploy_server.sh

# 首次启动（需要激活）- Web默认开放外部访问
./deploy_server.sh

# 如果已激活，可跳过激活流程
./deploy_server.sh --skip-activation

# 使用MQTT协议
./deploy_server.sh --mqtt

# 自定义Web端口
./deploy_server.sh --web-port 9090

# 仅允许本地访问Web
./deploy_server.sh --local-only

# 组合参数
./deploy_server.sh --skip-activation --web-port 9090
```

## 🌐 Web控制台配置

### Web控制台功能

Web控制台会**自动启动**，提供以下功能：

- 📊 **实时状态监控**：查看设备状态、对话流程
- 💬 **文本交互**：直接发送文本消息与AI对话
- 🎤 **语音控制**：触发"按住说话"、"自动对话"、"中断"等操作
- 📝 **日志查看**：实时查看STT/TTS/LLM消息流

### 默认配置

- **监听地址**：`0.0.0.0`（允许外部访问）
- **监听端口**：`8080`
- **访问示例**：`http://服务器IP:8080`

### 配置选项

#### 方法1：使用部署脚本参数

```bash
# 更改端口
./deploy_server.sh --web-port 9090

# 仅限本地访问
./deploy_server.sh --local-only

# 自定义监听地址
./deploy_server.sh --web-host 192.168.1.100 --web-port 9090
```

#### 方法2：使用环境变量

```bash
# 设置监听地址和端口
export XIAOZHI_WEB_HOST=0.0.0.0
export XIAOZHI_WEB_PORT=8080

# 启动程序
python3 main.py --mode cli
```

#### 方法3：在systemd服务中配置

编辑 `/etc/systemd/system/xiaozhi.service`：

```ini
[Service]
Environment="XIAOZHI_WEB_HOST=0.0.0.0"
Environment="XIAOZHI_WEB_PORT=8080"
```

### 🔒 Web安全配置

#### 防火墙配置

如果开放外部访问，需要配置防火墙：

```bash
# UFW防火墙
sudo ufw allow 8080/tcp

# iptables
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4

# firewalld
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

#### 限制访问IP

如果需要限制特定IP访问：

```bash
# UFW - 只允许特定IP访问
sudo ufw delete allow 8080/tcp
sudo ufw allow from 192.168.1.0/24 to any port 8080

# iptables - 只允许特定IP
sudo iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport 8080 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8080 -j DROP
```

#### Nginx反向代理（推荐）

使用Nginx添加HTTPS和访问控制：

```nginx
# /etc/nginx/sites-available/xiaozhi
server {
    listen 80;
    server_name xiaozhi.yourdomain.com;
    
    # 强制HTTPS（可选）
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name xiaozhi.yourdomain.com;
    
    # SSL配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 基础认证（可选）
    auth_basic "Xiaozhi Web Console";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    # IP白名单（可选）
    # allow 192.168.1.0/24;
    # deny all;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
}
```

启用配置：

```bash
# 创建基础认证文件（可选）
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin

# 启用站点
sudo ln -s /etc/nginx/sites-available/xiaozhi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 🎨 Web界面选项

项目提供多个Web界面：

- **`index.html`** - 默认界面（推荐）
- **`index_text.html`** - 纯文本界面（简洁）
- **`index_live2d.html`** - Live2D动画界面（实验性）

更换界面需要修改 `src/plugins/web_server.py` 中的 `_index_path`。


## 📝 激活流程

### CLI模式激活步骤

1. **启动程序**：
   ```bash
   python3 main.py --mode cli
   ```

2. **查看验证码**：
   程序会在终端显示6位验证码，例如：
   ```
   ============================================================
   设备激活信息
   ============================================================
   激活验证码: 123456
   验证码（请在网站输入）: 1 2 3 4 5 6
   ============================================================
   ```

3. **在网站完成绑定**：
   - 打开浏览器访问 https://xiaozhi.me
   - 登录您的账户
   - 选择"添加设备"
   - 输入终端显示的6位验证码
   - 确认添加

4. **等待激活完成**：
   程序会自动等待服务器确认，激活成功后会显示：
   ```
   ============================================================
   设备激活成功！
   ============================================================
   ```

## 🔧 手动启动命令

### 基础命令

```bash
# CLI模式（命令行模式）- 适合服务器
python3 main.py --mode cli

# 使用WebSocket协议（默认）
python3 main.py --mode cli --protocol websocket

# 使用MQTT协议
python3 main.py --mode cli --protocol mqtt

# 跳过激活流程（调试用）
python3 main.py --mode cli --skip-activation
```

### 环境变量配置

```bash
# 禁用系统托盘（服务器环境推荐）
export XIAOZHI_DISABLE_TRAY=1

# 禁用GUI（无头环境）
export QT_QPA_PLATFORM=offscreen

# 修改Web控制台监听地址（可选）
export XIAOZHI_WEB_HOST=0.0.0.0  # 允许外部访问
export XIAOZHI_WEB_PORT=8080
```

### 组合示例

```bash
# 完整的服务器启动命令
XIAOZHI_DISABLE_TRAY=1 \
QT_QPA_PLATFORM=offscreen \
XIAOZHI_WEB_HOST=0.0.0.0 \
python3 main.py --mode cli --protocol websocket
```

## 🌐 Web控制台访问

Web控制台会在程序启动时**自动启动**，即使在CLI模式下也可用：

### 快速访问

- **本地访问**：`http://127.0.0.1:8080`
- **远程访问**：`http://服务器IP:8080`（需要配置为外部可访问）

### 功能特性

通过Web控制台可以：
- 📊 查看实时对话流（STT/TTS/LLM）
- 📈 监控设备状态和连接状态
- 🎤 触发语音交互（按住说话/自动对话/中断）
- 💬 发送文本消息与AI对话
- 📝 查看系统日志和事件流

### 配置说明

**默认配置**（部署脚本）：
- 监听地址：`0.0.0.0`（允许外部访问）
- 端口：`8080`

**自定义配置**：
详见上方 [🌐 Web控制台配置](#-web控制台配置) 章节，包括：
- 更改端口和监听地址
- 安全配置（防火墙、IP限制）
- Nginx反向代理配置
- HTTPS配置

### 注意事项

⚠️ **音频处理**：Web控制台只负责远程交互，音频的采集与播放仍由Python客户端在服务器本机完成。

🔒 **安全提醒**：如果开放外部访问，强烈建议：
1. 使用防火墙限制访问IP
2. 配置Nginx反向代理并启用HTTPS
3. 添加HTTP基础认证

## 🔄 后台运行

### 使用screen

```bash
# 安装screen
sudo apt install screen

# 创建新会话
screen -S xiaozhi

# 在screen中启动
./deploy_server.sh

# 按 Ctrl+A 然后按 D 分离会话
# 重新连接: screen -r xiaozhi
```

### 使用systemd服务

创建服务文件 `/etc/systemd/system/xiaozhi.service`:

```ini
[Unit]
Description=Xiaozhi AI Client
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/py-xiaozhi
Environment="XIAOZHI_DISABLE_TRAY=1"
Environment="QT_QPA_PLATFORM=offscreen"
ExecStart=/usr/bin/python3 main.py --mode cli --protocol websocket
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start xiaozhi

# 设置开机自启
sudo systemctl enable xiaozhi

# 查看状态
sudo systemctl status xiaozhi

# 查看日志
sudo journalctl -u xiaozhi -f
```

## 🐛 常见问题

### 1. 无法显示验证码

**问题**：GUI模式在服务器中报错  
**解决**：必须使用 `--mode cli` 参数

### 2. 音频设备错误

**问题**：服务器没有音频设备  
**解决**：安装虚拟音频设备

```bash
# 安装虚拟音频
sudo apt install pulseaudio

# 创建虚拟音频设备
pactl load-module module-null-sink sink_name=virtual_speaker
pactl load-module module-virtual-source source_name=virtual_mic
```

### 3. 端口被占用

**问题**：8080端口已被占用  
**解决**：修改Web控制台端口

```bash
export XIAOZHI_WEB_PORT=9090
python3 main.py --mode cli
```

### 4. 权限问题

**问题**：没有权限访问音频设备  
**解决**：将用户添加到audio组

```bash
sudo usermod -a -G audio $USER
# 需要重新登录才能生效
```

## 📊 监控与日志

### 查看日志

```bash
# 日志默认位置
tail -f logs/xiaozhi_*.log

# 实时监控
watch -n 1 'ls -lht logs/ | head -10'
```

### 性能监控

```bash
# 查看进程资源使用
htop -p $(pgrep -f "python3 main.py")

# 查看网络连接
netstat -tulpn | grep python3
```

## 🔐 安全建议

1. **防火墙配置**：如果开放Web控制台，注意配置防火墙
   ```bash
   sudo ufw allow 8080/tcp
   ```

2. **使用HTTPS**：生产环境建议通过nginx反向代理并配置SSL

3. **访问控制**：限制Web控制台的访问IP范围

## 📚 参考资料

- [项目文档](https://huangjunsen0406.github.io/py-xiaozhi/)
- [视频教程](https://www.bilibili.com/video/BV1dWQhYEEmq/)
- [GitHub项目](https://github.com/huangjunsen0406/py-xiaozhi)

## 💡 提示

- CLI模式下验证码会在终端明文显示，请注意信息安全
- 建议在激活完成后重启服务，确保配置生效
- 如遇到问题，查看 `logs/` 目录下的日志文件
