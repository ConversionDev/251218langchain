"""
Hub MCP HTTP 클라이언트.

spokes(chat, spam)가 hub/mcp를 HTTP로 호출할 때 사용.
hub/mcp = Llama·ExaOne 호출 수신 (receiver), spokes = 호출하는 쪽 (caller).
"""

import json
from typing import Any, Dict, Optional

import httpx

from core.config import get_settings  # type: ignore


def _get_hub_base_url() -> str:
    """Hub MCP Base URL (trailing slash 제거)."""
    return get_settings().hub_service_url.rstrip("/")


# ---------------------------------------------------------------------------
# Llama HTTP 클라이언트
# ---------------------------------------------------------------------------


def llama_classify(text: str, *, timeout: float = 30.0) -> str:
    """Llama 시멘틱 분류. HTTP POST hub/internal/llama/classify."""
    base = _get_hub_base_url()
    url = f"{base}/internal/llama/classify"
    payload = {"text": text}
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", "POLICY_BASED")
    except Exception as e:
        print(f"[WARNING] Llama classify HTTP 실패, 기본값 사용: {e}")
        return "POLICY_BASED"


def llama_classify_spam(email_metadata: Dict[str, Any], *, timeout: float = 60.0) -> Dict[str, Any]:
    """Llama 스팸 분류. HTTP POST hub/internal/llama/classify_spam."""
    base = _get_hub_base_url()
    url = f"{base}/internal/llama/classify_spam"
    payload = {"email_metadata": email_metadata}
    default = {"spam_prob": 0.5, "confidence": "low", "label": "UNCERTAIN"}
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", default)
    except Exception as e:
        print(f"[WARNING] Llama classify_spam HTTP 실패, 기본값 사용: {e}")
        return default


# ---------------------------------------------------------------------------
# ExaOne HTTP 클라이언트
# ---------------------------------------------------------------------------


def exaone_generate(prompt: str, max_tokens: int = 512, *, timeout: float = 120.0) -> str:
    """ExaOne 텍스트 생성. HTTP POST hub/internal/exaone/generate."""
    base = _get_hub_base_url()
    url = f"{base}/internal/exaone/generate"
    payload = {"prompt": prompt, "max_tokens": max_tokens}
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", f"[ExaOne 오류] 빈 응답")
    except Exception as e:
        return f"[ExaOne HTTP 오류] {e}"


def exaone_analyze_email(
    subject: str,
    sender: str,
    body: str = "",
    recipient: str = "",
    date: str = "",
    attachments: Optional[list] = None,
    headers: Optional[Dict[str, Any]] = None,
    policy_context: str = "",
    *,
    timeout: float = 120.0,
) -> str:
    """ExaOne 이메일 분석. HTTP POST hub/internal/exaone/analyze_email."""
    base = _get_hub_base_url()
    url = f"{base}/internal/exaone/analyze_email"
    payload = {
        "subject": subject,
        "sender": sender,
        "body": body,
        "recipient": recipient,
        "date": date,
        "attachments": attachments or [],
        "headers": headers or {},
        "policy_context": policy_context,
    }
    default_result = {
        "raw_output": "HTTP 오류",
        "parsed": {
            "is_spam": False,
            "confidence": "low",
            "risk_level": "low",
            "risk_codes": [],
            "analysis": "분석 실패",
            "recommendation": "수동 검토 필요",
        },
        "risk_codes": [],
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            result = data.get("result", default_result)
            return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps(default_result, ensure_ascii=False)
