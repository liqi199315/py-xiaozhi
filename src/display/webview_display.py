# -*- coding: utf-8 -*-
"""
WebView内嵌浏览器显示界面
在窗口中直接显示Web界面，不打开外部浏览器
"""

import asyncio
import threading
from typing import Callable, Optional

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False

from src.display.base_display import BaseDisplay


class WebViewDisplay(BaseDisplay):
    """WebView内嵌显示类 - 在窗口中直接显示Web控制台"""

    def __init__(self):
        super().__init__()
        self.web_url = None
        self.window = None
        self._webview_thread = None
        self._started = False

    async def start(self):
        """启动WebView显示"""
        if not WEBVIEW_AVAILABLE:
            self.logger.error("pywebview未安装，请运行: pip install pywebview")
            raise ImportError("pywebview is not installed")

        import os

        host = os.getenv('XIAOZHI_WEB_HOST', '127.0.0.1')
        port = os.getenv('XIAOZHI_WEB_PORT', '8080')

        # WebView只能访问127.0.0.1
        if host == '0.0.0.0':
            host = '127.0.0.1'

        self.web_url = f'http://{host}:{port}'

        self.logger.info(f"正在启动内嵌浏览器窗口: {self.web_url}")

        # 等待Web服务器启动
        await asyncio.sleep(2)

        # 在新线程中启动WebView（因为webview.start()是阻塞的）
        self._webview_thread = threading.Thread(
            target=self._start_webview,
            daemon=True
        )
        self._webview_thread.start()

        self._started = True
        self.logger.info("内嵌浏览器窗口已启动")

    def _start_webview(self):
        """在新线程中启动WebView窗口"""
        try:
            # 创建WebView窗口
            self.window = webview.create_window(
                title='小智AI客户端',
                url=self.web_url,
                width=1280,
                height=800,
                resizable=True,
                fullscreen=False,
                min_size=(800, 600),
                background_color='#1a1a1a',
                text_select=True
            )

            # 启动WebView（阻塞调用）
            webview.start(debug=False)

        except Exception as e:
            self.logger.error(f"启动WebView窗口失败: {e}", exc_info=True)

    async def set_callbacks(
        self,
        press_callback: Optional[Callable] = None,
        release_callback: Optional[Callable] = None,
        mode_callback: Optional[Callable] = None,
        auto_callback: Optional[Callable] = None,
        abort_callback: Optional[Callable] = None,
        send_text_callback: Optional[Callable] = None,
    ):
        """WebView模式不需要回调"""
        pass

    async def update_status(self, status: str, connected: bool):
        """状态通过Web控制台的SSE推送"""
        pass

    async def update_text(self, text: str):
        """文本通过Web控制台显示"""
        pass

    async def update_emotion(self, emotion_name: str):
        """表情通过Web控制台显示"""
        pass

    async def update_button_status(self, text: str):
        """按钮状态通过Web控制台更新"""
        pass

    async def toggle_mode(self):
        """模式切换通过Web控制台操作"""
        pass

    async def toggle_window_visibility(self):
        """切换窗口显示/隐藏"""
        if self.window:
            try:
                # pywebview没有直接的hide/show方法
                # 可以通过最小化/恢复来实现
                pass
            except Exception as e:
                self.logger.warning(f"切换窗口状态失败: {e}")

    async def close(self):
        """关闭显示"""
        self.logger.info("正在关闭WebView窗口...")
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
        self._started = False
        self.logger.info("WebView窗口已关闭")
