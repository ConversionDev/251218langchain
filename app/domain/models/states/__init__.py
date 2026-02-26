"""
LangGraph·워크플로우 상태 정의.

- langgraph_state: ChatState, SpamState (채팅·스팸 플로우)
- database_result_state: DatabaseResult (DB 저장 결과 공통)
"""

from .database_result_state import DatabaseResult
from .langgraph_state import ChatState, SpamState

__all__ = [
    "ChatState",
    "DatabaseResult",
    "SpamState",
]
