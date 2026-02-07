"""PDF vs _alter.txt 대조 + 청킹 무결성 검증.

1) 추출 검증: 모든 PDF에 대해 대응 {stem}_alter.txt와 페이지 수·페이지별 텍스트 일치 여부.
2) 청킹 무결성: 각 _alter.txt를 ingest와 동일한 청킹으로 자른 뒤, 청크를 이어붙인 문자열이 원문과 일치하는지.
실행: app 디렉터리에서 python -m data.disclosure.pdf_verify
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
PAGE_SEP = "\n--- Page Break ---\n"

# ingest.py와 동일한 stem → standard_type 매핑 (청킹 무결성 검증 시 사용)
STANDARD_TYPE_MAP = {
    "2018-ISO-30414": "ISO30414",
    "2023-ifrs-s1-disclosure": "IFRS_S1",
    "2025-ifrs-s2-climate-disclosures": "IFRS_S2",
    "2025-oecd": "OECD",
    "2025-global-green-stocktake-": "GLOBAL_GREEN_STOCKTAKE",
}


def normalize(s: str) -> str:
    """비교용: 공백/줄바꿈 정규화."""
    return re.sub(r"\s+", " ", s).strip()


def verify_chunking_integrity(
    txt_path: Path, source: str, standard_type: str
) -> Tuple[int, int, int]:
    """
    _alter.txt를 ingest와 동일한 청킹으로 자른 뒤, 청크를 원래 구분자(\\n\\n, PAGE_SEP)로 이어붙여 원문과 일치하는지 검사.
    불일치 시 ValueError. 성공 시 (청크 수, 원문 글자 수, 재조합 글자 수) 반환.
    """
    from data.disclosure.pdf_ingest import load_txt_and_chunk  # type: ignore

    raw = txt_path.read_text(encoding="utf-8")
    docs = load_txt_and_chunk(txt_path, source=source, standard_type=standard_type)
    if not docs:
        if raw.strip():
            raise ValueError("청킹 무결성 실패: 원문은 있는데 청크가 0개입니다.")
        return (0, len(raw), 0)
    parts = [docs[0].page_content]
    for i in range(1, len(docs)):
        curr_page = docs[i - 1].metadata.get("page")
        next_page = docs[i].metadata.get("page")
        if next_page != curr_page:
            parts.append(PAGE_SEP)
        else:
            parts.append("\n\n")
        parts.append(docs[i].page_content)
    reassembled = "".join(parts)
    if normalize(raw) != normalize(reassembled):
        raise ValueError(
            "청킹 무결성 실패: 청크를 이어붙인 결과가 원문과 다릅니다. "
            f"(원문 {len(normalize(raw))}자, 재조합 {len(normalize(reassembled))}자)"
        )
    return (len(docs), len(raw), len(reassembled))


def verify_one(pdf_path: Path, txt_path: Path) -> Tuple[List[int], int]:
    """
    PDF 한 파일과 대응 TXT를 비교. (불일치한 페이지 번호 1-based 리스트, PDF 페이지 수) 반환.
    빈 리스트면 모두 일치.
    """
    import fitz  # type: ignore

    doc = fitz.open(pdf_path)
    pdf_page_count = len(doc)

    raw = txt_path.read_text(encoding="utf-8")
    blocks = raw.split(PAGE_SEP)
    txt_page_count = len(blocks)

    if pdf_page_count != txt_page_count:
        doc.close()
        raise ValueError(f"페이지 수 불일치: PDF={pdf_page_count}, TXT={txt_page_count}")

    mismatches = []
    for i in range(pdf_page_count):
        pdf_text = doc[i].get_text()
        txt_block = (blocks[i] if i < len(blocks) else "").strip()
        if normalize(pdf_text) != normalize(txt_block):
            mismatches.append(i + 1)
    doc.close()
    return (mismatches, pdf_page_count)


def main() -> None:
    pdfs = sorted(SCRIPT_DIR.glob("*.pdf"))
    if not pdfs:
        print("처리할 PDF가 없습니다.")
        sys.exit(0)

    failed: List[Tuple[Path, str]] = []
    ok_count = 0

    for pdf_path in pdfs:
        stem = pdf_path.stem
        txt_path = SCRIPT_DIR / f"{stem}_alter.txt"
        if not txt_path.exists():
            print(f"[SKIP] {pdf_path.name} — 대응 TXT 없음: {txt_path.name}")
            continue

        try:
            mismatches, page_count = verify_one(pdf_path, txt_path)
            if mismatches:
                failed.append((pdf_path, f"페이지 불일치: {mismatches}"))
                print(f"[FAIL] {pdf_path.name} — 페이지별 텍스트 불일치: {mismatches}")
                continue
            # 추출 검증 통과 → 청킹 무결성 검증 (청크 이어붙인 결과 == 원문)
            source = stem.replace("_alter", "")
            standard_type = STANDARD_TYPE_MAP.get(source, source.replace("-", "_").upper()[:50])
            try:
                num_chunks, raw_len, reassembled_len = verify_chunking_integrity(
                    txt_path, source=source, standard_type=standard_type
                )
            except ValueError as e:
                failed.append((pdf_path, str(e)))
                print(f"[FAIL] {pdf_path.name} — 청킹 무결성: {e}")
                continue
            ok_count += 1
            print(
                f"[OK]   {pdf_path.name} ↔ {txt_path.name} (추출+청킹 무결성) — "
                f"원문 {page_count}페이지, {raw_len:,}자 → 청킹 {num_chunks:,}개, 재조합 {reassembled_len:,}자"
            )
        except Exception as e:
            failed.append((pdf_path, str(e)))
            print(f"[FAIL] {pdf_path.name} — {e}")

    print("=" * 60)
    if failed:
        print(f"결론: {len(failed)}개 실패, {ok_count}개 성공. 추출/청킹 확인 후 다시 검증하세요.")
        sys.exit(1)
    print(f"결론: {ok_count}개 모두 추출·청킹 무결성 통과. 적재 진행해도 됩니다.")
    sys.exit(0)


if __name__ == "__main__":
    main()
