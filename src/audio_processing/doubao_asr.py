#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
豆包流式语音识别模块 (Doubao ASR)
独立模块，用于处理浏览器端发来的音频流并转为文字
"""

import asyncio
import json
import struct
import gzip
from typing import Optional, AsyncGenerator, Dict, Any
from dataclasses import dataclass
import logging

try:
    import websockets
except ImportError:
    websockets = None

logger = logging.getLogger(__name__)


# ==================== 协议常量定义 ====================

class ProtocolVersion:
    """协议版本"""
    V1 = 0b0001


class MessageType:
    """消息类型"""
    CLIENT_FULL_REQUEST = 0b0001
    CLIENT_AUDIO_ONLY_REQUEST = 0b0010
    SERVER_FULL_RESPONSE = 0b1001
    SERVER_ERROR_RESPONSE = 0b1111


class MessageTypeSpecificFlags:
    """消息类型特定标志"""
    NO_SEQUENCE = 0b0000
    POS_SEQUENCE = 0b0001
    NEG_SEQUENCE = 0b0010
    NEG_WITH_SEQUENCE = 0b0011


class SerializationType:
    """序列化类型"""
    NO_SERIALIZATION = 0b0000
    JSON = 0b0001


class CompressionType:
    """压缩类型"""
    NO_COMPRESSION = 0b0000
    GZIP = 0b0001


# ==================== 数据类 ====================

@dataclass
class DoubaoASRConfig:
    """豆包 ASR 配置"""
    app_key: str
    access_key: str
    url: str = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
    sample_rate: int = 16000
    bits: int = 16
    channels: int = 1
    enable_itn: bool = True  # 逆文本归一化
    enable_punc: bool = True  # 标点符号
    enable_ddc: bool = True   # 语气词过滤
    show_utterances: bool = True
    segment_duration_ms: int = 200  # 每段音频时长（毫秒）


@dataclass
class ASRResponse:
    """ASR 响应"""
    code: int = 0
    event: int = 0
    is_last_package: bool = False
    payload_sequence: int = 0
    payload_size: int = 0
    payload_msg: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "event": self.event,
            "is_last_package": self.is_last_package,
            "payload_sequence": self.payload_sequence,
            "payload_size": self.payload_size,
            "payload_msg": self.payload_msg
        }


# ==================== 协议处理类 ====================

class ASRRequestBuilder:
    """ASR 请求构建器"""

    @staticmethod
    def build_header(
        message_type: int = MessageType.CLIENT_FULL_REQUEST,
        message_type_specific_flags: int = MessageTypeSpecificFlags.POS_SEQUENCE,
        serialization_type: int = SerializationType.JSON,
        compression_type: int = CompressionType.GZIP
    ) -> bytes:
        """构建请求头"""
        header = bytearray()
        header.append((ProtocolVersion.V1 << 4) | 1)  # 版本 + 头部长度
        header.append((message_type << 4) | message_type_specific_flags)
        header.append((serialization_type << 4) | compression_type)
        header.append(0x00)  # 保留字节
        return bytes(header)

    @staticmethod
    def build_full_request(seq: int, config: DoubaoASRConfig) -> bytes:
        """构建完整初始化请求"""
        header = ASRRequestBuilder.build_header(
            message_type=MessageType.CLIENT_FULL_REQUEST,
            message_type_specific_flags=MessageTypeSpecificFlags.POS_SEQUENCE
        )

        payload = {
            "user": {
                "uid": "web_client"
            },
            "audio": {
                "format": "pcm",
                "codec": "raw",
                "rate": config.sample_rate,
                "bits": config.bits,
                "channel": config.channels
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": config.enable_itn,
                "enable_punc": config.enable_punc,
                "enable_ddc": config.enable_ddc,
                "show_utterances": config.show_utterances,
                "enable_nonstream": False
            }
        }

        payload_bytes = json.dumps(payload).encode('utf-8')
        compressed_payload = gzip.compress(payload_bytes)
        payload_size = len(compressed_payload)

        request = bytearray()
        request.extend(header)
        request.extend(struct.pack('>i', seq))  # 序列号
        request.extend(struct.pack('>I', payload_size))  # payload 长度
        request.extend(compressed_payload)

        return bytes(request)

    @staticmethod
    def build_audio_request(seq: int, audio_data: bytes, is_last: bool = False) -> bytes:
        """构建音频数据请求"""
        if is_last:
            flags = MessageTypeSpecificFlags.NEG_WITH_SEQUENCE
            seq = -seq
        else:
            flags = MessageTypeSpecificFlags.POS_SEQUENCE

        header = ASRRequestBuilder.build_header(
            message_type=MessageType.CLIENT_AUDIO_ONLY_REQUEST,
            message_type_specific_flags=flags
        )

        compressed_audio = gzip.compress(audio_data)

        request = bytearray()
        request.extend(header)
        request.extend(struct.pack('>i', seq))
        request.extend(struct.pack('>I', len(compressed_audio)))
        request.extend(compressed_audio)

        return bytes(request)


class ASRResponseParser:
    """ASR 响应解析器"""

    @staticmethod
    def parse(msg: bytes) -> ASRResponse:
        """解析服务器响应"""
        response = ASRResponse()

        try:
            # 解析头部
            header_size = msg[0] & 0x0f
            message_type = msg[1] >> 4
            message_type_specific_flags = msg[1] & 0x0f
            serialization_method = msg[2] >> 4
            message_compression = msg[2] & 0x0f

            payload = msg[header_size * 4:]

            # 解析标志
            if message_type_specific_flags & 0x01:
                response.payload_sequence = struct.unpack('>i', payload[:4])[0]
                payload = payload[4:]
            if message_type_specific_flags & 0x02:
                response.is_last_package = True
            if message_type_specific_flags & 0x04:
                response.event = struct.unpack('>i', payload[:4])[0]
                payload = payload[4:]

            # 解析消息类型
            if message_type == MessageType.SERVER_FULL_RESPONSE:
                response.payload_size = struct.unpack('>I', payload[:4])[0]
                payload = payload[4:]
            elif message_type == MessageType.SERVER_ERROR_RESPONSE:
                response.code = struct.unpack('>i', payload[:4])[0]
                response.payload_size = struct.unpack('>I', payload[4:8])[0]
                payload = payload[8:]

            if not payload:
                return response

            # 解压缩
            if message_compression == CompressionType.GZIP:
                try:
                    payload = gzip.decompress(payload)
                except Exception as e:
                    logger.error(f"解压缩失败: {e}")
                    return response

            # 解析 JSON
            if serialization_method == SerializationType.JSON:
                try:
                    response.payload_msg = json.loads(payload.decode('utf-8'))
                except Exception as e:
                    logger.error(f"解析 JSON 失败: {e}")

        except Exception as e:
            logger.error(f"解析响应失败: {e}")

        return response


# ==================== 主要的 ASR 客户端 ====================

class DoubaoASRClient:
    """豆包 ASR 客户端"""

    def __init__(self, config: DoubaoASRConfig):
        self.config = config
        self.seq = 1
        self.ws: Optional[Any] = None

    async def connect(self) -> bool:
        """连接到豆包服务器"""
        if websockets is None:
            logger.error("websockets 库未安装，无法使用豆包 ASR")
            return False

        try:
            headers = {
                "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
                "X-Api-Request-Id": f"web_client_{self.seq}",
                "X-Api-Access-Key": self.config.access_key,
                "X-Api-App-Key": self.config.app_key
            }

            logger.info(f"正在连接豆包 ASR 服务器: {self.config.url}")
            self.ws = await websockets.connect(self.config.url, extra_headers=headers)
            logger.info("✅ 已连接到豆包 ASR 服务器")
            return True

        except Exception as e:
            logger.error(f"连接豆包服务器失败: {e}")
            return False

    async def send_init_request(self) -> bool:
        """发送初始化请求"""
        try:
            request = ASRRequestBuilder.build_full_request(self.seq, self.config)
            await self.ws.send(request)
            logger.info(f"已发送初始化请求 (seq={self.seq})")
            self.seq += 1

            # 等待初始化响应
            response_data = await self.ws.recv()
            response = ASRResponseParser.parse(response_data)
            
            if response.code != 0:
                logger.error(f"初始化失败: {response.to_dict()}")
                return False

            logger.info("✅ 初始化成功")
            return True

        except Exception as e:
            logger.error(f"发送初始化请求失败: {e}")
            return False

    async def send_audio_chunk(self, audio_data: bytes, is_last: bool = False) -> None:
        """发送音频数据块"""
        try:
            request = ASRRequestBuilder.build_audio_request(self.seq, audio_data, is_last)
            await self.ws.send(request)
            logger.debug(f"已发送音频块 (seq={self.seq}, size={len(audio_data)}, last={is_last})")
            
            if not is_last:
                self.seq += 1

        except Exception as e:
            logger.error(f"发送音频数据失败: {e}")

    async def receive_results(self) -> AsyncGenerator[ASRResponse, None]:
        """接收识别结果"""
        try:
            while True:
                response_data = await self.ws.recv()
                response = ASRResponseParser.parse(response_data)
                
                logger.debug(f"收到响应: seq={response.payload_sequence}, last={response.is_last_package}")
                
                if response.payload_msg:
                    yield response
                
                if response.is_last_package or response.code != 0:
                    break

        except Exception as e:
            logger.error(f"接收结果时出错: {e}")

    async def close(self) -> None:
        """关闭连接"""
        if self.ws:
            try:
                await self.ws.close()
                logger.info("已关闭豆包 ASR 连接")
            except Exception as e:
                logger.error(f"关闭连接时出错: {e}")


# ==================== 便捷函数 ====================

async def recognize_audio_stream(
    config: DoubaoASRConfig,
    audio_chunks: AsyncGenerator[bytes, None]
) -> AsyncGenerator[str, None]:
    """
    识别音频流并返回文本
    
    Args:
        config: 豆包配置
        audio_chunks: 音频数据块生成器
        
    Yields:
        识别出的文本（增量）
    """
    client = DoubaoASRClient(config)
    
    try:
        # 连接并初始化
        if not await client.connect():
            logger.error("无法连接到豆包服务器")
            return
            
        if not await client.send_init_request():
            logger.error("初始化失败")
            return

        # 创建接收任务
        async def receiver():
            async for response in client.receive_results():
                if response.payload_msg:
                    # 提取文本
                    result = response.payload_msg.get('result', {})
                    text = result.get('text', '')
                    if text:
                        yield text

        # 创建发送任务
        async def sender():
            chunk_count = 0
            async for chunk in audio_chunks:
                chunk_count += 1
                await client.send_audio_chunk(chunk, is_last=False)
                # 控制发送速率
                await asyncio.sleep(config.segment_duration_ms / 1000)
            
            # 发送结束标记
            await client.send_audio_chunk(b'', is_last=True)
            logger.info(f"已发送所有音频数据 (共 {chunk_count} 块)")

        # 并行执行发送和接收
        async for text in receiver():
            asyncio.create_task(sender())
            yield text

    except Exception as e:
        logger.error(f"识别过程出错: {e}")
    finally:
        await client.close()
