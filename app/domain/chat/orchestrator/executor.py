"""
LangGraph 에이전트 실행기

에이전트 실행 및 스트리밍을 담당합니다.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from core.config import settings  # type: ignore
from domain.chat.models.state_models import AgentState
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from .checkpointer import get_checkpointer, get_thread_config
from .graph_builder import build_agent_graph, get_default_graph


def run_agent(
    user_text: str,
    provider: Optional[str] = None,
    use_rag: bool = True,
    system_prompt: Optional[str] = None,
    chat_history: Optional[List[BaseMessage]] = None,
    thread_id: Optional[str] = None,
) -> str:
    """에이전트를 실행하고 응답을 반환합니다.

    Args:
        user_text: 사용자 메시지
        provider: LLM 제공자
        use_rag: RAG 사용 여부
        system_prompt: 시스템 프롬프트
        chat_history: 이전 대화 기록
        thread_id: 대화 스레드 ID

    Returns:
        에이전트 응답 문자열
    """
    # 그래프 가져오기 또는 빌드
    # thread_id가 있으면 체크포인터 사용, 없으면 체크포인터 없이 빌드
    use_checkpointer = bool(thread_id)

    if use_rag and use_checkpointer:
        graph = get_default_graph()
    else:
        graph = build_agent_graph(use_rag=use_rag, use_checkpointer=use_checkpointer)

    # 메시지 구성
    messages: List[BaseMessage] = []

    # 시스템 프롬프트
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    else:
        messages.append(
            SystemMessage(content="당신은 도움이 되는 AI 어시스턴트입니다.")
        )

    # 이전 대화 기록
    if chat_history:
        messages.extend(chat_history)

    # 현재 사용자 메시지
    messages.append(HumanMessage(content=user_text))

    # 초기 상태
    initial_state: AgentState = {
        "messages": messages,
        "context": "",
        "model_provider": provider or "",
    }

    # 설정
    config = get_thread_config(thread_id)

    # 그래프 실행
    result = graph.invoke(initial_state, config=config)

    # 마지막 AI 메시지 추출
    response_messages = result.get("messages", [])
    for msg in reversed(response_messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)

    return ""


async def run_agent_stream(
    user_text: str,
    provider: Optional[str] = None,
    use_rag: bool = True,
    system_prompt: Optional[str] = None,
    chat_history: Optional[List[BaseMessage]] = None,
    thread_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """에이전트를 스트리밍 모드로 실행합니다.

    Args:
        user_text: 사용자 메시지
        provider: LLM 제공자
        use_rag: RAG 사용 여부
        system_prompt: 시스템 프롬프트
        chat_history: 이전 대화 기록
        thread_id: 대화 스레드 ID

    Yields:
        응답 청크
    """
    # 그래프 가져오기 또는 빌드
    # thread_id가 있으면 체크포인터 사용, 없으면 체크포인터 없이 빌드
    use_checkpointer = bool(thread_id)

    if use_rag and use_checkpointer:
        graph = get_default_graph()
    else:
        graph = build_agent_graph(use_rag=use_rag, use_checkpointer=use_checkpointer)

    # 메시지 구성
    messages: List[BaseMessage] = []

    # 시스템 프롬프트
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    else:
        messages.append(
            SystemMessage(content="당신은 도움이 되는 AI 어시스턴트입니다.")
        )

    # 이전 대화 기록
    if chat_history:
        messages.extend(chat_history)

    # 현재 사용자 메시지
    messages.append(HumanMessage(content=user_text))

    # 초기 상태
    initial_state: AgentState = {
        "messages": messages,
        "context": "",
        "model_provider": provider or "",
    }

    # 설정
    config = get_thread_config(thread_id)

    # 디버그 모드 확인
    debug_mode = settings.debug_streaming

    # 스트리밍 실행
    last_yielded_content = ""
    has_streamed = False
    final_response = ""

    try:
        async for event in graph.astream_events(
            initial_state, config=config, version="v2"
        ):
            kind = event.get("event", "")
            event_name = event.get("name", "")
            data = event.get("data", {})

            # 디버그 로깅 (흐름 추적 + 설명)
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
                    print(f"[DEBUG] {kind}: {event_name} ← {desc[key]}")
                elif kind == "on_chat_model_start":
                    print(f"[DEBUG] {kind}: {event_name} ← LLM 호출 시작")
                elif kind == "on_chat_model_end":
                    print(f"[DEBUG] {kind}: {event_name} ← LLM 응답 완료")

            # LLM 스트리밍 이벤트 처리
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

            # 체인 스트림에서 최종 응답 추출 (증분 업데이트)
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

            # 체인 종료 시 최종 응답 확인
            elif kind == "on_chain_end":
                output = data.get("output", {})
                if isinstance(output, dict):
                    messages_output = output.get("messages", [])
                    if messages_output:
                        for msg in reversed(messages_output):
                            if isinstance(msg, AIMessage):
                                content = str(msg.content)
                                # 아직 전송하지 않은 부분이 있으면 전송
                                if content and len(content) > len(last_yielded_content):
                                    new_chunk = content[len(last_yielded_content) :]
                                    yield new_chunk
                                    last_yielded_content = content
                                final_response = content
                                break

    except Exception as e:
        import traceback

        print(f"[ERROR] 스트리밍 중 오류 발생: {e}")
        if debug_mode:
            traceback.print_exc()
        # 오류 발생 시에도 이미 수집한 내용은 전송
        if final_response and len(final_response) > len(last_yielded_content):
            new_chunk = final_response[len(last_yielded_content) :]
            yield new_chunk
        raise

    # 스트리밍 이벤트가 없었다면 폴백
    if not has_streamed and final_response:
        if len(final_response) > len(last_yielded_content):
            new_chunk = final_response[len(last_yielded_content) :]
            yield new_chunk
    elif not has_streamed and not last_yielded_content:
        # 완전한 폴백: 동기 실행
        response = run_agent(
            user_text=user_text,
            provider=provider,
            use_rag=use_rag,
            system_prompt=system_prompt,
            chat_history=chat_history,
            thread_id=thread_id,
        )
        if response:
            yield response


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
        # 체크포인터에서 상태 조회
        checkpoint = checkpointer.get(config)
        if checkpoint:
            channel_values = checkpoint.get("channel_values", {})
            messages = channel_values.get("messages", [])
            return messages
    except Exception as e:
        print(f"[WARNING] 대화 기록 조회 실패: {e}")

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
        # MemorySaver의 경우 직접 storage에 접근
        if hasattr(checkpointer, "storage"):
            thread_key = config.get("configurable", {}).get("thread_id")
            if thread_key and thread_key in checkpointer.storage:
                del checkpointer.storage[thread_key]
                return True
    except Exception as e:
        print(f"[WARNING] 대화 기록 삭제 실패: {e}")

    return False


def run_spam_detection(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """스팸 감지를 실행합니다.

    Args:
        email_metadata: 이메일 메타데이터

    Returns:
        스팸 감지 결과
    """
    try:
        # 스팸 도메인의 그래프 사용
        print("[DEBUG] 스팸 감지 모듈 import 시도 중...")
        from domain.spam.agents.graph import run_spam_detection_graph  # type: ignore

        print("[DEBUG] 스팸 감지 모듈 import 성공")

        print(
            f"[DEBUG] 스팸 감지 그래프 실행 시작: subject={email_metadata.get('subject', 'N/A')}"
        )
        result = run_spam_detection_graph(email_metadata)
        print(
            f"[DEBUG] 스팸 감지 그래프 실행 완료: action={result.get('action')}, routing_strategy={result.get('routing_strategy')}"
        )
        return result
    except ImportError as e:
        # 스팸 그래프가 없는 경우 기본 응답
        print(f"[ERROR] 스팸 감지 모듈 import 실패 (ImportError): {e}")
        import traceback

        traceback.print_exc()
        return {
            "action": "deliver",
            "reason_codes": ["MODULE_NOT_FOUND"],
            "user_message": "스팸 감지 모듈을 찾을 수 없습니다.",
            "confidence": "low",
            "spam_prob": 0.0,
            "llama_result": {
                "spam_prob": 0.0,
                "confidence": "low",
                "label": "HAM",
            },
            "exaone_result": None,
            "routing_strategy": None,
            "routing_path": "Default",
        }
    except Exception as e:
        # 기타 예외 처리 (ImportError가 아닌 다른 오류)
        print(
            f"[ERROR] 스팸 감지 실행 중 오류 발생 (Exception): {type(e).__name__}: {e}"
        )
        import traceback

        traceback.print_exc()
        return {
            "action": "deliver",
            "reason_codes": ["EXECUTION_ERROR"],
            "user_message": f"스팸 감지 처리 중 오류가 발생했습니다: {str(e)}",
            "confidence": "low",
            "spam_prob": 0.0,
            "llama_result": {
                "spam_prob": 0.0,
                "confidence": "low",
                "label": "UNCERTAIN",
            },
            "exaone_result": None,
            "routing_strategy": None,
            "routing_path": "Error",
        }
