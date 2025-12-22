@echo off
chcp 65001 >nul
REM 快速部署脚本 - Windows

echo =========================================
echo    小智AI - 豆包ASR后端部署脚本
echo =========================================
echo.

REM 检查Python版本
echo 1. 检查Python版本...
python --version
if errorlevel 1 (
    echo    ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)
echo    ✅ Python已安装
echo.

REM 检查是否已创建虚拟环境
if not exist "venv" (
    echo 2. 创建Python虚拟环境...
    python -m venv venv
    echo    ✅ 虚拟环境创建完成
) else (
    echo 2. 虚拟环境已存在，跳过创建
)
echo.

REM 激活虚拟环境
echo 3. 激活虚拟环境...
call venv\Scripts\activate
echo    ✅ 虚拟环境已激活
echo.

REM 安装依赖
echo 4. 安装依赖包...
echo    选择安装方式：
echo    [1] 精简版 (仅Web服务和豆包ASR)
echo    [2] 完整版 (包含所有功能)
set /p choice="   请选择 (1/2): "

if "%choice%"=="1" (
    echo    正在安装精简版依赖...
    pip install -r requirements_web.txt
    echo    ✅ 精简版依赖安装完成
) else if "%choice%"=="2" (
    echo    正在安装完整版依赖...
    pip install -r requirements.txt
    echo    ✅ 完整版依赖安装完成
) else (
    echo    ❌ 无效选择，退出
    pause
    exit /b 1
)
echo.

REM 配置环境变量
echo 5. 配置环境变量...
if not exist ".env" (
    (
        echo # 豆包ASR凭证
        echo DOUBAO_APP_KEY=2785683478
        echo DOUBAO_ACCESS_KEY=OHl7yBW1VI5M9f4oI26RDU-3xPtkAGZp
        echo.
        echo # 小智WebSocket配置（可选）
        echo # WEBSOCKET_ACCESS_TOKEN=your-token
        echo # DEVICE_ID=your-device-id
        echo # CLIENT_ID=your-client-id
        echo.
        echo # Web服务配置
        echo XIAOZHI_WEB_HOST=0.0.0.0
        echo XIAOZHI_WEB_PORT=8080
    ) > .env
    echo    ✅ .env 文件已创建
    echo    💡 请编辑 .env 文件填入你的凭证
) else (
    echo    .env 文件已存在，跳过创建
)
echo.

REM 测试启动
echo =========================================
echo    部署完成！
echo =========================================
echo.
echo 启动命令：
echo    开发模式: python main_web.py --skip-activation
echo    生产模式: python main_web.py --skip-activation --web-host 0.0.0.0
echo.
echo 访问地址：
echo    本地: http://127.0.0.1:8080/index3.html
echo    远程: http://你的服务器IP:8080/index3.html
echo.
echo 查看日志：
echo    type logs\xiaozhi.log
echo.
echo =========================================
pause
