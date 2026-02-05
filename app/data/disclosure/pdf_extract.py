"""PDF 텍스트 추출 → disclosure 하위에 {파일이름}_alter.txt 로 저장.
PowerShell에서: (torch311 활성화 후) python pdf_extract.py
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PAGE_SEP = "\n--- Page Break ---\n"


def extract_pdf_to_txt(pdf_path: Path, out_path: Path) -> bool:
    import fitz
    try:
        doc = fitz.open(pdf_path)
        parts = []
        for page in doc:
            parts.append(page.get_text())
        doc.close()
        text = PAGE_SEP.join(parts)
        out_path.write_text(text, encoding="utf-8")
        return True
    except Exception as e:
        print(f"   오류: {e}")
        return False


def main():
    print("1. PyMuPDF import 확인 ...")
    try:
        import fitz
        print(f"   OK — PyMuPDF 버전: {fitz.version[0]}")
    except ImportError as e:
        print(f"   실패: {e}")
        print("   torch311 환경에서 실행했는지 확인하세요: conda activate torch311")
        sys.exit(1)

    pdfs = list(SCRIPT_DIR.glob("*.pdf"))
    if not pdfs:
        print("2. 처리할 PDF 없음.")
        return

    for pdf_path in sorted(pdfs):
        stem = pdf_path.stem
        out_path = SCRIPT_DIR / f"{stem}_alter.txt"
        print(f"2. 변환: {pdf_path.name} → {out_path.name}")
        if extract_pdf_to_txt(pdf_path, out_path):
            print(f"   저장됨: {out_path}")
        else:
            print(f"   실패: {pdf_path.name}")

    print("완료.")


if __name__ == "__main__":
    main()
