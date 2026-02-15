"""
FAISS 인덱스·id_map 로드/저장 및 검색 헬퍼.

- 벡터는 IndexFlatIP + L2 정규화로 코사인 유사도와 동일.
- disclosures / competency_anchors 각각 별도 인덱스·id_map.
"""

from typing import Any, List, Optional, Tuple

import numpy as np  # type: ignore

from core.paths import get_faiss_dir  # type: ignore
from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore

# 전역: 서버 기동 시 로드한 인덱스·id_map (없으면 None)
_disclosure_index: Any = None
_disclosure_id_map: Optional[List[str]] = None
_competency_index: Any = None
_competency_id_map: Optional[List[str]] = None


def _normalize_l2(vec: np.ndarray) -> np.ndarray:
    """제자리 L2 정규화. 1차원이면 (1, dim)으로 반환."""
    if vec.ndim == 1:
        vec = vec.reshape(1, -1).astype(np.float32)
    faiss = __import__("faiss", fromlist=["normalize_L2"])
    faiss.normalize_L2(vec)
    return vec


def load_faiss_indices() -> bool:
    """artifacts/faiss/ 에서 disclosures.index, competency_anchors.index 및 id_map 로드. 성공 시 True."""
    global _disclosure_index, _disclosure_id_map, _competency_index, _competency_id_map
    import pickle as pkl

    try:
        import faiss  # type: ignore
    except ImportError:
        return False

    base = get_faiss_dir()
    loaded = False

    # disclosures
    idx_path = base / "disclosures.index"
    map_path = base / "disclosures_id_map.pkl"
    if idx_path.exists() and map_path.exists():
        _disclosure_index = faiss.read_index(str(idx_path))
        with map_path.open("rb") as f:
            _disclosure_id_map = pkl.load(f)
        loaded = True

    # competency_anchors
    idx_path = base / "competency_anchors.index"
    map_path = base / "competency_anchors_id_map.pkl"
    if idx_path.exists() and map_path.exists():
        _competency_index = faiss.read_index(str(idx_path))
        with map_path.open("rb") as f:
            _competency_id_map = pkl.load(f)
        loaded = True

    return loaded


def get_disclosure_index():
    return _disclosure_index


def get_disclosure_id_map() -> Optional[List[str]]:
    return _disclosure_id_map


def get_competency_index():
    return _competency_index


def get_competency_id_map() -> Optional[List[str]]:
    return _competency_id_map


def is_faiss_disclosure_ready() -> bool:
    return _disclosure_index is not None and _disclosure_id_map is not None


def is_faiss_competency_ready() -> bool:
    return _competency_index is not None and _competency_id_map is not None


def search_faiss_disclosure(
    query_vec: List[float],
    k: int,
) -> Tuple[List[int], List[float]]:
    """
    정규화된 쿼리 벡터로 disclosures FAISS 검색.
    Returns: (index_list, ip_scores). 거리는 1 - ip 로 변환해 사용.
    """
    if not is_faiss_disclosure_ready():
        return [], []
    q = np.array([query_vec], dtype=np.float32)
    _normalize_l2(q)
    scores, indices = _disclosure_index.search(q, k)
    idx_list = []
    score_list = []
    for i, idx in enumerate(indices[0].tolist()):
        if idx >= 0:  # FAISS uses -1 for missing
            idx_list.append(idx)
            score_list.append(scores[0].tolist()[i])
    return idx_list, score_list


def search_faiss_competency(
    query_vec: List[float],
    k: int,
) -> Tuple[List[int], List[float]]:
    """정규화된 쿼리로 competency_anchors FAISS 검색. (index_list, ip_scores)."""
    if not is_faiss_competency_ready():
        return [], []
    q = np.array([query_vec], dtype=np.float32)
    _normalize_l2(q)
    scores, indices = _competency_index.search(q, k)
    idx_list = []
    score_list = []
    for i, idx in enumerate(indices[0].tolist()):
        if idx >= 0:
            idx_list.append(idx)
            score_list.append(scores[0].tolist()[i])
    return idx_list, score_list


def build_and_save_index(
    vectors: np.ndarray,
    unique_ids: List[str],
    name: str,
) -> None:
    """
    vectors: (N, 1024) float32. L2 정규화 후 IndexFlatIP로 저장.
    unique_ids: add 순서와 동일한 길이 N.
    name: "disclosures" | "competency_anchors"
    """
    import pickle as pkl

    import faiss  # type: ignore

    if vectors.size == 0 or len(unique_ids) != len(vectors):
        raise ValueError("vectors와 unique_ids 길이 불일치 또는 빈 벡터")
    vectors = vectors.astype(np.float32)
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(BGE_M3_DENSE_DIM)
    index.add(vectors)
    base = get_faiss_dir()
    faiss.write_index(index, str(base / f"{name}.index"))
    with (base / f"{name}_id_map.pkl").open("wb") as f:
        pkl.dump(unique_ids, f)
