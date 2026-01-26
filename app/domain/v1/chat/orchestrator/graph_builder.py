"""
LangGraph 그래프 빌더

에이전트 워크플로우 그래프를 구성합니다.
"""

from typing import Optional

from langgraph.graph import END, StateGraph

from domain.v1.chat.agents.nodes import model_node, rag_node, tool_node
from domain.v1.chat.models.state_models import AgentState
from .checkpointer import get_checkpointer
from .conditions import should_use_tools


def build_agent_graph(use_rag: bool = True, use_checkpointer: bool = True):
    """에이전트 그래프를 빌드합니다.

    Args:
        use_rag: RAG 노드 사용 여부
        use_checkpointer: 체크포인터 사용 여부

    Returns:
        컴파일된 LangGraph
    """
    # 그래프 생성
    graph = StateGraph(AgentState)

    # 노드 추가
    if use_rag:
        graph.add_node("rag", rag_node)
    graph.add_node("model", model_node)
    graph.add_node("tools", tool_node)

    # 엣지 정의
    if use_rag:
        graph.set_entry_point("rag")
        graph.add_edge("rag", "model")
    else:
        graph.set_entry_point("model")

    # 모델 노드에서 조건부 라우팅
    graph.add_conditional_edges(
        "model",
        should_use_tools,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    # 도구 실행 후 다시 모델로
    graph.add_edge("tools", "model")

    # 체크포인터 설정
    checkpointer = get_checkpointer() if use_checkpointer else None

    return graph.compile(checkpointer=checkpointer)


# 기본 그래프 (RAG + 체크포인터 사용)
_default_graph = None


def get_default_graph():
    """기본 에이전트 그래프를 반환합니다.

    Returns:
        컴파일된 LangGraph (싱글톤)
    """
    global _default_graph
    if _default_graph is None:
        _default_graph = build_agent_graph(use_rag=True, use_checkpointer=True)
    return _default_graph
