"""
신입사원 가상 이력서·역량 데이터 생성 (ExaOne).

학습된 엑사원을 '가상 이력서 및 역량 데이터 생성 전문가'로 사용해,
5대 Success DNA를 각각 대표하는 신입 100명 규모의 샘플을 생성합니다.
출력은 employees 테이블(EmployeePayload) 호환 JSONL.
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.services.resume_analyzer import _normalize_resume_parse_result  # type: ignore

logger = logging.getLogger(__name__)

# 부서 7개 (이력서·성과 샘플 공통, 균등 분포용)
CANONICAL_DEPARTMENTS = [
    "인사", "재무", "영업", "마케팅", "개발·IT", "경영지원", "전략·기획",
]
# 신입 직급 비율: 인턴 2 : 사원 3
JOB_TITLES_NEW_HIRE = ["인턴", "인턴", "사원", "사원", "사원"]

# Success DNA 정의 (프롬프트에 포함)
SUCCESS_DNA_DEFINITIONS = """
### Success DNA 정의:
1. 리더십(Leadership): 팀 프로젝트 리드, 의사결정 경험
2. 기술력(Technical): 개발 스택(Python, FastAPI 등), 프로젝트 완성도
3. 창의성(Creativity): 문제 해결을 위한 새로운 접근, 아이디어 제안
4. 협업(Collaboration): 갈등 해결, 팀워크 기여도
5. 적응력(Adaptability): 새로운 환경/기술 습득 속도, 유연성
"""

_SYSTEM_PROMPT = """당신은 우리 회사의 신입사원 채용을 위한 '가상 이력서 및 역량 데이터'를 생성하는 전문가입니다.
""" + SUCCESS_DNA_DEFINITIONS + """
요청한 역량이 두드러진 **신입사원(신규 채용 후보)** 프로필을 가상으로 만들어 주세요.
각 프로필은 서로 다른 이름, 학력, 경력(인턴/동아리/대외활동 등), 성별, 연령대를 가지며, 요청한 Success DNA 역량 점수가 특히 높게 나오도록 하세요.

**[필수 제약 — 반드시 준수]**
- 모든 텍스트 필드(resume 내 description, summary, coverLetter 등)는 반드시 2문장 이내, 총 150자 이하로 아주 간결하게 작성할 것.
- 설명이나 인사말은 절대 금지. 오직 JSON 배열만 출력하고 즉시 종료할 것.
- 불필요한 수식어는 빼고 전문 용어 위주로 핵심만 기술할 것.

**출력 형식:** 위 제약을 지키며 즉시 JSON 배열만 출력하세요. 다른 텍스트, 코드 블록 없이 `[ ... ]` 만 출력하세요.
배열의 각 요소는 아래와 같은 객체 하나입니다.

{
  "name": "한글 이름",
  "jobTitle": "직급 (예: 사원, 인턴)",
  "department": "희망/지원 부서",
  "email": "example@email.com",
  "joinedAt": "YYYY-MM-DD (입사 지원일)",
  "birthDate": "YYYY-MM-DD",
  "gender": "male|female|other|undisclosed",
  "age": 0,
  "employmentType": "new_hire",
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

- age: 만 나이(정수). birthDate 기준 22~35 범위. 짧게.
- successDna: 각 0~100 정수. **요청한 역량**이 가장 높고 나머지는 낮게. 간결하게.
- resume: **간결하게(Concise)** 작성. education 1~2건, experience 0~3건·항목당 description은 2문장 이내·핵심만, skills·certifications 2~6건. 불필요한 수식·서론 없이 핵심만."""


def _find_array_bounds(s: str) -> Optional[tuple[int, int]]:
    """첫 '[' 와 짝이 맞는 ']' 위치 반환. 문자열/이스케이프 무시한 단순 괄호 카운트."""
    start = s.find("[")
    if start == -1:
        return None
    depth = 0
    i = start
    in_string = False
    escape = False
    quote = None
    while i < len(s):
        c = s[i]
        if escape:
            escape = False
            i += 1
            continue
        if in_string:
            if c == "\\":
                escape = True
            elif c == quote:
                in_string = False
            i += 1
            continue
        if c in ('"', "'"):
            in_string = True
            quote = c
            i += 1
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return (start, i + 1)
        i += 1
    return None


def _extract_json_array_from_response(text: str) -> Optional[List[Dict[str, Any]]]:
    """응답에서 JSON 배열 추출. 잘린 응답은 부분 배열만이라도 복구 시도."""
    text = text.strip()
    # 코드 블록 내 JSON 추출
    json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    for match in re.findall(json_block_pattern, text):
        arr = _parse_or_salvage_array(match.strip())
        if arr is not None:
            return arr
    # 첫 [ ... ] 구간만 잘라서 파싱 (] 뒤 설명이 있으면 제외)
    bounds = _find_array_bounds(text)
    if bounds is not None:
        start, end = bounds
        chunk = text[start:end]
        arr = _parse_or_salvage_array(chunk)
        if arr is not None:
            return arr
    # fallback: 첫 [ 부터 끝까지 (기존 동작)
    array_pattern = r"\[[\s\S]*"
    m = re.search(array_pattern, text)
    if m:
        arr = _parse_or_salvage_array(m.group())
        if arr is not None:
            return arr
    return _parse_or_salvage_array(text)


def _parse_or_salvage_array(s: str) -> Optional[List[Dict[str, Any]]]:
    """문자열을 JSON 배열로 파싱. 실패 시 잘린 배열 복구 시도(닫는 괄호 추가)."""

    def _to_valid_list(lst: list) -> Optional[List[Dict[str, Any]]]:
        if not isinstance(lst, list) or not all(isinstance(x, dict) for x in lst):
            return None
        # 빈 객체 제거 후 반환 (잘린 복구 시 마지막이 {} 인 경우)
        non_empty = [x for x in lst if len(x) > 0]
        return non_empty if non_empty else None

    # 정상 파싱
    try:
        parsed = json.loads(s)
        out = _to_valid_list(parsed)
        if out is not None:
            return out
    except json.JSONDecodeError:
        pass
    # 잘린 응답 복구: 끝에 ], }], }}] ... 를 붙여서 유효한 배열 시도 (최대 32개 객체 가정)
    if not s.strip().startswith("["):
        return None
    close_options = ["]"]
    for _ in range(31):
        close_options.append("}" + close_options[-1])
    for close in close_options:
        try:
            parsed = json.loads(s + close)
            out = _to_valid_list(parsed)
            if out is not None:
                return out
        except json.JSONDecodeError:
            continue
    return None


# 신입 샘플 생성용 생성 파라미터 (배치 3 기준 넉넉한 상한 → 파싱 실패 방지)
_GENERATION_PARAMS = {
    "max_new_tokens": 4096,  # 3명분 풍부한 출력도 잘리지 않도록
    "temperature": 0.5,
    "top_p": 0.85,
    "do_sample": True,
}


def _invoke_exaone_for_batch(
    dimension: str,
    dimension_ko: str,
    count: int,
    temperature: float = 0.5,
    max_tokens: int = 4096,
) -> List[Dict[str, Any]]:
    """한 번의 LLM 호출로 count명 분량 생성. dimension이 두드러진 신입 프로필."""
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
    from domain.hub.llm import get_llm  # type: ignore
    from domain.hub.llm.exaone_provider import get_provider_name  # type: ignore

    llm = get_llm(provider=get_provider_name(), temperature=temperature, max_tokens=max_tokens)
    # 다이어트 파라미터 전달 (top_p 등은 invoke kwargs로 전달)
    invoke_kwargs = {"max_new_tokens": max_tokens, "temperature": temperature}
    invoke_kwargs["top_p"] = _GENERATION_PARAMS.get("top_p", 0.85)
    invoke_kwargs["do_sample"] = _GENERATION_PARAMS.get("do_sample", True)
    user_content = (
        f"{dimension_ko}({dimension})이/가 특히 두드러진 신입사원 후보 {count}명의 가상 이력서·역량 데이터를 짧고 간결하게 생성해 주세요. "
        "각 인물은 서로 다른 이름, 학력, 경력, 성별, 연령대를 가지며, successDna에서 해당 역량이 가장 높아야 합니다. "
        f"설명 없이 즉시 위 형식의 JSON 배열만 출력하세요. 배열 길이는 정확히 {count}개입니다."
    )
    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    # invoke 시 generation params 전달 (미전달 시 ExaOne 기본 2048 사용 → 응답 잘림)
    out = llm.invoke(messages, **invoke_kwargs)
    response_str = getattr(out, "content", None) or str(out)
    arr = _extract_json_array_from_response(response_str)
    if not arr or not isinstance(arr, list):
        logger.warning("배열 파싱 실패 dimension=%s response_len=%s", dimension, len(response_str))
        return []
    return arr


# 5대 역량 한글 라벨 (프롬프트용)
_DIMENSION_LABELS = {
    "leadership": "리더십",
    "technical": "기술력",
    "creativity": "창의성",
    "collaboration": "협업",
    "adaptability": "적응력",
}


def generate_new_hire_samples(
    total_count: int = 100,
    batch_size: int = 3,
    delay_seconds: float = 0.2,
    temperature: float = 0.5,
    max_tokens: int = 4096,
    parse_fail_retries: int = 2,
) -> List[Dict[str, Any]]:
    """
    5대 Success DNA를 각각 대표하는 신입사원 샘플을 ExaOne로 생성.

    total_count에 가깝게 생성하며, 각 역량당 균등 분배 후 batch_size명씩 요청합니다.
    반환 리스트의 각 항목은 EmployeePayload/employees 테이블 호환(camelCase, id는 호출자가 부여 가능).
    배열 파싱 실패 시 parse_fail_retries 횟수만큼 해당 배치만 재시도합니다.
    """
    dimensions = ["leadership", "technical", "creativity", "collaboration", "adaptability"]
    per_dim = max(1, total_count // len(dimensions))
    num_batches_per_dim = (per_dim + batch_size - 1) // batch_size
    total_batches = len(dimensions) * num_batches_per_dim
    collected: List[Dict[str, Any]] = []
    batch_times: List[float] = []
    start_wall = time.perf_counter()

    for dim in dimensions:
        dim_ko = _DIMENSION_LABELS.get(dim, dim)
        for b in range(num_batches_per_dim):
            want = min(batch_size, per_dim - b * batch_size)
            if want <= 0:
                break
            batch_start = time.perf_counter()
            raw_list: List[Dict[str, Any]] = []
            for attempt in range(parse_fail_retries + 1):
                try:
                    raw_list = _invoke_exaone_for_batch(dim, dim_ko, want, temperature, max_tokens)
                    if raw_list:
                        break
                    if attempt < parse_fail_retries:
                        logger.info("배열 파싱 실패 재시도 dimension=%s attempt=%s/%s", dim, attempt + 1, parse_fail_retries)
                except Exception as e:
                    if attempt < parse_fail_retries:
                        logger.warning("배치 호출 실패 재시도 dimension=%s: %s", dim, e)
                    else:
                        raise
            try:
                for raw in raw_list[:want]:
                    if not isinstance(raw, dict):
                        continue
                    try:
                        normalized = _normalize_resume_parse_result(raw)
                        normalized["employmentType"] = "new_hire"
                        collected.append(normalized)
                    except Exception as e:
                        logger.warning("정규화 실패 항목 건너뜀: %s", e)
            except Exception as e:
                logger.warning("LLM 배치 실패 dimension=%s batch=%s: %s", dim, b, e)
            elapsed = time.perf_counter() - batch_start
            batch_times.append(elapsed)
            done = len(collected)
            current_batch = len(batch_times)
            avg_sec = sum(batch_times) / len(batch_times) if batch_times else 0
            remain_batches = total_batches - current_batch
            eta_sec = avg_sec * remain_batches if remain_batches > 0 else 0
            eta_min = eta_sec / 60
            speed = done / (time.perf_counter() - start_wall) if (time.perf_counter() - start_wall) > 0 else 0
            print(
                f"[진행] {current_batch}/{total_batches} 배치 | 누적 {done}건 | "
                f"배치당 약 {avg_sec:.1f}초 | 속도 {speed:.1f}건/분 | 예상 남은 시간 약 {eta_min:.1f}분"
            )
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    return collected


def assign_ids(records: List[Dict[str, Any]], prefix: str = "E") -> List[Dict[str, Any]]:
    """레코드에 id를 E001, E002, ... 형식으로 부여."""
    out = []
    for i, r in enumerate(records, start=1):
        row = dict(r)
        row["id"] = f"{prefix}{str(i).zfill(3)}"
        out.append(row)
    return out


def apply_new_hire_metadata(
    records: List[Dict[str, Any]],
    application_date_start: str = "2025-01-01",
    application_date_end: str = "2025-06-30",
) -> None:
    """
    신입 샘플에 부서·직급·지원일을 골고루 분포시켜 덮어씀.
    - 부서: 7개 부서 순환 (인사, 재무, 영업, 마케팅, 개발·IT, 경영지원, 전략·기획)
    - 직급: 인턴/사원 비율에 따라 순환
    - applicationDate: start~end 구간 내 균등 분포
    """
    start_d = datetime.strptime(application_date_start[:10], "%Y-%m-%d")
    end_d = datetime.strptime(application_date_end[:10], "%Y-%m-%d")
    n = len(records)
    days_range = max(1, (end_d - start_d).days)
    for i, r in enumerate(records):
        r["department"] = CANONICAL_DEPARTMENTS[i % len(CANONICAL_DEPARTMENTS)]
        r["jobTitle"] = JOB_TITLES_NEW_HIRE[i % len(JOB_TITLES_NEW_HIRE)]
        # 지원일: start~end 구간에 균등 분포
        day_offset = (i * days_range) // max(1, n) if n else 0
        day_offset = min(day_offset, days_range - 1)
        app_d = start_d + timedelta(days=day_offset)
        r["applicationDate"] = app_d.strftime("%Y-%m-%d")
        r["status"] = "pending"


def save_samples_jsonl(records: List[Dict[str, Any]], path: Path) -> None:
    """EmployeePayload 호환 레코드 리스트를 JSONL로 저장."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    logger.info("저장 완료: %s (%d건)", path, len(records))


def run_and_save(
    output_dir: Optional[Path] = None,
    total_count: int = 100,
    batch_size: int = 3,
    delay_seconds: float = 0.2,
    filename_prefix: str = "new_hire_samples",
) -> Path:
    """
    샘플 생성 후 JSONL로 저장. output_dir 미지정 시 core.paths.get_resume_samples_dir() 사용.
    반환: 저장된 파일 경로.
    """
    if output_dir is None:
        from core.paths import get_resume_samples_dir  # type: ignore
        output_dir = get_resume_samples_dir()
    output_dir = Path(output_dir)
    records = generate_new_hire_samples(
        total_count=total_count,
        batch_size=batch_size,
        delay_seconds=delay_seconds,
    )
    records = assign_ids(records)
    apply_new_hire_metadata(records)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    path = output_dir / f"{filename_prefix}_{timestamp}.jsonl"
    save_samples_jsonl(records, path)
    return path
