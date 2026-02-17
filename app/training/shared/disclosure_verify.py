"""
Disclosure PDF ↔ prepared txt 일치 검증.

- raw 내 각 PDF에 대해 prepared/{stem}.txt 존재 여부.
- PDF 페이지 수와 txt 내 페이지 구분자로 나눈 segment 수 일치 여부.
- PDF 접근: domain/shared/document_extract 사용.
"""

from pathlib import Path
from typing import Optional, Tuple

from domain.shared.document_extract import get_pdf_page_count  # type: ignore

# disclosure_chunking, pdf_strategy와 동일
PAGE_SEP = "\n--- Page Break ---\n"


def verify_pdf_text_match(
    raw_dir: Path,
    prepared_dir: Path,
) -> Tuple[bool, Optional[str]]:
    """
    raw 내 각 .pdf에 대해 prepared/{stem}.txt가 있고,
    PDF 페이지 수와 txt의 페이지 구분자로 나눈 segment 수가 일치하는지 검증.

    Returns:
        (True, None) 성공.
        (False, "오류 메시지") 실패.
    """
    if not raw_dir.exists():
        return False, f"raw 디렉터리가 없습니다. 검증할 PDF가 없습니다: {raw_dir}"

    pdfs = list(sorted(raw_dir.glob("*.pdf")))
    if not pdfs:
        return False, "raw에 PDF 파일이 없습니다. 검증할 대상이 없으므로 실패합니다. raw에 PDF를 넣은 뒤 다시 실행하세요."

    prepared_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in pdfs:
        txt_path = prepared_dir / f"{pdf_path.stem}.txt"
        if not txt_path.exists():
            return False, f"PDF에 대응하는 txt 없음: {pdf_path.name} → {txt_path.name}"

        try:
            page_count = get_pdf_page_count(pdf_path)
        except Exception as e:
            return False, f"PDF 페이지 수 확인 실패 {pdf_path.name}: {e}"

        text = txt_path.read_text(encoding="utf-8", errors="replace")
        # PDF 페이지 수 = txt를 PAGE_SEP로 나눈 segment 수 (1페이지면 SEP 없음 → 1개)
        segments = text.split(PAGE_SEP)
        if len(segments) != page_count:
            return (
                False,
                f"PDF·txt 페이지 수 불일치: {pdf_path.name} (PDF {page_count}페이지, txt {len(segments)}개 segment)",
            )

    return True, None
