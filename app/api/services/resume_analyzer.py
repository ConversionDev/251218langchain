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
from typing import Any, Dict, List, Optional, Tuple

from api.shared.upload_store import load_upload_file  # type: ignore
from domain.shared.document_extract import extract_text_from_document  # type: ignore

logger = logging.getLogger(__name__)

# 지원 가능 부서 7개 (채용 공고·정규화 기준). 이 외는 "해당 부서는 지원할 수 없습니다" 처리.
ALLOWED_DEPARTMENTS = [
    "인사",
    "재무",
    "영업",
    "마케팅",
    "개발·IT",
    "경영지원",
    "전략·기획",
]

# 이력서 부서/직무 문구 → 지원 가능 부서 매핑 (부분 일치). 순서 유지해 먼저 매칭된 것 사용.
DEPARTMENT_NORMALIZE_MAP: List[Tuple[str, str]] = [
    ("인사", "인사"),
    ("재무", "재무"),
    ("회계", "재무"),
    ("영업", "영업"),
    ("마케팅", "마케팅"),
    ("브랜드", "마케팅"),
    ("개발·IT", "개발·IT"),
    ("개발", "개발·IT"),
    ("IT ", "개발·IT"),
    ("정보기술", "개발·IT"),
    ("정보 기술", "개발·IT"),
    ("솔루션 아키텍트", "개발·IT"),
    ("IT컨설팅", "개발·IT"),
    ("IT 컨설팅", "개발·IT"),
    ("기술연구", "개발·IT"),
    ("R&D", "개발·IT"),
    ("연구개발", "개발·IT"),
    ("경영지원", "경영지원"),
    ("총무", "경영지원"),
    ("전략·기획", "전략·기획"),
    ("전략", "전략·기획"),
    ("기획", "전략·기획"),
    ("리서치", "전략·기획"),
    ("컨설팅", "전략·기획"),
    ("정책", "전략·기획"),
]


def _normalize_department_for_apply(raw: str) -> str:
    """이력서 부서 문구를 지원 가능 부서 7개 중 하나로 정규화. 매칭 실패 시 '해당 부서는 지원할 수 없습니다'."""
    s = (raw or "").strip()
    if not s or "명시 불가" in s or "군집 데이터" in s:
        return "해당 부서는 지원할 수 없습니다"
    if s in ALLOWED_DEPARTMENTS:
        return s
    s_lower = s.lower()
    for keyword, canonical in DEPARTMENT_NORMALIZE_MAP:
        if keyword in s or keyword.lower() in s_lower:
            return canonical
    return "해당 부서는 지원할 수 없습니다"


# 동일 파일/텍스트 재요청 시 즉시 반환 (최대 50건, FIFO)
_RESUME_CACHE_MAX = 50
_resume_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
_text_resume_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

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
  },
  "successDnaReason": "각 역량별로 왜 이 점수를 줬는지 한 줄씩 요약. 예: 리더십 85: 동아리 회장·팀 리드 경험. 기술력 60: Python 중급, 실무 일부."
}

- department: **이력서에 적힌 지원 부서·희망 직무 문구를 그대로** 기재하세요. 예: "IT 컨설팅 / 솔루션 아키텍트"가 적혀 있으면 그대로 "IT 컨설팅 / 솔루션 아키텍트"로 출력. "정보 기술 부문", "IT 부서" 등으로 요약·축약하지 마세요. 직급이 아니라 지원 직무/희망 부서 원문을 유지하세요. **"군집 데이터에 따른 특정 부서 명시 불가" 같은 문구는 절대 사용하지 마세요.** 이력서에 부서/직무가 없으면 "미정"으로 출력하세요.
- resume.education: 학교, 학위, 전공, startDate, **endDate(졸업일)**. 이력서에 졸업일·졸업예정일이 있으면(예: 2020.02, 2020년 2월) **endDate를 YYYY-MM 형식**(예: "2020-02")으로 반드시 기입하세요.
- resume.experience: 회사, 역할, **startDate(근무 시작일), endDate(근무 종료일)**를 반드시 채우세요. 이력서에 "2015/03~2023/02", "2015.03-2023.02", "2015년 3월~2023년 2월"처럼 적혀 있으면 startDate "2015-03", endDate "2023-02"처럼 **YYYY-MM 형식**으로 출력. description(업무 설명)은 지원자가 직접 기입하므로 **비워 두세요**(빈 문자열 "").
- gender: 이력서에 성별이 명시되면 male(남)/female(여)/other(기타), 없으면 undisclosed.
- birthDate: 이력서에 생년월일이 있으면 YYYY-MM-DD로 **반드시** 기입, 없으면 빈 문자열 또는 생략.
- age: **이력서에 나이(만 나이) 또는 생년월일이 있으면 반드시 추출.** 생년월일이 있으면 오늘 기준 만 나이로 계산. 나이만 있으면 그대로 사용, 둘 다 없으면 0.
- employmentType: 이력서에 고용형태(정규직·계약직·인턴 등)가 있으면 해당 값(regular|contract|part_time|intern), 신입/미기재면 new_hire.
- trainingHours: 이력서에 연간 교육·연수 시간이 있으면 시간(정수), 없으면 0.
Success DNA는 리더십, 기술력, 창의성, 협업, 적응력 5대 역량을 0-100 점수로 평가하세요. 군집 데이터와 직무역량 기준에 맞춰 객관적으로 산정하세요.
- successDnaReason: 위 5개 역량 각각에 대해, 이력서의 어떤 근거로 그 점수를 부여했는지 한 문장 내외로 요약하세요. 관리자가 '왜 이렇게 평가했는지' 알 수 있도록 구체적으로 작성하세요."""

# ATS [AI 분석] 전용: 출력을 successDna + successDnaReason만 요청해 토큰·지연 감소
_RESUME_ATS_SYSTEM_PROMPT = """당신은 직무역량 전문가입니다. 아래 이력서 원문을 분석하여 **반드시 아래 JSON 형식으로만** 응답하세요. 다른 텍스트, 설명, 코드 블록 없이 JSON만 출력하세요.

{
  "successDna": {
    "leadership": 0,
    "technical": 0,
    "creativity": 0,
    "collaboration": 0,
    "adaptability": 0
  },
  "successDnaReason": "각 역량별로 왜 이 점수를 줬는지 한 줄씩 요약. 예: 리더십 85: 동아리 회장·팀 리드 경험. 기술력 60: Python 중급, 실무 일부."
}

Success DNA는 리더십, 기술력, 창의성, 협업, 적응력 5대 역량을 0-100 점수로 평가하세요.
successDnaReason은 위 5개 역량 각각에 대해, 이력서의 어떤 근거로 그 점수를 부여했는지 한 문장 내외로 요약하세요."""


def _extract_text_from_resume_file(data: bytes, filename: str) -> str:
    """이력서 파일에서 텍스트 추출. domain/shared/document_extract 공통 모듈 사용."""
    return extract_text_from_document(data=data, filename=filename)


def _fix_json_candidates(raw: str) -> List[str]:
    """파싱 실패 시 trailing comma 등 흔한 비표준 JSON을 고쳐서 후보 리스트 반환."""
    candidates = [raw]
    t1 = re.sub(r",\s*}", "}", raw)
    t2 = re.sub(r",\s*]", "]", raw)
    if t1 != raw:
        candidates.append(t1)
    if t2 != raw:
        candidates.append(t2)
    if t1 != raw and t2 != raw:
        candidates.append(re.sub(r",\s*]", "]", t1))  # 둘 다 적용
    return candidates


def _extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """응답에서 JSON 추출. 코드 블록/앞뒤 문장/ trailing comma 등 허용."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip()

    def try_parse(s: str) -> Optional[Dict[str, Any]]:
        if not s or not s.strip():
            return None
        s = s.strip()
        for candidate in _fix_json_candidates(s):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    # 1) 코드 블록 내 JSON
    json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    for match in re.findall(json_block_pattern, text):
        parsed = try_parse(match)
        if parsed:
            return parsed

    # 2) 첫 번째 { ... } 블록 (가능하면 가장 바깥쪽 한 덩어리)
    brace = text.find("{")
    if brace >= 0:
        depth = 0
        end = -1
        for i in range(brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end > brace:
            block = text[brace : end + 1]
            parsed = try_parse(block)
            if parsed:
                return parsed

    # 3) 정규식으로 임의의 { ... } (마지막 } 까지 가져오기 — 잘린 응답 대비)
    json_pattern = r"\{[\s\S]*\}"
    match = re.search(json_pattern, text)
    if match:
        parsed = try_parse(match.group())
        if parsed:
            return parsed

    # 4) 전체 텍스트
    parsed = try_parse(text)
    if parsed:
        return parsed

    logger.warning("LLM JSON 파싱 실패. 응답 앞 600자: %s", text[:600])
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


def _normalize_ym(val: Any) -> str:
    """날짜 문자열을 YYYY-MM 형식으로 정규화. 2015/03, 2015.03, 2015-03 등 → 2015-03. input type=month 호환."""
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    # 이미 YYYY-MM 또는 YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}(-\d{2})?$", s):
        return s[:7]  # YYYY-MM
    # YYYY/MM, YYYY.MM, YYYYMM
    m = re.match(r"^(\d{4})[/.\s-]?(\d{1,2})$", s.replace(" ", ""))
    if m:
        y, mon = m.group(1), int(m.group(2))
        if 1 <= mon <= 12:
            return f"{y}-{mon:02d}"
    m = re.match(r"^(\d{4})(\d{2})$", s)
    if m:
        y, mon = m.group(1), int(m.group(2))
        if 1 <= mon <= 12:
            return f"{y}-{mon:02d}"
    return s[:10] if s else ""


def _parse_ym_range(s: str) -> Tuple[str, str]:
    """'2015/03~2023/02', '2015.03-2023.02' 등 → ('2015-03', '2023-02'). 파싱 실패 시 ('','')."""
    if not s or not isinstance(s, str):
        return ("", "")
    s = s.strip()
    parts = re.split(r"[\s~\-]+", s, 1)
    if len(parts) >= 2:
        start = _normalize_ym(parts[0].strip())
        end = _normalize_ym(parts[1].strip())
        if start and end:
            return (start, end)
    return ("", "")


def _sanitize_department_in_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """캐시 등 기존 결과에서 부서 정규화: '명시 불가' 등 → 지원 가능 부서 또는 '해당 부서는 지원할 수 없습니다'."""
    if not result:
        return result
    dept = result.get("department")
    if isinstance(dept, str):
        result = {**result, "department": _normalize_department_for_apply(dept)}
    return result


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
    # 학력·경력 날짜 YYYY-MM 정규화 (2015/03 → 2015-03). 업무 설명은 지원자 기입용으로 비움.
    for item in education:
        for key in ("startDate", "endDate"):
            if key in item and item[key]:
                item[key] = _normalize_ym(item[key]) or item[key]
    for item in experience:
        for key in ("startDate", "endDate"):
            if key in item and item[key]:
                item[key] = _normalize_ym(item[key]) or item[key]
        # "2015/03~2023/02"처럼 한 필드에만 있는 경우 분리
        start, end = item.get("startDate") or "", item.get("endDate") or ""
        if (not start or not end) and (start or end):
            combined = start or end
            if "~" in combined or ("-" in combined and re.search(r"\d{4}", combined)):
                ps, pe = _parse_ym_range(combined)
                if ps:
                    item["startDate"] = ps
                if pe:
                    item["endDate"] = pe
        item["description"] = ""  # 업무 설명은 본인이 직접 기입하도록 비워 둠
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

    # successDnaReason: LLM이 문자열이 아닌 값(객체/배열)을 주면 파싱 오류 방지
    reason_raw = raw.get("successDnaReason")
    if reason_raw is None:
        success_dna_reason = None
    elif isinstance(reason_raw, str):
        success_dna_reason = reason_raw.strip() or None
    else:
        success_dna_reason = str(reason_raw).strip() or None

    dept_raw = str(raw.get("department") or "").strip() or ""
    # 지원 가능 부서 7개로 정규화. 미매칭·명시 불가 시 "해당 부서는 지원할 수 없습니다"
    department = _normalize_department_for_apply(dept_raw)

    return {
        "name": str(raw.get("name") or "").strip() or "신규",
        "jobTitle": str(raw.get("jobTitle") or "").strip() or "사원",
        "department": department,
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
        "successDnaReason": success_dna_reason,
    }


# 이력서 분석용 생성 설정 (속도·일관성)
_RESUME_MAX_TOKENS = 1024  # 파일 업로드 전체 분석용
_RESUME_ATS_MAX_TOKENS = 512  # ATS successDna+Reason 전용
_RESUME_TEMPERATURE = 0.3
_RESUME_TEXT_LIMIT = 10_000  # 문자 수 제한으로 토큰 절감


def _resume_dict_to_text(resume: Dict[str, Any]) -> str:
    """resume(학력·경력·스킬·자격증) dict → LLM에 넘길 한 덩어리 텍스트. 항목 수 제한으로 토큰 절감."""
    if not resume or not isinstance(resume, dict):
        return ""
    parts = []
    for edu in (resume.get("education") or [])[:3]:
        if isinstance(edu, dict):
            parts.append(
                f"학력: {(edu.get('school') or '')} {(edu.get('degree') or '')} {(edu.get('field') or '')} "
                f"{(edu.get('startDate') or '')}~{(edu.get('endDate') or '')}"
            )
    for exp in (resume.get("experience") or [])[:5]:
        if isinstance(exp, dict):
            desc = (exp.get("description") or "")[:200]
            parts.append(
                f"경력: {(exp.get('company') or '')} {(exp.get('role') or '')} "
                f"{(exp.get('startDate') or '')}~{(exp.get('endDate') or '')} {desc}"
            )
    for s in (resume.get("skills") or [])[:10]:
        if isinstance(s, dict):
            parts.append(f"기술: {(s.get('name') or '')} ({(s.get('level') or '')})")
        else:
            parts.append(f"기술: {s}")
    for c in (resume.get("certifications") or [])[:5]:
        if isinstance(c, dict):
            parts.append(f"자격: {(c.get('name') or '')} ({(c.get('issuer') or '')})")
    return "\n".join(parts).strip() or ""


def _normalize_ats_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """ATS 전용: 파싱된 JSON에서 successDna + successDnaReason만 정규화해 반환."""

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

    reason_raw = raw.get("successDnaReason")
    if reason_raw is None:
        success_dna_reason = None
    elif isinstance(reason_raw, str):
        success_dna_reason = reason_raw.strip() or None
    else:
        success_dna_reason = str(reason_raw).strip() or None

    return {"successDna": dna, "successDnaReason": success_dna_reason}


def analyze_resume_text(text: str, ats_only: bool = False) -> Dict[str, Any]:
    """이력서 텍스트 → ExaOne 분석.
    ats_only=True: ATS [AI 분석]용 — successDna+successDnaReason만 반환, 텍스트 해시 캐시 사용, 경량 프롬프트.
    ats_only=False: 파일 업로드용 — 전체 정보 반환."""
    if not text or len(text.strip()) < 10:
        raise ValueError("이력서 텍스트가 너무 짧습니다.")
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore

    from domain.hub.llm import get_llm  # type: ignore

    if ats_only:
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if cache_key in _text_resume_cache:
            _text_resume_cache.move_to_end(cache_key)
            logger.debug("이력서 텍스트 캐시 히트: %s", cache_key[:8])
            return dict(_text_resume_cache[cache_key])

        llm = get_llm(
            provider="exaone",
            temperature=_RESUME_TEMPERATURE,
            max_tokens=_RESUME_ATS_MAX_TOKENS,
        )
        messages = [
            SystemMessage(content=_RESUME_ATS_SYSTEM_PROMPT),
            HumanMessage(content=f"[이력서 원문]\n{text[:_RESUME_TEXT_LIMIT]}"),
        ]
        out = llm.invoke(messages)
        response_str = getattr(out, "content", None) or getattr(out, "text", None)
        if not isinstance(response_str, str):
            response_str = str(out) if out is not None else ""
        parsed = _extract_json_from_response(response_str)
        if not parsed:
            raise ValueError(f"LLM 응답에서 JSON을 파싱하지 못했습니다. raw: {response_str[:500]}")
        result = _normalize_ats_result(parsed)
        _text_resume_cache[cache_key] = result
        if len(_text_resume_cache) > _RESUME_CACHE_MAX:
            _text_resume_cache.popitem(last=False)
        return result

    user_message = f"[이력서 원문]\n{text[:_RESUME_TEXT_LIMIT]}"
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
    response_str = getattr(out, "content", None) or getattr(out, "text", None)
    if not isinstance(response_str, str):
        response_str = str(out) if out is not None else ""
    parsed = _extract_json_from_response(response_str)
    if not parsed:
        raise ValueError(f"LLM 응답에서 JSON을 파싱하지 못했습니다. raw: {response_str[:500]}")
    return _normalize_resume_parse_result(parsed)


def analyze_resume_file(data: bytes, filename: str) -> Dict[str, Any]:
    """이력서 파일 → 텍스트 추출 후 RAG+LLM으로 분석 → Success DNA + 기본 정보 반환."""
    cache_key = hashlib.sha256(data).hexdigest()
    if cache_key in _resume_cache:
        _resume_cache.move_to_end(cache_key)  # LRU 유지
        logger.debug("이력서 캐시 히트: %s", cache_key[:8])
        return _sanitize_department_in_result(dict(_resume_cache[cache_key]))

    text = _extract_text_from_resume_file(data, filename)
    if not text or len(text.strip()) < 10:
        raise ValueError("이력서에서 추출된 텍스트가 너무 짧습니다.")

    result = analyze_resume_text(text)
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
