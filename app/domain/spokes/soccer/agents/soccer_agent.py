"""
Soccer Agents — 선수/팀/경기장/일정 정책·규칙 처리

PlayerAgent(정책 기반 LLM·벡터 저장), Schedule/Stadium/Team은 Rule만 사용 시 서비스 직접 호출.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Player Agent (Policy: LLM + 벡터 저장 / Rule: 서비스에서 처리)
# -----------------------------------------------------------------------------


class PlayerAgent:
    """정책 기반 선수 데이터 처리 Agent.

    LLM·벡터 스토어를 사용합니다. 저장은 Store에 위임합니다.
    """

    def __init__(self, store: Any = None) -> None:
        if store is None:
            from domain.spokes.soccer.retrievers.soccer_store import SoccerStore  # type: ignore

            store = SoccerStore(entity_type="player")
        self.store = store
        self.logger = logging.getLogger(__name__)

    def process(
        self,
        data: List[Dict[str, Any]],
        db: Any = None,
        vector_store: Any = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """정책 기반으로 선수 데이터를 처리합니다. 벡터 스토어에 저장합니다."""
        if not vector_store or not data:
            return {"vector": 0}
        saved = 0
        for item in data:
            if self.store.save(item, vector_store):
                saved += 1
        return {"vector": saved}
