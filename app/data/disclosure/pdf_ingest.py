"""공시 문서(ISO 30414, IFRS S1/S2, OECD 등) 청킹 + disclosures 테이블 적재.

- 청킹: 조항/섹션 단위 + Recursive split (상한 3200자). load_txt_and_chunk()로 _alter.txt → Document 리스트.
- 적재: 다중 *_alter.txt 자동 발견 → standard_type 매핑 → DB INSERT + BGE-m3 임베딩.
- 재적재 시 해당 source 기존 행 삭제 후 INSERT.

실행 (app 디렉터리에서):
  python -m data.disclosure.pdf_ingest

사전: pdf_extract로 각 PDF → {stem}_alter.txt 생성.
필요: .env(DATABASE_URL 등), 임베딩 모델 다운로드 가능.
"""

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_core.documents import Document

# app 디렉터리가 PYTHONPATH에 있도록
SCRIPT_DIR = Path(__file__).resolve().parent
APP_ROOT = SCRIPT_DIR.parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

# ---- 청킹 상수 (pdf_extract와 동일 구분자) ----
PAGE_SEP = "\n--- Page Break ---\n"
MAX_CHUNK_CHARS = 3200
MIN_CHUNK_CHARS = 400
SECTION_TITLE_MAX_CHARS = 200

SECTION_HEADER_RE = re.compile(
    r"^(\d+(?:\.\d+)*)\s*(.*)$|^(Appendix\s+[A-Z0-9]+)\s*$|^(Section\s+[\d.]+)\s*$",
    re.IGNORECASE,
)


def _normalize_section_id(section_title: str, chunk_index: int) -> str:
    """unique_id용 section_id: 제목에서 특수문자 제거."""
    if not section_title:
        return f"p{chunk_index}"
    safe = re.sub(r"[^\w\s.]", "", section_title)[:80].strip()
    safe = re.sub(r"\s+", "_", safe) or f"chunk_{chunk_index}"
    return f"{safe}_{chunk_index}"


def _split_by_sections(text: str) -> List[Tuple[int, str, str]]:
    """PAGE_SEP로 페이지 구분 후, 각 페이지 내 조항/헤더로 섹션 구분. 빈 페이지도 유지."""
    pages = text.split(PAGE_SEP)
    result: List[Tuple[int, str, str]] = []

    for page_num, page_text in enumerate(pages, start=1):
        page_stripped = page_text.strip()
        blocks = [b.strip() for b in page_text.split("\n\n") if b.strip()]
        if not blocks:
            result.append((page_num, f"Page {page_num}", page_stripped))
            continue

        i = 0
        while i < len(blocks):
            block = blocks[i]
            first_line = block.split("\n")[0].strip() if "\n" in block else block
            match = SECTION_HEADER_RE.match(first_line)

            if match:
                g1, g2, g3, g4 = match.group(1), match.group(2), match.group(3), match.group(4)
                if g1:
                    section_title = ((g1 or "") + " " + (g2 or "")).strip()
                elif g3:
                    section_title = (g3 or "").strip()
                elif g4:
                    section_title = (g4 or "").strip()
                else:
                    section_title = first_line[:80]
                content_so_far = block
                i += 1
                while i < len(blocks):
                    next_block = blocks[i]
                    next_first = next_block.split("\n")[0].strip() if "\n" in next_block else next_block
                    if SECTION_HEADER_RE.match(next_first):
                        break
                    content_so_far = (content_so_far + "\n\n" + next_block).strip()
                    i += 1
                if content_so_far.strip():
                    result.append((page_num, section_title or first_line[:80], content_so_far.strip()))
            else:
                result.append((page_num, f"Page {page_num}", block))
                i += 1

    if not result:
        for page_num, page_text in enumerate(pages, start=1):
            if page_text.strip():
                result.append((page_num, f"Page {page_num}", page_text.strip()))
    return result


def _recursive_split(
    section_content: str,
    section_title: str,
    page_num: int,
    source: str,
    standard_type: str,
    section_id_base: str,
) -> List[Document]:
    """섹션 본문을 상한 이하로 재귀 분할. 문단 → 문장 순."""
    if len(section_content) <= MAX_CHUNK_CHARS:
        return [
            Document(
                page_content=section_content.strip(),
                metadata={
                    "source": source,
                    "page": page_num,
                    "section_title": section_title,
                    "standard_type": standard_type,
                    "unique_id": f"{source}|{section_id_base}|0",
                },
            )
        ]

    chunks: List[str] = []
    separators = ["\n\n", "\n", ". "]
    remaining = section_content.strip()
    while remaining:
        if len(remaining) <= MAX_CHUNK_CHARS:
            chunks.append(remaining.strip())
            break
        best_pos = -1
        best_sep = ""
        for sep in separators:
            pos = remaining.find(sep, MIN_CHUNK_CHARS, MAX_CHUNK_CHARS + 1)
            if pos == -1:
                pos = remaining.rfind(sep, 0, MAX_CHUNK_CHARS + 1)
            if pos >= MIN_CHUNK_CHARS and pos > best_pos:
                best_pos = pos
                best_sep = sep
        if best_pos <= 0:
            best_pos = min(MAX_CHUNK_CHARS, len(remaining))
            best_sep = ""
        end = best_pos + len(best_sep) if best_sep else best_pos
        chunk = remaining[:end].strip()
        remaining = remaining[end:].strip()
        if chunk:
            chunks.append(chunk)
        if not remaining:
            break

    docs = []
    for idx, chunk_text in enumerate(chunks):
        section_id = _normalize_section_id(section_title, idx) if len(chunks) > 1 else section_id_base
        unique_id = f"{source}|{section_id}|{idx}"
        docs.append(
            Document(
                page_content=chunk_text,
                metadata={
                    "source": source,
                    "page": page_num,
                    "section_title": section_title,
                    "standard_type": standard_type,
                    "unique_id": unique_id,
                },
            )
        )
    return docs


def chunk_disclosure_text(text: str, source: str, standard_type: str) -> List[Document]:
    """공시 원문 텍스트를 조항/섹션 단위로 나눈 뒤, 필요 시 재귀 분할하여 Document 리스트 반환."""
    sections = _split_by_sections(text)
    documents: List[Document] = []
    for page_num, section_title, section_content in sections:
        section_id_base = _normalize_section_id(section_title, 0)
        sub_docs = _recursive_split(
            section_content, section_title, page_num, source, standard_type, section_id_base
        )
        documents.extend(sub_docs)
    return documents


def load_txt_and_chunk(txt_path: Path, source: str, standard_type: str) -> List[Document]:
    """텍스트 파일을 읽어 청킹된 Document 리스트 반환."""
    content = txt_path.read_text(encoding="utf-8")
    return chunk_disclosure_text(content, source=source, standard_type=standard_type)


def build_embedding_content(standard_type: str, section_title: str, content: str) -> str:
    """[Standard] [Section]: Content 형태로 임베딩용 문자열 생성."""
    title = (section_title or "").strip()[:SECTION_TITLE_MAX_CHARS]
    return f"{standard_type} {title}: {content}".strip()


# ---- 적재용 설정·진입점 ----
STANDARD_TYPE_MAP = {
    "2018-ISO-30414": "ISO30414",
    "2023-ifrs-s1-disclosure": "IFRS_S1",
    "2025-ifrs-s2-climate-disclosures": "IFRS_S2",
    "2025-oecd": "OECD",
    "2025-global-green-stocktake-": "GLOBAL_GREEN_STOCKTAKE",
}


def discover_documents_config() -> List[Tuple[Path, str, str]]:
    """data/disclosure/*_alter.txt를 찾아 (path, standard_type, source) 리스트 반환."""
    result: List[Tuple[Path, str, str]] = []
    for txt_path in sorted(SCRIPT_DIR.glob("*_alter.txt")):
        stem = txt_path.stem
        base = stem.replace("_alter", "")
        standard_type = STANDARD_TYPE_MAP.get(base, base.replace("-", "_").upper()[:50])
        source = base
        result.append((txt_path, standard_type, source))
    return result


def run_ingest(documents_config: Optional[List[Tuple[Path, str, str]]] = None) -> int:
    """공시 문서 청킹 후 적재. documents_config가 없으면 _alter.txt 자동 발견. 적재된 청크 개수 반환."""
    from domain.hub.orchestrators.disclosure_orchestrator import (  # type: ignore
        run_disclosure_ingest_orchestrate,
    )
    from core.config import get_settings  # type: ignore

    if documents_config is None:
        documents_config = discover_documents_config()
    if not documents_config:
        raise FileNotFoundError(
            f"{SCRIPT_DIR}에 *_alter.txt가 없습니다. 먼저 pdf_extract로 PDF를 추출하세요."
        )

    settings = get_settings()
    print("[ingest] FlagEmbedding BGE-m3 로드 중 ...")
    from domain.shared.embedding import get_embedding_model  # type: ignore
    embeddings = get_embedding_model(use_fp16=True)
    print("[ingest] 문서 수:", len(documents_config), "-> 청킹 후 disclosures 적재 중 ...")
    result = run_disclosure_ingest_orchestrate(
        embeddings_model=embeddings,
        collection_name=settings.disclosure_collection_name,
        connection_string=settings.connection_string,
        documents_config=documents_config,
    )
    if not result.get("success"):
        err = result.get("error", "Unknown error")
        raise RuntimeError(f"Disclosure 적재 실패: {err}")
    n = result.get("doc_count", 0)
    print(f"[ingest] 완료: {n}개 적재됨 (disclosures 테이블)")
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
