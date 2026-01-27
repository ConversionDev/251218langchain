"""Hub 레벨 Repository 모듈

규칙 기반 처리 전략에서 사용하는 관계형 DB 저장 로직을 담당합니다.
"""

from domain.v10.soccer.hub.repositories.player_repository import PlayerRepository  # type: ignore

__all__ = ["PlayerRepository"]
