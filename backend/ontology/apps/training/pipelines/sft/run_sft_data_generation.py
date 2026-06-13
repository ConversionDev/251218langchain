"""
지식의 구조화: 군집 대표 문장 → SFT용 QA 세트 생성.

cluster_representatives.jsonl + cluster_labels.json을 읽어,
EXAONE에게 "직무 전문가로서 이 역량을 바탕으로 질문 1개 + 모범 답변 1개" 생성 요청 후
instruction/input/output 형식 JSONL로 저장.

저장: app/data/competency_anchors/sft/competency_qa.jsonl

사용:
  cd app && python -m training.pipelines.sft.run_sft_data_generation
  cd app && python -m training.pipelines.sft.run_sft_data_generation --max-clusters 50 --output my_qa.jsonl
"""

import argparse
import json
import re
import sys
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_clustering_dir  # type: ignore  # noqa: E402
from training.shared.competency_extract import get_competency_sft_dir  # type: ignore  # noqa: E402


# 군집당 여러 QA를 위해 질문 유형별 프롬프트 보조 문구
_QA_VARIANTS = [
    "면접에서 나올 법한 질문 1개와 모범 답변 1개",
    "실무 상황에서 상사가 물어볼 법한 질문 1개와 답변 1개",
    "이 역량을 보강하려는 지원자가 받을 법한 조언 질문 1개와 전문가 답변 1개",
]


def _qa_prompt(label: str, samples_text: str, variant: str) -> str:
    """역량 대표 문장 + 라벨을 주고 질문·답변 1쌍 생성 요청."""
    return f"""당신은 직무·역량 전문가입니다. 아래는 한 역량 군집의 대표 문장들과 그 군집의 이름입니다.
이 내용을 바탕으로, {variant}를 만들어 주세요.
답변은 "군집의 데이터에 따르면 ... 따라서 ..."처럼 근거를 담은 2~4문장으로 작성해 주세요.

형식 (아래 두 줄만 출력):
질문: (한 문장 질문)
답변: (2~4문장 답변)

군집 이름: {label}

대표 문장:
{samples_text}
"""


def _parse_qa_response(raw: str) -> tuple[str, str]:
    """응답에서 질문과 답변 추출. (instruction, output) 반환."""
    if not raw or not raw.strip():
        return "", ""
    text = raw.strip()
    q = ""
    a = ""
    # 질문: ... 답변: ... 또는 Q: ... A: ...
    for pattern in [
        (r"질문\s*:\s*(.+?)(?=답변\s*:|\Z)", r"답변\s*:\s*(.+)"),
        (r"Q\s*\.?\s*:\s*(.+?)(?=A\s*\.?\s*:|\Z)", r"A\s*\.?\s*:\s*(.+)"),
    ]:
        qm = re.search(pattern[0], text, re.DOTALL | re.IGNORECASE)
        am = re.search(pattern[1], text, re.DOTALL | re.IGNORECASE)
        if qm and am:
            q = qm.group(1).strip()
            a = am.group(1).strip()
            break
    if not q and "\n" in text:
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if len(lines) >= 2:
            q, a = lines[0], " ".join(lines[1:])
        elif len(lines) == 1:
            q = lines[0]
    q = q[:500] if len(q) > 500 else q
    a = a[:1500] if len(a) > 1500 else a
    return q, a


def _generate_qa_for_cluster(label: str, samples_text: str, variant: str) -> tuple[str, str]:
    """EXAONE으로 QA 1쌍 생성."""
    try:
        from infrastructure.llm import generate_text  # type: ignore  # noqa: E402

        raw = generate_text(
            _qa_prompt(label, samples_text, variant),
            max_tokens=512,
            temperature=0.5,
        )
        return _parse_qa_response(raw)
    except Exception as e:
        print(f"  [WARN] EXAONE 호출 실패: {e}")
    return "", ""


def main() -> None:
    parser = argparse.ArgumentParser(description="군집 기반 SFT용 QA 세트 생성 (지식의 구조화)")
    parser.add_argument(
        "--max-clusters",
        type=int,
        default=0,
        help="생성할 최대 군집 수 (0=전체)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="competency_qa.jsonl",
        help="출력 JSONL 파일명 (기본 competency_qa.jsonl)",
    )
    parser.add_argument(
        "--qa-per-cluster",
        type=int,
        default=3,
        help="군집당 생성할 QA 쌍 수 (1~5 권장, 기본 3 → 총 약 600건)",
    )
    args = parser.parse_args()

    clustering_dir = get_clustering_dir()
    sft_dir = get_competency_sft_dir()
    reps_path = clustering_dir / "cluster_representatives.jsonl"
    labels_path = clustering_dir / "cluster_labels.json"

    if not reps_path.exists():
        print(f"[ERROR] 파일 없음: {reps_path}")
        print("  먼저 inspect_clustering.py 로 대표 샘플을 추출하세요.")
        sys.exit(1)

    labels_dict = {}
    if labels_path.exists():
        with labels_path.open("r", encoding="utf-8") as f:
            labels_dict = json.load(f)

    clusters = []
    with reps_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            clusters.append(json.loads(line))

    if args.max_clusters > 0:
        clusters = clusters[: args.max_clusters]

    n_per = max(1, min(5, args.qa_per_cluster))
    variants = [_QA_VARIANTS[k % len(_QA_VARIANTS)] for k in range(n_per)]
    print(f"[INFO] 군집 수: {len(clusters)}, 군집당 QA {n_per}쌍, EXAONE 생성 후 {sft_dir} 에 저장")

    rows = []
    for i, row in enumerate(clusters):
        cid = row.get("cluster_id", i)
        label = labels_dict.get(str(cid), f"군집{cid}")
        samples = row.get("representative_samples", [])
        texts = [s.get("content", "").strip() for s in samples if s.get("content")]
        samples_text = "\n".join(f"- {t[:400]}" for t in texts[:10])
        if not samples_text:
            continue
        added = 0
        for v_idx, variant in enumerate(variants):
            question, answer = _generate_qa_for_cluster(label, samples_text, variant)
            if not question or not answer:
                continue
            rows.append({
                "instruction": question,
                "input": "",
                "output": answer,
                "cluster_id": cid,
                "cluster_label": label,
            })
            added += 1
        if added:
            print(f"  [{i+1}/{len(clusters)}] cluster_id={cid} ({label}) → QA {added}쌍")

    out_path = sft_dir / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[OK] SFT 데이터 저장: {out_path} (총 {len(rows)}건)")


if __name__ == "__main__":
    main()
