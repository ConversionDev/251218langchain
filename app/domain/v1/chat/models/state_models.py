"""
LangGraph Agent State 모델 정의

오케스트레이션 계층에서 사용하는 일반 에이전트 State 모델.
스팸 감지 전용 State는 domains/spam/schemas/state_model.py를 참조하세요.
"""

from typing import Annotated, List, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """일반 에이전트 상태 정의.

    일반적인 LangGraph 에이전트에서 사용하는 State.
    """

    # messages: 대화 로그 (누적)
    messages: Annotated[List[BaseMessage], add_messages]
    # context: RAG 검색 결과 (선택적)
    context: str
    # model_provider: 사용 중인 모델 제공자
    model_provider: str
