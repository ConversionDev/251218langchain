"""
ETL Extract: CSV to Raw JSONL

한국우편사업진흥원 스팸메일 차단 목록 CSV를 Raw JSONL 형식으로 변환.

역할: Extract (추출)
- CSV 파일 읽기
- BOM 제거, 인코딩 처리
- 기본 정제 (빈 행 제거)
- 원본 구조를 유지한 Raw JSONL 생성
"""

import csv
import json
from pathlib import Path
from typing import Dict, Optional


def normalize_row(row: Dict[str, str]) -> Optional[Dict[str, str]]:
    """CSV 행을 정규화 (BOM 제거, 기본 정제)."""
    normalized_row = {}
    for key, value in row.items():
        clean_key = key.lstrip("\ufeff").strip()
        normalized_row[clean_key] = value.strip() if value else ""

    date = normalized_row.get("수신일자", "").strip()
    subject = normalized_row.get("제목", "").strip()
    if not date or not subject:
        return None
    return normalized_row


def convert_csv_to_jsonl(
    csv_path: str, output_path: str, encoding: str = "utf-8"
) -> int:
    """CSV 파일을 Raw JSONL 형식으로 변환."""
    count = 0
    skipped = 0
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(csv_path, "r", encoding=encoding, errors="replace") as csv_f:
            reader = csv.DictReader(csv_f)
            with open(output_path, "w", encoding="utf-8") as jsonl_f:
                for row in reader:
                    normalized_row = normalize_row(row)
                    if normalized_row is None:
                        skipped += 1
                        continue
                    jsonl_f.write(json.dumps(normalized_row, ensure_ascii=False) + "\n")
                    count += 1
                    if count % 10000 == 0:
                        print(f"[진행] {count}개 샘플 변환 완료...")
    except UnicodeDecodeError:
        if encoding == "utf-8":
            print("[INFO] UTF-8 인코딩 실패, cp949로 재시도...")
            return convert_csv_to_jsonl(csv_path, output_path, encoding="cp949")
        raise

    if skipped > 0:
        print(f"[INFO] {skipped}개 행 스킵됨 (빈 데이터)")
    return count


def main():
    """메인 실행 함수."""
    app_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = app_dir / "data"
    csv_filename = "한국우편사업진흥원_스팸메일 수신차단 목록_20241231.csv"
    csv_path = data_dir / csv_filename
    jsonl_filename = csv_filename.replace(".csv", "_raw.jsonl")
    jsonl_path = data_dir / jsonl_filename

    if not csv_path.exists():
        print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_path}")
        return

    print(f"[INFO] CSV 파일: {csv_path}")
    print(f"[INFO] 출력 파일: {jsonl_path}")
    count = convert_csv_to_jsonl(str(csv_path), str(jsonl_path))
    print("[OK] 변환 완료!")
    print(f"[INFO] 총 {count}개 샘플이 {jsonl_path}에 저장되었습니다.")


if __name__ == "__main__":
    main()
