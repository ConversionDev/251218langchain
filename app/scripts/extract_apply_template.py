"""
app/data 내 KPMG 입사지원서 Template.docx 텍스트 추출.
실행: 프로젝트 루트에서  python -m app.scripts.extract_apply_template
"""
from pathlib import Path

def main():
    app_root = Path(__file__).resolve().parent.parent
    data_dir = app_root / "data"
    docx_files = list(data_dir.glob("*.docx"))
    if not docx_files:
        print("app/data/ 에 .docx 파일이 없습니다. KPMG_입사지원서_Template.docx 를 넣은 뒤 다시 실행하세요.")
        return
    from app.domain.shared.document_extract import extract_text_from_document
    for path in docx_files:
        print(f"--- {path.name} ---")
        print(extract_text_from_document(path=path))
        print()

if __name__ == "__main__":
    main()
