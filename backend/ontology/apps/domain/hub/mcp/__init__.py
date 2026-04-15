"""
v1 MCP 도메인: ExaOne(채팅) + LLaMA(스팸) FastMCP.

- 채팅: ExaOne만 사용. LLaMA는 채팅 경로에서 제거됨.
- LLaMA: 런타임에서는 스팸 분류(classify_spam)만 사용.
- generate_with_exaone / classify_then_generate: ExaOne 텍스트 생성.
"""

from .central_control_server import mcp  # type: ignore[import-untyped]

__all__ = ["mcp"]
