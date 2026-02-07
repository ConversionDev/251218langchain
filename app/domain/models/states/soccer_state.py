"""
Soccer 데이터 처리 LangGraph State 모델

휴리스틱 처리만 수행하는 단순한 State 정의.
채팅·스팸과 동일하게 messages는 add_messages 리듀서로 누적 관리.
임베딩 State는 베이스 테이블(Player 등)의 embedding, embedding_content 필드 구조 참조.
"""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore

EMBEDDING_VECTOR_DIM = BGE_M3_DENSE_DIM


class SoccerDataState(TypedDict, total=False):
    """Soccer 데이터 처리 워크플로우 상태 정의.

    휴리스틱 처리만 수행하므로 단순한 구조를 사용합니다.
    비선형 구조를 지원하기 위해 재시도 관련 필드를 추가합니다.
    """

    # 대화·메시지 (채팅/스팸과 동일한 리듀서)
    messages: Annotated[List[BaseMessage], add_messages]

    # 입력 데이터
    data: List[Dict[str, Any]]  # 처리할 전체 데이터 리스트
    preview_data: List[Dict[str, Any]]  # 미리보기 데이터 (로깅용)

    # 처리 단계별 결과
    validated_data: Optional[List[Dict[str, Any]]]  # 검증된 데이터
    transformed_data: Optional[List[Dict[str, Any]]]  # 변환된 데이터
    saved_count: Optional[int]  # DB 저장된 개수

    # 메타데이터
    data_type: str  # 데이터 타입 ("players", "teams", "stadiums", "schedules")
    processing_path: str  # 처리 경로 추적 (디버깅용)
    errors: Optional[List[Dict[str, Any]]]  # 에러 목록

    # DB 세션 (규칙 기반 저장용)
    db: Any  # SQLAlchemy Session (Optional이지만 저장 시 필요)

    # 재시도 관련 (비선형 구조 지원)
    save_retry_count: Optional[int]  # 저장 재시도 횟수
    save_failed: Optional[bool]  # 저장 실패 여부
    result: Optional[Dict[str, Any]]  # 최종 결과

    # 전략·세션 (오케스트레이터용)
    decided_strategy: Optional[str]
    vector_store: Any
    auto_commit: Optional[bool]


# ---------------------------------------------------------------------------
# 임베딩 State (베이스 테이블 embedding 컬럼 대응)
# LangGraph 임베딩 동기화 그래프 상태용.
# ---------------------------------------------------------------------------


class PlayerEmbeddingState(TypedDict, total=False):
    """선수 임베딩 상태. PlayerEmbedding ORM 필드 대응."""

    id: Optional[int]
    player_id: int
    content: str
    embedding: Optional[List[float]]  # EMBEDDING_VECTOR_DIM(1024)차원
    created_at: Optional[datetime]


class TeamEmbeddingState(TypedDict, total=False):
    """팀 임베딩 상태. TeamEmbedding ORM 필드 대응."""

    id: Optional[int]
    team_id: int
    content: str
    embedding: Optional[List[float]]
    created_at: Optional[datetime]


class ScheduleEmbeddingState(TypedDict, total=False):
    """경기 일정 임베딩 상태. ScheduleEmbedding ORM 필드 대응."""

    id: Optional[int]
    schedule_id: int
    content: str
    embedding: Optional[List[float]]
    created_at: Optional[datetime]


class StadiumEmbeddingState(TypedDict, total=False):
    """경기장 임베딩 상태. StadiumEmbedding ORM 필드 대응."""

    id: Optional[int]
    stadium_id: int
    content: str
    embedding: Optional[List[float]]
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# 임베딩 동기화 LangGraph State (워커 → 오케스트레이터 그래프용)
# ---------------------------------------------------------------------------


class EmbeddingSyncState(TypedDict, total=False):
    """임베딩 동기화 워크플로우 상태. LangGraph EmbeddingSync 그래프용."""

    entities: List[str]
    db: Any
    embeddings_model: Any
    batch_size: int
    results: Dict[str, Any]
    current_entity_index: int
    processing_path: str
    errors: Optional[List[Dict[str, Any]]]
