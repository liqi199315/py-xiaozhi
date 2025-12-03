"""
WebSocket 认证辅助模块
支持从 Header 和 URL 参数两种方式读取 token
"""

from urllib.parse import urlparse, parse_qs
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def extract_token_from_request(path: str, headers: dict) -> tuple[str, str, str]:
    """
    从 WebSocket 请求中提取认证信息
    
    支持两种方式：
    1. Header 方式（Python 客户端）: Authorization: Bearer {token}
    2. URL 参数方式（Web 浏览器）: ?token=xxx&device_id=xxx&client_id=xxx
    
    Args:
        path: WebSocket 请求路径，可能包含查询参数
        headers: 请求头字典
        
    Returns:
        tuple: (token, device_id, client_id)
    """
    token = None
    device_id = None
    client_id = None
    
    # 方法 1: 从 URL 参数读取（用于浏览器 WebSocket）
    parsed_url = urlparse(path)
    query_params = parse_qs(parsed_url.query)
    
    # 尝试多种可能的参数名
    if 'token' in query_params:
        token = query_params['token'][0]
        logger.info("从 URL 参数 'token' 读取到 token")
    elif 'access_token' in query_params:
        token = query_params['access_token'][0]
        logger.info("从 URL 参数 'access_token' 读取到 token")
    
    if 'device_id' in query_params:
        device_id = query_params['device_id'][0]
        logger.debug(f"从 URL 参数读取到 device_id: {device_id}")
    
    if 'client_id' in query_params:
        client_id = query_params['client_id'][0]
        logger.debug(f"从 URL 参数读取到 client_id: {client_id}")
    
    # 方法 2: 从 Header 读取（用于 Python 客户端）
    if not token and 'Authorization' in headers:
        auth_header = headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # 去掉 "Bearer " 前缀
            logger.info("从 Authorization Header 读取到 token")
    
    if not device_id and 'Device-Id' in headers:
        device_id = headers['Device-Id']
        logger.debug(f"从 Header 读取到 device_id: {device_id}")
    
    if not client_id and 'Client-Id' in headers:
        client_id = headers['Client-Id']
        logger.debug(f"从 Header 读取到 client_id: {client_id}")
    
    # 记录结果
    if token:
        # 只显示 token 的前后几位，中间用 * 隐藏
        masked_token = f"{token[:8]}...{token[-8:]}" if len(token) > 16 else "***"
        logger.info(f"✅ Token 提取成功: {masked_token}")
    else:
        logger.warning("⚠️ 未能提取到 token")
    
    return token, device_id, client_id


def validate_token(token: str, expected_token: str = None) -> bool:
    """
    验证 token 是否有效
    
    Args:
        token: 待验证的 token
        expected_token: 期望的 token 值（可选）
        
    Returns:
        bool: token 是否有效
    """
    if not token:
        logger.warning("Token 为空")
        return False
    
    # 排除测试 token
    if token == "test-token":
        logger.warning("使用了测试 token，认证失败")
        return False
    
    # 如果提供了期望值，进行比对
    if expected_token:
        is_valid = token == expected_token
        if not is_valid:
            logger.warning("Token 不匹配")
        return is_valid
    
    # 基本验证：长度检查
    if len(token) < 10:
        logger.warning(f"Token 长度过短: {len(token)}")
        return False
    
    logger.info("✅ Token 验证通过")
    return True
