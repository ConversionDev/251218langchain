"""
신입 샘플 JSONL에서 이름·이메일 중복을 정리합니다.

- 이메일: 중복 시 각 행을 고유하게 만듦 (id 기반: e001@sample.local).
  DB unique 제약이나 "이미 등록된 직원" 방지용.
- 이름: 분석만 출력. 동일 이름 다수는 그대로 두고, 필요 시 수동으로
  이름 풀을 넓히려면 생성기(resume_sample_generator) 프롬프트/후처리를 조정하면 됩니다.

실행 (프로젝트 루트에서, app이 cwd일 수 있음):
  python -m training.pipelines.resume_samples.deduplicate_new_hire_samples --file app/data/resume/samples/new_hire_samples_20260219_0256.jsonl
  python -m training.pipelines.resume_samples.deduplicate_new_hire_samples --file app/data/resume/samples/new_hire_samples_20260219_0256.jsonl --in-place   # 원본 덮어쓰기
  # 출력 파일 미지정 시: <원본경로>_dedup.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))


def _normalize_id_to_local_part(eid: str) -> str:
    """E001 -> e001, E023 -> e023."""
    if not eid:
        return "id"
    return eid.strip().lower().replace(" ", "")


def analyze(rows: list[dict]) -> dict:
    """이름·이메일 중복 집계."""
    names = [r.get("name") or "" for r in rows]
    emails = [r.get("email") or "" for r in rows]
    name_counts = Counter(names)
    email_counts = Counter(emails)
    dup_names = {n: c for n, c in name_counts.items() if c > 1}
    dup_emails = {e: c for e, c in email_counts.items() if c > 1}
    return {
        "total": len(rows),
        "unique_names": len(name_counts),
        "unique_emails": len(email_counts),
        "name_duplicates": dup_names,
        "email_duplicates": dup_emails,
        "duplicate_name_count": len(dup_names),
        "duplicate_email_count": len(dup_emails),
    }


def _build_unique_name_pool(n: int) -> list[str]:
    """성+이름을 골고루 섞어 n개 이름 생성. 일부 겹쳐도 됨."""
    surnames = [
        "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
        "한", "오", "서", "신", "권", "황", "안", "송", "류", "전",
        "홍", "문", "양", "손", "배", "백", "허", "유", "남", "심",
    ]
    given = [
        "민준", "서준", "예준", "도윤", "시우", "주원", "하준", "지호", "지후", "준서",
        "준우", "도현", "건우", "현우", "민재", "시현", "선우", "유준", "연우", "정우",
        "승우", "승현", "지우", "지훈", "수현", "서연", "서윤", "서현", "민서", "하은",
        "하윤", "윤서", "지유", "유나", "지민", "수아", "소율", "채원", "지아", "수빈",
        "예은", "지안", "소윤", "유진", "시은", "가은", "다은", "예나", "수민", "서영",
        "지원", "하린", "소민", "예린", "나연", "지현", "민호", "성민", "태윤", "재민",
        "동현", "성준", "시윤", "우진", "재윤", "태민", "준혁", "현서", "도훈", "성우",
        "시원", "민기", "태현", "준영", "지한", "소현", "예진", "수진", "지수", "서아",
        "다인", "하율", "민지", "서하", "예서", "수영", "유림", "세현", "동욱", "재현",
        "민성", "준호", "상우", "영호", "정민", "혜진", "미영", "지웅", "현지", "보라",
    ]
    # 성과 이름 조합을 모두 만들고 섞어서 다양하게
    pairs = [(s, g) for s in surnames for g in given]
    random.shuffle(pairs)
    out = []
    for i in range(n):
        if i < len(pairs):
            s, g = pairs[i]
            out.append(s + g)
        else:
            # n이 조합 수보다 크면 순환 (일부 겹침 허용)
            s, g = pairs[i % len(pairs)]
            out.append(s + g)
    return out


def deduplicate_emails(rows: list[dict]) -> list[dict]:
    """각 행에 고유 이메일 부여. 기존 이메일이 이미 나온 경우 id 기반으로 교체."""
    seen: set[str] = set()
    out = []
    for r in rows:
        row = dict(r)
        email = (row.get("email") or "").strip()
        eid = row.get("id") or ""
        local = _normalize_id_to_local_part(eid)
        unique_email = f"{local}@sample.local"
        if email and email not in seen:
            seen.add(email)
            row["email"] = email
        else:
            while unique_email in seen:
                base = local
                n = 0
                while unique_email in seen:
                    n += 1
                    unique_email = f"{base}{n}@sample.local"
            seen.add(unique_email)
            row["email"] = unique_email
        out.append(row)
    return out


def deduplicate_names_and_emails(rows: list[dict]) -> list[dict]:
    """각 행에 고유 이름·고유 이메일 부여. id 기반 이메일(e001@sample.local)."""
    name_pool = _build_unique_name_pool(len(rows))
    seen_emails: set[str] = set()
    out = []
    for i, r in enumerate(rows):
        row = dict(r)
        row["name"] = name_pool[i]
        eid = row.get("id") or ""
        local = _normalize_id_to_local_part(eid) or f"e{i+1:03d}"
        unique_email = f"{local}@sample.local"
        while unique_email in seen_emails:
            local = f"e{i+1:03d}_{len(seen_emails)}"
            unique_email = f"{local}@sample.local"
        seen_emails.add(unique_email)
        row["email"] = unique_email
        out.append(row)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="신입 샘플 JSONL 이름·이메일 중복 정리")
    parser.add_argument("--file", type=Path, required=True, help="입력 JSONL 경로")
    parser.add_argument("-o", "--output", type=Path, default=None, help="출력 JSONL 경로 (기본: <파일>_dedup.jsonl)")
    parser.add_argument("--in-place", action="store_true", help="출력을 원본 파일로 덮어쓰기 (원본 백업 없음)")
    parser.add_argument("--fix-names", action="store_true", help="이름도 고유하게 교체 (이름 풀에서 순서대로 부여)")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 분석만 출력")
    args = parser.parse_args()

    path = args.file
    if not path.is_absolute():
        path = (app_dir / path).resolve() if (app_dir / path).exists() else path.resolve()
    if not path.exists():
        print(f"파일 없음: {path}", file=sys.stderr)
        sys.exit(1)

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"JSON 오류: {e}", file=sys.stderr)

    if not rows:
        print("유효한 행이 없습니다.", file=sys.stderr)
        sys.exit(1)

    stats = analyze(rows)
    print("=== 중복 분석 ===")
    print(f"총 행 수: {stats['total']}")
    print(f"고유 이름 수: {stats['unique_names']} (중복된 이름 종류: {stats['duplicate_name_count']})")
    print(f"고유 이메일 수: {stats['unique_emails']} (중복된 이메일 종류: {stats['duplicate_email_count']})")
    if stats["email_duplicates"]:
        print("\n이메일 중복 (상위 10개):")
        for e, c in sorted(stats["email_duplicates"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {e}: {c}건")
    if stats["name_duplicates"]:
        print("\n이름 중복 (상위 10개):")
        for n, c in sorted(stats["name_duplicates"].items(), key=lambda x: -x[1])[:10]:
            print(f"  {n}: {c}건")

    if args.dry_run:
        print("\n[--dry-run] 저장하지 않음.")
        return

    fixed = deduplicate_names_and_emails(rows) if args.fix_names else deduplicate_emails(rows)
    if args.in_place:
        out_path = path
    else:
        out_path = args.output or path.with_name(path.stem + "_dedup.jsonl")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in fixed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    after = analyze(fixed)
    print(f"\n저장: {out_path} (행 수: {len(fixed)})")
    print(f"이메일: 이제 모두 고유 (고유 이메일 수: {after['unique_emails']})")


if __name__ == "__main__":
    main()
