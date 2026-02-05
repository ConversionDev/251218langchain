"""ISO 30414 공시 문서를 disclosure 전용 벡터 컬렉션에 적재.

LangGraph 오케스트레이터(disclosure_orchestrator)를 통해 적재합니다.
실행: app 디렉터리에서
  python -m data.disclosure.ingest

필요: .env 또는 환경변수(DATABASE_URL 등), 임베딩 모델 다운로드 가능 환경.
"""

import sys
from pathlib import Path

# app 디렉터리가 PYTHONPATH에 있도록 (app 상위에서 실행 시)
SCRIPT_DIR = Path(__file__).resolve().parent
APP_ROOT = SCRIPT_DIR.parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

TXT_NAME = "ISO-30414-2018_alter.txt"


def _get_embeddings():
    """앱과 동일한 임베딩 모델 반환."""
    from core.config import get_settings  # type: ignore

    settings = get_settings()
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore

    device = getattr(settings, "embedding_device", None) or "cpu"
    return HuggingFaceEmbeddings(
        model_name=settings.default_embedding_model,
        model_kwargs={"device": device},
    )


def run_ingest() -> int:
    """LangGraph로 ISO-30414-2018_alter.txt를 disclosure 컬렉션에 적재.

    그래프: load_chunks → embed_and_store → END
    Returns:
        적재된 문서(청크) 개수
    """
    from domain.hub.orchestrators.disclosure_orchestrator import (  # type: ignore
        run_disclosure_ingest_orchestrate,
    )

    from core.config import get_settings  # type: ignore

    txt_path = SCRIPT_DIR / TXT_NAME
    if not txt_path.exists():
        raise FileNotFoundError(f"{TXT_NAME} 없음: {txt_path}. 먼저 pdf_extract.py로 추출하세요.")

    settings = get_settings()
    print("[ingest] 임베딩 모델 로드 중 ...")
    embeddings = _get_embeddings()
    print("[ingest] LangGraph disclosure 적재 실행 중 ...")
    result = run_disclosure_ingest_orchestrate(
        embeddings_model=embeddings,
        collection_name=settings.disclosure_collection_name,
        connection_string=settings.connection_string,
        txt_path=txt_path,
    )
    if not result.get("success"):
        err = result.get("error", "Unknown error")
        raise RuntimeError(f"Disclosure 적재 실패: {err}")
    n = result.get("doc_count", 0)
    print(f"[ingest] 완료: {n}개 적재됨 (컬렉션: {settings.disclosure_collection_name})")
    return n


def main() -> None:
    try:
        n = run_ingest()
        print(f"정상 종료. 적재 문서 수: {n}")
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
