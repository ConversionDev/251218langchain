"""LangGraph 상태 정의.

스팸/채팅은 별도 그래프·별도 상태 타입. API 진입점(/mail, /agent 등)에서
어느 그래프로 보낼지 정해지고, 각 그래프는 자기 상태(SpamState / ChatState)만 사용.
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class SpamState(TypedDict, total=False):
    """스팸 감지 플로우 상태 (LLaMA·ExaOne 결과·라우팅)."""

    email_metadata: Dict[str, Any]
    llama_result: Optional[Dict[str, Any]]
    exaone_result: Optional[Dict[str, Any]]
    final_decision: Optional[Dict[str, Any]]
    routing_path: str
    messages: Annotated[List[BaseMessage], add_messages]
    task_id: Optional[str]
    adapter_path: Optional[str]
    routing_action: Optional[str]
    routing_strategy: Optional[str]  # "rule" | "policy"


class ChatState(TypedDict, total=False):
    """채팅 플로우 상태 (메시지·RAG 컨텍스트·프로바이더·이미지)."""

    messages: Annotated[List[BaseMessage], add_messages]
    context: Optional[str]
    model_provider: Optional[str]
    images: Optional[List[str]]  # base64 이미지 배열 (멀티모달 시 Gemini 사용)
