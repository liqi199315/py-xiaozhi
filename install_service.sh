#!/bin/bash
# systemd服务安装脚本
# 此脚本将自动安装和配置xiaozhi systemd服务

set -e  # 遇到错误立即退出

echo "========================================"
echo "小智AI客户端 - systemd服务安装向导"
echo "========================================"
echo ""

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用sudo运行此脚本"
    echo "   sudo $0"
    exit 1
fi

# 获取实际用户（sudo时获取真实用户）
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(eval echo ~$REAL_USER)

# 获取当前脚本所在目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📋 配置信息:"
echo "   用户: $REAL_USER"
echo "   项目目录: $SCRIPT_DIR"
echo ""

# 询问配置选项
read -p "Web监听地址 [0.0.0.0]: " WEB_HOST
WEB_HOST=${WEB_HOST:-0.0.0.0}

read -p "Web端口 [8080]: " WEB_PORT
WEB_PORT=${WEB_PORT:-8080}

read -p "通信协议 (websocket/mqtt) [websocket]: " PROTOCOL
PROTOCOL=${PROTOCOL:-websocket}

read -p "是否跳过激活? (y/N): " SKIP_ACTIVATION
if [[ $SKIP_ACTIVATION =~ ^[Yy]$ ]]; then
    ACTIVATION_FLAG="--skip-activation"
else
    ACTIVATION_FLAG=""
fi

echo ""
echo "✅ 配置确认:"
echo "   Web监听: $WEB_HOST:$WEB_PORT"
echo "   通信协议: $PROTOCOL"
echo "   跳过激活: ${SKIP_ACTIVATION:-否}"
echo ""

read -p "确认安装? (y/N): " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "❌ 安装已取消"
    exit 0
fi

echo ""
echo "🔧 开始安装..."

# 创建服务文件
SERVICE_FILE="/etc/systemd/system/xiaozhi.service"
echo "   创建服务文件: $SERVICE_FILE"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Xiaozhi AI Client
Documentation=https://github.com/huangjunsen0406/py-xiaozhi
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$SCRIPT_DIR

# 环境变量配置
Environment="XIAOZHI_DISABLE_TRAY=1"
Environment="QT_QPA_PLATFORM=offscreen"
Environment="XIAOZHI_WEB_HOST=$WEB_HOST"
Environment="XIAOZHI_WEB_PORT=$WEB_PORT"

# 启动命令
ExecStart=/usr/bin/python3 main.py --mode cli --protocol $PROTOCOL $ACTIVATION_FLAG

# 重启配置
Restart=on-failure
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=xiaozhi

[Install]
WantedBy=multi-user.target
EOF

# 设置权限
chmod 644 "$SERVICE_FILE"

# 重载systemd
echo "   重载systemd配置..."
systemctl daemon-reload

# 询问是否立即启动
echo ""
read -p "是否立即启动服务? (y/N): " START_NOW
if [[ $START_NOW =~ ^[Yy]$ ]]; then
    echo "   启动服务..."
    systemctl start xiaozhi
    
    # 等待一下
    sleep 2
    
    # 检查状态
    if systemctl is-active --quiet xiaozhi; then
        echo "   ✅ 服务启动成功"
    else
        echo "   ⚠️  服务启动可能失败，请检查日志"
    fi
fi

# 询问是否开机自启
echo ""
read -p "是否设置开机自启? (y/N): " ENABLE_BOOT
if [[ $ENABLE_BOOT =~ ^[Yy]$ ]]; then
    echo "   设置开机自启..."
    systemctl enable xiaozhi
    echo "   ✅ 已设置开机自启"
fi

# 显示完成信息
echo ""
echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "📋 服务管理命令:"
echo ""
echo "  启动服务:  sudo systemctl start xiaozhi"
echo "  停止服务:  sudo systemctl stop xiaozhi"
echo "  重启服务:  sudo systemctl restart xiaozhi"
echo "  查看状态:  sudo systemctl status xiaozhi"
echo "  查看日志:  sudo journalctl -u xiaozhi -f"
echo "  开机自启:  sudo systemctl enable xiaozhi"
echo "  禁用自启:  sudo systemctl disable xiaozhi"
echo ""

if [ "$WEB_HOST" = "0.0.0.0" ]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    if [ -n "$SERVER_IP" ]; then
        echo "🌐 Web控制台访问地址:"
        echo "  本地: http://127.0.0.1:$WEB_PORT"
        echo "  远程: http://$SERVER_IP:$WEB_PORT"
        echo ""
    fi
fi

echo "💡 提示:"
echo "  - 首次运行可能需要激活设备"
echo "  - 使用 sudo journalctl -u xiaozhi -f 实时查看运行日志"
echo "  - 修改配置后需要重启服务: sudo systemctl restart xiaozhi"
echo ""
