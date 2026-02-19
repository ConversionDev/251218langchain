"""
이력서 파일 → 텍스트 추출 → LLM 분석(ExaOne만, RAG 미사용) → Success DNA + 기본 정보.

Core 직원 등록 시 이력서 업로드로 연동.
- RAG/임베딩(BGE) 로드 없이 ExaOne만 호출해 GPU 메모리 절감.
- 텍스트 추출: domain/shared/document_extract (PDF/TXT/Word/HWP).
- 속도 최적화: 동일 파일 해시 캐시, max_tokens 1024, temperature 0.3, 입력 1만 자 제한.
"""

import hashlib
import json
import logging
import re
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from api.shared.upload_store import load_upload_file  # type: ignore
from domain.shared.document_extract import extract_text_from_document  # type: ignore

logger = logging.getLogger(__name__)

# 동일 파일 재업로드 시 즉시 반환 (최대 50건, FIFO)
_RESUME_CACHE_MAX = 50
_resume_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

_RESUME_SYSTEM_PROMPT = """당신은 직무역량 전문가입니다. 군집 데이터에 기반하여 이력서를 분석하세요.
아래 이력서 원문을 분석하여 **반드시 아래 JSON 형식으로만** 응답하세요. 다른 텍스트, 설명, 코드 블록 없이 JSON만 출력하세요.

{
  "name": "이름",
  "jobTitle": "직급",
  "department": "부서",
  "email": "이메일",
  "joinedAt": "YYYY-MM-DD",
  "birthDate": "YYYY-MM-DD",
  "gender": "male|female|other|undisclosed",
  "age": 0,
  "employmentType": "new_hire|regular|contract|part_time|intern",
  "trainingHours": 0,
  "resume": {
    "education": [{"school": "", "degree": "", "field": "", "startDate": "", "endDate": ""}],
    "experience": [{"company": "", "role": "", "startDate": "", "endDate": "", "description": ""}],
    "skills": [{"name": "", "level": ""}],
    "certifications": [{"name": "", "issuer": ""}]
  },
  "successDna": {
    "leadership": 0,
    "technical": 0,
    "creativity": 0,
    "collaboration": 0,
    "adaptability": 0
  }
}

- gender: 이력서에 성별이 명시되면 male(남)/female(여)/other(기타), 없으면 undisclosed.
- birthDate: 이력서에 생년월일이 있으면 YYYY-MM-DD로 반드시 기입, 없으면 빈 문자열 또는 생략.
- age: 만 나이(정수). 생년월일(birthDate)이 있으면 오늘 기준 만 나이로 계산: (현재연도 - 출생연도)에서 올해 생일이 아직 안 지났으면 1 빼기. 예: 1990년 3월 15일 → 2025년 2월 기준 34세. 나이만 있고 생년월일 없으면 그대로 사용, 둘 다 없으면 0.
- employmentType: 이력서에 고용형태(정규직·계약직·인턴 등)가 있으면 해당 값(regular|contract|part_time|intern), 신입/미기재면 new_hire.
- trainingHours: 이력서에 연간 교육·연수 시간이 있으면 시간(정수), 없으면 0.
Success DNA는 리더십, 기술력, 창의성, 협업, 적응력 5대 역량을 0-100 점수로 평가하세요. 군집 데이터와 직무역량 기준에 맞춰 객관적으로 산정하세요."""


def _extract_text_from_resume_file(data: bytes, filename: str) -> str:
    """이력서 파일에서 텍스트 추출. domain/shared/document_extract 공통 모듈 사용."""
    return extract_text_from_document(data=data, filename=filename)


def _extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """응답에서 JSON 추출."""
    text = text.strip()

    # 코드 블록 내 JSON 추출
    json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(json_block_pattern, text)
    if matches:
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

    # 직접 JSON 파싱 시도
    json_pattern = r"\{[\s\S]*\}"
    match = re.search(json_pattern, text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    return None


def _age_from_birth_date(birth_str: Optional[str]) -> Optional[int]:
    """생년월일(YYYY-MM-DD 또는 YYYY/MM/DD)을 오늘 기준 만 나이로 변환."""
    if not birth_str or not isinstance(birth_str, str):
        return None
    birth_str = birth_str.strip()[:10].replace("/", "-")
    if len(birth_str) < 10:
        return None
    try:
        from datetime import date
        parts = birth_str.split("-")
        if len(parts) != 3:
            return None
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        birth = date(y, m, d)
        today = date.today()
        age = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        return max(0, min(120, age))
    except (ValueError, TypeError):
        return None


def _normalize_resume_parse_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """raw JSON을 프론트엔드 형식으로 정규화."""
    from datetime import date

    def clamp(val: Any, lo: int, hi: int) -> int:
        try:
            v = int(val)
            return max(lo, min(hi, v))
        except (TypeError, ValueError):
            return (lo + hi) // 2

    success_dna = raw.get("successDna") or {}
    dna = {
        "leadership": clamp(success_dna.get("leadership"), 0, 100),
        "technical": clamp(success_dna.get("technical"), 0, 100),
        "creativity": clamp(success_dna.get("creativity"), 0, 100),
        "collaboration": clamp(success_dna.get("collaboration"), 0, 100),
        "adaptability": clamp(success_dna.get("adaptability"), 0, 100),
    }

    resume = raw.get("resume") or {}
    resume_education = resume.get("education") or []
    resume_experience = resume.get("experience") or []
    resume_skills = resume.get("skills") or []
    resume_certs = resume.get("certifications") or []

    def ensure_list(items: List[Any], keys: List[str]) -> List[Dict[str, Any]]:
        out = []
        for it in items if isinstance(items, list) else []:
            if isinstance(it, dict):
                out.append({k: (it.get(k) or "") for k in keys})
        return out[:20]

    education = ensure_list(resume_education, ["school", "degree", "field", "startDate", "endDate"])
    experience = ensure_list(resume_experience, ["company", "role", "startDate", "endDate", "description"])
    skills = ensure_list(resume_skills, ["name", "level"])
    certs = ensure_list(resume_certs, ["name", "issuer"])

    joined_at = raw.get("joinedAt") or str(date.today())

    _VALID_GENDER = {"male", "female", "other", "undisclosed"}
    gender_raw = str(raw.get("gender") or "undisclosed").strip().lower()
    gender = gender_raw if gender_raw in _VALID_GENDER else "undisclosed"
    # 생년월일이 있으면 만 나이를 서버에서 재계산(LLM 오차 보정)
    age = _age_from_birth_date(raw.get("birthDate") or raw.get("birth_date"))
    if age is None:
        try:
            age_val = int(raw.get("age") or 0)
            age = max(0, min(120, age_val)) if age_val else None
        except (TypeError, ValueError):
            age = None

    _VALID_EMPLOYMENT = {"new_hire", "regular", "contract", "part_time", "intern"}
    employment_raw = str(raw.get("employmentType") or "new_hire").strip().lower()
    employment_type = employment_raw if employment_raw in _VALID_EMPLOYMENT else "new_hire"

    try:
        th_val = int(raw.get("trainingHours") or 0)
        training_hours = max(0, min(9999, th_val))
    except (TypeError, ValueError):
        training_hours = 0

    return {
        "name": str(raw.get("name") or "").strip() or "신규",
        "jobTitle": str(raw.get("jobTitle") or "").strip() or "사원",
        "department": str(raw.get("department") or "").strip() or "미정",
        "email": str(raw.get("email") or "").strip() or "",
        "joinedAt": joined_at[:10] if len(joined_at) >= 10 else joined_at,
        "gender": gender,
        "age": age,
        "employmentType": employment_type,
        "trainingHours": training_hours,
        "resume": {
            "education": education,
            "experience": experience,
            "skills": skills,
            "certifications": certs,
        },
        "successDna": dna,
    }


# 이력서 분석용 생성 설정 (속도·일관성)
_RESUME_MAX_TOKENS = 1024
_RESUME_TEMPERATURE = 0.3
_RESUME_TEXT_LIMIT = 10_000  # 문자 수 제한으로 토큰 절감


def analyze_resume_file(data: bytes, filename: str) -> Dict[str, Any]:
    """이력서 파일 → 텍스트 추출 후 RAG+LLM으로 분석 → Success DNA + 기본 정보 반환."""
    cache_key = hashlib.sha256(data).hexdigest()
    if cache_key in _resume_cache:
        _resume_cache.move_to_end(cache_key)  # LRU 유지
        logger.debug("이력서 캐시 히트: %s", cache_key[:8])
        return dict(_resume_cache[cache_key])

    text = _extract_text_from_resume_file(data, filename)
    if not text or len(text.strip()) < 10:
        raise ValueError("이력서에서 추출된 텍스트가 너무 짧습니다.")

    user_message = f"[이력서 원문]\n{text[:_RESUME_TEXT_LIMIT]}"

    # RAG 그래프(rag_node → model_node) 대신 ExaOne만 직접 호출 → BGE 임베딩 미로드, GPU 절감
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore

    from domain.hub.llm import get_llm  # type: ignore

    llm = get_llm(
        provider="exaone",
        temperature=_RESUME_TEMPERATURE,
        max_tokens=_RESUME_MAX_TOKENS,
    )
    messages = [
        SystemMessage(content=_RESUME_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]
    out = llm.invoke(messages)
    response_str = getattr(out, "content", None) or str(out)

    parsed = _extract_json_from_response(response_str)
    if not parsed:
        raise ValueError(f"LLM 응답에서 JSON을 파싱하지 못했습니다. raw: {response_str[:500]}")

    result = _normalize_resume_parse_result(parsed)
    _resume_cache[cache_key] = result
    if len(_resume_cache) > _RESUME_CACHE_MAX:
        _resume_cache.popitem(last=False)
    return result


def analyze_resume_by_file_id(file_id: str, filename: str = "resume.pdf") -> Dict[str, Any]:
    """업로드된 파일 ID로 이력서 분석."""
    data = load_upload_file(file_id)
    if not data:
        raise ValueError("업로드된 파일을 찾을 수 없거나 만료되었습니다.")
    return analyze_resume_file(data, filename)
