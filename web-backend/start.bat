@echo off
REM 小智 WebSocket 代理 - 快速启动脚本（Node.js 版本）

echo ==================================================
echo   小智 WebSocket 代理服务器 (Node.js)
echo ==================================================
echo.

REM 检查 Node.js 是否已安装
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误: 未检测到 Node.js
    echo.
    echo 请先安装 Node.js: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo ✅ Node.js 版本:
node --version
echo.

REM 进入 web-backend 目录
cd web-backend

REM 检查 node_modules 是否存在
if not exist "node_modules" (
    echo 📦 首次运行，正在安装依赖...
    echo.
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ❌ 依赖安装失败！
        echo.
        pause
        exit /b 1
    )
    echo.
    echo ✅ 依赖安装完成
    echo.
)

echo 🚀 启动 WebSocket 代理服务器...
echo.
echo 提示:
echo   - 服务器将运行在 http://localhost:8080
echo   - WebSocket 端点: ws://localhost:8080/api/ws-proxy
echo   - 按 Ctrl+C 可以停止服务器
echo.
echo ==================================================
echo.

REM 启动服务器
node server.js

pause
