"""
Graph Orchestrator — 채팅 그래프 빌더

도구(TOOLS), 노드(model/rag/tool), 체크포인터, 조건 라우팅.
"""

import logging
import re
import sys
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from domain.models import ChatState

logger = logging.getLogger(__name__)


# --- 1. 도구 (오케스트레이터 → HTTP → Hub → call_tool → 도메인 MCP → Spoke) ---


def _hub_result_to_str(result: Any) -> str:
    """Hub call 결과를 문자열로."""
    if result is None:
        return "호출 실패"
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        import json
        return json.dumps(result, ensure_ascii=False)
    return str(result)


def _ats_pipeline_status_breakdown_lines(pipeline_rows: List[Dict[str, Any]]) -> List[str]:
    """신입·지원 풀 내 ATS status별 건수. '합격자'는 hired만 해당(전체 지원 풀 합계와 다름)."""
    counts = {"pending": 0, "screening": 0, "hired": 0, "rejected": 0}
    other = 0
    for e in pipeline_rows:
        st = str(e.get("status") or "").strip().lower()
        if st in counts:
            counts[st] += 1
        else:
            other += 1
    total = len(pipeline_rows)
    return [
        "[신입·지원 풀 — ATS 상태별]",
        f"- 풀 합계: {total}명 (지원·심사 단계 후보 전체; '합격자' 수와 동일하지 않음)",
        f"- 미검토(pending): {counts['pending']}명",
        f"- 심사 중(screening): {counts['screening']}명",
        f"- 합격(hired): {counts['hired']}명  ← '합격자' 질문은 반드시 이 숫자만 사용",
        f"- 탈락(rejected): {counts['rejected']}명",
        f"- 기타/상태 없음: {other}명",
        "※ 입사 확정 후에는 status가 비워지므로 과거 합격 이력은 DB에 남지 않습니다. '현재 신입 풀 합격자'만 위 hired 건수로 집계합니다.",
    ]


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
    """EXAONE으로 이메일 분석. HTTP → Hub → Spam MCP → Spoke."""
    from domain.hub.mcp.http_client import spam_call  # type: ignore

    args: Dict[str, Any] = {
        "subject": subject,
        "sender": sender,
        "body": body or "",
        "recipient": recipient or "",
        "date": date or "",
        "policy_context": _policy_context or "",
    }
    if attachments is not None:
        args["attachments"] = attachments
    if headers is not None:
        args["headers"] = headers
    result = spam_call("analyze_email", args)
    return _hub_result_to_str(result)


@tool
def search_documents(query: str) -> str:
    """문서에서 관련 정보를 검색합니다. HTTP → Hub → Chat MCP → Spoke."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("search_documents", {"query": query})
    return _hub_result_to_str(result)


@tool
def get_current_time() -> str:
    """현재 시간을 반환합니다. HTTP → Hub → Chat MCP → Spoke."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("get_current_time", {})
    return _hub_result_to_str(result)


@tool
def calculate(expression: str) -> str:
    """수학 표현식을 계산합니다. HTTP → Hub → Chat MCP → Spoke."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("calculate", {"expression": expression})
    return _hub_result_to_str(result)


@tool
def define(term: str) -> str:
    """용어(term)의 정의나 설명을 문서에서 검색해 반환합니다. 예: IFRS, OECD 등."""
    from domain.hub.mcp.http_client import chat_call  # type: ignore

    result = chat_call("search_documents", {"query": term})
    return _hub_result_to_str(result)


@tool
def get_hr_summary() -> str:
    """등록된 입사 확정(재직) 직원 수·신입·지원 단계 수와 RAG 적재 상태를 반환합니다.
    입사 확정 = employment_type=regular 이고 입사일(joinedAt) 있음. '전체 직원 수', '공시 완성도', '적재 상태' 등 질문에 사용합니다."""
    try:
        from core.database import SessionLocal  # type: ignore
        from domain.hub.repositories.competency_anchor_repository import get_anchor_doc_count  # type: ignore
        from domain.hub.repositories.disclosure_repository import get_disclosure_doc_count  # type: ignore
        from domain.hub.repositories.employee_repository import (  # type: ignore
            is_new_hire_pipeline_employee_row,
            is_onboarded_regular_employee_row,
            list_all as repo_list_all,
        )
        from domain.hub.repositories.performance_record_repository import get_performance_record_count  # type: ignore

        db = SessionLocal()
        try:
            employees = repo_list_all(db) or []
            employee_count = len(employees)

            def _is_high_performer(emp: Dict[str, Any]) -> bool:
                dna = emp.get("successDna")
                if not isinstance(dna, dict):
                    return False
                keys = ("leadership", "technical", "creativity", "collaboration", "adaptability")
                vals: List[float] = []
                for k in keys:
                    v = dna.get(k)
                    try:
                        if v is None:
                            continue
                        vals.append(float(v))
                    except Exception:
                        continue
                if not vals:
                    return False
                return (sum(vals) / len(vals)) >= 80.0

            new_hires = [e for e in employees if is_new_hire_pipeline_employee_row(e)]
            regulars = [e for e in employees if is_onboarded_regular_employee_row(e)]
            high_performers = [e for e in employees if _is_high_performer(e)]

            def _completeness(rows: List[Dict[str, Any]]) -> int:
                if not rows:
                    return 0
                fields = ("gender", "age", "employmentType", "trainingHours")
                filled = 0
                for r in rows:
                    for f in fields:
                        v = r.get(f)
                        if v is None:
                            continue
                        if isinstance(v, float) and v != v:  # NaN
                            continue
                        filled += 1
                return round((filled / (len(rows) * len(fields))) * 100)

            regular_completeness = _completeness(regulars)
            all_completeness = _completeness(employees)
            disclosure_count = get_disclosure_doc_count(db)
            anchor_count = get_anchor_doc_count(db)
            perf_count = get_performance_record_count(db)
            breakdown = _ats_pipeline_status_breakdown_lines(new_hires)
            return "\n".join(
                [
                    "[인원 구분(DB 기준)]",
                    "※ 일반 직원 = 입사 확정(employment_type=regular + 입사일 joinedAt 있음). 신입 = ATS·지원 단계.",
                    f"- 전체 레코드 수: {employee_count}명",
                    f"- 일반 직원 수(입사 확정·재직): {len(regulars)}명",
                    f"- 신입·지원 단계 수(풀 합계): {len(new_hires)}명",
                    *breakdown,
                    "※ '합격자'는 DB status=hired 뿐이며, 신입 지원 풀 전체 인원과 혼동하지 마세요.",
                    f"- 고성과자 수(Success DNA 평균 80점 이상): {len(high_performers)}명",
                    "[공시 완성도]",
                    f"- 일반 직원 기준 공시 완성도: {regular_completeness}%",
                    f"- 전체 직원 기준 공시 완성도: {all_completeness}%",
                    "[RAG 적재 상태]",
                    f"- 성과(performance_records) 기록: {perf_count}건",
                    f"- 공시(disclosures) RAG 문서 청크: {disclosure_count}건",
                    f"- 역량(competency_anchors) RAG 문서: {anchor_count}건",
                ]
            )
        finally:
            db.close()
    except Exception as e:
        return f"HR 요약 조회 실패: {str(e)}"


@tool
def get_employee_info(name: str) -> str:
    """이름으로 직원을 검색해 요약 정보를 반환합니다. '김도윤에 대해 설명해줘', 'OOO 직원 정보' 등 개별 직원 질문에 사용합니다. name에는 성명 일부(예: 김도윤, 도윤)를 넣습니다."""
    if not (name and name.strip()):
        return "이름을 입력해 주세요."
    try:
        from core.database import SessionLocal  # type: ignore
        from domain.hub.repositories.employee_repository import find_by_name  # type: ignore

        db = SessionLocal()
        try:
            employees = find_by_name(db, name.strip(), limit=5)
            if not employees:
                return f"'{name.strip()}'(으)로 검색된 직원이 없습니다."
            parts = []
            for i, emp in enumerate(employees, 1):
                pid = emp.get("id", "")
                pname = emp.get("name", "")
                job = emp.get("jobTitle", "") or "-"
                dept = emp.get("department", "") or "-"
                line = f"[{i}] ID: {pid}, 이름: {pname}, 직급: {job}, 부서: {dept}"
                if emp.get("trainingHours") is not None:
                    line += f", 교육훈련: {emp['trainingHours']}시간"
                if emp.get("successDna"):
                    line += ", Success DNA 보유"
                if emp.get("email"):
                    line += f", 이메일: {emp['email']}"
                parts.append(line)
            return "\n".join(parts)
        finally:
            db.close()
    except Exception as e:
        return f"직원 검색 실패: {str(e)}"


@tool
def list_employees(
    employment_type: Optional[str] = None,
    department: Optional[str] = None,
    job_title: Optional[str] = None,
    performance_tier: Optional[str] = None,
    limit: int = 50,
) -> str:
    """직원/신입/지원자 목록을 조회합니다.
    employment_type(all|new_hire|regular), performance_tier(all|high), department·job_title 부분 검색.
    regular=입사 확정(재직): employment_type=regular 이고 joinedAt(입사일) 있음. new_hire=ATS·지원 단계.
    전체 직원·명단·목록·고성과자 질문에 사용합니다.
    """
    et = (employment_type or "all").strip().lower()
    if et not in {"all", "new_hire", "regular"}:
        return "employment_type은 all, new_hire, regular 중 하나여야 합니다."
    pt = (performance_tier or "all").strip().lower()
    if pt not in {"all", "high"}:
        return "performance_tier는 all, high 중 하나여야 합니다."
    try:
        from core.database import SessionLocal  # type: ignore
        from domain.hub.repositories.employee_repository import (  # type: ignore
            count_for_chat,
            is_new_hire_pipeline_employee_row,
            list_for_chat,
        )

        db = SessionLocal()
        try:
            safe_limit = max(1, min(500, int(limit or 50)))
            if pt == "high":
                safe_limit = 500
            emp_type_filter = None if et == "all" else et
            dept_filter = (department or "").strip() or None
            title_filter = (job_title or "").strip() or None
            rows = list_for_chat(
                db,
                employment_type=emp_type_filter,
                department_part=dept_filter,
                job_title_part=title_filter,
                exclude_sample=False,
                limit=safe_limit,
            )
            if not rows:
                return "조건에 맞는 직원이 없습니다."
            filtered_total = count_for_chat(
                db,
                employment_type=emp_type_filter,
                department_part=dept_filter,
                job_title_part=title_filter,
                exclude_sample=False,
            )

            def _is_high_performer(emp: Dict[str, Any]) -> bool:
                dna = emp.get("successDna")
                if not isinstance(dna, dict):
                    return False
                keys = ("leadership", "technical", "creativity", "collaboration", "adaptability")
                vals: List[float] = []
                for k in keys:
                    v = dna.get(k)
                    try:
                        if v is None:
                            continue
                        vals.append(float(v))
                    except Exception:
                        continue
                if not vals:
                    return False
                return (sum(vals) / len(vals)) >= 80.0

            # 통계는 SQL count 쿼리로 정확하게 계산 (limit 무관)
            new_hire_total = count_for_chat(db, employment_type="new_hire", department_part=dept_filter, job_title_part=title_filter)
            regular_total = count_for_chat(db, employment_type="regular", department_part=dept_filter, job_title_part=title_filter)
            new_hire_count = new_hire_total
            regular_count = regular_total
            # 고성과자는 successDna 계산 필요 → 표시 대상(rows)에서 산출
            high_count = sum(1 for r in rows if _is_high_performer(r))

            if pt == "high":
                rows = [r for r in rows if _is_high_performer(r)]
                if not rows:
                    return "조건에 맞는 직원이 없습니다."
                high_count = len(rows)
                new_hire_count = sum(1 for r in rows if is_new_hire_pipeline_employee_row(r))
                regular_count = len(rows) - new_hire_count
                filtered_total = high_count

            # 명단은 상위 5명만 나열하고 나머지는 '… 외 N명'. 인원 수는 count 기준(filtered_total)으로 통일
            MAX_DISPLAY = 5
            displayed = min(len(rows), MAX_DISPLAY)
            # 조건 일치 인원은 count_for_chat 결과 사용 (list limit와 무관하게 301 등 정확 반영)
            remainder = max(0, filtered_total - displayed)
            lines: List[str] = [
                f"[조회 결과] 이번 조건에 맞는 인원: {filtered_total}명 (신입·지원 {new_hire_count} / 입사확정·일반 {regular_count} / 고성과 {high_count})",
                "※ 답변에는 반드시 아래 [1]~[5] 5줄을 그대로 복사해 넣고, 마지막에 '… 외 N명'만 추가하세요. 인원 수는 위 '이번 조건에 맞는 인원: N명'과 '… 외 K명'만 사용하세요.",
            ]
            for i, emp in enumerate(rows[:MAX_DISPLAY], 1):
                cls = "신입·지원" if is_new_hire_pipeline_employee_row(emp) else "입사확정"
                hp = ",고성과" if _is_high_performer(emp) else ""
                lines.append(
                    f"[{i}] 이름: {emp.get('name','')}, 부서: {emp.get('department') or '-'}, "
                    f"직급: {emp.get('jobTitle') or '-'}, 구분: {cls}{hp}"
                )
            if remainder > 0:
                lines.append(f"… 외 {remainder}명")
            return "\n".join(lines)
        finally:
            db.close()
    except Exception as e:
        return f"직원 목록 조회 실패: {str(e)}"


@tool
def get_employee_performance(employee_name_or_id: str, limit: int = 30) -> str:
    """직원의 성과 활동(performance_records)을 조회합니다. 'OOO 성과', 'OOO 활동/실적', 'OOO 회의록·보고서' 등 질문에 사용합니다. 인자에는 직원 이름(예: 강경구) 또는 직원 ID(예: E001)를 넣습니다."""
    if not (employee_name_or_id and employee_name_or_id.strip()):
        return "직원 이름 또는 ID를 입력해 주세요."
    try:
        from core.database import SessionLocal  # type: ignore
        from domain.hub.repositories.employee_repository import find_by_name, get_by_id  # type: ignore
        from domain.hub.repositories.performance_record_repository import list_by_employee  # type: ignore

        db = SessionLocal()
        try:
            key = employee_name_or_id.strip()
            # 먼저 이름으로 검색, 없으면 ID로 단건 조회
            employees = find_by_name(db, key, limit=5)
            if not employees:
                emp = get_by_id(db, key)
                if emp:
                    employees = [emp]
            employee_ids = [{"id": e.get("id", ""), "name": e.get("name", "")} for e in employees]
            if not employee_ids:
                return f"'{key}'(으)로 검색된 직원이 없습니다. 성과 조회는 직원 이름 또는 ID가 필요합니다."
            parts: List[str] = []
            for e in employee_ids:
                eid, ename = e.get("id", ""), e.get("name", "")
                if not eid:
                    continue
                rows = list_by_employee(db, eid, limit=max(1, min(50, int(limit or 30))))
                if not rows:
                    parts.append(f"[{ename or eid}] 성과 기록 없음.")
                    continue
                lines = [f"[{ename or eid}] 성과 {len(rows)}건:"]
                for r in rows[:20]:
                    period = r.get("period") or "-"
                    text_type = r.get("textType") or r.get("text_type") or "-"
                    content = (r.get("content") or "")[:200].replace("\n", " ")
                    if len((r.get("content") or "")) > 200:
                        content += "…"
                    lines.append(f"  - {period} {text_type}: {content}")
                if len(rows) > 20:
                    lines.append(f"  … 외 {len(rows) - 20}건")
                parts.append("\n".join(lines))
            return "\n\n".join(parts)
        finally:
            db.close()
    except Exception as e:
        return f"성과 조회 실패: {str(e)}"


TOOLS = [
    analyze_with_exaone,
    search_documents,
    get_current_time,
    calculate,
    define,
    get_hr_summary,
    get_employee_info,
    get_employee_performance,
    list_employees,
]
TOOL_MAP: Dict[str, Any] = {t.name: t for t in TOOLS}

TOOL_TABLE_MAP: Dict[str, List[str]] = {
    "get_employee_info": ["employees"],
    "get_employee_performance": ["performance_records"],
    "get_hr_summary": ["employees", "performance_records", "disclosures", "competency_anchors"],
    "list_employees": ["employees"],
    "search_documents": ["disclosures"],
    "define": ["disclosures"],
}


# --- 2. 노드 (model, rag, tool) ---


def _get_llm(provider: Optional[str] = None, **kwargs):
    """LLM 인스턴스 반환 (ExaOne)."""
    from domain.hub.llm import get_llm  # type: ignore

    return get_llm(provider=provider, **kwargs)


def _supports_tool_calling(provider: Optional[str] = None) -> bool:
    """Tool Calling 지원 여부 확인."""
    from domain.hub.llm.exaone_provider import supports_tool_calling  # type: ignore

    return supports_tool_calling(provider)


def _get_llm_provider():
    """LLMProvider 클래스 반환."""
    from domain.hub.llm.exaone_provider import LLMProvider  # type: ignore

    return LLMProvider


def _find_last_user_query(messages: List[BaseMessage]) -> Optional[str]:
    """메시지 목록에서 최근 사용자 질문 텍스트를 찾는다."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
    return None


def _has_tool_message(messages: List[BaseMessage]) -> bool:
    """현재 턴(최근 HumanMessage 이후)에 이미 도구가 실행되었는지 확인."""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return False
        if isinstance(m, ToolMessage):
            return True
    return False


def _extract_employee_name_from_query(query: str) -> Optional[str]:
    """개별 직원 조회/성과 질문에서 이름 후보를 추출."""
    if not query or not query.strip():
        return None
    q = query.strip()
    if not any(k in q for k in ("직원", "직급", "부서", "직무", "성과", "활동", "실적", "지표", "알려")):
        return None
    m = re.search(r"([가-힣]{2,4})의", q)
    if not m:
        return None
    candidate = m.group(1)
    stop_words = {
        "직원", "직급", "부서", "직무", "성과", "활동", "실적", "지표", "기준", "역량", "공시",
        "전체", "일반", "신입", "고성과", "요약", "전환", "준비도", "문서", "상태",
    }
    return None if candidate in stop_words else candidate


def _build_forced_tool_calls(user_query: str) -> List[Dict[str, Any]]:
    """
    모델이 도구를 설명만 하고 호출하지 않을 때, 최소한의 안전한 도구 호출을 강제 생성.
    - 총원/적재상태: get_hr_summary
    - 명단/목록: list_employees
    """
    if not user_query or not user_query.strip():
        return []

    forced_calls: List[Dict[str, Any]] = []
    forced_names: set = set()
    q = user_query.strip().lower()
    q_raw = (user_query or "").strip()
    employee_name = _extract_employee_name_from_query(user_query)

    # 단일 직원 속성 질의("강경구의 직급과 부서 알려줘" 등)는
    # get_employee_info 하나로 충분하다. 불필요한 list_employees·hr_summary
    # 강제 호출을 피해 프롬프트 토큰을 절감하고 응답 품질을 높인다.
    _SINGLE_EMP_ATTR_KWS = (
        "직급", "부서", "직무", "이메일", "기본 정보", "직원 정보",
        "성과", "실적", "활동", "지표", "역량", "입사일",
    )
    is_single_employee_attr = bool(employee_name) and any(
        k in q_raw for k in _SINGLE_EMP_ATTR_KWS
    )

    def _append_forced(name: str, args: Dict[str, Any]) -> None:
        if name in forced_names:
            return
        forced_names.add(name)
        forced_calls.append(
            {
                "id": f"call_{uuid4().hex[:12]}",
                "name": name,
                "args": args,
                "type": "tool_call",
            }
        )

    if _needs_hr_summary_prefetch(user_query) and not is_single_employee_attr:
        _append_forced("get_hr_summary", {})

    # 부서+신입/일반+몇명 질의는 hr_summary 여부와 관계없이 list_employees로 정확한 인원 수 제공
    # 단, 단일 직원 속성 질의는 제외한다.
    if _needs_employee_list_prefetch(user_query) and not is_single_employee_attr:
        is_new_hire_query = ("신입" in q or "지원자" in q)
        is_regular_query = ("기존 직원" in q or "일반 직원" in q)
        is_high_query = ("고성과" in q or "high performer" in q or "highperformer" in q)
        if is_new_hire_query:
            employment_type = "new_hire"
        elif is_regular_query or is_high_query:
            employment_type = "regular"
        else:
            employment_type = "all"
        performance_tier = "high" if ("고성과" in q or "high performer" in q or "highperformer" in q) else "all"
        job_title_part = _infer_job_title_part(user_query)
        department_part = _infer_department_part(user_query)
        is_full_list = any(k in q_raw for k in ("전체 명단", "전체 목록", "전원", "모두 보여", "다 보여", "전부"))
        list_limit = 500 if (is_full_list or is_high_query) else (200 if (department_part or job_title_part or is_new_hire_query) else 200)
        args: Dict[str, Any] = {"employment_type": employment_type, "performance_tier": performance_tier, "limit": list_limit}
        if job_title_part:
            args["job_title"] = job_title_part
        if department_part:
            args["department"] = department_part
        _append_forced("list_employees", args)
        if is_high_query:
            # 고성과자 질의는 성과 테이블 근거도 함께 확보해 source 누락을 줄인다.
            _append_forced("get_hr_summary", {})

    # 개별 직원 성과/지표 질의는 성과 도구 + 기본정보 모두 강제 (5대 지표 등 복합 질의 대응)
    if employee_name and _has_performance_keyword(user_query):
        _append_forced(
            "get_employee_performance",
            {"employee_name_or_id": employee_name, "limit": 30},
        )
        _append_forced("get_employee_info", {"name": employee_name})
    # 개별 직원 기본정보 질의는 직원 정보 도구를 강제
    elif employee_name and any(k in q_raw for k in ("직급", "부서", "직무", "이메일", "직원 정보", "기본 정보")):
        _append_forced("get_employee_info", {"name": employee_name})

    return forced_calls


def model_node(state: ChatState) -> ChatState:
    """모델 노드. LLM 호출·Tool Calling, 스트리밍 지원. 이미지 있으면 Gemini 멀티모달 사용."""
    images: Optional[List[str]] = state.get("images") or []
    if images:
        # 멀티모달: RAG 컨텍스트 + 사용자 메시지 + 이미지를 Gemini에 전달
        messages = list(state.get("messages", []))
        context = state.get("context") or ""
        user_text = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_text = str(msg.content)
                break
        from domain.hub.llm.gemini_adapter import generate_multimodal  # type: ignore

        full_response = generate_multimodal(user_text=user_text, images=images, context=context or None)
        return {"messages": [AIMessage(content=full_response)], "model_provider": "gemini"}

    LLMProvider = _get_llm_provider()
    provider = state.get("model_provider") or LLMProvider.get_provider_name()
    max_tokens = state.get("max_tokens") or 2048
    temperature = state.get("temperature") or 0.7
    llm = _get_llm(provider=provider, max_tokens=max_tokens, temperature=temperature)

    messages = list(state.get("messages", []))
    context = state.get("context")

    if context and messages:
        system_msg_idx = None
        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                system_msg_idx = i
                break
        context_addition = (
            f"\n\n참고 컨텍스트 (아래 문서를 우선 참고하여 답변하고, 인용 시 [출처: ...]를 밝혀 주세요):\n{context}"
            "\n\n답변은 일반 텍스트로만 작성하고, ```json 또는 빈 코드 블록을 사용하지 마세요."
        )
        if system_msg_idx is not None:
            old_content = str(messages[system_msg_idx].content)
            messages[system_msg_idx] = SystemMessage(
                content=old_content + context_addition
            )
        else:
            messages = [
                SystemMessage(
                    content=f"당신은 도움이 되는 AI 어시스턴트입니다.{context_addition}"
                )
            ] + messages

    if _supports_tool_calling(provider):
        llm_with_tools = llm.bind_tools(TOOLS)
        if _has_tool_message(messages):
            # 도구 실행 후 최종 답변 턴: stream() → 클라이언트 실시간 스트리밍
            stream_chunks: List[Any] = []
            for chunk in llm_with_tools.stream(messages):
                stream_chunks.append(chunk)
            if stream_chunks:
                content_parts: List[str] = []
                for c in stream_chunks:
                    part = getattr(c, "content", None) or ""
                    content_parts.append(part if isinstance(part, str) else str(part))
                response = AIMessage(content="".join(content_parts))
            else:
                response = AIMessage(content="")
            logger.info("[MODEL] 최종 답변 턴 스트리밍 완료 (청크 %d개)", len(stream_chunks))
        else:
            # 1턴 최적화: LLM invoke 생략, _build_forced_tool_calls로 직접 도구 결정
            user_query = _find_last_user_query(messages) or ""
            forced_calls = _build_forced_tool_calls(user_query)
            if forced_calls:
                logger.info("[MODEL] 1턴 최적화: LLM 미호출, 강제 도구 직접 적용: %s", [c["name"] for c in forced_calls])
                response = AIMessage(content="", tool_calls=forced_calls)
            else:
                # 도구 불필요 → LLM 1회만 호출하여 바로 스트리밍 답변
                logger.info("[MODEL] 1턴 최적화: 도구 불필요, 직접 스트리밍 답변")
                stream_chunks_direct: List[Any] = []
                for chunk in llm_with_tools.stream(messages):
                    stream_chunks_direct.append(chunk)
                if stream_chunks_direct:
                    content_parts_direct: List[str] = []
                    for c in stream_chunks_direct:
                        part = getattr(c, "content", None) or ""
                        content_parts_direct.append(part if isinstance(part, str) else str(part))
                    response = AIMessage(content="".join(content_parts_direct))
                else:
                    response = AIMessage(content="")
    else:
        chunks = []
        for chunk in llm.stream(messages):
            chunks.append(chunk)
        if chunks:
            full_content = "".join(
                chunk.content for chunk in chunks
                if hasattr(chunk, "content") and chunk.content
            )
            response = AIMessage(content=full_content)
        else:
            response = AIMessage(content="")

    return {"messages": [response], "model_provider": provider}


def tool_node(state: ChatState) -> ChatState:
    """도구 노드. tool_calls 실행 후 ToolMessage 반환."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    results: List[BaseMessage] = []

    tool_calls = getattr(last_message, "tool_calls", None) if last_message else None
    if tool_calls:
        logger.info("[TOOLS] executing tool_calls=%s", len(tool_calls))
        for call in tool_calls:
            name = call["name"]
            args = call.get("args", {})
            if name in TOOL_MAP:
                try:
                    output = TOOL_MAP[name].invoke(args)
                    logger.info("[TOOLS] executed: %s", name)
                except Exception as e:
                    output = f"도구 실행 오류: {str(e)}"
                    logger.warning("[TOOLS] failed: %s err=%s", name, e)
            else:
                output = f"알 수 없는 도구: {name}"
                logger.warning("[TOOLS] skipped unknown tool: %s", name)
            results.append(
                ToolMessage(
                    content=str(output),
                    tool_call_id=call["id"],
                    name=name,
                )
            )

    return {"messages": results}


# 질문과 무관한 문서 제외: 거리(score)가 이 값 이하인 문서만 참고 (코사인 거리, 작을수록 유사).
# 임계값 통과 0건이면 컨텍스트 없이 모델 자체 지식으로만 답하고 출처 미표시.
RAG_DISTANCE_THRESHOLD = 0.8
# 라우트 미감지 테이블 검색 시 엄격 임계값 — 정말 유사한 것만 포함
RAG_STRICT_THRESHOLD = 0.5
# 표준 키워드 없을 때: 최소거리가 이 값보다 크면 "공시 무관 질문"으로 보고 disclosure 결과 전부 제외
RAG_DISCLOSURE_NO_KEYWORD_MAX_DISTANCE = 0.75
# competency_anchors fallback: 최소거리 1건 넣을 때의 상한. 이보다 크면 무관한 질문으로 보고 fallback 안 함
RAG_ANCHOR_FALLBACK_MAX_DISTANCE = 0.9
# performance_records fallback: competency와 동일 패턴
RAG_PERF_FALLBACK_MAX_DISTANCE = 0.9
# 직원 검색: 엉뚱한 인물 추천 방지를 위해 disclosure/competency보다 엄격 (작을수록 유사, 0.6 이하만 포함)
RAG_EMPLOYEE_DISTANCE_THRESHOLD = 0.6

def _infer_disclosure_standard_filter(query: str) -> Optional[Dict[str, Any]]:
    """
    질문 텍스트에서 참조할 disclosure 표준을 추론해 메타데이터 필터 dict 반환.
    (메타데이터 필터용)
    """
    types = _infer_disclosure_standard_types(query)
    if not types:
        return None
    if len(types) == 1:
        return {"standard_type": types[0]}
    return {"standard_type": {"$in": types}}


def _infer_disclosure_standard_types(query: str) -> Optional[List[str]]:
    """
    질문 텍스트에서 참조할 disclosure 표준을 추론해 standard_type 리스트 반환.
    한글 검색도 적용 (공시, 기후, 탄소, 인적자본, OECD 등).
    - IFRS/S1/S2/국제 재무/기후 공시/탄소 → ['IFRS_S1', 'IFRS_S2']
    - OECD/경제협력 → ['OECD']
    - ISO/30414/인적자본 공시 → ['ISO30414']
    - green stock/stocktake/그린스톡 → ['GLOBAL_GREEN_STOCKTAKE']
    """
    if not query or not query.strip():
        return None
    q = query.strip().lower()
    q_no_space = q.replace(" ", "")
    # IFRS S1/S2: 국제 재무, 기후 공시, 탄소 공시, 지속가능성 공시 등
    if (
        "ifrs" in q or "s1" in q or "s2" in q
        or "국제 재무" in q or "국제재무" in q
        or "기후" in q or "탄소" in q or "지속가능" in q or "esg" in q
        or ("공시" in q_no_space and ("기후" in q or "탄소" in q or "재무" in q))
    ):
        return ["IFRS_S1", "IFRS_S2"]
    if "oecd" in q or "경제협력" in q or "경제 협력" in q or "경제협력기구" in q:
        return ["OECD"]
    if "iso" in q or "30414" in q or "인적자본" in q or "인적 자본" in q or "인사 공시" in q:
        return ["ISO30414"]
    # 글로벌 그린 스톡테이크
    if (
        "green stock" in q or "stocktake" in q or "global green" in q
        or "그린스탁" in q or "그린 스탁" in q or "그린 스톡" in q or "그린스톡" in q
        or "그린스톡" in q_no_space or "그린스탁" in q_no_space
        or "스톡테이크" in q or "스톡 테이크" in q
    ):
        return ["GLOBAL_GREEN_STOCKTAKE"]
    # "공시" 단독 — 특정 표준이 아닌 일반 공시 질문 → 전체 표준 검색
    if "공시" in q and not any(k in q for k in ("기후", "탄소", "재무")):
        return ["ISO30414", "IFRS_S1", "IFRS_S2"]
    return None


def _has_competency_keyword(query: str) -> bool:
    """질문에 직업/역량/능력 관련 키워드가 있는지. 없으면 competency_anchors 출처 미포함.
    O*NET 등 역량/능력 용어(comprehension, fluency, ideas 등) 포함."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    keywords = (
        "직업", "역량", "능력", "직무", "스킬", "skill", "competency", "ability",
        "onet", "o*net", "ncs", "수행준거", "지식", "기술", "태도",
        "comprehension", "fluency", "ideas", "expression", "reasoning", "writing",
        "oral", "written", "originality", "deductive", "inductive", "memorization",
        "mathematical", "number facility", "problem sensitivity", "selective attention",
        "문제해결", "의사소통", "리더십", "협업", "적응력",
        "leadership", "collaboration", "adaptability",
    )
    return any(kw in q for kw in keywords)


def _has_employee_keyword(query: str) -> bool:
    """질문에 직원/인력/이력서/부서/신입 관련 키워드가 있는지. 있으면 employees 테이블도 RAG 검색."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    keywords = (
        "직원", "임직원", "인력", "사람", "스태프", "employee", "staff", "직원 수",
        "이력서", "resume", "경력", "학력", "부서", "department", "팀", "team",
        "누가", "누구", "어떤 사람", "교육 이수", "훈련", "training",
        "신입", "지원자", "applicant", "채용", "입사", "후보",
        "성과", "활동", "실적", "performance", "회의록", "보고서",
        "명단", "목록", "인원", "사원", "직급", "소속",
        "고성과", "저성과", "기존 직원", "전체 직원", "현재 직원",
        "rag", "문서등록", "적재",
    )
    return any(kw in q for kw in keywords)


def _has_performance_keyword(query: str) -> bool:
    """질문에 성과/활동/실적 관련 키워드가 있는지."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    keywords = (
        "성과", "활동", "실적", "performance", "회의록", "보고서", "이메일 실적",
        "분기 성과", "kpi", "평가", "성과 기록",
        "지표", "목표", "달성", "업적", "고성과", "저성과", "기여",
        "성과등급", "고성과자", "분기별", "연간 성과", "프로젝트",
    )
    return any(kw in q for kw in keywords)


def _infer_query_routes(query: str) -> Dict[str, bool]:
    """질의에서 사용할 데이터 라우트 추론(명시 로그/범위 판별용)."""
    return {
        "employees": _has_employee_keyword(query),
        "performance_records": _has_performance_keyword(query),
        "competency_anchors": _has_competency_keyword(query),
        "disclosures": _infer_disclosure_standard_types(query) is not None,
    }


def _build_rag_sources(docs: List[Any]) -> List[Dict[str, Any]]:
    """프론트 출처 표시용: table, id, source, page, standard_type, section_title, name, department 등."""
    out: List[Dict[str, Any]] = []
    for doc in docs:
        meta = getattr(doc, "metadata", None) or {}
        row = {
            "table": meta.get("table", "disclosures"),
            "id": meta.get("id") or meta.get("doc_id"),
            "source": meta.get("source", ""),
            "page": meta.get("page"),
            "standard_type": meta.get("standard_type", ""),
            "section_title": meta.get("section_title", ""),
            "unique_id": meta.get("unique_id", ""),
        }
        if meta.get("name") is not None:
            row["name"] = meta.get("name")
        if meta.get("department") is not None:
            row["department"] = meta.get("department")
        if meta.get("job_title") is not None:
            row["job_title"] = meta.get("job_title")
        out.append(row)
    return out


def _build_context_with_sources(docs: List[Any]) -> str:
    """각 문서 앞에 [출처: id=..., source=..., page=...] 를 붙여 DB에서 찾을 수 있게 함."""
    parts = []
    for doc in docs:
        meta = getattr(doc, "metadata", None) or {}
        id_val = meta.get("id") or meta.get("doc_id")
        source = meta.get("source", "")
        page = meta.get("page", "")
        standard_type = meta.get("standard_type", "")
        unique_id = meta.get("unique_id", "")
        tokens = []
        if id_val is not None:
            tokens.append(f"id={id_val}")
        if source:
            tokens.append(f"source={source}")
        if page != "":
            tokens.append(f"page={page}")
        if standard_type:
            tokens.append(f"standard_type={standard_type}")
        if unique_id:
            tokens.append(f"unique_id={unique_id}")
        if meta.get("category"):
            tokens.append(f"category={meta.get('category')}")
        if meta.get("section_title"):
            tokens.append(f"section_title={meta.get('section_title')}")
        if meta.get("name"):
            tokens.append(f"name={meta.get('name')}")
        if meta.get("department"):
            tokens.append(f"department={meta.get('department')}")
        if meta.get("job_title"):
            tokens.append(f"job_title={meta.get('job_title')}")
        cite = "[출처: " + ", ".join(tokens) + "]" if tokens else "[출처: (메타데이터 없음)]"
        parts.append(f"{cite}\n{doc.page_content}")
    return "\n\n".join(parts)


def _infer_job_title_part(query: str) -> Optional[str]:
    """질의에서 직급 키워드를 추정해 list_for_chat의 job_title_part로 사용."""
    if not query or not query.strip():
        return None
    q = query.strip().lower()
    # '사원'은 일반적으로 "전체 직원" 의미로 쓰이는 경우가 많아 기본 필터에서 제외.
    # 직급 필터는 "직급 사원", "사원 직급", "사원만"처럼 명시된 경우에만 적용.
    explicit_staff_title = (
        "직급 사원" in q
        or "사원 직급" in q
        or "사원만" in q
        or "사원만 보여" in q
    )
    for token in ("팀장", "과장", "부장", "차장", "대리", "주임", "인턴"):
        if token in q:
            return token
    if explicit_staff_title:
        return "사원"
    return None


def _infer_department_part(query: str) -> Optional[str]:
    """질의에서 부서 키워드를 추정해 list_for_chat의 department_part로 사용. 부서명은 개발·IT로 통일."""
    if not query or not query.strip():
        return None
    q = query.strip().lower()
    q_no_space = q.replace(" ", "")
    if "개발·it" in q or "개발/it" in q or "개발it" in q_no_space:
        return "개발·IT"
    if "기술" in q:  # 부서명 통일: 기술/기술팀 등 → 개발·IT
        return "개발·IT"
    for token in ("영업", "마케팅", "인사", "재무", "전략기획", "경영지원", "감사"):
        if token in q_no_space:
            return token
    return None


def _needs_hr_summary_prefetch(query: str) -> bool:
    """총원/건수형 질문은 모델 도구호출 실패를 대비해 요약을 선제 조회."""
    if not query or not query.strip():
        return False
    q = query.strip().lower().replace(" ", "")
    keywords = (
        "직원수", "일반직원수", "임직원수", "총몇", "몇명", "몇명이", "전체직원", "전체임직원", "총원",
        "공시완성도", "적재상태", "rag문서", "rag", "등록되어",
        "합격", "탈락", "미검토", "심사중", "지원자",
    )
    return any(k in q for k in keywords)


def _needs_employee_list_prefetch(query: str) -> bool:
    """명단/누구/보여줘/알려줘 계열 질문은 직원 목록을 선제 조회. 부서+신입/일반+몇명도 list_employees로."""
    if not query or not query.strip():
        return False
    q = query.strip().lower()
    list_keywords = ("누가", "누구", "명단", "목록", "보여", "고성과")
    if any(k in q for k in list_keywords):
        return True
    if ("신입" in q or "지원자" in q) and any(ak in q for ak in ("알려", "조회", "검색", "확인")):
        return True
    # 부서별 신입/일반 인원 수 → list_employees 호출해 부서 필터 결과 사용 (prefetch 전체 수 301 사용 방지)
    if any(t in q for t in ("몇명", "몇 명", "인원", "수")) and any(t in q for t in ("신입", "일반", "지원자")):
        if any(d in q for d in ("부서", "개발", "it", "기술", "영업", "마케팅", "인사", "재무")):
            return True
    return False


def _build_prefetch_context(
    db: Any,
    user_query: str,
    routes: Dict[str, bool],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    모델이 tool call을 실패해도 답할 수 있도록 DB 기반 운영 컨텍스트를 선제 주입.
    - 직원 총원/적재상태 질문: HR 요약만 prefetch (명단은 list_employees 도구로만 제공)
    """
    parts: List[str] = []
    sources: List[Dict[str, Any]] = []

    if routes.get("employees") and _needs_hr_summary_prefetch(user_query):
        try:
            from domain.hub.repositories.employee_repository import (  # type: ignore
                count_all as repo_count_all,
                is_new_hire_pipeline_employee_row,
                is_onboarded_regular_employee_row,
                list_all as repo_list_all,
            )
            from domain.hub.repositories.performance_record_repository import get_performance_record_count  # type: ignore
            from domain.hub.repositories.disclosure_repository import get_disclosure_doc_count  # type: ignore
            from domain.hub.repositories.competency_anchor_repository import get_anchor_doc_count  # type: ignore

            employee_count = repo_count_all(db)
            rows_all = repo_list_all(db) or []

            regular_count = sum(1 for e in rows_all if is_onboarded_regular_employee_row(e))
            pipeline_rows = [e for e in rows_all if is_new_hire_pipeline_employee_row(e)]
            new_hire_count = len(pipeline_rows)
            breakdown_lines = _ats_pipeline_status_breakdown_lines(pipeline_rows)
            perf_count = get_performance_record_count(db)
            disclosure_count = get_disclosure_doc_count(db)
            anchor_count = get_anchor_doc_count(db)
            parts.append(
                "[운영 요약]\n"
                "※ 일반(입사 확정)=employment_type=regular + 입사일(joinedAt) 있음. 신입·지원=ATS 또는 new_hire.\n"
                "※ '합격자'=DB status=hired(ATS 합격). 신입 지원 풀 전체(298 등)와 다름.\n"
                f"전체 레코드 수: {employee_count}명\n"
                f"입사 확정·재직 직원 수: {regular_count}명\n"
                f"신입·지원 풀 합계: {new_hire_count}명\n"
                + "\n".join(breakdown_lines)
                + "\n"
                f"성과(performance_records) 기록: {perf_count}건\n"
                f"공시(disclosures) 문서 청크: {disclosure_count}건\n"
                f"역량(competency_anchors) 문서: {anchor_count}건"
            )
            sources.extend(
                [
                    {"table": "employees", "id": "prefetch:hr_summary", "source": "prefetch"},
                    {"table": "performance_records", "id": "prefetch:hr_summary", "source": "prefetch"},
                    {"table": "disclosures", "id": "prefetch:hr_summary", "source": "prefetch"},
                    {"table": "competency_anchors", "id": "prefetch:hr_summary", "source": "prefetch"},
                ]
            )
        except Exception as e:
            logger.info("[RAG] prefetch 실패(계속 진행): %s", e)

    text = "\n\n".join(parts).strip()
    if not text:
        return "", []
    # 중복 소스 제거
    uniq: List[Dict[str, Any]] = []
    seen = set()
    for s in sources:
        key = (s.get("table"), s.get("id"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(s)
    return text, uniq


def rag_node(state: ChatState) -> ChatState:
    """RAG 노드. Query 분류(공시 기준 / 인물·역량 / 복합)에 따라 검색 후 컨텍스트 융합.
    - 공시 기준 질문: disclosures 검색 (standard_types).
    - 인물·역량 질문: competency_anchors 검색.
    - 직원/인력 질문: employees 검색 (pgvector HNSW, 임계값 0.6).
    - 복합(예: 직원 중 ISO 30414 만족하는 사람): disclosure + employees 둘 다 검색해 all_docs에 합침.
    """
    messages = state.get("messages", [])

    user_query: Optional[str] = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = str(msg.content)
            break

    if not user_query:
        return {"context": "", "rag_sources": []}

    # 로그 레벨과 관계없이 RAG 진입을 확인할 수 있도록 WARNING 사용
    _q = (user_query[:80] + "…") if len(user_query) > 80 else user_query
    logger.warning("[RAG] 질의 처리 중: %s", _q)

    # 단일 직원 속성 질의("강경구의 직급과 부서 알려줘" 등)는 get_employee_info
    # 도구가 정답을 바로 제공하므로, 긴 employees RAG 문서 주입을 생략해
    # 프롬프트 토큰과 CPU 추론 시간을 크게 줄인다.
    _fast_name = _extract_employee_name_from_query(user_query)
    if _fast_name and any(
        k in user_query for k in ("직급", "부서", "직무", "이메일", "기본 정보", "직원 정보")
    ):
        logger.info(
            "[RAG] 단일 직원 속성 질의 감지(name=%s) → RAG 생략, get_employee_info 전용 경로",
            _fast_name,
        )
        return {"context": "", "rag_sources": []}

    routes = _infer_query_routes(user_query)
    logger.info(
        "[RAG] route: employees=%s, performance_records=%s, competency_anchors=%s, disclosures=%s",
        routes["employees"],
        routes["performance_records"],
        routes["competency_anchors"],
        routes["disclosures"],
    )

    # 모든 라우트가 False → 데이터 범위 밖 질문. 검색 없이 즉시 OOS 반환.
    if not any(routes.values()):
        logger.info("[RAG] 모든 라우트 미감지 → out_of_scope 즉시 반환")
        oos = (
            "★ 필수 지시: 답변의 첫 문장을 반드시 다음과 같이 시작하세요 → "
            "'[시스템 안내] 이 질문은 현재 데이터 범위(employees, performance_records, disclosures, competency_anchors) 밖의 질문입니다.'\n"
            "그 다음 줄부터 일반 지식으로 간략히 답변하세요."
        )
        return {
            "context": oos,
            "rag_sources": [{"table": "system", "source": "out_of_scope", "id": "OUT_OF_SCOPE"}],
        }

    try:
        if "fastapi_server" in sys.modules:
            import fastapi_server  # type: ignore

            fastapi_server.ensure_rag_initialized()
            all_docs: list = []
            main_count = 0  # LangChain PGVector 미사용 (disclosures·competency 테이블만 사용)
            # disclosures 테이블 검색 (id, content, embedding, source, page, standard_type, section_title, metadata, unique_id)
            # 표준 판별 시 해당 standard_type만 검색
            disclosure_count_before_threshold = 0
            try:
                from core.database import SessionLocal  # type: ignore
                from domain.hub.repositories.disclosure_repository import (  # type: ignore
                    search_disclosures_with_filter,
                    search_disclosures_hybrid,
                )
                from domain.hub.repositories.competency_anchor_repository import (  # type: ignore
                    search_competency_anchors_with_filter,
                    search_competency_anchors_hybrid,
                )
                from domain.hub.repositories.employee_repository import (  # type: ignore
                    search_employees_with_filter,
                )
                from domain.hub.repositories.performance_record_repository import (  # type: ignore
                    search_performance_records_with_filter,
                    search_performance_records_hybrid,
                )

                # disclosure 테이블은 FlagEmbedding(BGE-m3)으로 적재됨 → 쿼리도 동일 모델(fp16)로 같은 벡터 공간
                query_vec = None
                try:
                    from domain.shared.embedding import get_disclosure_embedding_model  # type: ignore
                    bge = get_disclosure_embedding_model()
                    if bge is not None and hasattr(bge, "embed_query"):
                        for attempt in range(2):
                            try:
                                query_vec = bge.embed_query(user_query)
                                break
                            except Exception as _e1:
                                if attempt == 0:
                                    logger.warning("[RAG] disclosure embed_query 1회 실패, 재시도: %s", _e1)
                                else:
                                    raise
                except Exception as _e:
                    logger.warning("[RAG] disclosure 쿼리 임베딩 실패: %s", _e)
                if query_vec is None:
                    emb = getattr(fastapi_server, "local_embeddings", None)
                    if emb is not None and hasattr(emb, "embed_query"):
                        query_vec = emb.embed_query(user_query)
                prefetch_text, prefetch_sources = "", []
                if query_vec is not None:
                    db = SessionLocal()
                    try:
                        prefetch_text, prefetch_sources = _build_prefetch_context(db, user_query, routes)
                        # --- disclosures: 항상 검색, 라우트 여부에 따라 임계값 차등 ---
                        disc_threshold = RAG_DISTANCE_THRESHOLD if routes["disclosures"] else RAG_STRICT_THRESHOLD
                        standard_types = _infer_disclosure_standard_types(user_query) if routes["disclosures"] else None
                        try:
                            pairs = search_disclosures_hybrid(
                                db, query_vec, user_query, k=10, standard_types=standard_types
                            )
                        except Exception:
                            pairs = search_disclosures_with_filter(
                                db, query_vec, k=10, standard_types=standard_types
                            )
                        disclosure_count_before_threshold = len(pairs)
                        disclosure_passed = 0
                        min_distance = None
                        closest_doc = None
                        passed_docs: List[Any] = []
                        for doc, distance in pairs:
                            if min_distance is None or distance < min_distance:
                                min_distance = distance
                                closest_doc = doc
                            if distance <= disc_threshold:
                                passed_docs.append(doc)
                                disclosure_passed += 1
                        no_kw_max = RAG_DISCLOSURE_NO_KEYWORD_MAX_DISTANCE if routes["disclosures"] else RAG_STRICT_THRESHOLD
                        if min_distance is not None and min_distance > no_kw_max:
                            passed_docs = []
                            disclosure_passed = 0
                            logger.info(
                                "[RAG] disclosure: 최소거리=%.4f > %.2f → disclosure 제외 (routed=%s)",
                                min_distance, no_kw_max, routes["disclosures"],
                            )
                        else:
                            for doc in passed_docs:
                                if getattr(doc, "metadata", None) is not None:
                                    doc.metadata["table"] = "disclosures"
                                all_docs.append(doc)
                            if (
                                disclosure_count_before_threshold > 0
                                and disclosure_passed == 0
                                and closest_doc is not None
                                and routes["disclosures"]
                            ):
                                if getattr(closest_doc, "metadata", None) is not None:
                                    closest_doc.metadata["table"] = "disclosures"
                                all_docs.append(closest_doc)
                                disclosure_passed = 1
                                logger.info(
                                    "[RAG] disclosure: 임계값 미통과 → 최소거리 1건 포함, 거리=%.4f",
                                    min_distance or 0,
                                )
                        logger.info(
                            "[RAG] disclosure(hybrid): standard_types=%s, 후보=%s, 임계값 통과=%s (threshold=%.2f, routed=%s)",
                            standard_types, disclosure_count_before_threshold,
                            disclosure_passed, disc_threshold, routes["disclosures"],
                        )
                        # --- competency_anchors: 항상 검색, 라우트 여부에 따라 임계값 차등 ---
                        anchor_threshold = RAG_DISTANCE_THRESHOLD if routes["competency_anchors"] else RAG_STRICT_THRESHOLD
                        anchor_passed = 0
                        try:
                            anchor_pairs = search_competency_anchors_hybrid(db, query_vec, user_query, k=5)
                        except Exception:
                            anchor_pairs = search_competency_anchors_with_filter(db, query_vec, k=5)
                        min_anchor_distance = None
                        closest_anchor_doc = None
                        for doc, distance in anchor_pairs:
                            if min_anchor_distance is None or distance < min_anchor_distance:
                                min_anchor_distance = distance
                                closest_anchor_doc = doc
                            if distance <= anchor_threshold:
                                if getattr(doc, "metadata", None) is not None:
                                    doc.metadata["table"] = "competency_anchors"
                                all_docs.append(doc)
                                anchor_passed += 1
                        if (
                            anchor_pairs
                            and anchor_passed == 0
                            and closest_anchor_doc is not None
                            and routes["competency_anchors"]
                            and (min_anchor_distance is not None and min_anchor_distance <= RAG_ANCHOR_FALLBACK_MAX_DISTANCE)
                        ):
                            if getattr(closest_anchor_doc, "metadata", None) is not None:
                                closest_anchor_doc.metadata["table"] = "competency_anchors"
                            all_docs.append(closest_anchor_doc)
                            anchor_passed = 1
                            logger.info(
                                "[RAG] competency_anchors: 임계값 미통과 → 최소거리 1건 포함 (거리=%.4f <= %.2f)",
                                min_anchor_distance or 0,
                                RAG_ANCHOR_FALLBACK_MAX_DISTANCE,
                            )
                        elif anchor_pairs and anchor_passed == 0 and min_anchor_distance is not None:
                            logger.info(
                                "[RAG] competency_anchors: 최소거리=%.4f, threshold=%.2f, routed=%s → 제외",
                                min_anchor_distance, anchor_threshold, routes["competency_anchors"],
                            )
                        logger.info(
                            "[RAG] competency_anchors(hybrid): 후보=%s, 임계값 통과=%s (threshold=%.2f, routed=%s)",
                            len(anchor_pairs), anchor_passed, anchor_threshold, routes["competency_anchors"],
                        )
                        # --- employees: 항상 검색, 라우트 여부에 따라 임계값 차등 ---
                        emp_threshold = RAG_EMPLOYEE_DISTANCE_THRESHOLD if routes["employees"] else RAG_STRICT_THRESHOLD
                        emp_pairs = search_employees_with_filter(db, query_vec, k=5)
                        emp_passed = 0
                        for doc, dist in emp_pairs:
                            if dist <= emp_threshold:
                                if getattr(doc, "metadata", None) is not None:
                                    doc.metadata["table"] = "employees"
                                all_docs.append(doc)
                                emp_passed += 1
                        logger.info(
                            "[RAG] employees: 후보=%s, 임계값 통과=%s (threshold=%.2f, routed=%s)",
                            len(emp_pairs), emp_passed, emp_threshold, routes["employees"],
                        )
                        # --- performance_records: 항상 검색, 하이브리드 + fallback ---
                        perf_threshold = RAG_DISTANCE_THRESHOLD if routes["performance_records"] else RAG_STRICT_THRESHOLD
                        try:
                            try:
                                perf_pairs = search_performance_records_hybrid(db, query_vec, user_query, k=5)
                            except Exception:
                                perf_pairs = search_performance_records_with_filter(db, query_vec, k=5)
                            perf_passed = 0
                            min_perf_dist = None
                            closest_perf_doc = None
                            for doc, dist in perf_pairs:
                                if min_perf_dist is None or dist < min_perf_dist:
                                    min_perf_dist = dist
                                    closest_perf_doc = doc
                                if dist <= perf_threshold:
                                    if getattr(doc, "metadata", None) is not None:
                                        doc.metadata["table"] = "performance_records"
                                    all_docs.append(doc)
                                    perf_passed += 1
                            if (
                                perf_pairs
                                and perf_passed == 0
                                and closest_perf_doc is not None
                                and routes["performance_records"]
                                and min_perf_dist is not None
                                and min_perf_dist <= RAG_PERF_FALLBACK_MAX_DISTANCE
                            ):
                                if getattr(closest_perf_doc, "metadata", None) is not None:
                                    closest_perf_doc.metadata["table"] = "performance_records"
                                all_docs.append(closest_perf_doc)
                                perf_passed = 1
                                logger.info(
                                    "[RAG] performance_records: 임계값 미통과 → 최소거리 1건 포함 (거리=%.4f <= %.2f)",
                                    min_perf_dist, RAG_PERF_FALLBACK_MAX_DISTANCE,
                                )
                            logger.info(
                                "[RAG] performance_records(hybrid): 후보=%s, 임계값 통과=%s (threshold=%.2f, routed=%s)",
                                len(perf_pairs), perf_passed, perf_threshold, routes["performance_records"],
                            )
                        except Exception as _pe:
                            logger.info("[RAG] performance_records 검색 생략 (embedding 미설정 가능): %s", _pe)
                    finally:
                        db.close()
                else:
                    logger.warning("RAG disclosure: embed_query 사용 가능한 모델 없음, disclosure 검색 생략")
            except Exception as e:
                logger.warning("RAG disclosure(테이블) 검색 실패: %s", e, exc_info=True)
                prefetch_text, prefetch_sources = "", []
            if all_docs:
                context = _build_context_with_sources(all_docs)
                rag_sources = _build_rag_sources(all_docs)
                if prefetch_text:
                    context = f"{prefetch_text}\n\n{context}".strip()
                    existing = {(s.get("table"), s.get("id")) for s in rag_sources}
                    for s in prefetch_sources:
                        key = (s.get("table"), s.get("id"))
                        if key not in existing:
                            rag_sources.append(s)
                            existing.add(key)
                logger.info(
                    "[RAG] context 사용: main=%s, disclosure+anchor 포함 총 %s건",
                    main_count,
                    len(all_docs),
                )
                return {"context": context, "rag_sources": rag_sources}
            if prefetch_text:
                logger.info("[RAG] 벡터 검색 0건, prefetch 컨텍스트로 답변 유도")
                return {"context": prefetch_text, "rag_sources": prefetch_sources}
            logger.info(
                "[RAG] 검색 결과 없음 (main=%s, disclosure 후보=%s, threshold=%.2f)",
                main_count,
                disclosure_count_before_threshold,
                RAG_DISTANCE_THRESHOLD,
            )
        return {"context": "", "rag_sources": []}
    except Exception as e:
        logger.warning("RAG 검색 실패: %s", e)
        return {"context": "", "rag_sources": []}


# --- 3. 체크포인터 ---

_checkpointer: Optional[MemorySaver] = None


def get_checkpointer() -> MemorySaver:
    """체크포인터 인스턴스 반환 (싱글톤)."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def get_thread_config(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """스레드 설정 반환."""
    if thread_id:
        return {"configurable": {"thread_id": thread_id}}
    return {}


# --- 4. 조건 (라우팅) ---
def should_use_tools(state: ChatState) -> Literal["tools", "__end__"]:
    """도구 사용 여부 결정. tool_calls 있으면 tools, 없으면 종료."""
    messages = state.get("messages", [])
    if not messages:
        return "__end__"
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, "tool_calls", None)
        if tool_calls:
            logger.info("[ROUTE] model -> tools (%s calls)", len(tool_calls))
            return "tools"
    logger.info("[ROUTE] model -> end (tool_calls 없음)")
    return "__end__"


# --- 5. 그래프 빌더 ---
_default_graph = None


def build_agent_graph(use_checkpointer: bool = True):
    """에이전트 그래프 빌드. RAG는 항상 사용 (진입점: rag → model)."""
    graph = StateGraph(ChatState)
    graph.add_node("rag", rag_node)
    graph.add_node("model", model_node)
    graph.add_node("tools", tool_node)

    # 진입점: rag → model (RAG 항상 사용)
    graph.set_entry_point("rag")
    graph.add_edge("rag", "model")

    graph.add_conditional_edges(
        "model",
        should_use_tools,
        {"tools": "tools", "__end__": END},
    )
    graph.add_edge("tools", "model")

    checkpointer = get_checkpointer() if use_checkpointer else None
    return graph.compile(checkpointer=checkpointer)


def get_default_graph():
    """기본 에이전트 그래프 반환 (싱글톤)."""
    global _default_graph
    if _default_graph is None:
        _default_graph = build_agent_graph(use_checkpointer=True)
    return _default_graph


__all__ = [
    "get_checkpointer",
    "get_thread_config",
    "should_use_tools",
    "TOOLS",
    "TOOL_MAP",
    "TOOL_TABLE_MAP",
    "build_agent_graph",
    "get_default_graph",
    "model_node",
    "rag_node",
    "tool_node",
]
