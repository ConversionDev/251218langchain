"""
그래프 오케스트레이터 (v1)

채팅 그래프 인프라: 체크포인터, 조건(should_use_tools), 그래프 빌더.
도구(TOOLS/TOOL_MAP)는 graph_tools에서 import하여 순환 참조를 피합니다.
"""

from typing import Any, Dict, Literal, Optional

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from domain.v1.hub.orchestrators.graph_tools import TOOL_MAP, TOOLS  # type: ignore
from domain.v1.models import AgentState
from domain.v1.spokes.chat.agents import model_node, rag_node, tool_node


# -----------------------------------------------------------------------------
# 1. 체크포인터 (대화 상태 인프라)
# -----------------------------------------------------------------------------

_checkpointer: Optional[MemorySaver] = None


def get_checkpointer() -> MemorySaver:
    """체크포인터 인스턴스를 반환합니다 (싱글톤)."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def get_thread_config(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """스레드 설정을 반환합니다."""
    if thread_id:
        return {"configurable": {"thread_id": thread_id}}
    return {}


# -----------------------------------------------------------------------------
# 2. 조건 (그래프 라우팅)
# -----------------------------------------------------------------------------


def should_use_tools(state: AgentState) -> Literal["tools", "__end__"]:
    """도구 사용 여부를 결정합니다.

    마지막 AI 메시지에 tool_calls가 있으면 tools 노드로, 없으면 종료합니다.
    """
    messages = state.get("messages", [])
    if not messages:
        return "__end__"
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, "tool_calls", None)
        if tool_calls:
            return "tools"
    return "__end__"


# -----------------------------------------------------------------------------
# 3. 도구 (graph_tools에서 re-export, 순환 참조 방지)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 4. 그래프 빌더 (노드·엣지·컴파일)
# -----------------------------------------------------------------------------

_default_graph = None


def build_agent_graph(use_rag: bool = True, use_checkpointer: bool = True):
    """에이전트 그래프를 빌드합니다.

    Args:
        use_rag: RAG 노드 사용 여부
        use_checkpointer: 체크포인터 사용 여부

    Returns:
        컴파일된 LangGraph
    """
    graph = StateGraph(AgentState)
    if use_rag:
        graph.add_node("rag", rag_node)
    graph.add_node("model", model_node)
    graph.add_node("tools", tool_node)

    if use_rag:
        graph.set_entry_point("rag")
        graph.add_edge("rag", "model")
    else:
        graph.set_entry_point("model")

    graph.add_conditional_edges(
        "model",
        should_use_tools,
        {"tools": "tools", "__end__": END},
    )
    graph.add_edge("tools", "model")

    checkpointer = get_checkpointer() if use_checkpointer else None
    return graph.compile(checkpointer=checkpointer)


def get_default_graph():
    """기본 에이전트 그래프를 반환합니다 (싱글톤)."""
    global _default_graph
    if _default_graph is None:
        _default_graph = build_agent_graph(use_rag=True, use_checkpointer=True)
    return _default_graph

__all__ = [
    "get_checkpointer",
    "get_thread_config",
    "should_use_tools",
    "TOOLS",
    "TOOL_MAP",
    "build_agent_graph",
    "get_default_graph",
]
