"""
Disclosure RAG 적재 LangGraph 오케스트레이터.

- 다중 파일 지원: documents_config = [(txt_path, standard_type, source), ...]
- 조항/섹션 단위 청킹 + Recursive split → 재적재 시 sources_to_replace로 기존 삭제 후 INSERT
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from langchain_core.documents import Document
from tqdm import tqdm
from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)

# (txt_path, standard_type, source_label)
DocumentsConfigItem = Tuple[Path, str, str]


class DisclosureIngestState(TypedDict, total=False):
    """Disclosure 적재 그래프 상태."""

    txt_path: Path
    documents_config: List[DocumentsConfigItem]
    documents: List[Document]
    sources_to_replace: List[str]
    embeddings_model: Any
    doc_count: int
    error: Optional[str]
    processing_path: str


def _load_chunks_node(state: DisclosureIngestState) -> DisclosureIngestState:
    """
    documents_config가 있으면 각 (txt_path, standard_type, source)별로 청킹.
    없으면 단일 txt_path로 기존 방식(페이지 단위) 대신 청킹 모듈 사용.
    """
    all_docs: List[Document] = []
    sources_to_replace: List[str] = []

    documents_config = state.get("documents_config")
    txt_path = state.get("txt_path")

    if documents_config:
        for path, standard_type, source in tqdm(documents_config, desc="Load chunks (disclosure)", unit="file"):
            p = Path(path)
            if not p.exists():
                logger.warning("[DisclosureIngest] 파일 없음, 건너뜀: %s", p)
                continue
            try:
                from training.shared.disclosure_chunking import load_txt_and_chunk  # type: ignore
                docs = load_txt_and_chunk(p, source=source, standard_type=standard_type)
                all_docs.extend(docs)
                sources_to_replace.append(source)
            except Exception as e:
                logger.exception("[DisclosureIngest] 청킹 실패 %s: %s", p, e)
    elif txt_path and Path(txt_path).exists():
        # 단일 파일: source/standard_type 기본값
        try:
            from training.shared.disclosure_chunking import load_txt_and_chunk  # type: ignore
            source = "ISO-30414-2018"
            standard_type = "ISO30414"
            docs = load_txt_and_chunk(Path(txt_path), source=source, standard_type=standard_type)
            all_docs.extend(docs)
            sources_to_replace.append(source)
        except Exception as e:
            logger.exception("[DisclosureIngest] 청킹 실패 %s: %s", txt_path, e)
            return {
                "error": str(e),
                "doc_count": 0,
                "processing_path": (state.get("processing_path") or "Start") + " -> LoadChunks(fail)",
            }
    else:
        return {
            "error": "documents_config 또는 txt_path 없음/파일 없음",
            "doc_count": 0,
            "processing_path": (state.get("processing_path") or "Start") + " -> LoadChunks(fail)",
        }

    if not all_docs:
        return {
            "error": "유효한 청크가 없습니다.",
            "doc_count": 0,
            "processing_path": (state.get("processing_path") or "Start") + " -> LoadChunks(empty)",
        }

    logger.info("[DisclosureIngest] LoadChunks: %s docs, sources_to_replace=%s", len(all_docs), sources_to_replace)
    return {
        "documents": all_docs,
        "sources_to_replace": sources_to_replace,
        "doc_count": len(all_docs),
        "processing_path": (state.get("processing_path") or "Start") + " -> LoadChunks",
    }


def _embed_and_store_node(state: DisclosureIngestState) -> DisclosureIngestState:
    """Document 리스트를 FAISS 인덱스 구축 + Neon 텍스트만 적재. sources_to_replace 있으면 해당 source 기존 행 삭제 후 INSERT."""
    import numpy as np  # type: ignore

    from core.database import SessionLocal  # type: ignore
    from core.faiss_store import build_and_save_index  # type: ignore
    from infrastructure.persistence.repositories.disclosure_repository import (  # type: ignore
        _build_embedding_content,
        save_batch_text_only,
    )

    docs = state.get("documents") or []
    embeddings_model = state.get("embeddings_model")
    sources_to_replace = state.get("sources_to_replace") or []
    path = state.get("processing_path") or "Start"

    if not docs or not embeddings_model:
        return {
            "error": "documents/embeddings_model 누락",
            "doc_count": 0,
            "processing_path": path + " -> EmbedAndStore(skip)",
        }
    db = SessionLocal()
    try:
        texts = [_build_embedding_content(doc) for doc in docs]
        vectors = embeddings_model.embed_documents(texts)
        if not vectors or len(vectors) != len(docs):
            return {
                "error": "임베딩 개수 불일치",
                "doc_count": 0,
                "processing_path": path + " -> EmbedAndStore(fail)",
            }
        arr = np.array(vectors, dtype=np.float32)
        unique_ids = [str((doc.metadata or {}).get("unique_id", "")) for doc in docs]
        build_and_save_index(arr, unique_ids, "disclosures")
        n = save_batch_text_only(db, docs, sources_to_replace=sources_to_replace)
        logger.info("[DisclosureIngest] FAISS+Neon(text): %s docs -> disclosures (replaced %s)", n, sources_to_replace)
        return {
            "doc_count": n,
            "processing_path": path + " -> EmbedAndStore",
        }
    except Exception as e:
        db.rollback()
        logger.exception("[DisclosureIngest] EmbedAndStore 실패: %s", e)
        return {
            "error": str(e),
            "doc_count": 0,
            "processing_path": path + " -> EmbedAndStore(fail)",
        }
    finally:
        db.close()


def build_disclosure_ingest_graph():
    """Disclosure 적재 그래프: load_chunks → embed_and_store → END."""
    g = StateGraph(DisclosureIngestState)
    g.add_node("load_chunks", _load_chunks_node)
    g.add_node("embed_and_store", _embed_and_store_node)
    g.set_entry_point("load_chunks")
    g.add_edge("load_chunks", "embed_and_store")
    g.add_edge("embed_and_store", END)
    return g.compile()


_disclosure_ingest_graph: Any = None


def get_disclosure_ingest_graph():
    global _disclosure_ingest_graph
    if _disclosure_ingest_graph is None:
        _disclosure_ingest_graph = build_disclosure_ingest_graph()
    return _disclosure_ingest_graph


def get_disclosure_prepared_dir() -> Path:
    """Disclosure prepared 텍스트 파일 기본 경로. core.paths 기준."""
    from core.paths import get_data_dir  # type: ignore
    return get_data_dir() / "disclosure" / "prepared"


def _infer_standard_type_from_stem(stem: str) -> str:
    """
    파일 stem에서 standard_type 추론. RAG 검색 쪽 값과 동일하게 맞춤.
    IFRS_S1, IFRS_S2, OECD, ISO30414, GLOBAL_GREEN_STOCKTAKE.
    """
    s = stem.lower()
    if "oecd" in s:
        return "OECD"
    if "iso" in s or "30414" in s:
        return "ISO30414"
    if "green" in s or "stocktake" in s:
        return "GLOBAL_GREEN_STOCKTAKE"
    if "ifrs" in s and "s1" in s:
        return "IFRS_S1"
    if "ifrs" in s and "s2" in s:
        return "IFRS_S2"
    if "ifrs" in s:
        return "IFRS_S1"
    return "IFRS_S1"


def build_documents_config_from_prepared_dir(
    prepared_dir: Optional[Path] = None,
) -> List[DocumentsConfigItem]:
    """
    prepared 디렉터리 내 *.txt 파일로 documents_config 생성.
    (path, standard_type, source) — standard_type은 RAG 검색과 동일 값(IFRS_S1, IFRS_S2, OECD, ISO30414, GLOBAL_GREEN_STOCKTAKE).
    """
    from core.paths import get_data_dir  # type: ignore
    base = prepared_dir or get_data_dir() / "disclosure" / "prepared"
    if not base.exists():
        return []
    config: List[DocumentsConfigItem] = []
    for p in sorted(base.glob("*.txt")):
        stem = p.stem
        standard_type = _infer_standard_type_from_stem(stem)
        config.append((p, standard_type, stem))
    return config


def run_disclosure_ingest_orchestrate(
    embeddings_model: Any,
    txt_path: Optional[Path] = None,
    documents_config: Optional[List[DocumentsConfigItem]] = None,
) -> Dict[str, Any]:
    """
    Disclosure 적재 실행. disclosures 테이블에 저장.

    Args:
        embeddings_model: BGE-m3 등 임베딩 모델.
        txt_path: 단일 파일 사용 시 (기존 방식).
        documents_config: 다중 파일 사용 시 [(Path, standard_type, source), ...].
            기본 경로 사용 시 build_documents_config_from_prepared_dir() 활용.

    Returns:
        {"success": bool, "doc_count": int, "error": str | None}
    """
    if documents_config:
        initial_state: DisclosureIngestState = {
            "documents_config": documents_config,
            "documents": [],
            "sources_to_replace": [],
            "embeddings_model": embeddings_model,
            "doc_count": 0,
            "error": None,
            "processing_path": "Start",
        }
    elif txt_path:
        initial_state = {
            "txt_path": txt_path,
            "documents": [],
            "sources_to_replace": [],
            "embeddings_model": embeddings_model,
            "doc_count": 0,
            "error": None,
            "processing_path": "Start",
        }
    else:
        return {"success": False, "doc_count": 0, "error": "txt_path 또는 documents_config 필요"}

    try:
        config = {"configurable": {"thread_id": "disclosure_ingest"}}
        graph = get_disclosure_ingest_graph()
        result_state = graph.invoke(initial_state, config=config)
        doc_count = result_state.get("doc_count", 0)
        error = result_state.get("error")
        success = error is None and doc_count > 0
        out = {"success": success, "doc_count": doc_count, "error": error}
        logger.info("[DisclosureIngest] 완료 %s", out)
        return out
    except Exception as e:
        logger.exception("[DisclosureIngest] 실패: %s", e)
        return {"success": False, "doc_count": 0, "error": str(e)}
