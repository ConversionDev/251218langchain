"""
Central Control Server (Hub MCP) - NEXUS

역할: FastMCP 중앙 허브 — 교통경찰.
- 모든 MCP 요청을 받아 spokes(chat, spam)로 라우팅
- spokes가 hub를 HTTP로 호출 (Llama·ExaOne 직접 연결 없음)
"""

import json

from fastmcp import FastMCP

mcp = FastMCP("Central MCP (Llama + ExaOne)")


# ---------------------------------------------------------------------------
# Chat Spoke로 라우팅 (spoke → hub HTTP)
# ---------------------------------------------------------------------------


@mcp.tool
def classify_with_llama(text: str) -> str:
    """Llama 시멘틱 분류. Chat Spoke 경유 → hub HTTP."""
    from domain.spokes.chat.mcp.chat_server import classify  # type: ignore

    return classify(text)


@mcp.tool
def generate_with_exaone(prompt: str, max_tokens: int = 512) -> str:
    """ExaOne 텍스트 생성. Chat Spoke 경유 → hub HTTP."""
    from domain.spokes.chat.mcp.chat_server import generate  # type: ignore

    return generate(prompt, max_tokens)


@mcp.tool
def classify_then_generate(
    text: str,
    generate_prompt: str,
    max_tokens: int = 512,
) -> dict:
    """Llama 분류 후 ExaOne 생성. Chat Spoke 경유. {text} 치환 지원."""
    from domain.spokes.chat.mcp.chat_server import classify, generate  # type: ignore

    classification = classify(text)
    result: dict = {
        "classification": classification,
        "generated": None,
        "skipped": False,
    }
    if classification == "BLOCK":
        result["skipped"] = True
        result["generated"] = "(BLOCK으로 생성 생략)"
        return result
    full_prompt = generate_prompt.strip()
    if "{text}" in full_prompt:
        full_prompt = full_prompt.replace("{text}", (text or "").strip())
    result["generated"] = generate(full_prompt, max_tokens)
    return result


# ---------------------------------------------------------------------------
# Spam Spoke로 라우팅 (spoke → hub HTTP)
# ---------------------------------------------------------------------------


@mcp.tool
def analyze_email(
    subject: str,
    sender: str,
    body: str = "",
    recipient: str = "",
    date: str = "",
    attachments: list | None = None,
    headers: dict | None = None,
    policy_context: str = "",
) -> str:
    """ExaOne 이메일 분석. Spam Spoke 경유 → hub HTTP."""
    from domain.spokes.spam.mcp.spam_server import _analyze_email_impl  # type: ignore

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
def classify_spam(email_metadata: dict) -> str:
    """Llama 스팸 분류. Spam Spoke 경유 → hub HTTP."""
    from domain.spokes.spam.mcp.spam_server import _classify_spam_impl  # type: ignore

    result = _classify_spam_impl(email_metadata)
    return json.dumps(result, ensure_ascii=False)


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
