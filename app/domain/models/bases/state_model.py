"""
에이전트/워크플로우 상태값 정의 (v1)

LangGraph 워크플로우에서 사용하는 State 모델 정의.
- SpamDetectionState: 스팸 감지 플로우
- AgentState: 채팅 에이전트 플로우
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class SpamDetectionState(TypedDict, total=False):
    """스팸 감지 워크플로우 상태 정의.

    LLaMA와 EXAONE을 연결하는 오케스트레이션 State.
    각 서비스의 결과는 dict 형태로 저장됩니다.
    """

    # email_metadata: 이메일 메타데이터
    email_metadata: Dict[str, Any]
    # llama_result: LLaMA 분류 결과 (dict 형태)
    llama_result: Optional[Dict[str, Any]]
    # exaone_result: EXAONE 분석 결과 (dict 형태, 선택적)
    exaone_result: Optional[Dict[str, Any]]
    # final_decision: 최종 결정
    final_decision: Optional[Dict[str, Any]]
    # routing_path: 라우팅 경로 추적 (디버깅용)
    routing_path: str
    # messages: LLM과의 대화 로그 (툴 호출용)
    messages: Annotated[List[BaseMessage], add_messages]
    # 새 아키텍처 필드
    task_id: Optional[str]  # 작업 ID (예: "spam_detection")
    adapter_path: Optional[str]  # 어댑터 경로
    routing_action: Optional[str]  # 라우팅 액션 ("reject", "allow", "exaone_llm")
    routing_strategy: Optional[str]  # 라우팅 전략 ("rule" 또는 "policy")


class AgentState(TypedDict, total=False):
    """채팅 에이전트 상태.

    - messages: 대화 메시지 목록
    - context: RAG 등에서 주입된 컨텍스트
    - model_provider: 사용할 LLM 프로바이더 이름
    """

    messages: List[BaseMessage]
    context: Optional[str]
    model_provider: Optional[str]
