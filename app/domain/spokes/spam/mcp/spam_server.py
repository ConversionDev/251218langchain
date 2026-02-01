"""
Spam MCP Server (호출자 Caller).

역할: hub/mcp를 HTTP로 호출. Central이 스팸 요청을 이 spoke로 라우팅.
Llama·ExaOne은 직접 연결하지 않고 hub를 HTTP로 호출.
"""

import json
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from domain.hub.mcp.http_client import (  # type: ignore
    exaone_analyze_email,
    llama_classify_spam,
)


# ---------------------------------------------------------------------------
# 구현 (hub HTTP 호출)
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
    """ExaOne 이메일 분석. hub/mcp HTTP 호출."""
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
    """Llama 스팸 분류. hub/mcp HTTP 호출."""
    return llama_classify_spam(email_metadata)


# ---------------------------------------------------------------------------
# Spam MCP 앱 (get_spam_mcp)
# ---------------------------------------------------------------------------


def get_spam_mcp() -> FastMCP:
    """Spam MCP 앱 반환."""
    mcp = FastMCP("Spam MCP")

    @mcp.tool
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
        """ExaOne으로 이메일 분석. hub HTTP 호출."""
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

    @mcp.tool
    def classify_spam(email_metadata: Dict[str, Any]) -> str:
        """Llama로 스팸 분류. hub HTTP 호출."""
        result = _classify_spam_impl(email_metadata)
        return json.dumps(result, ensure_ascii=False)

    return mcp
