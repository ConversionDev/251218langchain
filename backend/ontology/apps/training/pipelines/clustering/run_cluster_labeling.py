"""
클러스터 주제 라벨링 (4번 단계).

파이프라인: 군집화 = FAISS + K-Means (run_competency_clustering), 라벨링 = EXAONE(로컬).
cluster_representatives.jsonl을 읽어 각 클러스터에 주제명을 붙입니다.
- LLM: 로컬 EXAONE으로 대표 샘플 → 한글 직무/역량명 한 줄 (API 한도 없음)
- 수동: CSV 내보내기 → 편집 → CSV 가져오기

출력: artifacts/clustering/cluster_labels.json
  { "0": "의사소통", "1": "IT 스킬", ... }

사용:
  cd app && python -m training.pipelines.clustering.run_cluster_labeling --method llm   # 200개 한 번에
  cd app && python -m training.pipelines.clustering.run_cluster_labeling --method fill   # 임시 라벨(군집N)만 보완
  cd app && python -m training.pipelines.clustering.run_cluster_labeling --method export
  cd app && python -m training.pipelines.clustering.run_cluster_labeling --method import --import-csv out/labels.csv
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_clustering_dir  # type: ignore  # noqa: E402


def _label_prompt(samples_text: str) -> str:
    """라벨링용 프롬프트."""
    return f"""아래는 한 클러스터(군집)에 속한 대표 문장들입니다. 이 클러스터가 어떤 직무·역량을 나타내는지 구체적인 한글 이름(2~15자)을 한 개만 제시해 주세요.
예: 의료 소프트웨어 관리, 기계 설비 유지보수, SQL 데이터베이스, 대인관계 소통, 문제해결 분석
다른 설명 없이 직무/역량명만 한 줄로 출력해 주세요.

대표 문장:
{samples_text}
"""


def _parse_label_response(raw: str) -> str:
    """LLM 응답에서 직무/역량명 한 줄만 추출."""
    if not raw or not raw.strip():
        return ""
    line = raw.strip().split("\n")[0].strip()
    line = re.sub(r"^[\d\.\-\*\)\]]+\s*", "", line)
    return line[:30] if len(line) > 30 else line


def _label_for_cluster(samples_text: str) -> str:
    """로컬 EXAONE으로 주제명 한 줄 받기."""
    try:
        from infrastructure.llm import generate_text  # type: ignore  # noqa: E402

        raw = generate_text(
            _label_prompt(samples_text),
            max_tokens=64,
            temperature=0.3,
        )
        return _parse_label_response(raw)
    except Exception as e:
        print(f"  [WARN] EXAONE 호출 실패: {e}")
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="클러스터 주제 라벨링 (LLM or 수동)")
    parser.add_argument(
        "--method",
        choices=["llm", "fill", "export", "import"],
        default="llm",
        help="llm=전체 라벨링, fill=임시 라벨(군집N)만 보완, export=수동용 CSV 내보내기, import=CSV 가져오기",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="cluster_representatives.jsonl",
        help="대표 샘플 JSONL 파일명 (기본 cluster_representatives.jsonl)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="cluster_labels.json",
        help="라벨 저장 JSON 파일명 (기본 cluster_labels.json)",
    )
    parser.add_argument(
        "--import-csv",
        type=str,
        default="",
        help="method=import 일 때 불러올 CSV 경로 (cluster_id,label 컬럼)",
    )
    parser.add_argument(
        "--export-csv",
        type=str,
        default="cluster_labels_edit.csv",
        help="method=export 일 때 저장할 CSV 경로",
    )
    parser.add_argument(
        "--max-clusters",
        type=int,
        default=0,
        help="라벨링할 최대 클러스터 수 (0=전체)",
    )
    parser.add_argument(
        "--max-fill",
        type=int,
        default=0,
        help="fill 모드에서 한 번에 보완할 최대 개수 (0=전체)",
    )
    args = parser.parse_args()

    out_dir = get_clustering_dir()
    reps_path = out_dir / args.input
    labels_path = out_dir / args.output

    if not reps_path.exists():
        print(f"[ERROR] 파일 없음: {reps_path}")
        print("  먼저 inspect_clustering.py (대표 샘플 추출)을 실행하세요.")
        sys.exit(1)

    # 대표 샘플 로드
    clusters = []
    with reps_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            clusters.append(json.loads(line))

    n_total = len(clusters)
    if args.max_clusters > 0:
        clusters = clusters[: args.max_clusters]
    print(f"[INFO] 클러스터 수: {n_total} (라벨링 대상: {len(clusters)})")
    if args.method in ("llm", "fill"):
        print("[INFO] 라벨링: EXAONE(로컬)")

    if args.method == "export":
        # 수동 편집용 CSV 내보내기
        export_path = Path(args.export_csv)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with export_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["cluster_id", "sample_preview", "label"])
            for row in clusters:
                cid = row.get("cluster_id", 0)
                samples = row.get("representative_samples", [])
                preview = " | ".join(
                    (s.get("content", "")[:80] + "…" if len(s.get("content", "")) > 80 else s.get("content", ""))
                    for s in samples[:3]
                )
                w.writerow([cid, preview, ""])
        print(f"[OK] 수동 편집용 CSV 저장: {export_path}")
        print("  label 컬럼을 채운 뒤 --method import --import-csv <파일> 로 저장하세요.")
        return

    if args.method == "import":
        # 편집한 CSV에서 라벨 읽기
        if not args.import_csv or not Path(args.import_csv).exists():
            print("[ERROR] --import-csv 경로를 지정하고 해당 파일이 존재해야 합니다.")
            sys.exit(1)
        labels_dict = {}
        with open(args.import_csv, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                cid = row.get("cluster_id", "").strip()
                label = row.get("label", "").strip()
                if cid != "" and label != "":
                    labels_dict[str(cid)] = label
        with labels_path.open("w", encoding="utf-8") as f:
            json.dump(labels_dict, f, ensure_ascii=False, indent=2)
        print(f"[OK] cluster_labels.json 저장: {labels_path} (총 {len(labels_dict)}개)")
        return

    def _is_placeholder(label: str) -> bool:
        if not label or not label.strip():
            return True
        return bool(re.match(r"^군집\d+$", label.strip()))

    cid_to_row = {row.get("cluster_id", i): row for i, row in enumerate(clusters)}

    if args.method == "fill":
        # 기존 cluster_labels.json에서 '군집0', '군집6' 등 임시 라벨만 EXAONE으로 보완
        if labels_path.exists():
            with labels_path.open("r", encoding="utf-8") as f:
                labels_dict = json.load(f)
        else:
            labels_dict = {}
        to_fill = [
            cid for cid in cid_to_row
            if str(cid) not in labels_dict or _is_placeholder(labels_dict.get(str(cid), ""))
        ]
        if args.max_fill > 0:
            to_fill = to_fill[: args.max_fill]
            print(f"[INFO] 기존 라벨 유지, placeholder 중 상위 {len(to_fill)}개만 이번에 보완 (--max-fill)")
        else:
            print(f"[INFO] 기존 라벨 유지, placeholder {len(to_fill)}개만 EXAONE으로 보완")
        for idx, cid in enumerate(sorted(to_fill)):
            row = cid_to_row[cid]
            samples = row.get("representative_samples", [])
            texts = [s.get("content", "").strip() for s in samples if s.get("content")]
            samples_text = "\n".join(f"- {t[:400]}" for t in texts[:10])
            if not samples_text:
                labels_dict[str(cid)] = f"군집{cid}"
                continue
            label = _label_for_cluster(samples_text)
            labels_dict[str(cid)] = label if label else f"군집{cid}"
            print(f"  [{idx+1}/{len(to_fill)}] cluster_id={cid} → {labels_dict[str(cid)]}")
        with labels_path.open("w", encoding="utf-8") as f:
            json.dump(labels_dict, f, ensure_ascii=False, indent=2)
        print(f"[OK] cluster_labels.json 저장: {labels_path} (총 {len(labels_dict)}개)")
        return

    # method == llm: 클러스터당 주제명 생성 (전체, EXAONE)
    labels_dict = {}
    for i, row in enumerate(clusters):
        cid = row.get("cluster_id", i)
        samples = row.get("representative_samples", [])
        texts = [s.get("content", "").strip() for s in samples if s.get("content")]
        samples_text = "\n".join(f"- {t[:400]}" for t in texts[:10])
        if not samples_text:
            labels_dict[str(cid)] = f"군집{cid}"
            continue
        label = _label_for_cluster(samples_text)
        labels_dict[str(cid)] = label if label else f"군집{cid}"
        print(f"  [{i+1}/{len(clusters)}] cluster_id={cid} → {labels_dict[str(cid)]}")

    with labels_path.open("w", encoding="utf-8") as f:
        json.dump(labels_dict, f, ensure_ascii=False, indent=2)
    print(f"[OK] cluster_labels.json 저장: {labels_path}")


if __name__ == "__main__":
    main()
