"""
데이터베이스 저장 결과 상태 스키마.

Player, Team, Stadium, Schedule 등 soccer 도메인에서
state["result"]에 넣는 DB 저장 결과를 표현하는 공통 TypedDict.
현재 finalize_node의 { db, vector, processed, total } 형태와 호환하고,
추후 상세 결과(success_ids, failure_ids 등)를 쓸 수 있도록 확장 가능.
"""

from typing import Any, Dict, List, TypedDict


class DatabaseResult(TypedDict, total=False):
    """데이터베이스 저장 결과.

    - 현재 사용: db, vector, processed, total (finalize_node / soccer_router)
    - 확장 시: success_count, failure_count, success_ids, failure_ids, errors
    """

    # 현재 orchestrator·router에서 사용하는 필드
    db: int  # 저장된 레코드 수 (베이스 테이블)
    vector: int  # 벡터 저장 수 (임베딩 테이블, 현재 0)
    processed: int  # 처리된 레코드 수
    total: int  # 전체 레코드 수

    # 상세 저장 결과 (repository 확장 시 사용)
    success_count: int
    failure_count: int
    success_ids: List[int]
    failure_ids: List[int]
    errors: List[Dict[str, Any]]
