"""
채팅 그래프용 도구 정의 (TOOLS, TOOL_MAP).

graph_orchestrator·chat_agents에서 공유하며, 순환 import를 피하기 위해 단일 모듈로 분리합니다.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool


@tool
def analyze_with_exaone(
    subject: str,
    sender: str,
    body: Optional[str] = None,
    recipient: Optional[str] = None,
    date: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    headers: Optional[Dict[str, Any]] = None,
    _policy_context: Optional[str] = None,
) -> str:
    """EXAONE을 사용하여 이메일을 분석합니다. Hub ExaOne Adapter 경유."""
    try:
        from domain.v1.hub.llm import analyze_email  # type: ignore

        result = analyze_email(
            subject=subject,
            sender=sender,
            body=body,
            recipient=recipient,
            date=date,
            attachments=attachments,
            headers=headers,
            policy_context=_policy_context,
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        error_result = {
            "raw_output": f"EXAONE 분석 오류: {str(e)}",
            "parsed": {
                "is_spam": False,
                "confidence": "low",
                "risk_level": "low",
                "risk_codes": [],
                "analysis": f"분석 실패: {str(e)}",
                "recommendation": "수동 검토 필요",
            },
            "risk_codes": [],
        }
        return json.dumps(error_result, ensure_ascii=False)


@tool
def search_documents(query: str) -> str:
    """문서에서 관련 정보를 검색합니다."""
    return f"'{query}'에 대한 검색 결과가 없습니다."


@tool
def get_current_time() -> str:
    """현재 시간을 반환합니다."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """수학 표현식을 계산합니다."""
    try:
        allowed_chars = set("0123456789+-*/().% ")
        if not all(c in allowed_chars for c in expression):
            return "허용되지 않은 문자가 포함되어 있습니다."
        return str(eval(expression))
    except Exception as e:
        return f"계산 오류: {str(e)}"


TOOLS = [
    analyze_with_exaone,
    search_documents,
    get_current_time,
    calculate,
]
TOOL_MAP: Dict[str, Any] = {t.name: t for t in TOOLS}
