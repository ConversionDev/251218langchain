"""MCP call_tool 결과 파싱 등 공통 유틸. Hub·Spoke 모두 사용."""

import json
import os
from typing import Any


def result_to_str(result: Any) -> str:
    """call_tool 결과에서 문자열 추출 (content 블록 또는 data)."""
    if result is None:
        return ""
    if hasattr(result, "content") and result.content:
        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts) if parts else ""
    if hasattr(result, "data") and result.data is not None:
        if isinstance(result.data, str):
            return result.data
        return json.dumps(result.data, ensure_ascii=False)
    return str(result)


def get_chat_mcp_url() -> str:
    try:
        from core.config import get_settings  # type: ignore
        return get_settings().chat_mcp_url
    except Exception:
        return os.getenv("CHAT_MCP_URL", "http://127.0.0.1:8000/internal/mcp/chat/server")


def get_spam_mcp_url() -> str:
    try:
        from core.config import get_settings  # type: ignore
        return get_settings().spam_mcp_url
    except Exception:
        return os.getenv("SPAM_MCP_URL", "http://127.0.0.1:9021/server")


def get_soccer_mcp_url() -> str:
    try:
        from core.config import get_settings  # type: ignore
        return get_settings().soccer_mcp_url
    except Exception:
        return os.getenv("SOCCER_MCP_URL", "http://127.0.0.1:9031/server")


def get_chat_spoke_mcp_url() -> str:
    try:
        from core.config import get_settings  # type: ignore
        return get_settings().chat_spoke_mcp_url
    except Exception:
        return os.getenv("CHAT_SPOKE_MCP_URL", "http://127.0.0.1:8000/internal/mcp/chat-spoke/server")


def get_spam_spoke_mcp_url() -> str:
    try:
        from core.config import get_settings  # type: ignore
        return get_settings().spam_spoke_mcp_url
    except Exception:
        return os.getenv("SPAM_SPOKE_MCP_URL", "http://127.0.0.1:9022/server")


def get_soccer_spoke_mcp_url() -> str:
    try:
        from core.config import get_settings  # type: ignore
        return get_settings().soccer_spoke_mcp_url
    except Exception:
        return os.getenv("SOCCER_SPOKE_MCP_URL", "http://127.0.0.1:9032/server")
