#!/bin/bash

# 小智 WebSocket 代理 - 快速启动脚本（Node.js 版本）

echo "=================================================="
echo "  小智 WebSocket 代理服务器 (Node.js)"
echo "=================================================="
echo ""

# 检查 Node.js 是否已安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未检测到 Node.js"
    echo ""
    echo "请先安装 Node.js: https://nodejs.org/"
    echo ""
    exit 1
fi

echo "✅ Node.js 版本:"
node --version
echo ""

# 进入 web-backend 目录
cd "$(dirname "$0")"

# 检查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    echo ""
    npm install
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ 依赖安装失败！"
        echo ""
        exit 1
    fi
    echo ""
    echo "✅ 依赖安装完成"
    echo ""
fi

echo "🚀 启动 WebSocket 代理服务器..."
echo ""
echo "提示:"
echo "  - 服务器将运行在 http://localhost:8080"
echo "  - WebSocket 端点: ws://localhost:8080/api/ws-proxy"
echo "  - 按 Ctrl+C 可以停止服务器"
echo ""
echo "=================================================="
echo ""

# 启动服务器
node server.js
