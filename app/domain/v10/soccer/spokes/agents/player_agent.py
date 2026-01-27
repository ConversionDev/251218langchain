"""선수 데이터 정책 기반 처리 Agent"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PlayerAgent:
    """정책 기반 선수 데이터 처리 Agent

    LLM을 활용하여 복잡한 비즈니스 로직과 예외 케이스를 처리합니다.
    저장은 Store에 위임합니다.
    """

    def __init__(self, store=None):
        """
        PlayerAgent 초기화

        Args:
            store: PlayerStore 인스턴스 (None이면 자동 생성)
        """
        self.logger = logging.getLogger(__name__)
        if store is None:
            from domain.v10.soccer.hub.stores.player_store import PlayerStore  # type: ignore
            store = PlayerStore()
        self.store = store

    def process(
        self,
        data: List[Dict[str, Any]],
        db,
        vector_store,
        **kwargs
    ) -> Dict[str, Any]:
        """
        정책 기반으로 선수 데이터를 처리합니다.
        정책 처리만 수행하고, 저장은 Store에 위임합니다.

        Args:
            data: 처리할 선수 데이터 리스트
            db: 데이터베이스 세션 (정책 기반에서는 사용하지 않음)
            vector_store: 벡터 스토어
            **kwargs: 추가 파라미터

        Returns:
            처리 결과 딕셔너리
        """
        self.logger.info(f"[PlayerAgent] 정책 기반 처리 시작: {len(data)}개 선수 데이터")

        # 정책 기반 처리 로직
        # - LLM 기반 복잡한 비즈니스 로직 처리
        # - 데이터 검증 및 정규화
        # - 예외 케이스 처리
        # - 동적 규칙 적용
        # - 컨텍스트 기반 판단
        # 저장은 Store에 위임

        vector_count = 0
        errors = []

        for item in data:
            try:
                # 정책 기반 처리 로직
                if self._process_with_policy(item, vector_store):
                    vector_count += 1
            except Exception as e:
                errors.append({
                    "id": item.get("id"),
                    "error": str(e)
                })
                self.logger.warning(f"[PlayerAgent] 선수 ID {item.get('id')} 처리 실패: {str(e)}")

        return {
            "processed": vector_count,
            "db": 0,  # 정책 기반은 벡터 스토어만 저장
            "vector": vector_count,
            "total": len(data),
            "errors": errors
        }

    def _process_with_policy(
        self,
        item: Dict[str, Any],
        vector_store
    ) -> bool:
        """
        개별 선수 데이터를 정책 기반으로 처리합니다.

        Args:
            item: 선수 데이터 딕셔너리
            vector_store: 벡터 스토어

        Returns:
            저장 성공 여부
        """
        # 정책 기반 처리: 향후 LLM 기반 복잡한 비즈니스 로직 추가 가능
        # 예: 데이터 품질 검증, 비즈니스 규칙 적용 등

        # 현재는 기본 처리만 수행하고 Store에 위임
        # 향후 LLM을 사용한 정책 기반 검증 로직 추가 가능

        # Store를 통해 벡터 스토어에 저장
        return self.store.save(item, vector_store)
