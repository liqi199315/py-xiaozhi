@echo off
REM Web 小智 - 快速启动脚本
REM 这个脚本会启动必要的服务来运行 Web 小智

echo ==================================================
echo   小智 Web 客户端 - 快速启动
echo ==================================================
echo.

echo [1/2] 启动 WebSocket 代理和后台服务...
echo.
echo 正在启动: python main_web.py --web-port 8080 --skip-activation
echo.
echo 提示: 
echo   - WebSocket 代理将运行在: ws://127.0.0.1:8080/api/ws-proxy
echo   - HTTP 服务器将运行在: http://127.0.0.1:8080
echo.

start "小智 WebSocket 代理" cmd /k "python main_web.py --web-port 8080 --skip-activation"

timeout /t 3 /nobreak > nul

echo.
echo [2/2] 启动 Web 测试页面服务器...
echo.
echo 正在启动: python -m http.server 8006 (在 web-xiaozhi 目录)
echo.

cd web-xiaozhi
start "Web 测试页面" cmd /k "python -m http.server 8006"

cd ..

timeout /t 2 /nobreak > nul

echo.
echo ==================================================
echo   启动完成！
echo ==================================================
echo.
echo 现在你可以:
echo.
echo   1. 打开浏览器访问: http://localhost:8006/test/index.html
echo   2. 点击页面上的"连接"按钮
echo   3. 查看浏览器控制台（F12）的日志
echo.
echo 提示:
echo   - 确保你已经从 OTA 获取了有效的 token
echo   - 如果看到 "test-token"，说明设备未激活
echo   - 查看后台日志了解连接状态
echo.
echo 关闭这个窗口不会停止服务，请手动关闭另外两个窗口
echo.
pause
