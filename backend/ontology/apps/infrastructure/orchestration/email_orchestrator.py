"""
메일 1건 → 학습된 모델(ExaOne)이 성과/5대 역량 동시 판단 → 성과 기록/역량 태깅.

흐름:
  1. 메일 제목+본문을 ExaOne에 넘겨 JSON 응답 요청 (is_performance, competency_labels)
  2. 성과로 판단되면 performance_records에 자동 기록 (tags에 역량 라벨 포함)
  3. 5대 역량 관련으로 판단된 것은 tags로 저장 (추후 역량 수치 반영 파이프라인에서 활용)
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from infrastructure.persistence.repositories.performance_record_repository import create_submission  # type: ignore
from domain.hub.shared.period_utils import get_current_period  # type: ignore


# 5대 역량 라벨 (competency_anchors·Success DNA와 일치)
COMPETENCY_LABELS = ("리더십", "기술력", "창의성", "협업", "적응력")

# 본문 저장 시 최대 길이 (노이즈·DB 부담 고려)
BODY_PREVIEW_MAX_LEN = 1000


def _build_classify_prompt(subject: str, body: str) -> str:
    """메일 분류용 ExaOne 프롬프트 생성."""
    text = f"제목: {subject}\n\n본문:\n{(body or '').strip()}"
    if len(text) > 3000:
        text = text[:3000] + "\n...(생략)"
    return f"""다음 메일을 분석해서 아래 두 가지를 판단해 주세요.

1) 성과 관련: 이 메일 내용이 업무 성과·활동 기록으로 남길 만한가? (예: 업무 협의, 보고, 결정 사항, 프로젝트 진행 등)
2) 5대 역량 관련: 다음 역량 중 이 메일과 관련된 것이 있으면 모두 나열해 주세요. 없으면 빈 배열.
   - 리더십, 기술력, 창의성, 협업, 적응력

메일:
---
{text}
---

반드시 아래 JSON 형식만 출력하세요. 다른 설명 없이 JSON만.
{{"is_performance": true 또는 false, "competency_labels": ["리더십", "협업"] 또는 []}}"""


def _parse_classify_response(raw: str) -> Dict[str, Any]:
    """ExaOne 응답에서 is_performance, competency_labels 파싱."""
    out = {"is_performance": False, "competency_labels": []}
    try:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            parsed = json.loads(m.group())
            out["is_performance"] = bool(parsed.get("is_performance", False))
            labels = parsed.get("competency_labels") or []
            if isinstance(labels, list):
                out["competency_labels"] = [
                    str(x).strip() for x in labels
                    if str(x).strip() in COMPETENCY_LABELS
                ]
    except (json.JSONDecodeError, TypeError):
        pass
    return out


def _content_for_record(subject: str, body: Optional[str]) -> str:
    """성과 기록용 content 문자열 (제목 + 본문 요약)."""
    parts = [f"[메일] {subject or '(제목 없음)'}"]
    if body and body.strip():
        preview = (body.strip())[:BODY_PREVIEW_MAX_LEN]
        if len(body.strip()) > BODY_PREVIEW_MAX_LEN:
            preview += "..."
        parts.append(preview)
    return "\n\n".join(parts)


def run_email_classify_and_record(
    db: Session,
    subject: str,
    body: Optional[str],
    employee_id: str,
    period: Optional[str] = None,
    *,
    generate_text_fn=None,
) -> Dict[str, Any]:
    """메일 1건을 분류하고, 성과로 판단되면 performance_records에 기록한다.

    Args:
        db: DB 세션
        subject: 메일 제목
        body: 메일 본문 (선택)
        employee_id: 발신 직원 ID
        period: 분기 (예: 2025-Q1). None이면 현재 분기
        generate_text_fn: ExaOne 텍스트 생성 함수. None이면 domain.hub.llm.generate_text 사용

    Returns:
        {
            "classification": {"is_performance": bool, "competency_labels": ["리더십", ...]},
            "performance_record_id": str | None,  # 기록한 경우에만
            "raw_response": str,
        }
    """
    from infrastructure.llm import generate_text  # type: ignore

    gen = generate_text_fn or generate_text
    period = period or get_current_period()

    prompt = _build_classify_prompt(subject or "", body or "")
    raw_response = gen(prompt, max_tokens=256, temperature=0.3)
    classification = _parse_classify_response(raw_response)

    performance_record_id: Optional[str] = None
    if classification["is_performance"]:
        content = _content_for_record(subject, body)
        tags: List[str] = ["mail"]
        for c in classification["competency_labels"]:
            tags.append(f"역량:{c}")
        try:
            record = create_submission(
                db,
                employee_id=employee_id,
                text_type="email",
                content=content,
                period=period,
                tags=tags,
            )
            performance_record_id = record.get("id")
        except Exception:
            logger.warning(
                "성과 기록 실패 (employee_id=%s, period=%s) — 분류 결과는 반환",
                employee_id, period, exc_info=True,
            )

    return {
        "classification": classification,
        "performance_record_id": performance_record_id,
        "raw_response": raw_response[:500] if raw_response else "",
    }
