"""
Soccer 데이터 처리 LangGraph State 모델

휴리스틱 처리만 수행하는 단순한 State 정의.
"""

from typing import Any, Dict, List, Optional, TypedDict


class SoccerDataState(TypedDict, total=False):
    """Soccer 데이터 처리 워크플로우 상태 정의.

    휴리스틱 처리만 수행하므로 단순한 구조를 사용합니다.
    비선형 구조를 지원하기 위해 재시도 관련 필드를 추가합니다.
    """

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
