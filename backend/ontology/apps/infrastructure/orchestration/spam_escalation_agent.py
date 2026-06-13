"""스팸 에스컬레이션 에이전트 (애매 케이스 전용).

결정론 파이프라인(gateway→rule/policy→final_decision)이 **낮은 확신/애매** 판정을 낸
메일만 이 에이전트로 올린다. LLM이 도구(rule_check / llama_classify / deep_analyze)를
스스로 골라 다단계로 조사한 뒤 최종 판정을 JSON으로 낸다.

설계 원칙(안전 우선):
- 기본 OFF: `settings.spam_agent_escalation` 플래그가 True일 때만 호출됨(스팸 그래프에서 게이트).
- 애매 케이스 한정: 대량 트래픽은 기존 빠른 경로 그대로 → 비용/지연 영향 최소.
- 실패 시 None 반환 → 호출자가 **기존 결정을 그대로 유지**(라이브 파이프라인 절대 안 깨짐).
- tool-calling 미지원 제공자(예: 일부 CPU llama_cpp)면 None 반환 → 기존 결정 유지.

※ 검증된 langgraph.prebuilt.create_react_agent 사용(미검증 루프 코드 최소화).
"""

import contextvars
import json
import logging
import re
from typing import Any, Dict, Optional

from langchain_core.tools import tool  # type: ignore

logger = logging.getLogger(__name__)

# 현재 조사 중인 이메일(도구가 인자 없이 참조). invoke 직전 set, 직후 reset.
_current_email: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "spam_escalation_email"
)

_ESCALATION_SYSTEM_PROMPT = (
    "당신은 한국어 이메일 스팸 판정 보조 에이전트입니다. "
    "주어진 이메일이 애매하여 정밀 조사가 필요합니다. "
    "rule_check(규칙 점검), llama_classify(학습된 분류기 확률), deep_analyze(EXAONE 심층 분석) "
    "도구를 필요한 만큼 호출해 근거를 모은 뒤, 마지막에 반드시 아래 JSON 한 줄만 출력하세요.\n"
    '{"action": "deliver|deliver_with_warning|quarantine|reject", '
    '"is_spam": true|false, "confidence": "low|medium|high", '
    '"reason_codes": ["..."], "analysis": "간단한 근거"}'
)

_agent: Any = None


@tool
def rule_check() -> str:
    """현재 이메일에 규칙 기반 스팸 점검(발신자/키워드/링크 등)을 적용해 결과를 반환한다."""
    from domain.spokes.spam.services.rule_service import RuleService  # type: ignore

    return json.dumps(RuleService().process(_current_email.get()), ensure_ascii=False)


@tool
def llama_classify() -> str:
    """학습된 LLaMA 스팸 분류기로 현재 이메일의 스팸 확률(spam_prob/label/confidence)을 산출한다."""
    from infrastructure.mcp.http_client import spam_call  # type: ignore

    raw = spam_call("classify_spam", {"email_metadata": _current_email.get()})
    return json.dumps(raw or {}, ensure_ascii=False)


@tool
def deep_analyze() -> str:
    """EXAONE 정책 기반 심층 분석으로 현재 이메일의 위험 코드/근거를 산출한다."""
    from domain.spokes.spam.services.policy_service import PolicyService  # type: ignore

    return json.dumps(
        PolicyService().process(_current_email.get(), use_existing_policy=True),
        ensure_ascii=False,
    )


_TOOLS = [rule_check, llama_classify, deep_analyze]


def _format_email(email_metadata: Dict[str, Any]) -> str:
    return (
        f"제목: {email_metadata.get('subject', '')}\n"
        f"발신자: {email_metadata.get('sender', '')}\n"
        f"본문: {str(email_metadata.get('body', ''))[:1500]}"
    )


def _get_agent():
    """create_react_agent 인스턴스 (lazy). tool-calling 지원 시에만 생성."""
    global _agent
    if _agent is None:
        from langgraph.prebuilt import create_react_agent  # type: ignore
        from infrastructure.llm import get_llm, get_provider_name  # type: ignore

        llm = get_llm(provider=get_provider_name(), max_tokens=1024, temperature=0.2)
        _agent = create_react_agent(llm, _TOOLS, prompt=_ESCALATION_SYSTEM_PROMPT)
    return _agent


def _parse_verdict(text: str) -> Optional[Dict[str, Any]]:
    """LLM 최종 출력에서 JSON 판정 추출. 실패 시 None."""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    action = data.get("action")
    if action not in {"deliver", "deliver_with_warning", "quarantine", "reject"}:
        return None
    return {
        "action": action,
        "is_spam": data.get("is_spam"),
        "confidence": data.get("confidence", "medium"),
        "reason_codes": data.get("reason_codes", []) or [],
        "analysis": data.get("analysis", ""),
    }


def run_spam_escalation(email_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """애매 메일을 에이전트로 정밀 조사 → 정제된 판정(dict) 반환. 실패/미지원 시 None.

    None을 반환하면 호출자는 기존 결정론적 판정을 그대로 유지해야 한다.
    """
    try:
        from infrastructure.llm import get_provider_name, supports_tool_calling  # type: ignore

        provider = get_provider_name()
        if not supports_tool_calling(provider):
            logger.info("[SPAM-ESCALATION] tool-calling 미지원(provider=%s) → 기존 결정 유지", provider)
            return None
    except Exception as e:
        logger.warning("[SPAM-ESCALATION] provider 확인 실패 → 기존 결정 유지: %s", e)
        return None

    token = _current_email.set(email_metadata)
    try:
        agent = _get_agent()
        result = agent.invoke(
            {"messages": [("user", _format_email(email_metadata))]},
            config={"recursion_limit": 8},
        )
        messages = result.get("messages", []) if isinstance(result, dict) else []
        final_text = str(getattr(messages[-1], "content", "")) if messages else ""
        verdict = _parse_verdict(final_text)
        if verdict is None:
            logger.info("[SPAM-ESCALATION] 판정 파싱 실패 → 기존 결정 유지")
        return verdict
    except Exception as e:
        logger.warning("[SPAM-ESCALATION] 실행 실패 → 기존 결정 유지: %s", e)
        return None
    finally:
        _current_email.reset(token)
