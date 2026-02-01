"""
Chat MCP Server (호출자 Caller).

역할: hub/mcp를 HTTP로 호출. Central이 채팅 요청을 이 spoke로 라우팅.
Llama·ExaOne은 직접 연결하지 않고 hub를 HTTP로 호출.
"""

from datetime import datetime

from fastmcp import FastMCP

from domain.hub.mcp.http_client import (  # type: ignore
    exaone_generate,
    llama_classify,
)


# ---------------------------------------------------------------------------
# Central 라우팅용 진입점 (hub를 HTTP로 호출)
# ---------------------------------------------------------------------------


def classify(text: str) -> str:
    """시멘틱 분류. hub/mcp HTTP 호출."""
    return llama_classify(text)


def generate(prompt: str, max_tokens: int = 512) -> str:
    """ExaOne 텍스트 생성. hub/mcp HTTP 호출."""
    return exaone_generate(prompt, max_tokens=max_tokens)


# ---------------------------------------------------------------------------
# 도구 구현 (search_documents, get_current_time, calculate)
# ---------------------------------------------------------------------------


def _search_documents_impl(query: str) -> str:
    """문서 검색 (채팅용)."""
    return f"'{query}'에 대한 검색 결과가 없습니다."


def _get_current_time_impl() -> str:
    """현재 시간."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _calculate_impl(expression: str) -> str:
    """수학 계산."""
    try:
        allowed = set("0123456789+-*/().% ")
        if not all(c in allowed for c in expression):
            return "허용되지 않은 문자가 포함되어 있습니다."
        return str(eval(expression))
    except Exception as e:
        return f"계산 오류: {str(e)}"


# ---------------------------------------------------------------------------
# Chat MCP 앱 (get_chat_mcp)
# ---------------------------------------------------------------------------


def get_chat_mcp() -> FastMCP:
    """Chat MCP 앱 반환."""
    mcp = FastMCP("Chat MCP")

    @mcp.tool
    def classify(text: str) -> str:
        """시멘틱 분류. hub HTTP 호출."""
        return llama_classify(text)

    @mcp.tool
    def generate(prompt: str, max_tokens: int = 512) -> str:
        """ExaOne 텍스트 생성. hub HTTP 호출."""
        return exaone_generate(prompt, max_tokens=max_tokens)

    @mcp.tool
    def search_documents(query: str) -> str:
        """문서 검색."""
        return _search_documents_impl(query)

    @mcp.tool
    def get_current_time() -> str:
        """현재 시간 반환."""
        return _get_current_time_impl()

    @mcp.tool
    def calculate(expression: str) -> str:
        """수학 표현식 계산."""
        return _calculate_impl(expression)

    return mcp
