"""스팸 에스컬레이션 — 애매 케이스 LLM 판정(judge).

결정론 파이프라인이 '낮은 확신/애매' 판정을 낸 메일만 여기로 올린다.
방식: tool-calling 루프 대신 **증거 수집 + LLM 판정**(CPU/GGUF tool-calling 신뢰성 회피).
  1) 증거 수집: 규칙 점검(rule) + 학습된 LLaMA 분류 결과 + EXAONE 심층 분석
  2) LLM이 그 증거를 보고 최종 판정(JSON) — 환경별 LLM 선택:
       - 로컬: 학습/로컬 모델(EXAONE 등, settings.llm_provider)
       - 배포: Gemini (raw google-generativeai SDK, 신규 의존성 없음)

LLM 선택: settings.spam_agent_llm
  - "auto"(기본): 현재 llm_provider 사용
  - "gemini": Gemini로 판정 (배포 권장 — CPU에서 tool-calling 불필요·견고)
  - "exaone" | "llama_cpp": 해당 로컬 모델로 판정

안전: 어떤 단계든 실패하면 None 반환 → 호출자가 기존 결정론 판정을 그대로 유지.
"""

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_VALID_ACTIONS = {"deliver", "deliver_with_warning", "quarantine", "reject"}

_SYSTEM_PROMPT = (
    "당신은 한국어 이메일 스팸 판정관입니다. 아래 [수집된 증거]를 종합해 최종 판정을 내리세요.\n"
    "증거: 규칙 점검 결과, 학습된 분류기의 스팸 확률, EXAONE 심층 분석.\n"
    "반드시 아래 JSON 한 줄만 출력하세요(설명 금지):\n"
    '{"action":"deliver|deliver_with_warning|quarantine|reject",'
    '"is_spam":true|false,"confidence":"low|medium|high",'
    '"reason_codes":["..."],"analysis":"간단한 근거"}'
)


def _format_email(email: Dict[str, Any]) -> str:
    return (
        f"제목: {email.get('subject', '')}\n"
        f"발신자: {email.get('sender', '')}\n"
        f"본문: {str(email.get('body', ''))[:1500]}"
    )


def _gather_evidence(
    email: Dict[str, Any],
    llama_result: Optional[Dict[str, Any]],
    exaone_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """파이프라인 증거를 재활용하고 부족분만 추가 수집."""
    evidence: Dict[str, Any] = {}
    # 규칙 점검 (항상, 저렴)
    try:
        from domain.spokes.spam.services.rule_service import RuleService  # type: ignore

        evidence["rule"] = RuleService().process(email)
    except Exception as e:
        evidence["rule"] = {"error": str(e)}
    # 학습된 LLaMA 분류 결과 (gateway가 이미 산출 → 재활용)
    evidence["llama"] = llama_result or {}
    # EXAONE 심층 분석 (policy 경로면 이미 있음, 아니면 추가 수행)
    if exaone_result:
        evidence["deep_analysis"] = exaone_result.get("analysis") or exaone_result
    else:
        try:
            from domain.spokes.spam.services.policy_service import PolicyService  # type: ignore

            evidence["deep_analysis"] = PolicyService().process(email, use_existing_policy=True)
        except Exception as e:
            evidence["deep_analysis"] = {"error": str(e)}
    return evidence


def _resolve_llm_choice() -> str:
    from core.config import get_settings  # type: ignore

    choice = (getattr(get_settings(), "spam_agent_llm", "auto") or "auto").lower()
    if choice == "auto":
        from infrastructure.llm import get_provider_name  # type: ignore

        return get_provider_name()
    return choice


def _judge_via_gemini(prompt: str) -> Optional[str]:
    """Gemini raw SDK로 판정 텍스트 생성 (신규 의존성 없음)."""
    from core.config import get_settings  # type: ignore

    settings = get_settings()
    api_key = settings.gemini_api_key
    if not api_key:
        logger.info("[SPAM-ESCALATION] GEMINI_API_KEY 없음 → 기존 결정 유지")
        return None
    import google.generativeai as genai  # type: ignore

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    resp = model.generate_content(f"{_SYSTEM_PROMPT}\n\n{prompt}")
    return getattr(resp, "text", None)


def _judge_via_local(prompt: str, provider: str) -> Optional[str]:
    """로컬/학습 모델(EXAONE 등)로 판정 텍스트 생성."""
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
    from infrastructure.llm import get_llm  # type: ignore

    llm = get_llm(provider=provider, max_tokens=512, temperature=0.2)
    resp = llm.invoke([SystemMessage(content=_SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return str(getattr(resp, "content", "") or "")


def _parse_verdict(text: Optional[str]) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    if data.get("action") not in _VALID_ACTIONS:
        return None
    return {
        "action": data["action"],
        "is_spam": data.get("is_spam"),
        "confidence": data.get("confidence", "medium"),
        "reason_codes": data.get("reason_codes") or [],
        "analysis": data.get("analysis", ""),
    }


def run_spam_escalation(
    email_metadata: Dict[str, Any],
    llama_result: Optional[Dict[str, Any]] = None,
    exaone_result: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """애매 메일을 증거 종합 + LLM 판정으로 재판정. 실패 시 None(기존 결정 유지)."""
    try:
        evidence = _gather_evidence(email_metadata, llama_result, exaone_result)
        prompt = (
            f"[이메일]\n{_format_email(email_metadata)}\n\n"
            f"[수집된 증거]\n{json.dumps(evidence, ensure_ascii=False, default=str)}"
        )
        choice = _resolve_llm_choice()
        logger.info("[SPAM-ESCALATION] judge LLM=%s", choice)
        text = _judge_via_gemini(prompt) if choice == "gemini" else _judge_via_local(prompt, choice)
        verdict = _parse_verdict(text)
        if verdict is None:
            logger.info("[SPAM-ESCALATION] 판정 파싱 실패 → 기존 결정 유지")
        return verdict
    except Exception as e:
        logger.warning("[SPAM-ESCALATION] 실행 실패 → 기존 결정 유지: %s", e)
        return None
