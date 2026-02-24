"""
Chat Orchestrator — 채팅 그래프 실행 진입점

run_agent, run_agent_stream, get_thread_history, clear_thread_history
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

from core.config import settings  # type: ignore
from domain.models import ChatState
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from langchain_core.messages import ToolMessage as _ToolMessage

from .graph_orchestrator import (
    TOOL_TABLE_MAP,
    build_agent_graph,
    get_checkpointer,
    get_default_graph,
    get_thread_config,
)

logger = logging.getLogger(__name__)


def _merge_tool_sources(
    rag_sources: List[Dict[str, Any]],
    tools_used: set,
) -> List[Dict[str, Any]]:
    """도구 사용 내역을 rag_sources에 병합. 도구가 사용됐으면 OUT_OF_SCOPE 제거."""
    if not tools_used:
        return rag_sources
    tool_tables: set = set()
    for tool_name in tools_used:
        for table in TOOL_TABLE_MAP.get(tool_name, []):
            tool_tables.add((table, tool_name))
    if not tool_tables:
        return rag_sources
    merged = [s for s in rag_sources if s.get("id") != "OUT_OF_SCOPE"]
    existing = {s.get("table") for s in merged}
    for table, tool_name in tool_tables:
        if table not in existing:
            merged.append({"table": table, "id": f"tool:{tool_name}", "source": f"tool:{tool_name}"})
            existing.add(table)
    return merged


def _extract_tool_name(message: Any) -> Optional[str]:
    """ToolMessage/직렬화 dict 모두에서 도구명을 안전하게 추출."""
    if isinstance(message, _ToolMessage):
        name = getattr(message, "name", None)
        if isinstance(name, str) and name:
            return name
    if isinstance(message, dict):
        name = message.get("name")
        if isinstance(name, str) and name:
            return name
    name = getattr(message, "name", None)
    if isinstance(name, str) and name:
        return name
    return None


def _extract_tool_call_names(message: Any) -> List[str]:
    """AIMessage(tool_calls)에서 도구명 목록을 안전하게 추출."""
    out: List[str] = []
    tool_calls: Any = None
    if isinstance(message, dict):
        tool_calls = message.get("tool_calls")
    else:
        tool_calls = getattr(message, "tool_calls", None)
    if isinstance(tool_calls, list):
        for call in tool_calls:
            if isinstance(call, dict):
                name = call.get("name")
                if isinstance(name, str) and name:
                    out.append(name)
    return out


def run_agent(
    user_text: str,
    provider: Optional[str] = None,
    system_prompt: Optional[str] = None,
    chat_history: Optional[List[BaseMessage]] = None,
    thread_id: Optional[str] = None,
    images: Optional[List[str]] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Tuple[str, str, List[Dict[str, Any]]]:
    """에이전트를 실행하고 응답을 반환합니다. RAG는 항상 사용.

    Args:
        user_text: 사용자 메시지
        provider: LLM 제공자
        system_prompt: 시스템 프롬프트
        chat_history: 이전 대화 기록
        thread_id: 대화 스레드 ID
        max_tokens: 생성 최대 토큰 (이력서 등 속도 최적화 시 1024 등)
        temperature: 생성 온도 (이력서 등 0.3 권장)

    Returns:
        (에이전트 응답 문자열, RAG에서 사용한 컨텍스트)
    """
    use_checkpointer = bool(thread_id)
    graph = get_default_graph() if use_checkpointer else build_agent_graph(use_checkpointer=False)

    # 이미지만 첨부한 경우: 이미지에서 검색용 문장 추출 → RAG 쿼리로 사용
    if images and (not (user_text or "").strip() or (user_text or "").strip() == "[이미지 첨부]"):
        from domain.hub.llm.gemini_adapter import get_image_caption_for_rag  # type: ignore

        caption = get_image_caption_for_rag(images)
        if caption:
            user_text = caption
            logger.info("[이미지→RAG] 캡션 추출 후 쿼리 사용: %s", (caption[:80] + "…") if len(caption) > 80 else caption)

    _DEFAULT_SYSTEM = (
        "당신은 도움이 되는 AI 어시스턴트입니다. "
        "답변은 일반 텍스트(문단)로만 작성하고, ```json 또는 불필요한 코드 블록을 사용하지 마세요."
    )
    _HR_TOOLS_GUIDE = (
        "HR 관련 질문 시 반드시 아래 도구와 RAG를 사용하세요. 답변은 도구·RAG 결과(employees, performance_records, disclosures, competency_anchors)를 종합해 작성합니다.\n"
        "직원 수·등록 인원·공시/역량/성과 적재 상태 질문 → get_hr_summary 도구 호출.\n"
        "특정 직원(이름) 기본 정보·직급·부서 질문 → get_employee_info(이름) 도구 호출.\n"
        "특정 직원(이름 또는 ID) 성과·활동·실적·회의록·보고서 질문 → get_employee_performance(이름 또는 ID) 도구 호출.\n"
        "직원·신입·지원자 목록/조회 질문(예: 누가 있나, 전체 명단, 부서별·직급별 목록) → list_employees(employment_type, performance_tier, department, job_title, limit) 도구를 우선 호출하세요.\n"
        "'사원'이라는 단어는 기본적으로 '전체 직원(신입+일반)'으로 해석하고, 사용자가 명시적으로 '직급 사원'을 요청한 경우에만 직급 필터를 적용하세요.\n"
        "고성과자 질문은 반드시 performance_tier=high를 사용해 조회 결과를 생성하세요.\n"
        "\n★★★ 명단/목록 질문 답변 규칙 (반드시 준수) ★★★\n"
        "1. list_employees 도구가 반환한 직원 이름·부서·직급을 한 명씩 줄바꿈 목록으로 그대로 나열하세요.\n"
        "2. 절대로 요약·통계·분석으로 대체하지 마세요. '대부분이 신입사원입니다' 같은 요약은 금지합니다.\n"
        "3. 출력 형식: 먼저 총 인원 요약 한 줄, 그 뒤 각 직원을 [번호] 이름 / 부서 / 직급 형태로 나열하세요.\n"
        "4. 조건에 맞는 직원이 없을 때만 '조건에 맞는 직원이 없습니다.'로 답하세요.\n"
        "5. 개인정보 비식별 안내 문구를 사용하지 마세요. DB에 있는 이름을 그대로 제시하세요.\n"
        "6. 도구 결과에 없는 인원/수치를 추가하거나 재계산하지 마세요.\n"
        "\n"
        "인원 관련 답변 시에는 용어를 명확히 구분하세요: '전체 직원 수(신입+일반)'와 '일반 직원 수'를 분리해 숫자를 제시합니다.\n"
        "문서/용어 검색 → RAG 컨텍스트 또는 search_documents·define 활용.\n"
        "도구(get_hr_summary, list_employees, get_employee_info, get_employee_performance)가 반환한 숫자/명단/건수는 절대 재계산하거나 서로 다른 값으로 중복 제시하지 마세요.\n"
        "사용자 질문의 핵심 명사(예: 공시, 역량, 성과)는 답변 본문에 그대로 포함하세요.\n"
        "답변 시 사실 근거를 문장 끝에 [근거: employees], [근거: performance_records], [근거: disclosures], [근거: competency_anchors], [근거: tool:get_employee_info] 형식으로 간단히 표시하세요.\n"
        "질문이 데이터 범위 밖이면 '[시스템 안내] 데이터 범위 밖 질문'임을 먼저 명시하고, 일반 지식 답변임을 분리해 적으세요."
    )
    messages_list: List[BaseMessage] = []
    base_prompt = _DEFAULT_SYSTEM + "\n\n" + _HR_TOOLS_GUIDE + ("\n\n" + system_prompt if system_prompt else "")
    messages_list.append(SystemMessage(content=base_prompt))

    if chat_history:
        messages_list.extend(chat_history)
    messages_list.append(HumanMessage(content=user_text))

    initial_state: ChatState = {
        "messages": messages_list,
        "context": "",
        "model_provider": provider or "",
        "images": images or [],
    }
    if max_tokens is not None:
        initial_state["max_tokens"] = max_tokens
    if temperature is not None:
        initial_state["temperature"] = temperature
    config = get_thread_config(thread_id)
    result: ChatState = graph.invoke(initial_state, config=config)

    context_used = result.get("context") or ""
    rag_sources = result.get("rag_sources") or []

    response_messages = result.get("messages", [])
    tools_used: set = set()
    for msg in response_messages:
        tool_name = _extract_tool_name(msg)
        if tool_name:
            tools_used.add(tool_name)
        for call_name in _extract_tool_call_names(msg):
            tools_used.add(call_name)
    rag_sources = _merge_tool_sources(rag_sources, tools_used)

    for msg in reversed(response_messages):
        if isinstance(msg, AIMessage):
            return (str(msg.content), context_used, rag_sources)
    return ("", context_used, rag_sources)


async def run_agent_stream(
    user_text: str,
    provider: Optional[str] = None,
    system_prompt: Optional[str] = None,
    chat_history: Optional[List[BaseMessage]] = None,
    thread_id: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
    """에이전트를 스트리밍 모드로 실행합니다. RAG는 항상 사용.

    Yields:
        str: 응답 텍스트 청크
        dict: 스트림 종료 시 {"context_preview": "..."} (RAG 참고 문서 미리보기)
    """
    use_checkpointer = bool(thread_id)
    graph = get_default_graph() if use_checkpointer else build_agent_graph(use_checkpointer=False)

    # 이미지만 첨부한 경우: 이미지에서 검색용 문장 추출 → RAG 쿼리로 사용
    if images and (not (user_text or "").strip() or (user_text or "").strip() == "[이미지 첨부]"):
        from domain.hub.llm.gemini_adapter import get_image_caption_for_rag  # type: ignore

        caption = get_image_caption_for_rag(images)
        if caption:
            user_text = caption
            logger.info("[이미지→RAG] 캡션 추출 후 쿼리 사용: %s", (caption[:80] + "…") if len(caption) > 80 else caption)

    _DEFAULT_SYSTEM = (
        "당신은 도움이 되는 AI 어시스턴트입니다. "
        "답변은 일반 텍스트(문단)로만 작성하고, ```json 또는 불필요한 코드 블록을 사용하지 마세요."
    )
    _HR_TOOLS_GUIDE = (
        "HR 관련 질문 시 반드시 아래 도구와 RAG를 사용하세요. 답변은 도구·RAG 결과(employees, performance_records, disclosures, competency_anchors)를 종합해 작성합니다.\n"
        "직원 수·등록 인원·공시/역량/성과 적재 상태 질문 → get_hr_summary 도구 호출.\n"
        "특정 직원(이름) 기본 정보·직급·부서 질문 → get_employee_info(이름) 도구 호출.\n"
        "특정 직원(이름 또는 ID) 성과·활동·실적·회의록·보고서 질문 → get_employee_performance(이름 또는 ID) 도구 호출.\n"
        "직원·신입·지원자 목록/조회 질문(예: 누가 있나, 전체 명단, 부서별·직급별 목록) → list_employees(employment_type, performance_tier, department, job_title, limit) 도구를 우선 호출하세요.\n"
        "'사원'이라는 단어는 기본적으로 '전체 직원(신입+일반)'으로 해석하고, 사용자가 명시적으로 '직급 사원'을 요청한 경우에만 직급 필터를 적용하세요.\n"
        "고성과자 질문은 반드시 performance_tier=high를 사용해 조회 결과를 생성하세요.\n"
        "\n★★★ 명단/목록 질문 답변 규칙 (반드시 준수) ★★★\n"
        "1. list_employees 도구가 반환한 직원 이름·부서·직급을 한 명씩 줄바꿈 목록으로 그대로 나열하세요.\n"
        "2. 절대로 요약·통계·분석으로 대체하지 마세요. '대부분이 신입사원입니다' 같은 요약은 금지합니다.\n"
        "3. 출력 형식: 먼저 총 인원 요약 한 줄, 그 뒤 각 직원을 [번호] 이름 / 부서 / 직급 형태로 나열하세요.\n"
        "4. 조건에 맞는 직원이 없을 때만 '조건에 맞는 직원이 없습니다.'로 답하세요.\n"
        "5. 개인정보 비식별 안내 문구를 사용하지 마세요. DB에 있는 이름을 그대로 제시하세요.\n"
        "6. 도구 결과에 없는 인원/수치를 추가하거나 재계산하지 마세요.\n"
        "\n"
        "인원 관련 답변 시에는 용어를 명확히 구분하세요: '전체 직원 수(신입+일반)'와 '일반 직원 수'를 분리해 숫자를 제시합니다.\n"
        "문서/용어 검색 → RAG 컨텍스트 또는 search_documents·define 활용.\n"
        "도구(get_hr_summary, list_employees, get_employee_info, get_employee_performance)가 반환한 숫자/명단/건수는 절대 재계산하거나 서로 다른 값으로 중복 제시하지 마세요.\n"
        "사용자 질문의 핵심 명사(예: 공시, 역량, 성과)는 답변 본문에 그대로 포함하세요.\n"
        "답변 시 사실 근거를 문장 끝에 [근거: employees], [근거: performance_records], [근거: disclosures], [근거: competency_anchors], [근거: tool:get_employee_info] 형식으로 간단히 표시하세요.\n"
        "질문이 데이터 범위 밖이면 '[시스템 안내] 데이터 범위 밖 질문'임을 먼저 명시하고, 일반 지식 답변임을 분리해 적으세요."
    )
    messages: List[BaseMessage] = []
    base_prompt = _DEFAULT_SYSTEM + "\n\n" + _HR_TOOLS_GUIDE + ("\n\n" + system_prompt if system_prompt else "")
    messages.append(SystemMessage(content=base_prompt))

    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=user_text))

    initial_state: ChatState = {
        "messages": messages,
        "context": "",
        "model_provider": provider or "",
        "images": images or [],
    }
    config = get_thread_config(thread_id)
    debug_mode = settings.debug_streaming

    last_yielded_content = ""
    has_streamed = False
    final_response = ""
    context_used = ""
    rag_sources: List[Dict[str, Any]] = []
    tools_used: set = set()
    # 도구 실행이 끝난 뒤의 최종 모델 응답만 스트리밍 (첫 턴 중간 출력과 섞이지 않도록)
    has_seen_tools_end = False

    try:
        async for event in graph.astream_events(
            initial_state, config=config, version="v2"
        ):
            kind = event.get("event", "")
            event_name = event.get("name", "")
            data = event.get("data", {})

            if debug_mode:
                desc = {
                    ("on_chain_start", "LangGraph"): "그래프 시작",
                    ("on_chain_start", "rag"): "RAG 노드 시작",
                    ("on_chain_end", "rag"): "RAG 노드 완료",
                    ("on_chain_start", "model"): "Model 노드 시작",
                    ("on_chain_start", "should_use_tools"): "조건 분기 시작",
                    ("on_chain_end", "should_use_tools"): "조건 분기 완료",
                    ("on_chain_end", "model"): "Model 노드 완료",
                    ("on_chain_end", "LangGraph"): "그래프 종료",
                    ("on_chain_start", "tools"): "Tools 노드 시작",
                    ("on_chain_end", "tools"): "Tools 노드 완료",
                }
                key = (kind, event_name)
                if key in desc:
                    logger.debug("%s: %s ← %s", kind, event_name, desc[key])
                elif kind == "on_chat_model_start":
                    logger.debug("%s: %s ← LLM 호출 시작", kind, event_name)
                elif kind == "on_chat_model_end":
                    logger.debug("%s: %s ← LLM 응답 완료", kind, event_name)

            if kind == "on_chain_end" and event_name == "tools":
                has_seen_tools_end = True

            if kind == "on_chat_model_stream":
                # 도구 실행이 끝난 뒤의 최종 답변만 실시간 스트리밍 (첫 턴 중간 출력은 제외)
                if has_seen_tools_end:
                    chunk = data.get("chunk")
                    if chunk is not None and hasattr(chunk, "content") and chunk.content:
                        content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                        if content:
                            last_yielded_content += content
                            has_streamed = True
                            yield content
                continue

            if kind == "on_llm_stream":
                if has_seen_tools_end:
                    chunk = data.get("chunk")
                    if chunk is not None and hasattr(chunk, "content") and chunk.content:
                        content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
                        if content:
                            last_yielded_content += content
                            has_streamed = True
                            yield content
                continue

            if kind == "on_chain_stream":
                output = data.get("chunk", {})
                if isinstance(output, dict):
                    messages_output = output.get("messages", [])
                    if messages_output:
                        last_msg = messages_output[-1] if messages_output else None
                        if last_msg and isinstance(last_msg, AIMessage):
                            content = str(last_msg.content)
                            if content:
                                final_response = content
                elif isinstance(output, str) and output:
                    final_response = output

            elif kind == "on_chain_end":
                output = data.get("output", {})
                if isinstance(output, dict):
                    if event_name in ("rag", "rag_node"):
                        context_used = (output.get("context") or "") or context_used
                        if output.get("rag_sources"):
                            rag_sources = output.get("rag_sources")
                    if event_name == "tools":
                        tool_msgs = output.get("messages", [])
                        for m in tool_msgs:
                            tool_name = _extract_tool_name(m)
                            if tool_name:
                                tools_used.add(tool_name)
                    # 그래프 종료 시 state에서 한 번 더 채움 (이벤트 구조 차이 대비)
                    if event_name == "LangGraph" and output.get("rag_sources"):
                        rag_sources = output.get("rag_sources")
                if isinstance(output, dict):
                    messages_output = output.get("messages", [])
                    if messages_output:
                        for m in messages_output:
                            for call_name in _extract_tool_call_names(m):
                                tools_used.add(call_name)
                        for msg in reversed(messages_output):
                            if isinstance(msg, AIMessage):
                                content = str(msg.content)
                                if content:
                                    final_response = content
                                break

    except Exception as e:
        import traceback

        logger.error("스트리밍 중 오류 발생: %s", e, exc_info=debug_mode)
        if debug_mode:
            traceback.print_exc()
        if final_response and len(final_response) > len(last_yielded_content):
            new_chunk = final_response[len(last_yielded_content) :]
            yield new_chunk
        raise

    if not has_streamed and final_response:
        if len(final_response) > len(last_yielded_content):
            yield final_response[len(last_yielded_content) :]
    elif not has_streamed and not last_yielded_content:
        response, ctx, sources_from_agent = run_agent(
            user_text=user_text,
            provider=provider,
            system_prompt=system_prompt,
            chat_history=chat_history,
            thread_id=thread_id,
            images=images,
        )
        if response:
            yield response
        context_used = ctx or context_used
        rag_sources = sources_from_agent or rag_sources

    rag_sources = _merge_tool_sources(rag_sources, tools_used)

    preview = ""
    if context_used and context_used.strip():
        preview = (context_used[:600] + "…") if len(context_used) > 600 else context_used
    yield {"context_preview": preview, "sources": rag_sources}


def get_thread_history(thread_id: str) -> List[BaseMessage]:
    """스레드의 대화 기록을 조회합니다.

    Args:
        thread_id: 대화 스레드 ID

    Returns:
        메시지 목록
    """
    checkpointer = get_checkpointer()
    config = get_thread_config(thread_id)
    try:
        checkpoint = checkpointer.get(config)
        if checkpoint:
            channel_values = checkpoint.get("channel_values", {})
            messages = channel_values.get("messages", [])
            return messages
    except Exception as e:
        logger.warning("대화 기록 조회 실패: %s", e)
    return []


def clear_thread_history(thread_id: str) -> bool:
    """스레드의 대화 기록을 삭제합니다.

    Args:
        thread_id: 대화 스레드 ID

    Returns:
        삭제 성공 여부
    """
    checkpointer = get_checkpointer()
    config = get_thread_config(thread_id)
    try:
        if hasattr(checkpointer, "storage"):
            thread_key = config.get("configurable", {}).get("thread_id")
            if thread_key and thread_key in checkpointer.storage:
                del checkpointer.storage[thread_key]
                return True
    except Exception as e:
        logger.warning("대화 기록 삭제 실패: %s", e)
    return False


__all__ = [
    "run_agent",
    "run_agent_stream",
    "get_thread_history",
    "clear_thread_history",
]
