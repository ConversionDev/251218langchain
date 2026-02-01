"""
ExaOne Adapter - Hub의 ExaOne 진입점.

ExaOne 모델(텍스트 생성, 채팅, 이메일 분석) 접근은 이 어댑터를 통해서만 수행합니다.
내부적으로 exaone_provider 및 ExaoneManager를 사용합니다.
"""

import json
import re
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 텍스트 생성 (프롬프트 → 문자열)
# ---------------------------------------------------------------------------


def generate_text(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """ExaOne으로 프롬프트에 대한 텍스트를 생성합니다.

    Args:
        prompt: 입력 프롬프트.
        max_tokens: 최대 생성 토큰 수.
        temperature: 생성 온도.

    Returns:
        생성된 문자열.
    """
    try:
        from domain.hub.llm.exaone_provider import get_llm  # type: ignore
        from langchain_core.messages import HumanMessage  # type: ignore

        llm = get_llm(provider="exaone", max_tokens=max_tokens, temperature=temperature)
        messages = [HumanMessage(content=prompt.strip())]
        response = llm.invoke(messages)
        content = getattr(response, "content", None) or str(response)
        return content if isinstance(content, str) else str(content)
    except Exception as e:
        return f"[ExaOne 오류] {e}"


# ---------------------------------------------------------------------------
# LangChain LLM 인스턴스 (채팅·도구 호출용)
# ---------------------------------------------------------------------------


def get_llm(
    temperature: float = 0.7,
    max_tokens: int = 2048,
    **kwargs: Any,
):
    """ExaOne LangChain 호환 LLM 인스턴스를 반환합니다.

    채팅 에이전트·도구 호출 등에서 사용합니다.
    """
    from domain.hub.llm.exaone_provider import get_llm as _get_llm  # type: ignore

    # provider 중복 전달 방지 (graph_orchestrator 등에서 get_llm(provider=...) 호출 시 kwargs에도 들어감)
    kwargs.pop("provider", None)
    return _get_llm(
        provider="exaone",
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 이메일 스팸/위험 분석 (정책 기반)
# ---------------------------------------------------------------------------


def analyze_email(
    subject: str,
    sender: str,
    body: Optional[str] = None,
    recipient: Optional[str] = None,
    date: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    headers: Optional[Dict[str, Any]] = None,
    policy_context: Optional[str] = None,
) -> Dict[str, Any]:
    """ExaOne으로 이메일을 분석합니다. 스팸 여부·위험 요소.

    Args:
        subject: 제목
        sender: 발신자
        body: 본문 (선택)
        recipient: 수신자 (선택)
        date: 날짜 (선택)
        attachments: 첨부 목록 (선택)
        headers: 헤더 (선택)
        policy_context: 정책 컨텍스트 (선택)

    Returns:
        {"raw_output": str, "parsed": dict, "risk_codes": list}
    """
    try:
        from core.resource_manager.exaone_manager import ExaoneManager  # type: ignore

        exaone_manager = ExaoneManager()
        exaone_model = exaone_manager.get_base_model()

        email_text = f"제목: {subject}\n발신자: {sender}"
        if body:
            email_text += f"\n본문: {body}"
        if recipient:
            email_text += f"\n수신자: {recipient}"
        if attachments:
            email_text += f"\n첨부파일: {', '.join(attachments)}"
        policy_info = f"\n정책: {policy_context}" if policy_context else ""

        prompt = f"""이메일 스팸 분석:
{email_text}{policy_info}

판단 기준:
- 스팸: 피싱, 사기, 광고성 링크, 개인정보 요청
- 정상: 일반 업무, 개인 소통, 일정 안내

confidence 기준:
- high: 명확한 스팸 또는 명확한 정상
- medium: 일부 의심 요소 있음
- low: 판단 어려움

JSON만 답변:
{{"is_spam": false, "confidence": "high", "risk_codes": [], "analysis": "분석내용"}}"""

        response = exaone_model.invoke(prompt, max_new_tokens=256, temperature=0.3)
        raw_output = response if isinstance(response, str) else str(response)

        try:
            json_match = re.search(r"\{[\s\S]*\}", raw_output)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {
                    "is_spam": False,
                    "confidence": "low",
                    "risk_level": "low",
                    "risk_codes": [],
                    "analysis": raw_output,
                    "recommendation": "추가 검토 필요",
                }
        except json.JSONDecodeError:
            parsed = {
                "is_spam": False,
                "confidence": "low",
                "risk_level": "low",
                "risk_codes": [],
                "analysis": raw_output,
                "recommendation": "추가 검토 필요",
            }

        return {
            "raw_output": raw_output,
            "parsed": parsed,
            "risk_codes": parsed.get("risk_codes", []),
        }
    except Exception as e:
        return {
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
