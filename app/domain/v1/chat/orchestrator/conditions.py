"""
LangGraph 조건 함수

그래프 라우팅을 위한 조건 함수들을 정의합니다.
"""

from typing import Literal

from langchain_core.messages import AIMessage

from domain.v1.chat.models.state_models import AgentState


def should_use_tools(state: AgentState) -> Literal["tools", "__end__"]:
    """도구 사용 여부를 결정합니다.

    마지막 AI 메시지에 tool_calls가 있으면 tools 노드로,
    없으면 종료합니다.

    Args:
        state: 현재 에이전트 상태

    Returns:
        다음 노드 이름 ("tools" 또는 "__end__")
    """
    messages = state.get("messages", [])
    if not messages:
        return "__end__"

    last_message = messages[-1]

    # AIMessage이고 tool_calls가 있는 경우
    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, "tool_calls", None)
        if tool_calls:
            return "tools"

    return "__end__"
