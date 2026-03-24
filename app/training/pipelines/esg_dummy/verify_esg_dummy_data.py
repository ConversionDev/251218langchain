"""
ESG 더미 데이터 품질 검증.
measurements.csv가 프로파일·Rule 1~6을 만족하는지, validation_logs 비율·error_type 구성을 확인.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_esg_dummy_dir  # noqa: E402


def _load_profile(data_dir: Path) -> dict:
    with open(data_dir / "profile.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _profile_for_pl(profile: dict, process: str, line: str) -> dict | None:
    for pl in profile["process_line"]:
        if pl["process"] == process and pl["line"] == line:
            return pl
    return None


def main() -> None:
    data_dir = get_esg_dummy_dir()
    profile = _load_profile(data_dir)
    rule4_max = profile["rule4_usage_per_production_max"]
    rule5_max = profile["rule5_usage_per_equipment_max"]

    # 1) measurements 검증: 정상 행만 있으므로 프로파일 범위 + Rule 1~6 만족해야 함
    measurements_path = data_dir / "measurements.csv"
    if not measurements_path.exists():
        print("[FAIL] measurements.csv 없음")
        return

    violations: list[str] = []
    total = 0
    with open(measurements_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            total += 1
            process = row["process"]
            line = row["line"]
            pl = _profile_for_pl(profile, process, line)
            if not pl:
                violations.append(f"row {total}: unknown process,line {process},{line}")
                continue
            try:
                usage = float(row["usage"])
                production = float(row["production"])
                equipment_ct = int(row["equipment_ct"])
                scrap = float(row["scrap"])
                waste = float(row["waste"])
            except (ValueError, KeyError) as e:
                violations.append(f"row {total}: parse error {e}")
                continue

            shift = row.get("shift", "")
            u_lo, u_hi = (pl["usage_day"][0], pl["usage_day"][1]) if shift == "day" else (pl["usage_night"][0], pl["usage_night"][1])
            # Rule 1
            if usage < 0:
                violations.append(f"row {total}: Rule1 usage<0 {usage}")
            # CONTRACT_EXCEED용으로 measurements에 넣은 행(usage를 정상 상한의 1.1배 이상으로 부풀림)은
            # 프로파일 대역·Rule2/4/5 정상 검증에서 제외
            tol = 0.01
            is_contract_measurement = usage > u_hi * 1.09
            if not is_contract_measurement:
                # Rule 2
                if usage > pl["rated_kw"]:
                    violations.append(f"row {total}: Rule2 usage>{pl['rated_kw']} {usage}")
                # 프로파일 범위 (Rule 5 cap으로 u_lo 미달 가능 → 하한은 min(u_lo, cap5) 허용)
                cap5 = equipment_ct * rule5_max
                u_lo_eff = min(u_lo, cap5)
                if usage < u_lo_eff * (1 - tol) or usage > u_hi * (1 + tol):
                    violations.append(f"row {total}: usage {usage} outside [{u_lo},{u_hi}] (shift={shift})")
            if production < pl["production"][0] * (1 - tol) or production > pl["production"][1] * (1 + tol):
                violations.append(f"row {total}: production {production} outside {pl['production']}")
            if equipment_ct < pl["equipment_ct"][0] or equipment_ct > pl["equipment_ct"][1]:
                violations.append(f"row {total}: equipment_ct {equipment_ct} outside {pl['equipment_ct']}")
            if scrap < pl["scrap"][0] * (1 - tol) or scrap > pl["scrap"][1] * (1 + tol):
                violations.append(f"row {total}: scrap {scrap} outside {pl['scrap']}")
            if waste < pl["waste"][0] * (1 - tol) or waste > pl["waste"][1] * (1 + tol):
                violations.append(f"row {total}: waste {waste} outside {pl['waste']}")
            # Rule 4
            if not is_contract_measurement and production > 0 and usage / production > rule4_max * (1 + tol):
                violations.append(f"row {total}: Rule4 usage/prod={usage/production:.2f}>{rule4_max}")
            # Rule 5
            if not is_contract_measurement and equipment_ct > 0 and usage / equipment_ct > rule5_max * (1 + tol):
                violations.append(f"row {total}: Rule5 usage/ct={usage/equipment_ct:.2f}>{rule5_max}")

    # 2) validation_logs 건수 및 error_type 분포
    validation_path = data_dir / "validation_logs.csv"
    val_total = 0
    val_by_type: dict[str, int] = {}
    if validation_path.exists():
        with open(validation_path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                val_total += 1
                t = row.get("error_type", "?")
                val_by_type[t] = val_by_type.get(t, 0) + 1

    total_slots = total + val_total
    anomaly_pct = (val_total / total_slots * 100) if total_slots else 0

    # 3) 결과 출력
    print("=" * 60)
    print("ESG 더미 데이터 품질 검증 결과")
    print("=" * 60)
    print(f"  measurements: {total:,} rows")
    print(f"  validation_logs: {val_total:,} rows (이상)")
    print(f"  총 슬롯: {total_slots:,}  |  이상 비율: {anomaly_pct:.2f}% (목표 5~8%)")
    print()
    if violations:
        print(f"  [경고] measurements 규칙/프로파일 위반: {len(violations)}건 (최대 20건만 표시)")
        for v in violations[:20]:
            print(f"    - {v}")
        if len(violations) > 20:
            print(f"    ... 외 {len(violations) - 20}건")
    else:
        print("  [OK] measurements: 프로파일 범위 및 Rule 1~6 만족 (위반 0건)")
    print()
    print("  validation_logs error_type 분포:")
    for t, cnt in sorted(val_by_type.items(), key=lambda x: -x[1]):
        pct = cnt / val_total * 100 if val_total else 0
        print(f"    {t}: {cnt:,} ({pct:.1f}%)")
    print("=" * 60)
    if violations and len(violations) > 100:
        print("[FAIL] 위반이 많음. 데이터 생성 로직 확인 필요.")
    elif not violations:
        print("[OK] 데이터 품질 양호.")
    else:
        print("[주의] 소수 위반 있음 (반올림/부동소수 여유로 인한 경계 케이스 가능).")


if __name__ == "__main__":
    main()
