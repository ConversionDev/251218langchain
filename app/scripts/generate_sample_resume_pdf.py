"""
샘플 이력서 PDF 생성 (PyMuPDF).

이력서 업로드·파싱 테스트용 1페이지 샘플 PDF를 생성합니다.
실행: 프로젝트 루트에서
  cd app && python scripts/generate_sample_resume_pdf.py
  python scripts/generate_sample_resume_pdf.py --output data/resume/samples/sample_resume.pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# app 루트 (스크립트가 app/scripts/ 또는 repo 루트에서 실행될 수 있음)
_script_dir = Path(__file__).resolve().parent
APP_ROOT = _script_dir.parent if _script_dir.name == "scripts" else _script_dir
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF가 필요합니다: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


def get_output_path() -> Path:
    """기본 출력 경로: app/data/resume/samples/sample_resume.pdf"""
    samples_dir = APP_ROOT / "data" / "resume" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    return samples_dir / "sample_resume.pdf"


def main() -> None:
    parser = argparse.ArgumentParser(description="샘플 이력서 PDF 생성")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="출력 PDF 경로 (기본: app/data/resume/samples/sample_resume.pdf)",
    )
    args = parser.parse_args()
    out_path = args.output or get_output_path()
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # 한글 폰트: 기본 내장 폰트 또는 helv 사용 (한글은 시스템에 따라 깨질 수 있음 → 텍스트 위주)
    fontname = "helv"
    fontsize_title = 16
    fontsize_heading = 12
    fontsize_body = 10

    y = 50
    line_height = 22

    def add_text(text: str, size: float = fontsize_body, bold: bool = False) -> None:
        nonlocal y
        fs = size
        if bold:
            page.insert_text((72, y), text, fontname=fontname, fontsize=fs)
        else:
            page.insert_text((72, y), text, fontname=fontname, fontsize=fs)
        y += line_height

    # 샘플 내용 (영문 위주로 하면 폰트 이슈 없음; 한글은 환경에 따라 지원)
    add_text("RESUME / SAMPLE", fontsize_title, bold=True)
    y += 10
    add_text("Name: Hong Gildong")
    add_text("Position: Software Engineer")
    add_text("Email: sample@example.com | Phone: 010-0000-0000")
    y += 10
    add_text("Education", fontsize_heading, bold=True)
    add_text("  - OO University, Computer Science, B.S. (20XX.03 - 20XX.02)")
    y += 5
    add_text("Experience", fontsize_heading, bold=True)
    add_text("  - Company A, Developer (20XX - 20XX)")
    add_text("  - Company B, Intern (20XX - 20XX)")
    y += 5
    add_text("Skills", fontsize_heading, bold=True)
    add_text("  - Python, FastAPI, React, PostgreSQL")

    doc.save(str(out_path))
    doc.close()
    print(f"Created: {out_path}")


if __name__ == "__main__":
    main()
