"""선수 데이터 벡터 DB 저장 Store

정책 기반 처리 전략에서 사용하는 벡터 스토어 저장 로직을 담당합니다.
"""

import logging
from typing import Dict, Any

from langchain_core.documents import Document  # type: ignore[import-untyped]

from domain.v10.shared.data_loader import player_to_text  # type: ignore

logger = logging.getLogger(__name__)


class PlayerStore:
    """선수 데이터 벡터 스토어 저장 Store

    정책 기반 처리에서 벡터 스토어에만 저장하는 책임을 가집니다.
    """

    def __init__(self):
        """PlayerStore 초기화"""
        self.logger = logging.getLogger(__name__)

    def save(
        self,
        item: Dict[str, Any],
        vector_store
    ) -> bool:
        """
        선수 데이터를 벡터 스토어에 저장합니다.

        Args:
            item: 선수 데이터 딕셔너리
            vector_store: 벡터 스토어 인스턴스

        Returns:
            저장 성공 여부
        """
        try:
            # 벡터 스토어용 문서 생성
            text = player_to_text(item)
            metadata = {
                "id": item.get("id"),
                "type": "player",
                "team_id": item.get("team_id"),
                "player_name": item.get("player_name"),
                "position": item.get("position"),
                "back_no": item.get("back_no"),
                "nation": item.get("nation"),
                "join_yyyy": item.get("join_yyyy"),
            }
            # None 값 제거
            metadata = {k: v for k, v in metadata.items() if v is not None}

            # 벡터 스토어에 저장
            vector_store.add_documents([Document(page_content=text, metadata=metadata)])
            self.logger.debug(
                f"[PlayerStore] 선수 ID {item.get('id')} ({item.get('player_name')}) 벡터 스토어에 저장됨"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"[PlayerStore] 선수 ID {item.get('id')} 벡터 스토어 저장 실패: {str(e)}"
            )
            return False
