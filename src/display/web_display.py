# -*- coding: utf-8 -*-
"""
Web版本的显示界面
启动后台服务并打开浏览器访问Web控制台
"""

import asyncio
import webbrowser
from typing import Callable, Optional

from src.display.base_display import BaseDisplay


class WebBrowserDisplay(BaseDisplay):
    """Web浏览器显示类 - 自动打开浏览器访问Web控制台"""

    def __init__(self):
        super().__init__()
        self.web_url = None
        self._browser_opened = False

    async def start(self):
        """启动Web显示"""
        # Web服务器会通过插件系统启动
        # 这里只需要等待并打开浏览器
        import os
        
        host = os.getenv('XIAOZHI_WEB_HOST', '127.0.0.1')
        port = os.getenv('XIAOZHI_WEB_PORT', '8080')
        
        # 如果监听0.0.0.0，浏览器应该访问127.0.0.1
        if host == '0.0.0.0':
            host = '127.0.0.1'
        
        self.web_url = f'http://{host}:{port}'
        
        self.logger.info(f"Web控制台地址: {self.web_url}")
        
        # 延迟打开浏览器，等待Web服务器启动
        await asyncio.sleep(2)
        
        if not self._browser_opened:
            try:
                webbrowser.open(self.web_url)
                self._browser_opened = True
                self.logger.info(f"已在浏览器中打开: {self.web_url}")
            except Exception as e:
                self.logger.warning(f"无法自动打开浏览器: {e}")
                self.logger.info(f"请手动访问: {self.web_url}")

    async def set_callbacks(
        self,
        press_callback: Optional[Callable] = None,
        release_callback: Optional[Callable] = None,
        mode_callback: Optional[Callable] = None,
        auto_callback: Optional[Callable] = None,
        abort_callback: Optional[Callable] = None,
        send_text_callback: Optional[Callable] = None,
    ):
        """Web模式不需要回调"""
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
        """Web模式没有窗口"""
        pass

    async def close(self):
        """关闭显示"""
        self.logger.info("Web显示模式关闭")
