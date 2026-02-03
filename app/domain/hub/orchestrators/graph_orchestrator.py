"""
Graph Orchestrator — 채팅 그래프 빌더

도구(TOOLS), 노드(model/rag/tool), 체크포인터, 조건 라우팅.
"""

import logging
import sys
from typing import Any, Dict, List, Literal, Optional

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


TOOLS = [
    analyze_with_exaone,
    search_documents,
    get_current_time,
    calculate,
]
TOOL_MAP: Dict[str, Any] = {t.name: t for t in TOOLS}


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


def model_node(state: ChatState) -> ChatState:
    """모델 노드. LLM 호출·Tool Calling, 스트리밍 지원."""
    LLMProvider = _get_llm_provider()
    provider = state.get("model_provider") or LLMProvider.get_provider_name()
    llm = _get_llm(provider=provider)

    messages = list(state.get("messages", []))
    context = state.get("context")

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

    if _supports_tool_calling(provider):
        llm_with_tools = llm.bind_tools(TOOLS)
        chunks = []
        tool_calls = []
        for chunk in llm_with_tools.stream(messages):
            chunks.append(chunk)
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                tool_calls.extend(chunk.tool_calls)
        if chunks:
            full_content = "".join(
                chunk.content for chunk in chunks
                if hasattr(chunk, "content") and chunk.content
            )
            response = (
                AIMessage(content=full_content, tool_calls=tool_calls)
                if tool_calls
                else AIMessage(content=full_content)
            )
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


def rag_node(state: ChatState) -> ChatState:
    """RAG 노드. PGVector similarity_search로 컨텍스트 검색."""
    messages = state.get("messages", [])

    user_query: Optional[str] = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = str(msg.content)
            break

    if not user_query:
        return {"context": ""}

    try:
        if "fastapi_server" in sys.modules:
            import fastapi_server  # type: ignore

            fastapi_server.ensure_rag_initialized()
            if fastapi_server.vector_store:
                docs = fastapi_server.vector_store.similarity_search(user_query, k=3)
                if docs:
                    context = "\n\n".join([doc.page_content for doc in docs])
                    return {"context": context}
        return {"context": ""}
    except Exception as e:
        logger.warning("RAG 검색 실패: %s", e)
        return {"context": ""}


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
            return "tools"
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
    "build_agent_graph",
    "get_default_graph",
    "model_node",
    "rag_node",
    "tool_node",
]
