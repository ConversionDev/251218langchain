"""
Central Control Server (Hub MCP) - NEXUS

역할: FastMCP 중앙 허브 — 교통경찰.
- 모든 MCP 요청을 받아 Chat MCP / Spam MCP / Soccer MCP로 call_tool 위임만 수행.
- 무거운 모델·Spoke 직접 호출 없음. 각 도메인 MCP가 Spoke로 call_tool.
"""

from typing import Any, Dict

from fastmcp import FastMCP

from domain.hub.mcp.utils import (  # type: ignore
    get_chat_mcp_url,
    get_soccer_mcp_url,
    get_spam_mcp_url,
    result_to_str,
)

mcp = FastMCP("Central MCP (Llama + ExaOne)")


# ---------------------------------------------------------------------------
# Chat MCP로 call_tool 위임
# ---------------------------------------------------------------------------


@mcp.tool
async def classify_with_llama(text: str) -> str:
    """Llama 시멘틱 분류. Chat MCP → Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    url = get_chat_mcp_url()
    async with Client(url) as client:
        result = await client.call_tool("classify_with_llama", {"text": text})
        return result_to_str(result)


@mcp.tool
async def generate_with_exaone(prompt: str, max_tokens: int = 512) -> str:
    """ExaOne 텍스트 생성. Chat MCP → Chat Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    url = get_chat_mcp_url()
    async with Client(url) as client:
        result = await client.call_tool(
            "generate_with_exaone",
            {"prompt": prompt, "max_tokens": max_tokens},
        )
        return result_to_str(result)


@mcp.tool
async def classify_then_generate(
    text: str,
    generate_prompt: str,
    max_tokens: int = 512,
) -> dict:
    """Llama 분류 후 ExaOne 생성. Chat MCP → Chat Spoke call_tool. {text} 치환 지원."""
    from fastmcp.client import Client  # type: ignore
    url = get_chat_mcp_url()
    async with Client(url) as client:
        result = await client.call_tool(
            "classify_then_generate",
            {
                "text": text,
                "generate_prompt": generate_prompt,
                "max_tokens": max_tokens,
            },
        )
        if hasattr(result, "data") and isinstance(result.data, dict):
            return result.data
        if hasattr(result, "content") and result.content:
            return {"classification": "", "generated": result_to_str(result), "skipped": False}
        return {"classification": "", "generated": "", "skipped": False}


# ---------------------------------------------------------------------------
# Spam MCP로 call_tool 위임
# ---------------------------------------------------------------------------


@mcp.tool
async def analyze_email(
    subject: str,
    sender: str,
    body: str = "",
    recipient: str = "",
    date: str = "",
    attachments: list | None = None,
    headers: dict | None = None,
    policy_context: str = "",
) -> str:
    """ExaOne 이메일 분석. Spam MCP → Spam Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    url = get_spam_mcp_url()
    args: Dict[str, Any] = {
        "subject": subject,
        "sender": sender,
        "body": body,
        "recipient": recipient,
        "date": date,
        "policy_context": policy_context,
    }
    if attachments is not None:
        args["attachments"] = attachments
    if headers is not None:
        args["headers"] = headers
    async with Client(url) as client:
        result = await client.call_tool("analyze_email", args)
        return result_to_str(result)


@mcp.tool
async def classify_spam(email_metadata: dict) -> str:
    """Llama 스팸 분류. Spam MCP → Spam Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    url = get_spam_mcp_url()
    async with Client(url) as client:
        result = await client.call_tool("classify_spam", {"email_metadata": email_metadata})
        return result_to_str(result)


# ---------------------------------------------------------------------------
# Soccer MCP로 call_tool 위임
# ---------------------------------------------------------------------------


@mcp.tool
async def soccer_route(question: str) -> str:
    """질문을 어느 오케스트레이터로 보낼지 결정(라우팅만). Soccer MCP call_tool."""
    from fastmcp.client import Client  # type: ignore
    url = get_soccer_mcp_url()
    async with Client(url) as client:
        result = await client.call_tool("soccer_route", {"question": question})
        return result_to_str(result)


@mcp.tool
async def soccer_call(
    orchestrator: str,
    tool: str,
    arguments: Dict[str, Any] | None = None,
) -> Any:
    """중앙 → Soccer MCP → Spoke call_tool 프록시."""
    from fastmcp.client import Client  # type: ignore
    url = get_soccer_mcp_url()
    async with Client(url) as client:
        result = await client.call_tool(
            "soccer_call",
            {"orchestrator": orchestrator, "tool": tool, "arguments": arguments or {}},
        )
        if hasattr(result, "data") and result.data is not None:
            return result.data
        return result_to_str(result)


@mcp.tool
async def soccer_route_and_call(
    question: str,
    tool: str,
    arguments: Dict[str, Any] | None = None,
) -> Any:
    """라우팅 후 Soccer MCP → Spoke call_tool까지 한 번에 수행."""
    from fastmcp.client import Client  # type: ignore
    url = get_soccer_mcp_url()
    async with Client(url) as client:
        result = await client.call_tool(
            "soccer_route_and_call",
            {"question": question, "tool": tool, "arguments": arguments or {}},
        )
        if hasattr(result, "data") and result.data is not None:
            return result.data
        return result_to_str(result)


def get_http_app():
    """Fast MCP ASGI 앱: GET /health + MCP 프로토콜(/server)."""
    from fastapi import FastAPI  # type: ignore

    wrapper = FastAPI(title="MCP (Llama + ExaOne)", tags=["MCP"])

    @wrapper.get("/health")
    async def health():
        return {"status": "ok", "service": "MCP", "protocol": "Fast MCP"}

    mcp_asgi = mcp.http_app(path="/server")
    wrapper.mount("/server", mcp_asgi)

    return wrapper
