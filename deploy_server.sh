#!/bin/bash
# 服务器部署脚本 - Ubuntu/Linux 环境
# 此脚本简化了服务器部署流程，自动使用CLI模式并配置Web控制台

echo "========================================"
echo "小智AI客户端 - 服务器部署脚本"
echo "========================================"
echo ""

# 检查Python版本
echo "检查Python环境..."
python3 --version

# 检查依赖
echo ""
echo "检查依赖包..."
if ! python3 -c "import asyncio" 2>/dev/null; then
    echo "警告: Python环境可能不完整"
fi

# 设置环境变量
echo ""
echo "配置环境..."
export XIAOZHI_DISABLE_TRAY=1  # 禁用系统托盘（服务器无需）
export QT_QPA_PLATFORM=offscreen  # 无头模式

# Web控制台配置（默认允许外部访问）
export XIAOZHI_WEB_HOST="${XIAOZHI_WEB_HOST:-0.0.0.0}"  # 默认监听所有接口
export XIAOZHI_WEB_PORT="${XIAOZHI_WEB_PORT:-8080}"     # 默认端口8080

# 启动选项
MODE="cli"
PROTOCOL="websocket"
SKIP_ACTIVATION=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-activation)
            SKIP_ACTIVATION="--skip-activation"
            echo "提示: 将跳过激活流程"
            shift
            ;;
        --mqtt)
            PROTOCOL="mqtt"
            echo "提示: 使用MQTT协议"
            shift
            ;;
        --web-host)
            XIAOZHI_WEB_HOST="$2"
            echo "提示: Web监听地址设置为 $2"
            shift 2
            ;;
        --web-port)
            XIAOZHI_WEB_PORT="$2"
            echo "提示: Web端口设置为 $2"
            shift 2
            ;;
        --local-only)
            XIAOZHI_WEB_HOST="127.0.0.1"
            echo "提示: Web仅限本地访问"
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo ""
            echo "可用参数:"
            echo "  --skip-activation    跳过激活流程"
            echo "  --mqtt               使用MQTT协议"
            echo "  --web-host HOST      设置Web监听地址（默认: 0.0.0.0）"
            echo "  --web-port PORT      设置Web端口（默认: 8080）"
            echo "  --local-only         Web仅限本地访问（127.0.0.1）"
            exit 1
            ;;
    esac
done

# 显示启动信息
echo ""
echo "启动配置:"
echo "  - 运行模式: CLI (命令行)"
echo "  - 通信协议: $PROTOCOL"
echo "  - 系统托盘: 已禁用"
echo "  - Web控制台: http://$XIAOZHI_WEB_HOST:$XIAOZHI_WEB_PORT"
echo ""

# 显示访问提示
if [ "$XIAOZHI_WEB_HOST" = "0.0.0.0" ]; then
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    if [ -n "$SERVER_IP" ]; then
        echo "Web控制台访问地址:"
        echo "  - 本地: http://127.0.0.1:$XIAOZHI_WEB_PORT"
        echo "  - 远程: http://$SERVER_IP:$XIAOZHI_WEB_PORT"
    fi
elif [ "$XIAOZHI_WEB_HOST" = "127.0.0.1" ]; then
    echo "Web控制台访问地址:"
    echo "  - 本地: http://127.0.0.1:$XIAOZHI_WEB_PORT"
    echo "  - 注意: 仅限本地访问"
fi
echo ""

# 启动应用
echo "正在启动小智AI客户端..."
echo "========================================"
echo ""

python3 main.py --mode "$MODE" --protocol "$PROTOCOL" $SKIP_ACTIVATION
