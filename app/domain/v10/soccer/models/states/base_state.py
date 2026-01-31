"""
공통 상태 베이스 클래스

모든 데이터 타입의 State가 공통으로 사용하는 필드를 정의합니다.
"""

from typing import Any, Dict, List, Optional, TypedDict


class BaseProcessingState(TypedDict, total=False):
    """공통 데이터 처리 워크플로우 상태 정의.

    모든 데이터 타입의 State가 상속받는 베이스 클래스입니다.
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
    decided_strategy: Optional[str]  # 결정된 전략 ("policy" 또는 "rule")

    # DB 세션
    db: Any  # SQLAlchemy Session (Optional이지만 저장 시 필요)
    vector_store: Any  # 벡터 스토어 (Policy 기반 처리용)
    auto_commit: Optional[bool]  # True면 서비스에서 commit, False면 오케스트레이터에서 한 번만 commit

    # 재시도 관련 (비선형 구조 지원)
    save_retry_count: Optional[int]  # 저장 재시도 횟수
    save_failed: Optional[bool]  # 저장 실패 여부
    result: Optional[Dict[str, Any]]  # 최종 결과
