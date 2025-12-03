@echo off
REM ========================================
REM 小智AI客户端 - Windows EXE打包脚本
REM ========================================

echo.
echo ========================================
echo 小智AI客户端 - EXE打包工具
echo ========================================
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
if exist "dist" rmdir /s /q "dist"

echo.
echo [3/5] 开始打包...
echo.

REM 执行打包
pyinstaller build_exe.spec

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
if not exist "dist\XiaozhiAI\logs" mkdir "dist\XiaozhiAI\logs"
if not exist "dist\XiaozhiAI\cache" mkdir "dist\XiaozhiAI\cache"

REM 复制README
if exist "README.md" copy "README.md" "dist\XiaozhiAI\"

echo.
echo [5/5] 创建使用说明...
echo.

REM 创建使用说明文件
(
echo ========================================
echo 小智AI客户端 - 使用说明
echo ========================================
echo.
echo 启动方法：
echo   双击 XiaozhiAI.exe 启动程序
echo.
echo 首次使用：
echo   1. 程序会弹出激活窗口
echo   2. 显示6位验证码
echo   3. 访问 xiaozhi.me 输入验证码完成激活
echo.
echo Web控制台访问：
echo   - 本地：http://127.0.0.1:8080
echo   - 远程：http://本机IP:8080
echo.
echo 配置文件位置：
echo   config/config.json
echo.
echo 日志文件位置：
echo   logs/app.log
echo.
echo 常见问题：
echo   Q: 如何修改Web端口？
echo   A: 设置环境变量 XIAOZHI_WEB_PORT=端口号
echo.
echo   Q: 如何跳过激活？
echo   A: 使用命令行启动：
echo      XiaozhiAI.exe --skip-activation
echo.
echo 更多帮助：
echo   https://github.com/huangjunsen0406/py-xiaozhi
echo.
) > "dist\XiaozhiAI\使用说明.txt"

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 输出目录: dist\XiaozhiAI\
echo 主程序: dist\XiaozhiAI\XiaozhiAI.exe
echo 大小: 约 200-300 MB
echo.
echo 可以将整个 XiaozhiAI 文件夹打包分发
echo.

REM 询问是否打开文件夹
set /p OPEN_FOLDER="是否打开输出文件夹？(Y/N): "
if /i "%OPEN_FOLDER%"=="Y" (
    explorer "dist\XiaozhiAI"
)

pause
