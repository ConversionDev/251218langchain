"""PDF 텍스트 추출 → disclosure 하위에 {파일이름}_alter.txt 로 저장.

전략: StrategyFactory로 경로에 맞는 추출 전략 선택 (pdf_strategy.md).
공시(IFRS/ISO/OECD)는 FastExtract(PyMuPDF) 사용.
PowerShell에서: (torch311 활성화 후) python pdf_extract.py
"""
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def extract_pdf_to_txt(pdf_path: Path, out_path: Path) -> bool:
    from domain.shared.strategies import StrategyFactory  # type: ignore

    try:
        strategy = StrategyFactory.get_strategy(pdf_path)
        text = strategy.extract(pdf_path)
        out_path.write_text(text, encoding="utf-8")
        return True
    except Exception as e:
        print(f"   오류: {e}")
        return False


def main():
    print("1. PDF 추출 전략 로드 확인 ...")
    try:
        from domain.shared.strategies import StrategyFactory  # type: ignore
        _ = StrategyFactory.get_strategy(Path("dummy_ifrs.pdf"))
        print("   OK — StrategyFactory 사용 (공시 경로 → FastExtract/PyMuPDF)")
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
