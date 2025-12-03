#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebView版启动脚本
使用内嵌浏览器窗口显示Web界面，不打开外部浏览器
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 确保项目根目录在sys.path中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging, get_logger

logger = get_logger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="小智AI客户端 - Web版")
    parser.add_argument(
        "--protocol",
        choices=["mqtt", "websocket"],
        default="websocket",
        help="通信协议：mqtt 或 websocket",
    )
    parser.add_argument(
        "--skip-activation",
        action="store_true",
        help="跳过激活流程，直接启动应用（仅用于调试）",
    )
    parser.add_argument(
        "--web-host",
        default="127.0.0.1",
        help="Web服务器监听地址（默认：127.0.0.1）",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8080,
        help="Web服务器端口（默认：8080）",
    )
    return parser.parse_args()


async def handle_activation() -> bool:
    """处理设备激活流程"""
    try:
        from src.core.system_initializer import SystemInitializer

        logger.info("开始设备激活流程检查...")

        system_initializer = SystemInitializer()
        # 使用CLI模式的激活
        result = await system_initializer.handle_activation_process(mode="cli")
        success = bool(result.get("is_activated", False))
        logger.info(f"激活流程完成，结果: {success}")
        return success
    except Exception as e:
        logger.error(f"激活流程异常: {e}", exc_info=True)
        return False


async def start_app(protocol: str, skip_activation: bool, web_host: str, web_port: int) -> int:
    """启动应用"""
    logger.info("启动小智AI客户端 - WebView版")

    # 设置Web服务器环境变量
    import os
    os.environ["XIAOZHI_WEB_HOST"] = web_host
    os.environ["XIAOZHI_WEB_PORT"] = str(web_port)
    os.environ["XIAOZHI_DISABLE_TRAY"] = "1"  # 禁用系统托盘

    # 处理激活流程
    if not skip_activation:
        activation_success = await handle_activation()
        if not activation_success:
            logger.error("设备激活失败，程序退出")
            return 1
    else:
        logger.warning("跳过激活流程（调试模式）")

    # 创建并启动应用程序
    from src.application import Application

    app = Application.get_instance()

    # 使用webview模式（在窗口中显示Web界面）
    return await app.run(mode="webview", protocol=protocol)


if __name__ == "__main__":
    exit_code = 1
    try:
        args = parse_args()
        setup_logging()

        # 使用标准asyncio事件循环
        exit_code = asyncio.run(
            start_app(
                args.protocol,
                args.skip_activation,
                args.web_host,
                args.web_port,
            )
        )

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        exit_code = 0
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)
        exit_code = 1
    finally:
        sys.exit(exit_code)
