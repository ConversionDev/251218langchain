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


@mcp_proxy.tool
async def define(term: str) -> str:
    """용어 정의/설명 검색. Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_chat_spoke_mcp_url()) as client:
        result = await client.call_tool("define", {"term": term})
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

    @mcp_spoke.tool
    def define(term: str) -> str:
        """용어 정의/설명을 문서에서 검색해 반환."""
        return _search_documents_impl(term)

    return mcp_spoke


# ---------------------------------------------------------------------------
# in-process 호출 (main.py에 Chat MCP 마운트되어 있으므로 HTTP 없이 직접 호출)
# ---------------------------------------------------------------------------


def _invoke_chat_spoke_tool(name: str, args: dict) -> str:
    """Spoke 도구를 HTTP 없이 직접 실행."""
    a = args or {}
    if name == "search_documents":
        return _search_documents_impl(str(a.get("query", "")))
    if name == "get_current_time":
        return _get_current_time_impl()
    if name == "calculate":
        return _calculate_impl(str(a.get("expression", "")))
    if name == "define":
        return _search_documents_impl(str(a.get("term", "")))
    if name == "classify":
        return llama_classify(str(a.get("text", "")))
    if name == "generate":
        return exaone_generate(str(a.get("prompt", "")), max_tokens=int(a.get("max_tokens", 512)))
    return f"알 수 없는 도구: {name}"


async def _invoke_chat_mcp_tool(name: str, args: dict) -> str:
    """Chat MCP 도구를 HTTP 없이 직접 실행 (graph 도구: search_documents, get_current_time, calculate, define 등)."""
    return _invoke_chat_spoke_tool(name, args)


# ---------------------------------------------------------------------------
# 동일 프로세스 마운트용 ASGI 앱 (Hub 8000에 /internal/mcp/chat, /internal/mcp/chat-spoke)
# ---------------------------------------------------------------------------


def get_chat_mcp_http_app():
    """Chat MCP FastAPI 앱. mount('/internal/mcp/chat', app) 시 MCP 엔드포인트: .../internal/mcp/chat/server"""
    from fastapi import FastAPI  # type: ignore

    app = FastAPI(title="Chat MCP", tags=["Chat MCP"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "Chat MCP"}

    mcp_asgi = mcp_proxy.http_app(path="/server")
    app.mount("/server", mcp_asgi)
    return app


def get_chat_spoke_http_app():
    """Chat Spoke FastAPI 앱. mount('/internal/mcp/chat-spoke', app) 시 MCP 엔드포인트: .../internal/mcp/chat-spoke/server"""
    from fastapi import FastAPI  # type: ignore

    app = FastAPI(title="Chat Spoke MCP", tags=["Chat Spoke MCP"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "Chat Spoke MCP"}

    spoke = get_chat_spoke_mcp()
    mcp_asgi = spoke.http_app(path="/server")
    app.mount("/server", mcp_asgi)
    return app
