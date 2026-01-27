"""경기장 데이터 규칙 기반 처리 Service"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class StadiumService:
    """규칙 기반 경기장 데이터 처리 Service

    명확한 규칙에 따라 데이터를 검증하고 변환합니다.
    저장은 Repository에 위임합니다.
    """

    def __init__(self, repository=None):
        """
        StadiumService 초기화

        Args:
            repository: StadiumRepository 인스턴스 (None이면 자동 생성)
        """
        self.logger = logging.getLogger(__name__)
        if repository is None:
            from domain.v10.soccer.hub.repositories.stadium_repository import StadiumRepository  # type: ignore
            repository = StadiumRepository()
        self.repository = repository

    def process(
        self,
        data: List[Dict[str, Any]],
        db,
        vector_store,
        **kwargs
    ) -> Dict[str, Any]:
        """
        규칙 기반으로 경기장 데이터를 처리합니다.
        검증 및 변환만 수행하고, 저장은 Repository에 위임합니다.

        Args:
            data: 처리할 경기장 데이터 리스트
            db: 데이터베이스 세션
            vector_store: 벡터 스토어 (규칙 기반에서는 사용하지 않음)
            **kwargs: 추가 파라미터

        Returns:
            처리 결과 딕셔너리
        """
        self.logger.info(f"[StadiumService] 규칙 기반 처리 시작: {len(data)}개 경기장 데이터")

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
                self.logger.warning(f"[StadiumService] 경기장 ID {item.get('id')} 처리 실패: {str(e)}")

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
            item: 경기장 데이터 딕셔너리

        Returns:
            검증 및 변환된 데이터

        Raises:
            ValueError: 검증 실패 시
        """
        # 필수 필드 검증
        required_fields = ["id", "stadium_code", "statdium_name"]
        for field in required_fields:
            if field not in item or item[field] is None:
                raise ValueError(f"필수 필드 '{field}'가 없습니다.")

        # 데이터 타입 변환 및 기본값 설정
        validated = {
            "id": int(item["id"]),
            "stadium_code": str(item.get("stadium_code", "")).strip(),
            "statdium_name": str(item.get("statdium_name", "")).strip(),
            "hometeam_id": int(item["hometeam_id"]) if item.get("hometeam_id") else None,
            "hometeam_code": str(item.get("hometeam_code", "")).strip() if item.get("hometeam_code") else None,
            "seat_count": int(item["seat_count"]) if item.get("seat_count") else None,
            "address": str(item.get("address", "")).strip() if item.get("address") else None,
            "ddd": str(item.get("ddd", "")).strip() if item.get("ddd") else None,
            "tel": str(item.get("tel", "")).strip() if item.get("tel") else None,
        }

        return validated
