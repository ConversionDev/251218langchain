"""PDF vs _alter.txt 대조: 페이지 수·페이지별 텍스트 일치 여부 검증."""
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PDF_PATH = SCRIPT_DIR / "ISO-30414-2018.pdf"
TXT_PATH = SCRIPT_DIR / "ISO-30414-2018_alter.txt"
PAGE_SEP = "\n--- Page Break ---\n"


def normalize(s: str) -> str:
    """비교용: 공백/줄바꿈 정규화."""
    return re.sub(r"\s+", " ", s).strip()


def main():
    if not PDF_PATH.exists():
        print(f"PDF 없음: {PDF_PATH}")
        sys.exit(1)
    if not TXT_PATH.exists():
        print(f"TXT 없음: {TXT_PATH}")
        sys.exit(1)

    import fitz
    doc = fitz.open(PDF_PATH)
    pdf_page_count = len(doc)

    raw = TXT_PATH.read_text(encoding="utf-8")
    blocks = raw.split(PAGE_SEP)
    txt_page_count = len(blocks)

    print("=" * 60)
    print("PDF vs ISO-30414-2018_alter.txt 대조 결과")
    print("=" * 60)
    print(f"  PDF 페이지 수:     {pdf_page_count}")
    print(f"  TXT 페이지 블록 수: {txt_page_count}")
    if pdf_page_count != txt_page_count:
        print("  → 페이지 수 불일치.")
        doc.close()
        sys.exit(1)
    print("  → 페이지 수 일치.")

    mismatches = []
    for i in range(pdf_page_count):
        pdf_text = doc[i].get_text()
        txt_block = blocks[i] if i < len(blocks) else ""
        if normalize(pdf_text) != normalize(txt_block):
            mismatches.append(i + 1)

    doc.close()

    if not mismatches:
        print("  페이지별 텍스트: 모두 일치.")
        print("=" * 60)
        print("결론: 모든 정보가 올바르게 매핑되었습니다.")
        return

    print(f"  페이지별 텍스트 불일치 페이지: {mismatches}")
    print("=" * 60)
    print("결론: 위 페이지에서 PDF와 TXT 내용이 다릅니다.")
    sys.exit(1)


if __name__ == "__main__":
    main()
