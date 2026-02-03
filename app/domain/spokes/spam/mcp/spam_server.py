"""
Spam MCP Server (역할 통합).

- MCP: Central이 call_tool로 호출. Spoke로 call_tool 위임만 수행.
- Spoke: Spam MCP가 call_tool로 호출. analyze_email/classify_spam 실행.
- Llama·ExaOne은 hub HTTP로 호출.
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from domain.hub.mcp.http_client import (  # type: ignore
    exaone_analyze_email,
    llama_classify,
    llama_classify_spam,
)
from domain.hub.mcp.utils import get_spam_spoke_mcp_url, result_to_str  # type: ignore


# ---------------------------------------------------------------------------
# Spoke 구현 (실행)
# ---------------------------------------------------------------------------


def _analyze_email_impl(
    subject: str,
    sender: str,
    body: Optional[str] = None,
    recipient: Optional[str] = None,
    date: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    headers: Optional[Dict[str, Any]] = None,
    policy_context: Optional[str] = None,
) -> str:
    """ExaOne 이메일 분석. hub HTTP 호출."""
    return exaone_analyze_email(
        subject=subject,
        sender=sender,
        body=body or "",
        recipient=recipient or "",
        date=date or "",
        attachments=attachments,
        headers=headers,
        policy_context=policy_context or "",
    )


def _classify_spam_impl(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Llama 스팸 분류. hub HTTP 호출."""
    return llama_classify_spam(email_metadata)


# ---------------------------------------------------------------------------
# MCP Proxy (Central → Spoke call_tool)
# ---------------------------------------------------------------------------

mcp_proxy = FastMCP("Spam MCP (Routing + Spoke Proxy)")


@mcp_proxy.tool
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
    """ExaOne 이메일 분석. Spam Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
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
    async with Client(get_spam_spoke_mcp_url()) as client:
        result = await client.call_tool("analyze_email", args)
        return result_to_str(result)


@mcp_proxy.tool
async def classify_spam(email_metadata: dict) -> str:
    """Llama 스팸 분류. Spam Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_spam_spoke_mcp_url()) as client:
        result = await client.call_tool("classify_spam", {"email_metadata": email_metadata})
        return result_to_str(result)


@mcp_proxy.tool
async def classify_routing(text: str) -> str:
    """규칙/정책 라우팅용 시멘틱 분류 (RULE_BASED | POLICY_BASED). Spam Spoke call_tool."""
    from fastmcp.client import Client  # type: ignore
    async with Client(get_spam_spoke_mcp_url()) as client:
        result = await client.call_tool("classify_routing", {"text": text})
        return result_to_str(result)


# ---------------------------------------------------------------------------
# Spoke MCP 앱 (Spam MCP가 call_tool로 호출)
# ---------------------------------------------------------------------------


def get_spam_mcp() -> FastMCP:
    """Spam MCP 앱 반환 (Central이 call_tool로 호출하는 대상)."""
    return mcp_proxy


def get_spam_spoke_mcp() -> FastMCP:
    """Spam Spoke MCP 앱 반환 (Spam MCP가 call_tool로 호출하는 대상)."""
    import json
    mcp_spoke = FastMCP("Spam Spoke MCP")

    @mcp_spoke.tool
    def classify_routing(text: str) -> str:
        """규칙/정책 라우팅용 시멘틱 분류. Hub Llama HTTP 호출."""
        return llama_classify(text)

    @mcp_spoke.tool
    def analyze_email(
        subject: str,
        sender: str,
        body: Optional[str] = None,
        recipient: Optional[str] = None,
        date: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        headers: Optional[Dict[str, Any]] = None,
        policy_context: Optional[str] = None,
    ) -> str:
        return _analyze_email_impl(
            subject=subject,
            sender=sender,
            body=body,
            recipient=recipient,
            date=date,
            attachments=attachments,
            headers=headers,
            policy_context=policy_context,
        )

    @mcp_spoke.tool
    def classify_spam(email_metadata: Dict[str, Any]) -> str:
        result = _classify_spam_impl(email_metadata)
        return json.dumps(result, ensure_ascii=False)

    return mcp_spoke
