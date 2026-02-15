# training.shared — 학습/적재 공용: 검증, 청킹 등
# disclosure, competency_anchors 등 테이블별 청킹·검증은 이 패키지 하위에서 관리.

from training.shared.disclosure_chunking import load_txt_and_chunk  # type: ignore  # noqa: F401

__all__ = ["load_txt_and_chunk"]
