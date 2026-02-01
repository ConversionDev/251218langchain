"""Spam MCP - 스팸 관련 도구만 노출. Hub LLM 호출."""

from .spam_server import get_spam_mcp

__all__ = ["get_spam_mcp"]
