"""
Chat MCP Server (역할 통합).

- MCP: Central이 call_tool로 호출. Spoke로 call_tool 위임만 수행.
- Spoke: Chat MCP가 call_tool로 호출. classify/generate/search_documents 등 실행.
- Llama·ExaOne은 hub HTTP로 호출.
"""

from datetime import datetime

from fastmcp import FastMCP

from domain.hub.mcp.http_client import (  # type: ignore
    exaone_generate,
    llama_classify,
)
from domain.hub.mcp.utils import get_chat_spoke_mcp_url, result_to_str  # type: ignore


# ---------------------------------------------------------------------------
# Spoke 구현 (실행)
# ---------------------------------------------------------------------------

def classify(text: str) -> str:
    """시멘틱 분류. hub HTTP 호출."""
    return llama_classify(text)


def generate(prompt: str, max_tokens: int = 512) -> str:
    """ExaOne 텍스트 생성. hub HTTP 호출."""
    return exaone_generate(prompt, max_tokens=max_tokens)


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
# MCP Proxy (Central → Spoke call_tool)
# ---------------------------------------------------------------------------

mcp_proxy = FastMCP("Chat MCP (Routing + Spoke Proxy)")


@mcp_proxy.tool
async def classify_with_llama(text: str) -> str:
    """Llama 시멘틱 분류. Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_chat_spoke_mcp_url()) as client:
        result = await client.call_tool("classify", {"text": text})
        return result_to_str(result)


@mcp_proxy.tool
async def generate_with_exaone(prompt: str, max_tokens: int = 512) -> str:
    """ExaOne 텍스트 생성. Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_chat_spoke_mcp_url()) as client:
        result = await client.call_tool("generate", {"prompt": prompt, "max_tokens": max_tokens})
        return result_to_str(result)


@mcp_proxy.tool
async def classify_then_generate(
    text: str,
    generate_prompt: str,
    max_tokens: int = 512,
) -> dict:
    """Llama 분류 후 ExaOne 생성. Chat Spoke call_tool. {text} 치환 지원."""
    from fastmcp.client import Client  # type: ignore
    url = get_chat_spoke_mcp_url()
    async with Client(url) as client:
        classification_result = await client.call_tool("classify", {"text": text})
        classification = result_to_str(classification_result)
        result_dict: dict = {"classification": classification, "generated": None, "skipped": False}
        if classification == "BLOCK":
            result_dict["skipped"] = True
            result_dict["generated"] = "(BLOCK으로 생성 생략)"
            return result_dict
        full_prompt = generate_prompt.strip().replace("{text}", (text or "").strip())
        gen_result = await client.call_tool("generate", {"prompt": full_prompt, "max_tokens": max_tokens})
        result_dict["generated"] = result_to_str(gen_result)
        return result_dict


@mcp_proxy.tool
async def search_documents(query: str) -> str:
    """문서 검색. Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_chat_spoke_mcp_url()) as client:
        result = await client.call_tool("search_documents", {"query": query})
        return result_to_str(result)


@mcp_proxy.tool
async def get_current_time() -> str:
    """현재 시간. Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_chat_spoke_mcp_url()) as client:
        result = await client.call_tool("get_current_time", {})
        return result_to_str(result)


@mcp_proxy.tool
async def calculate(expression: str) -> str:
    """수학 계산. Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_chat_spoke_mcp_url()) as client:
        result = await client.call_tool("calculate", {"expression": expression})
        return result_to_str(result)


# ---------------------------------------------------------------------------
# Spoke MCP 앱 (Chat MCP가 call_tool로 호출)
# ---------------------------------------------------------------------------


def get_chat_mcp() -> FastMCP:
    """Chat MCP 앱 반환 (Central이 call_tool로 호출하는 대상)."""
    return mcp_proxy


def get_chat_spoke_mcp() -> FastMCP:
    """Chat Spoke MCP 앱 (Chat MCP가 call_tool로 호출하는 대상)."""
    mcp_spoke = FastMCP("Chat Spoke MCP")

    @mcp_spoke.tool
    def classify(text: str) -> str:
        return llama_classify(text)

    @mcp_spoke.tool
    def generate(prompt: str, max_tokens: int = 512) -> str:
        return exaone_generate(prompt, max_tokens=max_tokens)

    @mcp_spoke.tool
    def search_documents(query: str) -> str:
        return _search_documents_impl(query)

    @mcp_spoke.tool
    def get_current_time() -> str:
        return _get_current_time_impl()

    @mcp_spoke.tool
    def calculate(expression: str) -> str:
        return _calculate_impl(expression)

    return mcp_spoke
