"""
v1 MCP 도메인: Llama + ExaOne 연결 FastMCP.

- classify_with_llama: Llama 3.2(시멘틱 분류기)로 텍스트 분류
- generate_with_exaone: ExaOne 7.8B로 텍스트 생성
- classify_then_generate: 분류 후 ExaOne으로 생성 파이프라인
"""

from .app import mcp  # type: ignore[import-untyped]

__all__ = ["mcp"]
