"""
competency_qa.jsonl (instruction/input/output) → EXAONE 채팅 형식 JSONL 변환.

apply_chat_template에 넣을 수 있도록 각 행을 messages: [{role, content}, ...] 형태로 저장.
- system: 고정 안내 (선택)
- user: instruction (+ input)
- assistant: output

기본 동작: 출력 파일이 있으면 이미 변환된 (user, assistant) 쌍은 유지하고, 새 행만 변환해 끝에 추가.
  --no-incremental 이면 기존 출력을 무시하고 전부 새로 씀.

사용 예:
  python -m app.training.pipelines.sft.run_qa_to_chat_format
  python -m app.training.pipelines.sft.run_qa_to_chat_format --input competency_qa.jsonl --output competency_qa_chat.jsonl
"""

import argparse
import json
import sys
from pathlib import Path

# app/ 기준 경로
_app_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_app_root) not in sys.path:
    sys.path.insert(0, str(_app_root))

from training.shared.competency_extract import get_competency_sft_dir  # type: ignore  # noqa: E402

DEFAULT_SYSTEM = "당신은 직무·역량 전문가입니다. 질문에 대해 데이터에 기반한 답변을 해 주세요."


def main() -> None:
    parser = argparse.ArgumentParser(description="QA JSONL → EXAONE messages 형식 변환")
    parser.add_argument(
        "--input",
        type=str,
        default="competency_qa.jsonl",
        help="입력 JSONL 파일명 (기본 competency_qa.jsonl)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="competency_qa_chat.jsonl",
        help="출력 JSONL 파일명 (기본 competency_qa_chat.jsonl)",
    )
    parser.add_argument(
        "--no-system",
        action="store_true",
        help="system 메시지 없이 user/assistant만 사용",
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="기존 출력 무시하고 전부 새로 변환 (기본: 이미 변환된 행은 유지, 새 행만 추가)",
    )
    args = parser.parse_args()

    sft_dir = get_competency_sft_dir()
    in_path = sft_dir / args.input
    out_path = sft_dir / args.output

    if not in_path.exists():
        print(f"[ERROR] 파일 없음: {in_path}")
        sys.exit(1)

    # 이미 변환된 (user_content, output) 쌍 수집 (incremental 시)
    seen: set[tuple[str, str]] = set()
    use_append = False
    if not args.no_incremental and out_path.exists():
        with out_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    msgs = obj.get("messages") or []
                    user_content = ""
                    assistant_content = ""
                    for m in msgs:
                        role, content = m.get("role", ""), (m.get("content") or "").strip()
                        if role == "user":
                            user_content = content
                        elif role == "assistant":
                            assistant_content = content
                    if user_content or assistant_content:
                        seen.add((user_content, assistant_content))
                except (json.JSONDecodeError, TypeError):
                    pass
        use_append = True
        print(f"[INFO] 기존 변환본 {len(seen)}건 유지, 새 행만 추가")

    count = 0
    skipped = 0
    mode = "a" if use_append else "w"
    with in_path.open("r", encoding="utf-8") as fr, out_path.open(mode, encoding="utf-8") as fw:
        for line in fr:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            instruction = row.get("instruction", "").strip()
            inp = row.get("input", "").strip()
            output = row.get("output", "").strip()
            if not instruction or not output:
                continue
            user_content = f"{instruction}\n{inp}".strip() if inp else instruction
            key = (user_content, output)
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            messages = []
            if not args.no_system:
                messages.append({"role": "system", "content": DEFAULT_SYSTEM})
            messages.append({"role": "user", "content": user_content})
            messages.append({"role": "assistant", "content": output})

            out_row = {"messages": messages}
            if "cluster_id" in row:
                out_row["cluster_id"] = row["cluster_id"]
            if "cluster_label" in row:
                out_row["cluster_label"] = row["cluster_label"]
            fw.write(json.dumps(out_row, ensure_ascii=False) + "\n")
            count += 1

    if skipped:
        print(f"[OK] 기존과 중복 건너뜀 {skipped}건, 새로 변환 {count}건 → {out_path}")
    else:
        print(f"[OK] {count}건 변환 완료: {out_path}")


if __name__ == "__main__":
    main()
