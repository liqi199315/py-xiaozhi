# 快速参考卡片 - 服务器部署

## 🚀 一键启动

```bash
# 基础启动（Web外部可访问）
./deploy_server.sh

# 跳过激活
./deploy_server.sh --skip-activation

# 自定义Web端口
./deploy_server.sh --web-port 9090

# 仅本地访问
./deploy_server.sh --local-only
```

## 🌐 Web访问地址

- **默认**: http://服务器IP:8080
- **本地**: http://127.0.0.1:8080

## 📋 常用命令

### 启动选项

| 参数 | 说明 | 示例 |
|------|------|------|
| `--skip-activation` | 跳过激活流程 | `./deploy_server.sh --skip-activation` |
| `--mqtt` | 使用MQTT协议 | `./deploy_server.sh --mqtt` |
| `--web-port PORT` | 设置Web端口 | `./deploy_server.sh --web-port 9090` |
| `--web-host HOST` | 设置Web监听地址 | `./deploy_server.sh --web-host 0.0.0.0` |
| `--local-only` | Web仅本地访问 | `./deploy_server.sh --local-only` |

### 环境变量

```bash
# Web服务器配置
export XIAOZHI_WEB_HOST=0.0.0.0    # 监听地址
export XIAOZHI_WEB_PORT=8080        # 监听端口

# 其他配置
export XIAOZHI_DISABLE_TRAY=1       # 禁用系统托盘
export QT_QPA_PLATFORM=offscreen    # 无头模式
```

### 手动启动

```bash
# CLI模式
python3 main.py --mode cli

# CLI + WebSocket
python3 main.py --mode cli --protocol websocket

# CLI + MQTT
python3 main.py --mode cli --protocol mqtt

# 跳过激活
python3 main.py --mode cli --skip-activation

# 组合环境变量
XIAOZHI_WEB_HOST=0.0.0.0 \
XIAOZHI_WEB_PORT=8080 \
python3 main.py --mode cli
```

## 🔒 安全配置

### 防火墙

```bash
# UFW
sudo ufw allow 8080/tcp

# 只允许特定网段
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

### Nginx反向代理（简版）

```nginx
server {
    listen 80;
    server_name xiaozhi.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
    }
}
```

## 🔄 服务管理

### systemd服务

```bash
# 创建服务文件
sudo nano /etc/systemd/system/xiaozhi.service
```

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
Environment="XIAOZHI_WEB_HOST=0.0.0.0"
Environment="XIAOZHI_WEB_PORT=8080"
ExecStart=/usr/bin/python3 main.py --mode cli --protocol websocket
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl daemon-reload
sudo systemctl start xiaozhi
sudo systemctl enable xiaozhi

# 查看状态
sudo systemctl status xiaozhi

# 查看日志
sudo journalctl -u xiaozhi -f
```

### Screen会话

```bash
# 创建会话
screen -S xiaozhi

# 在screen中启动
./deploy_server.sh

# 分离会话: Ctrl+A, D
# 重新连接
screen -r xiaozhi

# 查看所有会话
screen -ls

# 结束会话
screen -X -S xiaozhi quit
```

## 🐛 故障排查

### 查看日志

```bash
# 应用日志
tail -f logs/xiaozhi_*.log

# systemd日志
sudo journalctl -u xiaozhi -n 100 --no-pager

# 实时日志
sudo journalctl -u xiaozhi -f
```

### 检查端口

```bash
# 查看端口监听状态
sudo netstat -tlnp | grep 8080
# 或
sudo lsof -i:8080
```

### 测试Web访问

```bash
# 本地测试
curl http://127.0.0.1:8080

# 远程测试
curl http://服务器IP:8080
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 验证码看不到 | 使用 `--mode cli` 参数 |
| Web无法访问 | 检查防火墙和监听地址 |
| 端口被占用 | 使用 `--web-port` 更改端口 |
| 音频设备错误 | 安装虚拟音频设备 |

## 📚 更多信息

- 完整文档: [DEPLOY_SERVER.md](DEPLOY_SERVER.md)
- 项目主页: https://github.com/huangjunsen0406/py-xiaozhi
- 在线文档: https://huangjunsen0406.github.io/py-xiaozhi/
