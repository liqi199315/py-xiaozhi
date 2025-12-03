@echo off
REM ========================================
REM 小智AI客户端 - Web版 EXE打包脚本
REM ========================================

echo.
echo ========================================
echo 小智AI客户端 - WebView内嵌版本EXE打包工具
echo ========================================
echo.
echo 特点:
echo   - 内嵌浏览器窗口显示界面
echo   - 不打开外部浏览器
echo   - 不包含PyQt5（体积更小）
echo   - 使用系统浏览器引擎
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo [1/5] 检查依赖...
echo.

REM 安装PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
)

REM 安装项目依赖
echo 检查项目依赖...
pip install -r requirements.txt

echo.
echo [2/5] 清理旧的构建文件...
echo.

REM 清理旧文件
if exist "build" rmdir /s /q "build"
if exist "dist\XiaozhiAI-Web" rmdir /s /q "dist\XiaozhiAI-Web"

echo.
echo [3/5] 开始打包Web版本...
echo.

REM 执行打包
pyinstaller build_exe_web.spec

if errorlevel 1 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo [4/5] 复制必要文件...
echo.

REM 确保dist目录结构正确
if not exist "dist\XiaozhiAI-Web\logs" mkdir "dist\XiaozhiAI-Web\logs"
if not exist "dist\XiaozhiAI-Web\cache" mkdir "dist\XiaozhiAI-Web\cache"

REM 复制README
if exist "README.md" copy "README.md" "dist\XiaozhiAI-Web\"

echo.
echo [5/5] 创建使用说明...
echo.

REM 创建使用说明文件
(
echo ========================================
echo 小智AI客户端 - WebView内嵌版使用说明
echo ========================================
echo.
echo 启动方法：
echo   双击 XiaozhiAI-Web.exe 启动程序
echo.
echo 首次使用：
echo   1. 程序会在命令行显示激活验证码
echo   2. 访问 xiaozhi.me 输入验证码完成激活
echo   3. 激活成功后会自动打开内嵌浏览器窗口
echo.
echo WebView界面：
echo   - 程序启动后会在独立窗口中显示
echo   - 不会打开外部浏览器
echo   - 默认窗口大小：1280x800
echo   - 包含完整的Live2D数字人界面
echo   - 支持文本输入和语音交互
echo.
echo 系统要求：
echo   - Windows 10/11
echo   - 需要 Edge WebView2 运行时（Win10/11通常已自带）
echo.
echo 自定义配置：
echo   - Web端口：设置环境变量 XIAOZHI_WEB_PORT
echo   - Web地址：设置环境变量 XIAOZHI_WEB_HOST
echo.
echo 命令行参数：
echo   --skip-activation  跳过激活流程
echo   --protocol mqtt    使用MQTT协议
echo   --web-port 9090    使用自定义端口
echo.
echo 与GUI版区别：
echo   ✓ 内嵌浏览器窗口（不打开外部浏览器）
echo   ✓ 使用系统浏览器引擎（无需打包Chromium）
echo   ✓ 体积更小（不含PyQt5）
echo   ✓ 完整功能（音频、Live2D等）
echo.
echo 更多帮助：
echo   https://github.com/huangjunsen0406/py-xiaozhi
echo.
) > "dist\XiaozhiAI-Web\使用说明.txt"

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 输出目录: dist\XiaozhiAI-Web\
echo 主程序: dist\XiaozhiAI-Web\XiaozhiAI-Web.exe
echo 大小: 约 150-250 MB（比GUI版小）
echo.
echo WebView版特点:
echo   ✓ 内嵌浏览器窗口显示
echo   ✓ 不打开外部浏览器
echo   ✓ 使用系统WebView2引擎
echo   ✓ 无需PyQt5环境
echo   ✓ 体积更小，性能更好
echo.
echo 可以将整个 XiaozhiAI-Web 文件夹打包分发
echo.

REM 询问是否打开文件夹
set /p OPEN_FOLDER="是否打开输出文件夹？(Y/N): "
if /i "%OPEN_FOLDER%"=="Y" (
    explorer "dist\XiaozhiAI-Web"
)

pause
