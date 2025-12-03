import asyncio
import contextlib
import json
import os
import ssl
from pathlib import Path
from typing import Any

import websockets
from aiohttp import web, WSMsgType

from src.constants.constants import AbortReason, DeviceState
from src.core.ota import Ota
from src.plugins.base import Plugin
from src.utils.logging_config import get_logger
from src.utils.resource_finder import resource_finder

logger = get_logger(__name__)


class _EventBroadcaster:
    """Lightweight fan-out helper for SSE clients."""

    def __init__(self) -> None:
        self._queues: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._queues.discard(queue)

    def publish(self, payload: dict[str, Any]) -> None:
        """Push payload to all listeners without blocking."""
        dead_queues: list[asyncio.Queue] = []
        for queue in list(self._queues):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait(payload)
                except Exception:
                    dead_queues.append(queue)
            except Exception:
                dead_queues.append(queue)

        for queue in dead_queues:
            self.unsubscribe(queue)


class WebServerPlugin(Plugin):
    """Expose a minimal HTTP API + web UI for text/voice control."""

    name = "web_server"
    priority = 80

    def __init__(self) -> None:
        super().__init__()
        self.app = None
        self._aiohttp_app: web.Application | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._broadcaster = _EventBroadcaster()
        self._index_path = (
            Path(__file__).resolve().parents[2] / "web" / "index.html"
        )
        self._host = os.getenv("XIAOZHI_WEB_HOST", "127.0.0.1")
        self._port = int(os.getenv("XIAOZHI_WEB_PORT", "8080"))

    async def setup(self, app: Any) -> None:
        self.app = app
        if not self._index_path.exists():
            logger.warning("Web UI文件未找到: %s", self._index_path)

        self._aiohttp_app = web.Application()
        self._aiohttp_app.router.add_get("/", self._handle_index)
        self._aiohttp_app.router.add_get("/events", self._handle_events)
        self._aiohttp_app.router.add_post("/api/text", self._handle_text)
        self._aiohttp_app.router.add_post("/api/voice/manual/start", self._handle_voice_start)  # fmt: skip
        self._aiohttp_app.router.add_post("/api/voice/manual/stop", self._handle_voice_stop)  # fmt: skip
        self._aiohttp_app.router.add_post("/api/voice/auto", self._handle_auto_conversation)  # fmt: skip
        self._aiohttp_app.router.add_post("/api/abort", self._handle_abort)
        self._aiohttp_app.router.add_get("/api/config", self._handle_config)
        
        # WebSocket 代理路由（用于 Web 前端）
        self._aiohttp_app.router.add_get("/api/ws-proxy", self._handle_websocket_proxy)
        
        # Add static file serving for web directory
        web_dir = self._index_path.parent
        self._aiohttp_app.router.add_static("/", web_dir, show_index=False)

    async def start(self) -> None:
        if not self._aiohttp_app or self._runner:
            return

        self._runner = web.AppRunner(self._aiohttp_app, access_log=None)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()
        logger.info("Web控制台已启动: http://%s:%s", self._host, self._port)
        logger.info("WebSocket代理已启动: ws://%s:%s/api/ws-proxy", self._host, self._port)

    async def stop(self) -> None:
        if self._site:
            await self._site.stop()
            self._site = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None
        logger.info("Web控制台已停止")

    async def shutdown(self) -> None:
        await self.stop()

    # -------------------- HTTP handlers --------------------
    async def _handle_index(self, _: web.Request) -> web.StreamResponse:
        if self._index_path.exists():
            return web.FileResponse(self._index_path)

        return web.Response(
            text="Web UI 文件缺失", status=404, content_type="text/plain"
        )

    async def _handle_events(self, request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
        await response.prepare(request)
        queue = self._broadcaster.subscribe()

        # 立即推送一次当前状态
        snapshot = (
            self.app.get_state_snapshot()
            if hasattr(self.app, "get_state_snapshot")
            else {}
        )
        initial_event = {
            "event": "state_snapshot",
            "payload": snapshot,
        }
        await response.write(self._sse_payload(initial_event))

        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15)
                    await response.write(self._sse_payload(payload))
                except asyncio.TimeoutError:
                    await response.write(b": keepalive\n\n")
                except ConnectionResetError:
                    break
        finally:
            self._broadcaster.unsubscribe(queue)
            with contextlib.suppress(Exception):
                await response.write_eof()

        return response

    async def _handle_text(self, request: web.Request) -> web.Response:
        data = await request.json()
        text = str(data.get("text", "")).strip()
        if not text:
            return web.json_response({"error": "text不能为空"}, status=400)

        if not await self._ensure_protocol():
            return web.json_response({"error": "协议未连接"}, status=503)

        await self.app.protocol.send_wake_word_detected(text)
        self._broadcaster.publish(
            {"event": "local", "payload": {"type": "stt", "text": text}}
        )
        return web.json_response({"status": "ok"})

    async def _handle_voice_start(self, _: web.Request) -> web.Response:
        await self.app.start_listening_manual()
        return web.json_response({"status": "listening"})

    async def _handle_voice_stop(self, _: web.Request) -> web.Response:
        await self.app.stop_listening_manual()
        return web.json_response({"status": "idle"})

    async def _handle_auto_conversation(self, _: web.Request) -> web.Response:
        await self.app.start_auto_conversation()
        return web.json_response({"status": "auto"})

    async def _handle_abort(self, _: web.Request) -> web.Response:
        await self.app.abort_speaking(AbortReason.USER_INTERRUPTION)
        return web.json_response({"status": "aborted"})

    async def _handle_config(self, _: web.Request) -> web.Response:
        """Return minimal config for the web UI."""
        try:
            cfg = getattr(self.app, "config", None)
            if not cfg:
                return web.json_response({"error": "config unavailable"}, status=503)

            token = cfg.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_ACCESS_TOKEN")
            device_id = cfg.get_config("SYSTEM_OPTIONS.DEVICE_ID")
            client_id = cfg.get_config("SYSTEM_OPTIONS.CLIENT_ID")
            websocket_url = cfg.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_URL")

            # 优先使用环境变量覆盖（便于在容器/脚本中注入最新 token）
            env_token = os.getenv("WEBSOCKET_ACCESS_TOKEN") or os.getenv("XIAOZHI_WS_TOKEN")
            env_device = os.getenv("DEVICE_ID")
            env_client = os.getenv("CLIENT_ID")
            if env_token:
                token = env_token
            if env_device:
                device_id = env_device
            if env_client:
                client_id = env_client

            # 如果是占位 token，先尝试通过 OTA 刷新一次配置
            if not token or token == "test-token":
                try:
                    ota = await Ota.get_instance()
                    await ota.fetch_and_update_config()
                    token = cfg.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_ACCESS_TOKEN")
                    device_id = cfg.get_config("SYSTEM_OPTIONS.DEVICE_ID")
                    client_id = cfg.get_config("SYSTEM_OPTIONS.CLIENT_ID")
                    websocket_url = cfg.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_URL")
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[WebConfig] OTA refresh failed: {e}")

            # 依然是占位 token，再尝试从磁盘 config/config.json 读取真实值
            if not token or token == "test-token":
                try:
                    cfg_path = resource_finder.find_file("config/config.json")
                    if cfg_path and cfg_path.exists():
                        raw = json.loads(cfg_path.read_text(encoding="utf-8"))
                        net = raw.get("SYSTEM_OPTIONS", {}).get("NETWORK", {})
                        token_disk = net.get("WEBSOCKET_ACCESS_TOKEN")
                        device_disk = raw.get("SYSTEM_OPTIONS", {}).get("DEVICE_ID")
                        client_disk = raw.get("SYSTEM_OPTIONS", {}).get("CLIENT_ID")
                        ws_disk = net.get("WEBSOCKET_URL")
                        if token_disk and token_disk != "test-token":
                            token = token_disk
                        if device_disk:
                            device_id = device_disk
                        if client_disk:
                            client_id = client_disk
                        if ws_disk:
                            websocket_url = ws_disk
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[WebConfig] fallback load config.json failed: {e}")

            return web.json_response(
                {
                    "token": token,
                    "device_id": device_id,
                    "client_id": client_id,
                    "websocket_url": websocket_url,
                }
            )
        except Exception as e:
            logger.error(f"[WebConfig] Failed to read config: {e}", exc_info=True)
            return web.json_response({"error": "config error"}, status=500)

    async def _handle_websocket_proxy(self, request: web.Request) -> web.WebSocketResponse:
        """
        WebSocket 代理端点
        前端可以不传 token/device/client，本端会用配置/环境/磁盘兜底后转发到后台 WebSocket。
        """
        # 1. 获取认证信息（可为空，后端兜底）
        query = request.query
        token = query.get('token') or query.get('access_token')
        device_id = query.get('device_id')
        client_id = query.get('client_id')

        try:
            cfg = getattr(self.app, "config", None)
            # 配置兜底
            if not token and cfg:
                token_cfg = cfg.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_ACCESS_TOKEN")
                if token_cfg:
                    token = token_cfg
            if not device_id and cfg:
                device_id = cfg.get_config("SYSTEM_OPTIONS.DEVICE_ID")
            if not client_id and cfg:
                client_id = cfg.get_config("SYSTEM_OPTIONS.CLIENT_ID")

            # 环境变量兜底
            if not token or token == "test-token":
                env_token = os.getenv("WEBSOCKET_ACCESS_TOKEN") or os.getenv("XIAOZHI_WS_TOKEN")
                if env_token and env_token != "test-token":
                    token = env_token
            if not device_id:
                device_id = os.getenv("DEVICE_ID")
            if not client_id:
                client_id = os.getenv("CLIENT_ID")

            # 磁盘兜底
            if (not token or token == "test-token"):
                cfg_path = resource_finder.find_file("config/config.json")
                if cfg_path and cfg_path.exists():
                    raw = json.loads(cfg_path.read_text(encoding="utf-8"))
                    net = raw.get("SYSTEM_OPTIONS", {}).get("NETWORK", {})
                    token_disk = net.get("WEBSOCKET_ACCESS_TOKEN")
                    if token_disk and token_disk != "test-token":
                        token = token_disk
                    device_disk = raw.get("SYSTEM_OPTIONS", {}).get("DEVICE_ID")
                    client_disk = raw.get("SYSTEM_OPTIONS", {}).get("CLIENT_ID")
                    device_id = device_id or device_disk
                    client_id = client_id or client_disk
        except Exception as e:
            logger.warning(f"[WebSocket代理] 兜底读取 token 失败: {e}")

        # 默认值
        device_id = device_id or 'web-client'
        client_id = client_id or 'web-client'

        if not token:
            logger.warning("[WebSocket代理] 缺少 token，且后台未获取到有效 token")
            return web.json_response({'error': '缺少 token，且后台未获取到有效 token'}, status=401)

        if token == 'test-token':
            logger.warning("[WebSocket代理] 使用了测试 token，可能导致认证失败")

        logger.info(f"[WebSocket代理] 收到连接请求: device_id={device_id}, client_id={client_id}")

        # 2. 准备客户端 WebSocket
        client_ws = web.WebSocketResponse()
        await client_ws.prepare(request)

        # 3. 连接后台 WebSocket
        try:
            backend_url = self.app.config.get_config("SYSTEM_OPTIONS.NETWORK.WEBSOCKET_URL")
            if not backend_url:
                logger.error("[WebSocket代理] 后台 WebSocket URL 未配置")
                await client_ws.close(code=1011, reason="Backend URL not configured")
                return client_ws

            headers = {
                "Authorization": f"Bearer {token}",
                "Protocol-Version": "1",
                "Device-Id": device_id,
                "Client-Id": client_id,
            }
            logger.info(f"[WebSocket代理] 连接到后台: {backend_url}")

            ssl_context = None
            if backend_url.startswith("wss://"):
                ssl_context = ssl._create_unverified_context()

            try:
                async with websockets.connect(
                    backend_url,
                    extra_headers=headers,
                    ssl=ssl_context,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,
                ) as backend_ws:
                    logger.info(f"[WebSocket代理] ✅ 已连接到后台服务器 (device_id={device_id})")
                    await self._proxy_bidirectional(client_ws, backend_ws, device_id)
            except websockets.InvalidURI as e:
                logger.error(f"[WebSocket代理] 无效的后台 URL: {e}")
                await client_ws.close(code=1011, reason="Invalid backend URL")
            except websockets.InvalidHandshake as e:
                logger.error(f"[WebSocket代理] 后台握手失败 (可能是认证失败): {e}")
                await client_ws.close(code=1008, reason="Backend authentication failed")
            except Exception as e:
                logger.error(f"[WebSocket代理] 连接后台失败: {e}", exc_info=True)
                await client_ws.close(code=1011, reason=f"Backend connection error: {str(e)}")

        except Exception as e:
            logger.error(f"[WebSocket代理] 处理请求失败: {e}", exc_info=True)
            if not client_ws.closed:
                await client_ws.close(code=1011, reason="Proxy error")

        return client_ws


    async def _proxy_bidirectional(
        self,
        client_ws: web.WebSocketResponse,
        backend_ws: websockets.WebSocketClientProtocol,
        device_id: str
    ) -> None:
        """
        双向转发 WebSocket 消息
        
        同时运行两个任务：
        1. 客户端 -> 后台
        2. 后台 -> 客户端
        """
        
        async def forward_client_to_backend():
            """转发：客户端 -> 后台"""
            try:
                async for msg in client_ws:
                    if msg.type == WSMsgType.TEXT:
                        # 文本消息
                        logger.debug(f"[WebSocket代理][{device_id}] 客户端→后台: {msg.data[:100]}...")
                        await backend_ws.send(msg.data)
                    elif msg.type == WSMsgType.BINARY:
                        # 二进制消息（音频数据）
                        logger.debug(f"[WebSocket代理][{device_id}] 客户端→后台: {len(msg.data)} 字节")
                        await backend_ws.send(msg.data)
                    elif msg.type == WSMsgType.ERROR:
                        logger.error(f"[WebSocket代理][{device_id}] 客户端 WebSocket 错误")
                        break
                    elif msg.type == WSMsgType.CLOSE:
                        logger.info(f"[WebSocket代理][{device_id}] 客户端主动关闭连接")
                        break
            except Exception as e:
                logger.error(f"[WebSocket代理][{device_id}] 客户端→后台转发错误: {e}")
            finally:
                logger.debug(f"[WebSocket代理][{device_id}] 客户端→后台通道关闭")
        
        async def forward_backend_to_client():
            """转发：后台 -> 客户端"""
            try:
                async for msg in backend_ws:
                    if isinstance(msg, str):
                        # 文本消息
                        logger.debug(f"[WebSocket代理][{device_id}] 后台→客户端: {msg[:100]}...")
                        await client_ws.send_str(msg)
                    elif isinstance(msg, bytes):
                        # 二进制消息（音频数据）
                        logger.debug(f"[WebSocket代理][{device_id}] 后台→客户端: {len(msg)} 字节")
                        await client_ws.send_bytes(msg)
            except websockets.ConnectionClosed:
                logger.info(f"[WebSocket代理][{device_id}] 后台服务器关闭连接")
            except Exception as e:
                logger.error(f"[WebSocket代理][{device_id}] 后台→客户端转发错误: {e}")
            finally:
                logger.debug(f"[WebSocket代理][{device_id}] 后台→客户端通道关闭")
        
        # 同时运行两个转发任务
        try:
            await asyncio.gather(
                forward_client_to_backend(),
                forward_backend_to_client(),
                return_exceptions=True
            )
        finally:
            logger.info(f"[WebSocket代理][{device_id}] 代理连接关闭")
            # 确保两端都关闭
            if not client_ws.closed:
                await client_ws.close()
            if not backend_ws.closed:
                await backend_ws.close()

    # -------------------- plugin hooks --------------------
    async def on_incoming_json(self, message: Any) -> None:
        if isinstance(message, dict):
            self._broadcaster.publish({"event": "json", "payload": message})

    async def on_device_state_changed(self, state: DeviceState) -> None:
        self._broadcaster.publish(
            {
                "event": "state",
                "payload": getattr(state, "value", state),
            }
        )

    # -------------------- helpers --------------------
    async def _ensure_protocol(self) -> bool:
        try:
            return await self.app.connect_protocol()
        except Exception:
            return False

    @staticmethod
    def _sse_payload(message: dict[str, Any]) -> bytes:
        data = json.dumps(message, ensure_ascii=False)
        return f"data: {data}\n\n".encode("utf-8")
