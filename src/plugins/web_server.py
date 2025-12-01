import asyncio
import contextlib
import json
import os
from pathlib import Path
from typing import Any

from aiohttp import web

from src.constants.constants import AbortReason, DeviceState
from src.plugins.base import Plugin
from src.utils.logging_config import get_logger

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
