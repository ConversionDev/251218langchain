"""
일반 에이전트 노드

일반 LangGraph 에이전트 워크플로우에서 사용하는 노드들.
내부적으로 LangChain 컴포넌트를 사용합니다.

LangGraph 노드 역할:
- State 입력 → Dict 출력 (LangGraph 노드 인터페이스)

LangChain 컴포넌트 사용:
- BaseChatModel: LLM 인터페이스
- BaseMessage: HumanMessage, SystemMessage, ToolMessage
- PGVector: 벡터 스토어 검색
"""

import sys
from typing import Any, Dict, List, Optional

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from domain.chat.models.state_models import AgentState
from domain.chat.orchestrator.tools import TOOL_MAP, TOOLS
from .base import _get_llm, _get_llm_provider, _supports_tool_calling


def model_node(state: AgentState) -> Dict[str, Any]:
    """모델 노드 - LLM 호출 및 응답 생성 (Tool Calling 사용).

    LangGraph 노드 역할:
    - AgentState 입력 → State 업데이트 반환
    - graph_builder.py에서 "model" 노드로 등록됨

    LangChain 컴포넌트 사용:
    - BaseChatModel: llm.bind_tools(), llm.invoke()
    - SystemMessage: 시스템 프롬프트 생성

    스트리밍 지원:
    - stream() 메서드를 사용하여 토큰 단위 스트리밍
    - astream_events에서 on_chat_model_stream 이벤트 발생
    """
    from langchain_core.messages import AIMessage, AIMessageChunk

    LLMProvider = _get_llm_provider()
    provider = state.get("model_provider") or LLMProvider.get_provider_name()
    llm = _get_llm(provider=provider)

    messages = list(state.get("messages", []))
    context = state.get("context")

    # 컨텍스트가 있으면 시스템 메시지에 추가
    if context and messages:
        system_msg_idx = None
        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                system_msg_idx = i
                break

        context_addition = f"\n\n참고 컨텍스트:\n{context}"
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

    # Tool Calling 지원 여부에 따라 처리
    if _supports_tool_calling(provider):
        # Tool Calling 지원 모델 (EXAONE 등)
        llm_with_tools = llm.bind_tools(TOOLS)

        # 스트리밍 모드로 호출하여 토큰 단위 이벤트 발생
        chunks = []
        tool_calls = []
        for chunk in llm_with_tools.stream(messages):
            chunks.append(chunk)
            # tool_calls 수집
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)

        # 청크들을 합쳐서 최종 응답 생성
        if chunks:
            full_content = "".join(
                chunk.content for chunk in chunks if hasattr(chunk, "content") and chunk.content
            )
            # tool_calls가 있으면 포함
            if tool_calls:
                response = AIMessage(content=full_content, tool_calls=tool_calls)
            else:
                response = AIMessage(content=full_content)
        else:
            response = AIMessage(content="")
    else:
        # Tool Calling 미지원 모델 - 스트리밍 모드로 호출
        chunks = []
        for chunk in llm.stream(messages):
            chunks.append(chunk)

        if chunks:
            full_content = "".join(
                chunk.content for chunk in chunks if hasattr(chunk, "content") and chunk.content
            )
            response = AIMessage(content=full_content)
        else:
            response = AIMessage(content="")

    return {"messages": [response], "model_provider": provider}


def tool_node(state: AgentState) -> Dict[str, Any]:
    """도구 노드 - 도구 실행.

    LangGraph 노드 역할:
    - AgentState 입력 → State 업데이트 반환
    - graph_builder.py에서 "tools" 노드로 등록됨

    LangChain 컴포넌트 사용:
    - ToolMessage: 툴 실행 결과를 LangChain 메시지 형식으로 변환
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    results: List[BaseMessage] = []

    # AIMessage의 tool_calls 확인
    tool_calls = getattr(last_message, "tool_calls", None) if last_message else None
    if tool_calls:
        for call in tool_calls:
            name = call["name"]
            args = call.get("args", {})

            if name in TOOL_MAP:
                try:
                    output = TOOL_MAP[name].invoke(args)
                except Exception as e:
                    output = f"도구 실행 오류: {str(e)}"
            else:
                output = f"알 수 없는 도구: {name}"

            results.append(
                ToolMessage(
                    content=str(output),
                    tool_call_id=call["id"],
                    name=name,
                )
            )

    return {"messages": results}


def rag_node(state: AgentState) -> Dict[str, Any]:
    """RAG 노드 - 벡터 스토어에서 관련 문서 검색.

    LangGraph 노드 역할:
    - AgentState 입력 → State 업데이트 반환
    - graph_builder.py에서 "rag" 노드로 등록됨

    LangChain 컴포넌트 사용:
    - PGVector: vector_store.similarity_search() - LangChain 벡터 스토어
    """
    messages = state.get("messages", [])

    # 마지막 사용자 메시지 찾기
    user_query: Optional[str] = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = str(msg.content)
            break

    if not user_query:
        return {"context": ""}

    try:
        if "server" in sys.modules:
            import server  # type: ignore

            if server.vector_store:
                docs = server.vector_store.similarity_search(user_query, k=3)
                if docs:
                    context = "\n\n".join([doc.page_content for doc in docs])
                    return {"context": context}

        return {"context": ""}
    except Exception as e:
        print(f"[WARNING] RAG 검색 실패: {str(e)}")
        return {"context": ""}
