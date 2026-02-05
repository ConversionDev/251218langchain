"""
Disclosure(ISO 30414) RAG 적재 LangGraph 오케스트레이터.

그래프: load_chunks → embed_and_store → END
- LangChain PGVector에 넣는 작업을 LangGraph 흐름으로 실행.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)

PAGE_SEP = "\n--- Page Break ---\n"
DEFAULT_TXT_NAME = "ISO-30414-2018_alter.txt"


class DisclosureIngestState(TypedDict, total=False):
    """Disclosure 적재 그래프 상태."""

    txt_path: Path
    documents: List[Document]
    embeddings_model: Any
    collection_name: str
    connection_string: str
    doc_count: int
    error: Optional[str]
    processing_path: str


def _load_chunks_node(state: DisclosureIngestState) -> DisclosureIngestState:
    """텍스트 파일을 읽어 페이지 단위 Document 리스트 생성."""
    txt_path = state.get("txt_path")
    if not txt_path or not Path(txt_path).exists():
        return {
            "error": f"파일 없음: {txt_path}",
            "doc_count": 0,
            "processing_path": (state.get("processing_path") or "Start") + " -> LoadChunks(fail)",
        }
    text = Path(txt_path).read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.split(PAGE_SEP) if b.strip()]
    if not blocks:
        return {
            "error": "유효한 페이지 블록이 없습니다.",
            "doc_count": 0,
            "processing_path": (state.get("processing_path") or "Start") + " -> LoadChunks(empty)",
        }
    docs = [
        Document(
            page_content=block,
            metadata={"source": "ISO-30414-2018", "page": i + 1},
        )
        for i, block in enumerate(blocks)
    ]
    logger.info("[DisclosureIngest] LoadChunks: %s chunks from %s", len(docs), txt_path)
    return {
        "documents": docs,
        "doc_count": len(docs),
        "processing_path": (state.get("processing_path") or "Start") + " -> LoadChunks",
    }


def _embed_and_store_node(state: DisclosureIngestState) -> DisclosureIngestState:
    """Document 리스트를 임베딩해 disclosure 컬렉션에 적재."""
    from langchain_community.vectorstores import PGVector  # type: ignore[import-untyped]

    docs = state.get("documents") or []
    embeddings_model = state.get("embeddings_model")
    collection_name = state.get("collection_name")
    connection_string = state.get("connection_string")
    path = state.get("processing_path") or "Start"

    if not docs or not embeddings_model or not collection_name or not connection_string:
        return {
            "error": "documents/embeddings_model/collection_name/connection_string 누락",
            "doc_count": 0,
            "processing_path": path + " -> EmbedAndStore(skip)",
        }
    try:
        store = PGVector(
            embedding_function=embeddings_model,
            collection_name=collection_name,
            connection_string=connection_string,
        )
        store.add_documents(docs)
        logger.info(
            "[DisclosureIngest] EmbedAndStore: %s docs -> %s",
            len(docs),
            collection_name,
        )
        return {
            "doc_count": len(docs),
            "processing_path": path + " -> EmbedAndStore",
        }
    except Exception as e:
        logger.exception("[DisclosureIngest] EmbedAndStore 실패: %s", e)
        return {
            "error": str(e),
            "doc_count": 0,
            "processing_path": path + " -> EmbedAndStore(fail)",
        }


def build_disclosure_ingest_graph():
    """Disclosure 적재 LangGraph 빌드: load_chunks → embed_and_store → END."""
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


def run_disclosure_ingest_orchestrate(
    embeddings_model: Any,
    collection_name: str,
    connection_string: str,
    txt_path: Path,
) -> Dict[str, Any]:
    """
    LangGraph로 ISO 30414 disclosure 적재 실행.

    Returns:
        {"success": bool, "doc_count": int, "error": str | None}
    """
    try:
        initial_state: DisclosureIngestState = {
            "txt_path": txt_path,
            "documents": [],
            "embeddings_model": embeddings_model,
            "collection_name": collection_name,
            "connection_string": connection_string,
            "doc_count": 0,
            "error": None,
            "processing_path": "Start",
        }
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
