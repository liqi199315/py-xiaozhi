#!/bin/bash
# 快速部署脚本 - Linux/Mac

set -e  # 遇到错误立即退出

echo "========================================="
echo "   小智AI - 豆包ASR后端部署脚本"
echo "========================================="
echo ""

# 检查Python版本
echo "1. 检查Python版本..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   当前Python版本: $PYTHON_VERSION"

# 检查是否已创建虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "2. 创建Python虚拟环境..."
    python3 -m venv venv
    echo "   ✅ 虚拟环境创建完成"
else
    echo ""
    echo "2. 虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo ""
echo "3. 激活虚拟环境..."
source venv/bin/activate
echo "   ✅ 虚拟环境已激活"

# 安装依赖
echo ""
echo "4. 安装依赖包..."
echo "   选择安装方式："
echo "   [1] 精简版 (仅Web服务和豆包ASR)"
echo "   [2] 完整版 (包含所有功能)"
read -p "   请选择 (1/2): " choice

if [ "$choice" = "1" ]; then
    echo "   正在安装精简版依赖..."
    pip install -r requirements_web.txt
    echo "   ✅ 精简版依赖安装完成"
elif [ "$choice" = "2" ]; then
    echo "   正在安装完整版依赖..."
    pip install -r requirements.txt
    echo "   ✅ 完整版依赖安装完成"
else
    echo "   ❌ 无效选择，退出"
    exit 1
fi

# 配置环境变量
echo ""
echo "5. 配置环境变量..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# 豆包ASR凭证
DOUBAO_APP_KEY=2785683478
DOUBAO_ACCESS_KEY=OHl7yBW1VI5M9f4oI26RDU-3xPtkAGZp

# 小智WebSocket配置（可选）
# WEBSOCKET_ACCESS_TOKEN=your-token
# DEVICE_ID=your-device-id
# CLIENT_ID=your-client-id

# Web服务配置
XIAOZHI_WEB_HOST=0.0.0.0
XIAOZHI_WEB_PORT=8080
EOF
    echo "   ✅ .env 文件已创建"
    echo "   💡 请编辑 .env 文件填入你的凭证"
else
    echo "   .env 文件已存在，跳过创建"
fi

# 测试启动
echo ""
echo "========================================="
echo "   部署完成！"
echo "========================================="
echo ""
echo "启动命令："
echo "   开发模式: python main_web.py --skip-activation"
echo "   生产模式: python main_web.py --skip-activation --web-host 0.0.0.0"
echo ""
echo "访问地址："
echo "   本地: http://127.0.0.1:8080/index3.html"
echo "   远程: http://你的服务器IP:8080/index3.html"
echo ""
echo "查看日志："
echo "   tail -f logs/xiaozhi.log"
echo ""
echo "========================================="
