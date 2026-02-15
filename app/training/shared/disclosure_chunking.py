"""
Disclosure용 txt 청킹 — prepared/*.txt 읽어 Document 리스트 반환.

- 페이지 구분자: domain/shared pdf_strategy와 동일한 PAGE_SEP 사용.
- 청킹: RecursiveCharacterTextSplitter (chunk_size 800, overlap 100).
- 메타데이터: source, standard_type, page, section_title, unique_id.
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# disclosure 파이프라인과 동일한 페이지 구분자 (pdf_strategy 호환)
PAGE_SEP = "\n--- Page Break ---\n"

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 100


def load_txt_and_chunk(
    txt_path: Path,
    *,
    source: str,
    standard_type: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Document]:
    """
    prepared 텍스트 파일을 읽어 청크 단위 Document 리스트로 반환.

    Args:
        txt_path: .txt 파일 경로.
        source: 문서 식별자 (예: 파일 stem).
        standard_type: IFRS, ISO30414 등.
        chunk_size: 청크 최대 문자 수.
        chunk_overlap: 청크 간 겹침 문자 수.

    Returns:
        metadata에 source, standard_type, page, section_title, unique_id 포함.
    """
    path = Path(txt_path)
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    docs: List[Document] = []
    if PAGE_SEP in text:
        pages = text.split(PAGE_SEP)
        for page_no, page_text in enumerate(pages, start=1):
            page_text = page_text.strip()
            if not page_text:
                continue
            chunks = splitter.split_text(page_text)
            for idx, content in enumerate(chunks):
                section_title = _first_line_or_empty(content)
                unique_id = f"{source}_{page_no}_{idx}"
                docs.append(
                    Document(
                        page_content=content,
                        metadata={
                            "source": source,
                            "standard_type": standard_type,
                            "page": page_no,
                            "section_title": section_title[:200] if section_title else "",
                            "unique_id": unique_id,
                        },
                    )
                )
    else:
        chunks = splitter.split_text(text)
        for idx, content in enumerate(chunks):
            section_title = _first_line_or_empty(content)
            unique_id = f"{source}_0_{idx}"
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": source,
                        "standard_type": standard_type,
                        "page": None,
                        "section_title": section_title[:200] if section_title else "",
                        "unique_id": unique_id,
                    },
                )
            )

    return docs


def _first_line_or_empty(text: str) -> str:
    """첫 번째 비어 있지 않은 줄을 반환 (섹션 제목 추정용)."""
    for line in text.splitlines():
        s = line.strip()
        if s:
            return s
    return ""
