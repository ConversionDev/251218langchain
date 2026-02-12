"""
O*NET xlsx 적재 전 검증: 파일 존재, 추출 행 수, 필수 키, content/level/embedding_content, unique_id 중복, DB 테이블.

실행: app 디렉터리에서 python -m data.competency_anchors.xlsx_verify
"""
import sys
from pathlib import Path
from typing import Any

# app이 PYTHONPATH에 있도록
SCRIPT_DIR = Path(__file__).resolve().parent
APP_ROOT = SCRIPT_DIR.parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

REQUIRED_KEYS = ("content", "category", "level", "section_title", "source", "source_type", "metadata")
LEVEL_RANGE = (1, 8)


def _check_files() -> list[Path]:
    """*.xlsx 존재 확인 후 목록 반환."""
    xlsx = sorted(SCRIPT_DIR.glob("*.xlsx"))
    if not xlsx:
        print("[verify] 경고: *.xlsx 파일이 없습니다.")
    return xlsx


def _check_extract(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """한 파일 추출 후 필수 키·content·level·embedding_content·unique_id 검증. (rows, errors) 반환."""
    from domain.shared.strategies import ExcelStrategyFactory  # type: ignore

    strategy = ExcelStrategyFactory.get_strategy(SCRIPT_DIR)
    rows = strategy.extract(path)
    errors: list[str] = []

    for i, r in enumerate(rows):
        for key in REQUIRED_KEYS:
            if key not in r:
                errors.append(f"{path.name} 행{i}: 필수 키 누락 '{key}'")
        content = (r.get("content") or "").strip()
        if not content:
            errors.append(f"{path.name} 행{i}: content 비어 있음")
        level = r.get("level")
        if level is not None:
            try:
                lv = int(level)
                if lv < LEVEL_RANGE[0] or lv > LEVEL_RANGE[1]:
                    errors.append(f"{path.name} 행{i}: level {lv}는 1~8 범위 아님")
            except (TypeError, ValueError):
                errors.append(f"{path.name} 행{i}: level 정수 아님")

    # embedding_content·unique_id는 ingest에서 부여하므로 여기서는 행 구조만 검증
    return rows, errors


def _check_unique_ids(rows: list[dict[str, Any]], source_stem: str) -> list[str]:
    """unique_id 시뮬레이션 후 중복 검사."""
    from .xlsx_ingest import _make_unique_id, _prepare_rows  # type: ignore

    prepared = _prepare_rows(rows, source_stem)
    ids = [r.get("unique_id") for r in prepared if r.get("unique_id")]
    seen: set[str] = set()
    errors: list[str] = []
    for uid in ids:
        if uid in seen:
            errors.append(f"unique_id 중복: {uid[:80]}...")
        seen.add(uid)
    return errors


def _check_db_table() -> bool:
    """competency_anchors 테이블 존재 여부."""
    from sqlalchemy import text as sql_text  # type: ignore
    from core.database import SessionLocal  # type: ignore

    try:
        db = SessionLocal()
        try:
            r = db.execute(sql_text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'competency_anchors'"
            ))
            return r.scalar() is not None
        finally:
            db.close()
    except Exception:
        return False


def run_verify() -> bool:
    """모든 검증 수행. 성공 시 True."""
    all_errors: list[str] = []
    xlsx_files = _check_files()
    if not xlsx_files:
        print("[verify] *.xlsx 없음 → 검증 중단.")
        return False

    total_rows = 0
    for path in xlsx_files:
        rows, errs = _check_extract(path)
        all_errors.extend(errs)
        total_rows += len(rows)
        if rows:
            id_errs = _check_unique_ids(rows, path.stem)
            all_errors.extend(id_errs)
        print(f"[verify] {path.name}: {len(rows)}행")

    if not _check_db_table():
        all_errors.append("DB에 competency_anchors 테이블이 없습니다. alembic upgrade head 실행 후 재시도.")

    if all_errors:
        print("[verify] 실패:")
        for e in all_errors[:50]:
            print(f"  - {e}")
        if len(all_errors) > 50:
            print(f"  ... 외 {len(all_errors) - 50}건")
        return False

    print(f"[verify] 통과: 총 {total_rows}행, 필수 키·content·level·unique_id·DB 테이블 OK.")
    return True


def main() -> None:
    try:
        ok = run_verify()
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
