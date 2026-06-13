"""
Disclosure 파이프라인: raw PDF → prepared txt → 검증 → 적재.

한 번 실행 시:
  1. raw/*.pdf → prepared/*.txt (텍스트 추출)
  2. 검증: PDF 페이지 수와 txt segment 수 일치 여부
  3. 검증 실패 시 종료, 통과 시 prepared/*.txt → disclosures 테이블 적재

사용:
  cd app && python -m training.pipelines.ingest.run_disclosure_ingest
"""

import sys
from pathlib import Path

# app 루트를 경로에 추가
app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from infrastructure.orchestration.disclosure_orchestrator import (
    build_documents_config_from_prepared_dir,
    run_disclosure_ingest_orchestrate,
)
from domain.shared.embedding import get_embedding_model  # type: ignore
from training.shared.disclosure_extract import (  # type: ignore
    extract_raw_to_prepared,
    get_disclosure_prepared_dir as get_prepared_dir,
    get_disclosure_raw_dir,
)
from training.shared.disclosure_verify import verify_pdf_text_match  # type: ignore


def main() -> None:
    raw_dir = get_disclosure_raw_dir()
    prepared_dir = get_prepared_dir()

    # 1. raw에 PDF가 있으면 → prepared로 추출
    if raw_dir.exists():
        pdfs = list(raw_dir.glob("*.pdf"))
        if pdfs:
            print(f"[INFO] raw PDF {len(pdfs)}개 → prepared txt 변환 중...")
            try:
                extracted = extract_raw_to_prepared(raw_dir, prepared_dir)
                print(f"[INFO] 추출 완료: {len(extracted)}개")
            except RuntimeError as e:
                print(f"[ERROR] {e}")
                sys.exit(1)

    # 2. 검증: PDF와 txt 일치 (페이지 수)
    ok, err = verify_pdf_text_match(raw_dir, prepared_dir)
    if not ok:
        print(f"[ERROR] 검증 실패: {err}")
        sys.exit(1)
    print("[INFO] 검증 통과 (PDF·txt 일치)")

    # 3. prepared에서 적재
    if not prepared_dir.exists():
        print(f"[ERROR] prepared 디렉터리가 없습니다: {prepared_dir}")
        sys.exit(1)

    documents_config = build_documents_config_from_prepared_dir()
    if not documents_config:
        print(f"[WARNING] .txt 파일이 없습니다: {prepared_dir}")
        sys.exit(1)

    print(f"[INFO] 적재 입력: {prepared_dir}, 파일 수: {len(documents_config)}")
    embeddings_model = get_embedding_model(use_fp16=True)
    result = run_disclosure_ingest_orchestrate(
        embeddings_model,
        documents_config=documents_config,
    )
    if result.get("success"):
        print(f"[OK] 적재 완료: {result.get('doc_count', 0)}건")
    else:
        print(f"[ERROR] 적재 실패: {result.get('error', '')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
