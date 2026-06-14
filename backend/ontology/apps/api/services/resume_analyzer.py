"""
이력서 파일 → 텍스트 추출 → LLM 분석(ExaOne만, RAG 미사용) → Success DNA + 기본 정보.

Core 직원 등록 시 이력서 업로드로 연동.
- RAG/임베딩(BGE) 로드 없이 ExaOne만 호출해 GPU 메모리 절감.
- 텍스트 추출: domain/shared/document_extract (PDF/TXT/Word).
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
- resume.education: 학교, 졸업여부(degree), 전공(field), startDate, **endDate(졸업일)**.
  - **degree**: 졸업 여부 컬럼의 값("졸업"·"수료"·"재학"·"중퇴"·"편입"·"휴학"·"졸업예정")을 기입. 학위명(학사·석사·박사)만 적혀 있으면 "졸업"으로 기입. 없으면 빈 문자열.
  - **endDate**: 이력서에 졸업일·졸업예정일이 있으면(예: 2020.02, 2020년 2월) **YYYY-MM 형식**(예: "2020-02")으로 반드시 기입. "졸업(2017.03)" 형식이면 괄호 안 날짜를 endDate로 추출하세요.
  - **field**: "전공" 또는 "계열" 컬럼의 값(예: 중어중문학, 컴퓨터공학)을 기입하세요.
- resume.experience: 회사, 역할, **startDate(근무 시작일), endDate(근무 종료일)**를 반드시 채우세요. 이력서에 "2015/03~2023/02", "2015.03-2023.02", "2015년 3월~2023년 2월"처럼 적혀 있으면 startDate "2015-03", endDate "2023-02"처럼 **YYYY-MM 형식**으로 출력. description은 담당업무가 있으면 1~2문장으로 요약, 없으면 빈 문자열.
- gender: 이력서에 성별이 명시되면 male(남)/female(여)/other(기타), 없으면 undisclosed.
- birthDate: 이력서에 생년월일이 있으면 YYYY-MM-DD로 **반드시** 기입, 없으면 빈 문자열 또는 생략.
- age: **이력서에 나이(만 나이) 또는 생년월일이 있으면 반드시 추출.** 생년월일이 있으면 오늘 기준 만 나이로 계산. 나이만 있으면 그대로 사용, 둘 다 없으면 0.
- employmentType: 이력서에 고용형태(정규직·계약직·인턴 등)가 있으면 해당 값(regular|contract|part_time|intern), 신입/미기재면 new_hire.
- trainingHours: 이력서에 연간 교육·연수 시간이 있으면 시간(정수), 없으면 0.
Success DNA는 리더십, 기술력, 창의성, 협업, 적응력 5대 역량을 0-100 점수로 평가하세요. 군집 데이터와 직무역량 기준에 맞춰 객관적으로 산정하세요.
- successDnaReason: 위 5개 역량 각각에 대해, 이력서의 어떤 근거로 그 점수를 부여했는지 한 문장 내외로 요약하세요. 관리자가 '왜 이렇게 평가했는지' 알 수 있도록 구체적으로 작성하세요."""

# apply 폼 채우기 전용: successDna 없이 기본 정보·학력·경력만 추출
# Few-shot 예시 포함 — 다양한 한국 이력서 템플릿에서 컬럼명·포맷이 달라도 의미 기반으로 매핑
_RESUME_FORM_SYSTEM_PROMPT = """당신은 한국어 이력서 파싱 전문가입니다.
이력서 원문을 분석하여 **반드시 아래 JSON 형식으로만** 응답하세요. 설명·코드 블록 없이 JSON만 출력하세요.

출력 형식:
{"name":"","jobTitle":"","department":"","phone":"","email":"","birthDate":"","gender":"male|female|other|undisclosed","age":0,"employmentType":"new_hire|regular|contract|part_time|intern","resume":{"education":[{"school":"","degree":"","field":"","startDate":"","endDate":""}],"experience":[{"company":"","role":"","startDate":"","endDate":"","description":""}],"skills":[{"name":"","level":""}],"certifications":[{"name":"","issuer":""}]}}

---
## 매핑 규칙 (Few-shot 예시 포함)

### 이름·성별
이름 셀에 성별이 함께 표기되는 경우 분리:
  입력: "성명: 강경구(남)"  → name:"강경구", gender:"male"
  입력: "이름: 김지원(여)"  → name:"김지원", gender:"female"
  입력: 성별 컬럼 "남"     → gender:"male"
  입력: "남□ 여☑"         → gender:"female"
  성별 정보가 없으면        → gender:"undisclosed"

### 생년월일 (birthDate → YYYY-MM-DD)
  입력: "1991.10.31"  → "1991-10-31"
  입력: "1991년 10월 31일" → "1991-10-31"
  입력: "19911031"    → "1991-10-31"

### 학력 (education)
degree = **졸업 여부** 컬럼의 값만 기입. 허용값: "졸업", "수료", "재학", "중퇴", "편입", "휴학", "졸업예정", "수료예정", "고졸".
         이력서에 학위명(학사·석사·박사)만 있고 졸업여부 표기가 없으면 → "졸업"으로 기입.
         아무 정보도 없으면 → "".
field  = 전공·학과명 ("전공", "학과", "계열" 컬럼).
endDate = 졸업·수료 월(YYYY-MM). **degree가 졸업/수료이면 endDate는 반드시 채움.** 빈 문자열 금지(재학·중퇴만 비움).
  입력: "졸업(2017.03)"         → degree:"졸업", endDate:"2017-03"
  입력: "2017년 2월 졸업"       → degree:"졸업", endDate:"2017-02"
  입력: "2017.02 수료"          → degree:"수료", endDate:"2017-02"
  입력: "재학중"                → degree:"재학", endDate:""
  입력: 학위 "학사", 전공 "컴퓨터공학", 졸업 "2020.02"
        → degree:"졸업", field:"컴퓨터공학", endDate:"2020-02"

### 경력 (experience)
role = 직책·직위 컬럼이 **명시된 경우만** 기입. 없으면 "" (추측 금지).
description = "담당업무"·"주요업무"·"업무내용"·"수행업무" 컬럼 내용을 1~2문장 요약. 없으면 "".
  입력: 직책 없음, 담당업무 "LIS 프로그램 교육 및 원격 안내, 병원 장비 데이터 호환 확인"
        → role:"", description:"LIS 프로그램 사용 교육·원격 안내 및 병원 장비 데이터 호환 확인 담당."
  입력: 직책 "대리", 업무내용 "신규 고객 영업 및 계약 관리"
        → role:"대리", description:"신규 고객 영업 및 계약 관리 담당."
startDate/endDate: "2022.09~2022.12", "2022년 9월 - 2022년 12월" 등 → "2022-09", "2022-12"

### 기타
phone: 010-XXXX-XXXX 형식. "연락처"·"H.P"·"휴대폰" 등.
department: 희망부서·희망직무 원문 그대로. 없으면 "미정".
age: 생년월일 기준 만 나이. 없으면 0.
employmentType: 신입·미기재 → new_hire. 경력직 → regular."""

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
    # 2017년 3월 / 2017년03월
    m = re.match(r"^(\d{4})\s*년\s*(\d{1,2})\s*월", s)
    if m:
        y, mon = m.group(1), int(m.group(2))
        if 1 <= mon <= 12:
            return f"{y}-{mon:02d}"
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


def _fill_education_enddates_from_source(source_text: str, items: List[Dict[str, Any]]) -> None:
    """LLM이 endDate를 비운 경우: 학교명 근처 → 문서 순서의 졸업(YYYY.MM) 후보를 행별로 배분."""
    st = (source_text or "").strip()
    if not st or not items:
        return
    patterns = (
        r"졸업\s*[\(\（]\s*(\d{4})\s*[./\-]\s*(\d{1,2})\s*[\)\）]",
        r"수료\s*[\(\（]\s*(\d{4})\s*[./\-]\s*(\d{1,2})\s*[\)\）]",
        r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(?:졸업|수료)",
    )
    for item in items:
        if (item.get("endDate") or "").strip():
            continue
        school = (item.get("school") or "").strip()
        if len(school) >= 2 and school in st:
            i = st.index(school)
            window = st[i : i + 700]
            for pat in patterns:
                m = re.search(pat, window)
                if m:
                    item["endDate"] = _normalize_ym(f"{m.group(1)}-{m.group(2)}") or ""
                    break
    matches: List[Tuple[int, str]] = []
    seen_pos: set[int] = set()
    for pat in patterns:
        for m in re.finditer(pat, st):
            if m.start() in seen_pos:
                continue
            ym = _normalize_ym(f"{m.group(1)}-{m.group(2)}")
            if ym and re.match(r"^\d{4}-\d{2}$", ym):
                matches.append((m.start(), ym))
                seen_pos.add(m.start())
    matches.sort(key=lambda x: x[0])
    ordered_ym = []
    seen_ym: set[str] = set()
    for _, ym in matches:
        if ym not in seen_ym:
            seen_ym.add(ym)
            ordered_ym.append(ym)
    di = 0
    for item in items:
        if (item.get("endDate") or "").strip():
            continue
        if di < len(ordered_ym):
            item["endDate"] = ordered_ym[di]
            di += 1


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


def _regex_extract_phone(text: str) -> str:
    """원문 텍스트에서 한국 전화번호 추출. 010-XXXX-XXXX 형식으로 정규화."""
    pattern = r"(?:010|011|016|017|018|019)[-\s]?\d{3,4}[-\s]?\d{4}"
    m = re.search(pattern, text)
    if not m:
        return ""
    digits = re.sub(r"\D", "", m.group())
    # XXX-XXXX-XXXX 형식으로 정규화
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return m.group().strip()


def _regex_extract_email(text: str) -> str:
    """원문 텍스트에서 이메일 주소 추출."""
    m = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return m.group().strip() if m else ""


def _regex_extract_birthdate(text: str) -> str:
    """원문 텍스트에서 생년월일 추출 → YYYY-MM-DD 정규화.
    지원 패턴: 1991-10-31 / 1991.10.31 / 1991/10/31 / 19911031"""
    patterns = [
        r"(19\d{2}|20\d{2})[-./](0[1-9]|1[0-2])[-./](0[1-9]|[12]\d|3[01])",
        r"(19\d{2}|20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            parts = [g for g in m.groups() if g]
            if len(parts) == 3:
                return f"{parts[0]}-{parts[1]}-{parts[2]}"
    return ""


def _normalize_resume_parse_result(raw: Dict[str, Any], source_text: str = "") -> Dict[str, Any]:
    """raw JSON을 프론트엔드 형식으로 정규화.

    정형 필드(전화번호·이메일·생년월일)는 LLM 결과가 비어있거나 형식이 맞지 않으면
    source_text 에서 regex로 재추출(후보정). 비정형 필드(이름·학력·경력·부서 등)는
    LLM 결과를 그대로 사용.
    """
    from datetime import date

    def clamp(val: Any, lo: int, hi: int) -> int:
        try:
            v = int(val)
            return max(lo, min(hi, v))
        except (TypeError, ValueError):
            return (lo + hi) // 2

    # 폼 채우기 경로(_RESUME_FORM_SYSTEM_PROMPT)는 successDna를 산출하지 않는다.
    # raw에 successDna가 없으면 가짜 50점을 만들지 말고 None 반환(ATS 경로가 실제 점수 산출).
    raw_dna = raw.get("successDna")
    if isinstance(raw_dna, dict) and raw_dna:
        dna: Optional[Dict[str, int]] = {
            "leadership": clamp(raw_dna.get("leadership"), 0, 100),
            "technical": clamp(raw_dna.get("technical"), 0, 100),
            "creativity": clamp(raw_dna.get("creativity"), 0, 100),
            "collaboration": clamp(raw_dna.get("collaboration"), 0, 100),
            "adaptability": clamp(raw_dna.get("adaptability"), 0, 100),
        }
    else:
        dna = None

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

    # ── 학력 후보정 ──────────────────────────────────────────────────────────
    # degree = 졸업 여부(졸업/수료/재학/중퇴 등). 프롬프트 지시 기준.
    # 안전망: "졸업(2017.03)" 처럼 날짜가 degree·field에 묻혀 있으면 endDate로 분리.
    _EDU_DATE_IN_PAREN = re.compile(r"[\(\（](\d{4}[./\-]\d{1,2})[\)\）]")
    _EDU_COMPLETION = {"졸업", "수료", "재학", "중퇴", "편입", "휴학", "졸업예정", "수료예정", "고졸"}
    for item in education:
        deg = item.get("degree") or ""
        fld = item.get("field") or ""
        for src in (deg, fld):
            m = _EDU_DATE_IN_PAREN.search(src)
            if m and not (item.get("endDate") or "").strip():
                item["endDate"] = _normalize_ym(m.group(1)) or m.group(1)
        item["degree"] = _EDU_DATE_IN_PAREN.sub("", deg).strip()
        item["field"] = _EDU_DATE_IN_PAREN.sub("", fld).strip()
        for key in ("startDate", "endDate"):
            if item.get(key):
                item[key] = _normalize_ym(item[key]) or item[key]
    _fill_education_enddates_from_source(source_text, education)
    for item in education:
        if item.get("endDate"):
            item["endDate"] = _normalize_ym(item["endDate"]) or item["endDate"]
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
        # description: LLM이 채운 요약 그대로 사용. 없으면 빈 문자열 유지.
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

    import re as _re

    def _clean_name(v: str) -> str:
        """표 셀 정렬 아티팩트 제거: 한글 음절 사이 공백 삭제. '강 경 구' → '강경구'"""
        v = _re.sub(r"(?<=[\uac00-\ud7a3])\s+(?=[\uac00-\ud7a3])", "", v)
        # 이름 끝 괄호 부가 정보 제거: '강경구(남)' → '강경구'
        v = _re.sub(r"\s*[\(\（][^\)\）]{1,10}[\)\）]\s*$", "", v)
        return v.strip()

    # ── 정형 필드 regex 후보정 ───────────────────────────────────────────────
    # LLM 결과가 유효하면 그대로 사용. 비어있거나 형식 불일치 시에만 regex로 보완.
    def _valid_phone(v: str) -> bool:
        return bool(_re.match(r"0\d{1,2}-\d{3,4}-\d{4}$", v))

    def _valid_email(v: str) -> bool:
        return bool(_re.match(r"[^@]+@[^@]+\.[^@]+$", v))

    def _valid_birthdate(v: str) -> bool:
        return bool(_re.match(r"\d{4}-\d{2}-\d{2}$", v))

    llm_phone = str(raw.get("phone") or raw.get("phoneNumber") or "").strip()
    phone = llm_phone if _valid_phone(llm_phone) else (
        _regex_extract_phone(source_text) if source_text else llm_phone
    )

    llm_email = str(raw.get("email") or "").strip()
    email = llm_email if _valid_email(llm_email) else (
        _regex_extract_email(source_text) if source_text else llm_email
    )

    llm_birth = str(raw.get("birthDate") or raw.get("birth_date") or "").strip()
    birth_date = llm_birth if _valid_birthdate(llm_birth) else (
        _regex_extract_birthdate(source_text) if source_text else llm_birth
    )
    # birthDate regex 결과로 만 나이 재계산
    if birth_date and not _valid_birthdate(llm_birth):
        age = _age_from_birth_date(birth_date) or age

    return {
        "name": _clean_name(str(raw.get("name") or "")),
        "jobTitle": str(raw.get("jobTitle") or "").strip(),
        "department": department,
        "phone": phone,
        "email": email,
        "birthDate": birth_date,
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
_RESUME_MAX_TOKENS = 1024       # (레거시, 현재 미사용)
_RESUME_FORM_MAX_TOKENS = 512   # apply 폼 채우기 전용 — successDna 없으므로 출력 짧음
_RESUME_ATS_MAX_TOKENS = 512    # ATS successDna+Reason 전용
_RESUME_TEMPERATURE = 0.3
_RESUME_TEXT_LIMIT = 10_000     # ATS 분석용 텍스트 입력 한도
_RESUME_FORM_TEXT_LIMIT = 4_000 # apply 폼 채우기 전용 — 한 장 이력서 기준 충분


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
    """이력서 텍스트 → LLM 분석 (LLM_PROVIDER: exaone | llama_cpp).
    ats_only=True: ATS [AI 분석]용 — successDna+successDnaReason만 반환, 텍스트 해시 캐시 사용, 경량 프롬프트.
    ats_only=False: 파일 업로드용 — 전체 정보 반환."""
    if not text or len(text.strip()) < 10:
        raise ValueError("이력서 텍스트가 너무 짧습니다.")
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore

    from infrastructure.llm import get_llm  # type: ignore
    from infrastructure.llm.exaone_provider import get_provider_name  # type: ignore

    _prov = get_provider_name()

    if ats_only:
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if cache_key in _text_resume_cache:
            _text_resume_cache.move_to_end(cache_key)
            logger.debug("이력서 텍스트 캐시 히트: %s", cache_key[:8])
            return dict(_text_resume_cache[cache_key])

        llm = get_llm(
            provider=_prov,
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

    # apply 폼 채우기 전용 경량 경로 — successDna 제외, 입력·출력 토큰 축소.
    # 업로드 즉시 응답을 위해 배포(RESUME_FORM_LLM=gemini)에선 Gemini flash-lite 사용(무거운 EXAONE 미로드).
    user_message = f"[이력서 원문]\n{text[:_RESUME_FORM_TEXT_LIMIT]}"
    from core.config import get_settings  # type: ignore

    response_str: Optional[str] = None
    if (getattr(get_settings(), "resume_form_llm", "exaone") or "exaone").lower() == "gemini":
        from infrastructure.llm.gemini_adapter import gemini_complete  # type: ignore

        response_str = gemini_complete(_RESUME_FORM_SYSTEM_PROMPT, user_message)
        if response_str:
            logger.debug("이력서 폼 추출: Gemini")
        else:
            logger.info("이력서 폼 Gemini 실패 → EXAONE 폴백")

    if not response_str:  # 로컬(exaone) 또는 Gemini 실패 시 폴백
        llm = get_llm(provider=_prov, temperature=_RESUME_TEMPERATURE, max_tokens=_RESUME_FORM_MAX_TOKENS)
        out = llm.invoke(
            [SystemMessage(content=_RESUME_FORM_SYSTEM_PROMPT), HumanMessage(content=user_message)]
        )
        response_str = getattr(out, "content", None) or getattr(out, "text", None)
        if not isinstance(response_str, str):
            response_str = str(out) if out is not None else ""

    parsed = _extract_json_from_response(response_str)
    if not parsed:
        raise ValueError(f"LLM 응답에서 JSON을 파싱하지 못했습니다. raw: {response_str[:500]}")
    return _normalize_resume_parse_result(parsed, source_text=text)


def analyze_resume_file(data: bytes, filename: str) -> Dict[str, Any]:
    """이력서 파일 → 텍스트 추출 후 LLM으로 분석 → 기본 정보 반환.
    반환값에 _resumeText 키로 원본 추출 텍스트 포함 (ATS AI 분석용 원문 보존).
    캐시 히트 시에도 _resumeText가 포함된 채로 반환."""
    cache_key = hashlib.sha256(data).hexdigest()
    if cache_key in _resume_cache:
        _resume_cache.move_to_end(cache_key)
        logger.debug("이력서 캐시 히트: %s", cache_key[:8])
        return _sanitize_department_in_result(dict(_resume_cache[cache_key]))

    text = _extract_text_from_resume_file(data, filename)
    if not text or len(text.strip()) < 10:
        raise ValueError("이력서에서 추출된 텍스트가 너무 짧습니다.")

    result = analyze_resume_text(text)
    # 원본 텍스트를 결과에 포함 — router에서 DB resumeText 컬럼으로 저장
    result["_resumeText"] = text
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
