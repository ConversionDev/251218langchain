"""
Chat Orchestrator — 채팅 그래프 실행 진입점

run_agent, run_agent_stream, get_thread_history, clear_thread_history
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

from core.config import settings  # type: ignore
from domain.models import ChatState
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from .graph_orchestrator import (
    build_agent_graph,
    get_checkpointer,
    get_default_graph,
    get_thread_config,
)

logger = logging.getLogger(__name__)


# 시멘틱 분류 결과 반영 (답변과 UI 태그 일치)
_SEMANTIC_PROMPT = (
    "이 질문의 시멘틱 분류 결과는 {label}입니다. "
    "사용자가 \"규칙 기반입니까, 정책 기반입니까, 차단 대상입니까\"라고 물으면 반드시 이 분류 결과에 맞게 답하세요."
)
_SEMANTIC_LABELS = {"RULE_BASED": "규칙 기반", "POLICY_BASED": "정책 기반", "BLOCK": "차단 대상"}


def run_agent(
    user_text: str,
    provider: Optional[str] = None,
    system_prompt: Optional[str] = None,
    chat_history: Optional[List[BaseMessage]] = None,
    thread_id: Optional[str] = None,
    semantic_action: Optional[str] = None,
) -> Tuple[str, str]:
    """에이전트를 실행하고 응답을 반환합니다. RAG는 항상 사용.

    Args:
        user_text: 사용자 메시지
        provider: LLM 제공자
        system_prompt: 시스템 프롬프트
        chat_history: 이전 대화 기록
        thread_id: 대화 스레드 ID
        semantic_action: 시멘틱 분류 결과 (RULE_BASED/POLICY_BASED) → 답변과 UI 태그 일치용

    Returns:
        (에이전트 응답 문자열, RAG에서 사용한 컨텍스트)
    """
    use_checkpointer = bool(thread_id)
    graph = get_default_graph() if use_checkpointer else build_agent_graph(use_checkpointer=False)

    messages_list: List[BaseMessage] = []
    base_prompt = system_prompt or "당신은 도움이 되는 AI 어시스턴트입니다."
    if semantic_action and semantic_action in _SEMANTIC_LABELS:
        label = _SEMANTIC_LABELS[semantic_action]
        base_prompt = base_prompt + "\n\n" + _SEMANTIC_PROMPT.format(label=label)
    messages_list.append(SystemMessage(content=base_prompt))

    if chat_history:
        messages_list.extend(chat_history)
    messages_list.append(HumanMessage(content=user_text))

    initial_state: ChatState = {
        "messages": messages_list,
        "context": "",
        "model_provider": provider or "",
    }
    config = get_thread_config(thread_id)
    result: ChatState = graph.invoke(initial_state, config=config)

    context_used = result.get("context") or ""

    response_messages = result.get("messages", [])
    for msg in reversed(response_messages):
        if isinstance(msg, AIMessage):
            return (str(msg.content), context_used)
    return ("", context_used)


async def run_agent_stream(
    user_text: str,
    provider: Optional[str] = None,
    system_prompt: Optional[str] = None,
    chat_history: Optional[List[BaseMessage]] = None,
    thread_id: Optional[str] = None,
    semantic_action: Optional[str] = None,
) -> AsyncGenerator[Union[str, Dict[str, Any]], None]:
    """에이전트를 스트리밍 모드로 실행합니다. RAG는 항상 사용.

    Yields:
        str: 응답 텍스트 청크
        dict: 스트림 종료 시 {"context_preview": "..."} (RAG 참고 문서 미리보기)
    """
    use_checkpointer = bool(thread_id)
    graph = get_default_graph() if use_checkpointer else build_agent_graph(use_checkpointer=False)

    messages: List[BaseMessage] = []
    base_prompt = system_prompt or "당신은 도움이 되는 AI 어시스턴트입니다."
    if semantic_action and semantic_action in _SEMANTIC_LABELS:
        label = _SEMANTIC_LABELS[semantic_action]
        base_prompt = base_prompt + "\n\n" + _SEMANTIC_PROMPT.format(label=label)
    messages.append(SystemMessage(content=base_prompt))

    if chat_history:
        messages.extend(chat_history)
    messages.append(HumanMessage(content=user_text))

    initial_state: ChatState = {
        "messages": messages,
        "context": "",
        "model_provider": provider or "",
    }
    config = get_thread_config(thread_id)
    debug_mode = settings.debug_streaming

    last_yielded_content = ""
    has_streamed = False
    final_response = ""
    context_used = ""

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

            if kind == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    has_streamed = True
                    yield chunk.content
                    last_yielded_content += chunk.content

            elif kind == "on_llm_stream":
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    has_streamed = True
                    yield chunk.content
                    last_yielded_content += chunk.content

            elif kind == "on_chain_stream":
                output = data.get("chunk", {})
                if isinstance(output, dict):
                    messages_output = output.get("messages", [])
                    if messages_output:
                        last_msg = messages_output[-1] if messages_output else None
                        if last_msg and isinstance(last_msg, AIMessage):
                            content = str(last_msg.content)
                            if content and len(content) > len(last_yielded_content):
                                new_chunk = content[len(last_yielded_content) :]
                                has_streamed = True
                                yield new_chunk
                                last_yielded_content = content
                                final_response = content
                elif isinstance(output, str) and output:
                    if len(output) > len(last_yielded_content):
                        new_chunk = output[len(last_yielded_content) :]
                        has_streamed = True
                        yield new_chunk
                        last_yielded_content = output
                        final_response = output

            elif kind == "on_chain_end":
                output = data.get("output", {})
                if event_name in ("rag", "rag_node") and isinstance(output, dict):
                    context_used = (output.get("context") or "") or context_used
                if isinstance(output, dict):
                    messages_output = output.get("messages", [])
                    if messages_output:
                        for msg in reversed(messages_output):
                            if isinstance(msg, AIMessage):
                                content = str(msg.content)
                                if content and len(content) > len(last_yielded_content):
                                    new_chunk = content[len(last_yielded_content) :]
                                    yield new_chunk
                                    last_yielded_content = content
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
        response, ctx = run_agent(
            user_text=user_text,
            provider=provider,
            system_prompt=system_prompt,
            chat_history=chat_history,
            thread_id=thread_id,
            semantic_action=semantic_action,
        )
        if response:
            yield response
        context_used = ctx or context_used

    # RAG로 실제 검색된 문서가 있을 때만 전송 (없으면 보내지 않아 일반 답변으로 보이게)
    if context_used and context_used.strip():
        preview = (context_used[:600] + "…") if len(context_used) > 600 else context_used
        yield {"context_preview": preview}


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
