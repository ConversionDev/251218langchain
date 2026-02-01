"""
ETL Transform: Raw JSONL to SFT Format

JSONL 파일을 SFT(Supervised Fine-Tuning) 학습용 형식으로 변환.

입력: csv_to_raw_jsonl.py가 생성한 _raw.jsonl 파일
출력: sft_train.jsonl (SFT 학습용 표준 형식)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    """JSONL을 한 줄씩 읽습니다. 깨진 라인은 건너뜁니다."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    """JSONL 파일로 저장합니다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_attachments(raw: str) -> List[str]:
    """첨부파일 문자열에서 파일명 목록을 추출합니다."""
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    names: List[str] = []
    for p in parts:
        p = re.sub(r"\s*\([^)]*\)\s*$", "", p).strip()
        if p:
            names.append(p)
    return names


def detect_data_format(row: Dict[str, Any]) -> str:
    """데이터 형식을 자동 감지합니다."""
    if "instruct_text" in row or "dataset_info" in row:
        return "mixed_email"
    elif "수신일자" in row or "제목" in row or "메일 종류" in row:
        return "email"
    elif (
        "도메인" in row
        or "화자" in row
        or "고객질문(요청)" in row
        or "상담사질문(요청)" in row
    ):
        return "customer_service"
    return "email"


def normalize_raw(row: Dict[str, Any]) -> Dict[str, Any]:
    """raw 한 줄을 정규화한 clean 레코드로 변환합니다."""
    data_format = detect_data_format(row)

    if data_format == "mixed_email":
        instruct_text = (row.get("instruct_text") or "").strip()
        dataset_info = row.get("dataset_info", {})
        category = dataset_info.get("category", -1)
        ref = (row.get("ref") or "").strip()
        date = row.get("date", "")
        date_str = ""
        if date:
            try:
                date_str = (
                    f"{date // 10000}-{(date % 10000) // 100:02d}-{date % 100:02d}"
                )
            except (TypeError, ValueError, AttributeError):
                date_str = str(date)
        if category == 0:
            mail_type = "정상"
        elif category == 1:
            mail_type = "스팸"
        else:
            mail_type = "정상" if ref == "정상" else "스팸"
        return {
            "data_format": "mixed_email",
            "received_date": date_str,
            "received_time": "",
            "received_at": date_str,
            "subject": instruct_text,
            "attachments": [],
            "mail_type": mail_type,
            "attachments_raw": "",
            "category": category,
            "ref": ref,
        }
    elif data_format == "customer_service":
        customer_question = (row.get("고객질문(요청)") or "").strip()
        customer_answer = (row.get("고객답변") or "").strip()
        consultant_question = (row.get("상담사질문(요청)") or "").strip()
        consultant_answer = (row.get("상담사답변") or "").strip()
        subject_parts = []
        if customer_question:
            subject_parts.append(f"고객: {customer_question}")
        if customer_answer:
            subject_parts.append(f"고객답변: {customer_answer}")
        if consultant_question:
            subject_parts.append(f"상담사: {consultant_question}")
        if consultant_answer:
            subject_parts.append(f"상담사답변: {consultant_answer}")
        subject = " | ".join(subject_parts) if subject_parts else ""
        category = (row.get("카테고리") or "").strip()
        domain = (row.get("도메인") or "").strip()
        mail_type = f"{domain}_{category}" if domain or category else ""
        dialog_id = (row.get("대화셋일련번호") or "").strip()
        sentence_num = (row.get("문장번호") or "").strip()
        received_at = f"{dialog_id}_{sentence_num}" if dialog_id or sentence_num else ""
        return {
            "data_format": "customer_service",
            "received_date": "",
            "received_time": "",
            "received_at": received_at,
            "subject": subject,
            "attachments": [],
            "mail_type": mail_type,
            "attachments_raw": "",
        }
    else:
        date = (row.get("수신일자") or "").strip()
        time = (row.get("수신시간") or "").strip()
        subject = (row.get("제목") or "").strip()
        mail_type = (row.get("메일 종류") or "").strip()
        attach_raw = (row.get("첨부") or "").strip()
        attachments = parse_attachments(attach_raw)
        received_at = f"{date} {time}".strip()
        return {
            "data_format": "email",
            "received_date": date,
            "received_time": time,
            "received_at": received_at,
            "subject": subject,
            "attachments": attachments,
            "mail_type": mail_type,
            "attachments_raw": attach_raw,
        }


def dedup_key(clean: Dict[str, Any], mode: str = "subject+attachments") -> Tuple:
    """중복 제거 기준을 선택합니다."""
    if mode == "datetime+subject+attachments":
        return (
            clean.get("received_at", ""),
            clean.get("subject", ""),
            tuple(clean.get("attachments", [])),
        )
    return (clean.get("subject", ""), tuple(clean.get("attachments", [])))


def rule_label(clean: Dict[str, Any]) -> Tuple[str, str, float]:
    """rule-based labeling을 수행합니다."""
    subject = (clean.get("subject") or "").lower()
    attachments = clean.get("attachments") or []
    mail_type = (clean.get("mail_type") or "").strip()
    data_format = clean.get("data_format", "email")

    if data_format == "mixed_email":
        category = clean.get("category", -1)
        ref = clean.get("ref", "").strip()
        if category == 0:
            return "ALLOW", "정상 이메일 데이터셋", 0.95
        elif category == 1:
            return "BLOCK", "유해 질의 데이터셋 (스팸)", 0.95
        else:
            if ref == "정상":
                return "ALLOW", "ref 필드 기준: 정상", 0.90
            return "BLOCK", "ref 필드 기준: 스팸", 0.90

    if mail_type == "스팸":
        base_action = "BLOCK"
    elif mail_type == "정상":
        base_action = "ALLOW"
    else:
        base_action = "BLOCK"

    reasons = []
    score = 0.0
    if "(광고)" in (clean.get("subject") or ""):
        reasons.append("제목에 (광고) 표기가 포함됨")
        score += 0.5
    spam_keywords = ["offer", "보험", "임플란트", "치아보험", "이벤트", "할인", "진단금", "간병"]
    if any(k.lower() in subject for k in [kw.lower() for kw in spam_keywords]):
        reasons.append("스팸/광고성 키워드 패턴이 포함됨")
        score += 0.35
    if attachments:
        reasons.append("첨부파일이 포함됨")
        score += 0.2
    if not reasons:
        reasons.append("메타데이터만으로는 뚜렷한 단서가 적음")
        score += 0.1
    confidence = min(0.99, max(0.85, 0.80 + score))
    reason = " / ".join(reasons)
    return base_action, reason, float(f"{confidence:.2f}")


def to_sft(clean: Dict[str, Any]) -> Dict[str, Any]:
    """정규화된 데이터를 SFT 형식으로 변환합니다."""
    action, reason, confidence = rule_label(clean)
    data_format = clean.get("data_format", "email")
    if data_format == "mixed_email":
        instruction = "다음 이메일 내용을 분석하여 스팸 여부를 판정하고 JSON 형식으로만 답하세요."
    elif data_format == "customer_service":
        instruction = "다음 콜센터 대화 내용을 분석하여 스팸 여부를 판정하고 JSON 형식으로만 답하세요."
    else:
        instruction = "다음 이메일 메타데이터를 분석하여 스팸 여부를 판정하고 JSON 형식으로만 답하세요."
    return {
        "instruction": instruction,
        "input": {
            "subject": clean.get("subject", ""),
            "attachments": clean.get("attachments", []),
            "received_at": clean.get("received_at", ""),
        },
        "output": {"action": action, "reason": reason, "confidence": confidence},
    }


def convert_jsonl_to_sft(
    input_jsonl_path: Path,
    output_sft_path: Path,
    output_dedup_path: Optional[Path] = None,
    output_clean_path: Optional[Path] = None,
    dedup_mode: str = "subject+attachments",
) -> Tuple[int, int, int]:
    """JSONL 파일을 SFT 형식으로 변환합니다."""
    seen = set()
    dedup_rows = []
    clean_rows = []
    sft_rows = []
    for row in iter_jsonl(input_jsonl_path):
        clean = normalize_raw(row)
        key = dedup_key(clean, mode=dedup_mode)
        if key in seen:
            continue
        seen.add(key)
        if output_dedup_path is not None:
            dedup_rows.append(row)
        if output_clean_path is not None:
            clean_rows.append(clean)
        sft_rows.append(to_sft(clean))
    write_jsonl(output_sft_path, sft_rows)
    if output_dedup_path is not None:
        write_jsonl(output_dedup_path, dedup_rows)
    if output_clean_path is not None:
        write_jsonl(output_clean_path, clean_rows)
    return len(sft_rows), len(dedup_rows), len(clean_rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JSONL 파일을 SFT 형식으로 변환")
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--dedup_mode", type=str, default="subject+attachments")
    args = parser.parse_args()

    app_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = app_dir / "data"
    if not data_dir.exists():
        print(f"오류: data 디렉토리를 찾을 수 없습니다: {data_dir}")
        sys.exit(1)

    raw_jsonl_file: Optional[Path] = None
    if args.input:
        raw_jsonl_file = Path(args.input)
    else:
        possible_files = [
            "mixed_email_dataset.jsonl",
            "한국우편사업진흥원_스팸메일 수신차단 목록_20241231_raw.jsonl",
            "민원(콜센터) 질의응답_K쇼핑_통합_Training.jsonl",
        ]
        for filename in possible_files:
            candidate = data_dir / filename
            if candidate.exists():
                raw_jsonl_file = candidate
                break
        if raw_jsonl_file is None:
            print("[ERROR] 입력 JSONL 파일을 찾을 수 없습니다.")
            sys.exit(1)

    if not raw_jsonl_file.exists():
        print(f"[ERROR] 입력 파일을 찾을 수 없습니다: {raw_jsonl_file}")
        sys.exit(1)

    sft_file = Path(args.output) if args.output else data_dir / "sft_dataset" / "sft_train.jsonl"
    try:
        sft_count, _, _ = convert_jsonl_to_sft(
            input_jsonl_path=raw_jsonl_file,
            output_sft_path=sft_file,
            dedup_mode=args.dedup_mode,
        )
        print(f"[OK] SFT 변환 완료: {sft_file.name} (samples={sft_count})")
    except Exception as e:
        print(f"[ERROR] 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
