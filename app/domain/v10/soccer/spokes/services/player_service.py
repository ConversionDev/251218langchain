"""선수 데이터 규칙 기반 처리 Service"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PlayerService:
    """규칙 기반 선수 데이터 처리 Service

    명확한 규칙에 따라 데이터를 검증하고 변환합니다.
    저장은 Repository에 위임합니다.
    """

    def __init__(self, repository=None):
        """
        PlayerService 초기화

        Args:
            repository: PlayerRepository 인스턴스 (None이면 자동 생성)
        """
        self.logger = logging.getLogger(__name__)
        if repository is None:
            from domain.v10.soccer.hub.repositories.player_repository import PlayerRepository  # type: ignore
            repository = PlayerRepository()
        self.repository = repository

    def process(
        self,
        data: List[Dict[str, Any]],
        db,
        vector_store,
        **kwargs
    ) -> Dict[str, Any]:
        """
        규칙 기반으로 선수 데이터를 처리합니다.
        검증 및 변환만 수행하고, 저장은 Repository에 위임합니다.

        Args:
            data: 처리할 선수 데이터 리스트
            db: 데이터베이스 세션
            vector_store: 벡터 스토어 (규칙 기반에서는 사용하지 않음)
            **kwargs: 추가 파라미터

        Returns:
            처리 결과 딕셔너리
        """
        self.logger.info(f"[PlayerService] 규칙 기반 처리 시작: {len(data)}개 선수 데이터")

        # 규칙 기반 처리 로직
        # - 필수 필드 검증
        # - 데이터 타입 변환
        # - 기본값 설정
        # 저장은 Repository에 위임

        db_count = 0
        errors = []

        for item in data:
            try:
                # 규칙 기반 검증 및 변환
                validated_item = self._validate_and_transform(item)
                # Repository를 통해 관계형 DB에만 저장
                if self.repository.save(validated_item, db):
                    db_count += 1
            except Exception as e:
                errors.append({
                    "id": item.get("id"),
                    "error": str(e)
                })
                self.logger.warning(f"[PlayerService] 선수 ID {item.get('id')} 처리 실패: {str(e)}")

        return {
            "processed": db_count,
            "db": db_count,
            "vector": 0,  # 규칙 기반은 관계형 DB만 저장
            "total": len(data),
            "errors": errors
        }

    def _validate_and_transform(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터를 규칙에 따라 검증하고 변환합니다.

        Args:
            item: 선수 데이터 딕셔너리

        Returns:
            검증 및 변환된 데이터

        Raises:
            ValueError: 검증 실패 시
        """
        # 필수 필드 검증
        required_fields = ["id", "player_name", "team_id"]
        for field in required_fields:
            if field not in item or item[field] is None:
                raise ValueError(f"필수 필드 '{field}'가 없습니다.")

        # 데이터 타입 변환 및 기본값 설정
        validated = {
            "id": int(item["id"]),
            "player_name": str(item.get("player_name", "")).strip(),
            "team_id": int(item["team_id"]) if item["team_id"] else None,
            "e_player_name": str(item.get("e_player_name", "")).strip() if item.get("e_player_name") else None,
            "nickname": str(item.get("nickname", "")).strip() if item.get("nickname") else None,
            "join_yyyy": int(item["join_yyyy"]) if item.get("join_yyyy") else None,
            "position": str(item.get("position", "")).strip() if item.get("position") else None,
            "back_no": int(item["back_no"]) if item.get("back_no") else None,
            "nation": str(item.get("nation", "")).strip() if item.get("nation") else None,
            "birth_date": str(item.get("birth_date", "")).strip() if item.get("birth_date") else None,
            "solar": str(item.get("solar", "")).strip() if item.get("solar") else None,
            "height": int(item["height"]) if item.get("height") else None,
            "weight": int(item["weight"]) if item.get("weight") else None,
        }

        return validated
