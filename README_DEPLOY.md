# 服务器部署文件说明

本目录包含用于在Ubuntu/Linux服务器上部署py-xiaozhi的配置文件和脚本。

## 📁 文件列表

### 部署脚本

| 文件 | 用途 | 使用方法 |
|------|------|----------|
| `deploy_server.sh` | 一键部署脚本 | `./deploy_server.sh` |
| `install_service.sh` | systemd服务安装向导 | `sudo ./install_service.sh` |

### 配置文件

| 文件 | 用途 | 说明 |
|------|------|------|
| `xiaozhi.service` | systemd服务模板 | 可直接使用或参考 |

### 文档

| 文件 | 内容 | 适合人群 |
|------|------|----------|
| `DEPLOY_SERVER.md` | 完整部署文档 | 详细了解部署流程 |
| `SERVER_QUICKREF.md` | 快速参考卡片 | 快速查找命令 |
| `README_DEPLOY.md` | 本文件 | 了解文件结构 |

## 🚀 快速开始

### 方法1：使用部署脚本（推荐新手）

```bash
# 1. 添加执行权限
chmod +x deploy_server.sh

# 2. 启动（Web自动开放外部访问）
./deploy_server.sh

# 3. 在终端查看验证码，在网站完成绑定
# 访问Web: http://服务器IP:8080
```

### 方法2：安装systemd服务（推荐生产环境）

```bash
# 1. 添加执行权限
chmod +x install_service.sh

# 2. 运行安装向导
sudo ./install_service.sh

# 3. 按照提示配置服务
# 4. 服务将在后台运行并开机自启
```

### 方法3：手动命令

```bash
# 直接运行，Web默认本地访问
python3 main.py --mode cli

# Web开放外部访问
XIAOZHI_WEB_HOST=0.0.0.0 python3 main.py --mode cli
```

## 📋 详细说明

### deploy_server.sh - 一键部署脚本

**功能**：
- ✅ 自动配置CLI模式
- ✅ 禁用不需要的GUI组件
- ✅ 配置Web控制台外部访问
- ✅ 支持多种参数定制

**常用命令**：

```bash
# 基础启动
./deploy_server.sh

# 跳过激活
./deploy_server.sh --skip-activation

# 自定义Web端口
./deploy_server.sh --web-port 9090

# 仅本地访问Web
./deploy_server.sh --local-only

# 使用MQTT协议
./deploy_server.sh --mqtt

# 组合使用
./deploy_server.sh --skip-activation --web-port 9090
```

**参数说明**：

| 参数 | 说明 |
|------|------|
| `--skip-activation` | 跳过激活流程（已激活设备使用） |
| `--mqtt` | 使用MQTT协议（默认websocket） |
| `--web-port PORT` | 设置Web端口（默认8080） |
| `--web-host HOST` | 设置Web监听地址（默认0.0.0.0） |
| `--local-only` | Web仅限本地访问（127.0.0.1） |

### install_service.sh - systemd服务安装向导

**功能**：
- ✅ 交互式配置Web地址和端口
- ✅ 自动生成systemd服务文件
- ✅ 一键安装并启动服务
- ✅ 支持开机自启配置

**使用步骤**：

```bash
# 1. 运行安装向导（需要sudo）
sudo ./install_service.sh

# 2. 按提示输入配置:
#    - Web监听地址（默认0.0.0.0）
#    - Web端口（默认8080）
#    - 通信协议（websocket/mqtt）
#    - 是否跳过激活

# 3. 确认配置并安装

# 4. 选择是否立即启动和开机自启
```

**安装后管理**：

```bash
# 查看状态
sudo systemctl status xiaozhi

# 启动/停止/重启
sudo systemctl start xiaozhi
sudo systemctl stop xiaozhi
sudo systemctl restart xiaozhi

# 查看日志
sudo journalctl -u xiaozhi -f

# 开机自启
sudo systemctl enable xiaozhi
sudo systemctl disable xiaozhi
```

### xiaozhi.service - systemd服务模板

手动安装systemd服务的参考模板。

**使用方法**：

```bash
# 1. 编辑服务文件
sudo nano xiaozhi.service
# 修改 User、WorkingDirectory、ExecStart 等配置

# 2. 复制到systemd目录
sudo cp xiaozhi.service /etc/systemd/system/

# 3. 重载配置
sudo systemctl daemon-reload

# 4. 启动服务
sudo systemctl start xiaozhi

# 5. 设置开机自启
sudo systemctl enable xiaozhi
```

## 🌐 Web控制台说明

### 默认配置

使用部署脚本时，Web控制台默认配置：
- **监听地址**：`0.0.0.0`（允许外部访问）
- **端口**：`8080`
- **访问地址**：`http://服务器IP:8080`

### 自定义配置

**方法1 - 脚本参数**：
```bash
./deploy_server.sh --web-host 192.168.1.100 --web-port 9090
```

**方法2 - 环境变量**：
```bash
export XIAOZHI_WEB_HOST=0.0.0.0
export XIAOZHI_WEB_PORT=8080
```

**方法3 - systemd服务**：
在服务文件中配置环境变量。

### 安全建议

⚠️ 如果Web开放外部访问，建议：

1. **配置防火墙**：
   ```bash
   sudo ufw allow 8080/tcp
   # 或限制IP段
   sudo ufw allow from 192.168.1.0/24 to any port 8080
   ```

2. **使用Nginx反向代理**：
   - 添加HTTPS
   - 配置HTTP基础认证
   - 限制访问IP

详见 `DEPLOY_SERVER.md` 中的安全配置章节。

## 📚 文档索引

### 快速开始
- 阅读 `SERVER_QUICKREF.md` - 快速参考所有命令

### 详细教程
- 阅读 `DEPLOY_SERVER.md` - 完整部署文档，包括：
  - 系统要求和依赖安装
  - CLI模式激活流程
  - Web控制台详细配置
  - 后台运行配置（screen/systemd）
  - 安全配置和Nginx反向代理
  - 常见问题解决方案

### 在线资源
- [项目主页](https://github.com/huangjunsen0406/py-xiaozhi)
- [在线文档](https://huangjunsen0406.github.io/py-xiaozhi/)
- [视频教程](https://www.bilibili.com/video/BV1dWQhYEEmq/)

## ❓ 常见问题

### Q: 为什么要用CLI模式？
A: 在Ubuntu服务器等无GUI环境中，CLI模式可以在终端直接显示验证码，不需要图形界面。

### Q: Web控制台会自动启动吗？
A: 是的！无论是GUI还是CLI模式，Web控制台都会自动启动，默认在8080端口。

### Q: 如何外部访问Web控制台？
A: 使用部署脚本默认就是外部可访问（0.0.0.0），或设置环境变量 `XIAOZHI_WEB_HOST=0.0.0.0`。

### Q: 如何后台运行？
A: 推荐使用systemd服务（`install_service.sh`），或使用screen会话。

### Q: 激活后每次都要重新激活吗？
A: 不需要！激活一次后，使用 `--skip-activation` 参数启动即可。

## 🆘 获取帮助

遇到问题？

1. 📖 查看 `DEPLOY_SERVER.md` 的故障排查章节
2. 📝 查看日志：`tail -f logs/xiaozhi_*.log`
3. 💬 在GitHub提issue：[点击这里](https://github.com/huangjunsen0406/py-xiaozhi/issues)

## 📝 更新日志

- 2025-12-01: 添加Web控制台外部访问配置
- 2025-12-01: 创建systemd服务安装向导
- 2025-12-01: 完善部署文档和快速参考

## 📄 许可证

与主项目相同，采用 [MIT License](LICENSE)
