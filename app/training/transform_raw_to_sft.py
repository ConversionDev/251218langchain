"""
ETL Transform: Raw JSONL to SFT Format

JSONL 파일을 SFT(Supervised Fine-Tuning) 학습용 형식으로 변환.

역할: Transform (변환)
1. JSONL 파일 스트리밍 읽기/쓰기
2. 데이터 정규화 및 중복 제거
3. 규칙 기반 라벨링
4. SFT 형식 변환

입력: extract_csv_to_jsonl.py가 생성한 _raw.jsonl 파일
출력: sft_train.jsonl (SFT 학습용 표준 형식)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    """JSONL을 한 줄씩 읽습니다. 깨진 라인은 건너뜁니다.

    Args:
        path: 읽을 JSONL 파일 경로

    Yields:
        각 행의 JSON 객체 딕셔너리
    """
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # 운영에서는 별도 로그 파일로 남기는 것이 좋습니다.
                continue


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    """JSONL 파일로 저장합니다.

    Args:
        path: 저장할 파일 경로
        rows: 저장할 딕셔너리들의 반복 가능 객체
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_attachments(raw: str) -> List[str]:
    """첨부파일 문자열에서 파일명 목록을 추출합니다.

    "Offer.docx (16.4 K), Offer - contextual advertising.docx (15.8 K)"
    -> ["Offer.docx", "Offer - contextual advertising.docx"]

    Args:
        raw: 첨부파일 원본 문자열

    Returns:
        파일명 목록
    """
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    names: List[str] = []
    for p in parts:
        # 뒤의 "(16.4 K)" 같은 용량 표기를 제거
        p = re.sub(r"\s*\([^)]*\)\s*$", "", p).strip()
        if p:
            names.append(p)
    return names


def detect_data_format(row: Dict[str, Any]) -> str:
    """데이터 형식을 자동 감지합니다.

    Args:
        row: 원본 JSONL 행 데이터

    Returns:
        "email", "customer_service", 또는 "mixed_email"
    """
    # mixed_email 형식 필드 확인 (우선순위 1)
    if "instruct_text" in row or "dataset_info" in row:
        return "mixed_email"
    # 스팸 메일 형식 필드 확인
    elif "수신일자" in row or "제목" in row or "메일 종류" in row:
        return "email"
    # 콜센터 대화 형식 필드 확인
    elif (
        "도메인" in row
        or "화자" in row
        or "고객질문(요청)" in row
        or "상담사질문(요청)" in row
    ):
        return "customer_service"
    else:
        # 기본값은 email 형식으로 가정
        return "email"


def normalize_raw(row: Dict[str, Any]) -> Dict[str, Any]:
    """raw 한 줄을 정규화한 clean 레코드로 변환합니다.

    Args:
        row: 원본 JSONL 행 데이터

    Returns:
        정규화된 딕셔너리
    """
    data_format = detect_data_format(row)

    if data_format == "mixed_email":
        # mixed_email 데이터 처리
        instruct_text = (row.get("instruct_text") or "").strip()
        dataset_info = row.get("dataset_info", {})
        category = dataset_info.get("category", -1)  # 0=정상, 1=스팸
        ref = (row.get("ref") or "").strip()
        date = row.get("date", "")

        # 날짜 형식 변환 (20260115 -> "2026-01-15")
        date_str = ""
        if date:
            try:
                date_str = (
                    f"{date // 10000}-{(date % 10000) // 100:02d}-{date % 100:02d}"
                )
            except (TypeError, ValueError, AttributeError):
                date_str = str(date)

        # category 기반 mail_type 설정
        if category == 0:
            mail_type = "정상"
        elif category == 1:
            mail_type = "스팸"
        else:
            # ref 필드로 판단
            if ref == "정상":
                mail_type = "정상"
            else:
                mail_type = "스팸"

        return {
            "data_format": "mixed_email",
            "received_date": date_str,
            "received_time": "",
            "received_at": date_str,
            "subject": instruct_text,
            "attachments": [],
            "mail_type": mail_type,
            "attachments_raw": "",
            "category": category,  # 원본 category 보존
            "ref": ref,  # 원본 ref 보존
        }
    elif data_format == "customer_service":
        # 콜센터 대화 데이터 처리
        # 고객 질문/요청을 subject로, 상담사 질문/요청을 답변으로 사용
        customer_question = (row.get("고객질문(요청)") or "").strip()
        customer_answer = (row.get("고객답변") or "").strip()
        consultant_question = (row.get("상담사질문(요청)") or "").strip()
        consultant_answer = (row.get("상담사답변") or "").strip()

        # 질문과 답변을 결합하여 subject 생성
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

        # 카테고리나 도메인을 mail_type으로 사용
        category = (row.get("카테고리") or "").strip()
        domain = (row.get("도메인") or "").strip()
        mail_type = f"{domain}_{category}" if domain or category else ""

        # 대화셋일련번호와 문장번호를 received_at으로 사용
        dialog_id = (row.get("대화셋일련번호") or "").strip()
        sentence_num = (row.get("문장번호") or "").strip()
        received_at = f"{dialog_id}_{sentence_num}" if dialog_id or sentence_num else ""

        return {
            "data_format": "customer_service",  # 형식 정보 추가
            "received_date": "",
            "received_time": "",
            "received_at": received_at,
            "subject": subject,
            "attachments": [],
            "mail_type": mail_type,
            "attachments_raw": "",
        }
    else:
        # 기존 스팸 메일 데이터 처리
        date = (row.get("수신일자") or "").strip()
        time = (row.get("수신시간") or "").strip()
        subject = (row.get("제목") or "").strip()
        mail_type = (row.get("메일 종류") or "").strip()
        attach_raw = (row.get("첨부") or "").strip()
        attachments = parse_attachments(attach_raw)

        received_at = f"{date} {time}".strip()

        return {
            "data_format": "email",  # 형식 정보 추가
            "received_date": date,
            "received_time": time,
            "received_at": received_at,
            "subject": subject,
            "attachments": attachments,
            "mail_type": mail_type,
            "attachments_raw": attach_raw,
        }


def dedup_key(clean: Dict[str, Any], mode: str = "subject+attachments") -> Tuple:
    """중복 제거 기준을 선택합니다.

    Args:
        clean: 정규화된 데이터 딕셔너리
        mode: 중복 제거 모드
            - "subject+attachments": 제목과 첨부가 같으면 중복
            - "datetime+subject+attachments": 시간까지 포함(더 엄격)

    Returns:
        중복 체크용 튜플 키
    """
    if mode == "datetime+subject+attachments":
        return (
            clean.get("received_at", ""),
            clean.get("subject", ""),
            tuple(clean.get("attachments", [])),
        )
    return (clean.get("subject", ""), tuple(clean.get("attachments", [])))


def rule_label(clean: Dict[str, Any]) -> Tuple[str, str, float]:
    """rule-based labeling을 수행합니다.

    Args:
        clean: 정규화된 데이터 딕셔너리

    Returns:
        (action, reason, confidence) 튜플
        - action: BLOCK/ALLOW
        - reason: 짧은 근거
        - confidence: 0~1 사이의 신뢰도
    """
    subject = (clean.get("subject") or "").lower()
    attachments = clean.get("attachments") or []
    mail_type = (clean.get("mail_type") or "").strip()
    data_format = clean.get("data_format", "email")

    # mixed_email 형식의 경우 category 직접 사용
    if data_format == "mixed_email":
        category = clean.get("category", -1)
        ref = clean.get("ref", "").strip()

        # category 기반 판단 (0=정상, 1=스팸)
        if category == 0:
            base_action = "ALLOW"
            reason = "정상 이메일 데이터셋"
            confidence = 0.95
        elif category == 1:
            base_action = "BLOCK"
            reason = "유해 질의 데이터셋 (스팸)"
            confidence = 0.95
        else:
            # ref 필드로 판단
            if ref == "정상":
                base_action = "ALLOW"
                reason = "ref 필드 기준: 정상"
                confidence = 0.90
            else:
                base_action = "BLOCK"
                reason = "ref 필드 기준: 스팸"
                confidence = 0.90

        return base_action, reason, confidence

    # 기존 로직 (email, customer_service)
    # 1) 원천 데이터에 '스팸' 라벨이 있으면 기본적으로 BLOCK
    if mail_type == "스팸":
        base_action = "BLOCK"
    elif mail_type == "정상":
        base_action = "ALLOW"
    else:
        # 라벨이 없으면 rule로 추정(초기엔 보수적으로)
        base_action = "BLOCK"

    # 2) reason / confidence 규칙
    reasons = []
    score = 0.0

    if "(광고)" in (clean.get("subject") or ""):
        reasons.append("제목에 (광고) 표기가 포함됨")
        score += 0.5

    # 흔한 스팸 키워드 예시(필요시 확장)
    spam_keywords = [
        "offer",
        "보험",
        "임플란트",
        "치아보험",
        "이벤트",
        "할인",
        "진단금",
        "간병",
    ]
    if any(k.lower() in subject for k in [kw.lower() for kw in spam_keywords]):
        reasons.append("스팸/광고성 키워드 패턴이 포함됨")
        score += 0.35

    if attachments:
        reasons.append("첨부파일이 포함됨")
        score += 0.2

    if not reasons:
        reasons.append("메타데이터만으로는 뚜렷한 단서가 적음")
        score += 0.1

    # confidence는 0.85~0.99 사이로 클램프(초기 모델 학습 안정 목적)
    confidence = min(0.99, max(0.85, 0.80 + score))

    # action은 base_action을 따르되, 이유가 약하면 confidence만 낮게
    action = base_action
    reason = " / ".join(reasons)

    return action, reason, float(f"{confidence:.2f}")


def to_sft(clean: Dict[str, Any]) -> Dict[str, Any]:
    """정규화된 데이터를 SFT 형식으로 변환합니다.

    Args:
        clean: 정규화된 데이터 딕셔너리

    Returns:
        SFT 형식의 딕셔너리
    """
    action, reason, confidence = rule_label(clean)
    data_format = clean.get("data_format", "email")

    # 데이터 형식에 따라 instruction 변경
    if data_format == "mixed_email":
        instruction = (
            "다음 이메일 내용을 분석하여 스팸 여부를 판정하고 JSON 형식으로만 답하세요."
        )
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
        "output": {
            "action": action,
            "reason": reason,
            "confidence": confidence,
        },
    }


def convert_jsonl_to_sft(
    input_jsonl_path: Path,
    output_sft_path: Path,
    output_dedup_path: Optional[Path] = None,
    output_clean_path: Optional[Path] = None,
    dedup_mode: str = "subject+attachments",
) -> Tuple[int, int, int]:
    """JSONL 파일을 SFT 형식으로 변환합니다.

    Args:
        input_jsonl_path: 입력 JSONL 파일 경로
        output_sft_path: 출력 SFT JSONL 파일 경로
        output_dedup_path: (선택) 중복 제거된 JSONL 파일 경로
        output_clean_path: (선택) 정규화된 JSONL 파일 경로
        dedup_mode: 중복 제거 모드

    Returns:
        (sft_count, dedup_count, clean_count) 튜플
    """
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

        # dedup 단계 산출물(원본 형태 유지가 필요하면 row를, 정규화 형태면 clean을 저장)
        if output_dedup_path is not None:
            dedup_rows.append(row)

        # clean 단계 산출물
        if output_clean_path is not None:
            clean_rows.append(clean)

        # sft 산출물
        sft_rows.append(to_sft(clean))

    # 저장
    write_jsonl(output_sft_path, sft_rows)
    if output_dedup_path is not None:
        write_jsonl(output_dedup_path, dedup_rows)
    if output_clean_path is not None:
        write_jsonl(output_clean_path, clean_rows)

    return len(sft_rows), len(dedup_rows), len(clean_rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="JSONL 파일을 SFT 형식으로 변환")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="입력 JSONL 파일 경로 (None이면 자동 탐지)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="출력 SFT JSONL 파일 경로 (None이면 자동 생성)",
    )
    parser.add_argument(
        "--dedup_mode",
        type=str,
        default="subject+attachments",
        help="중복 제거 모드 (기본값: subject+attachments)",
    )

    args = parser.parse_args()

    # data 디렉토리 경로 (app/training -> app -> app/data)
    app_dir = Path(__file__).parent.parent  # training -> app
    data_dir = app_dir / "data"

    if not data_dir.exists():
        print(f"오류: data 디렉토리를 찾을 수 없습니다: {data_dir}")
        sys.exit(1)

    # 입력 파일 자동 탐지
    raw_jsonl_file: Optional[Path] = None
    if args.input:
        raw_jsonl_file = Path(args.input)
    else:
        # 여러 가능한 파일명 시도
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
            print(f"[INFO] 가능한 파일명: {possible_files}")
            print("[INFO] 또는 --input 옵션으로 파일 경로를 지정하세요.")
            sys.exit(1)

    if not raw_jsonl_file.exists():
        print(f"[ERROR] 입력 파일을 찾을 수 없습니다: {raw_jsonl_file}")
        sys.exit(1)

    # 출력 파일명 생성
    if args.output:
        sft_file = Path(args.output)
    else:
        sft_file = data_dir / "sft_dataset" / "sft_train.jsonl"

    print(f"[INFO] 변환 중: {raw_jsonl_file.name} -> {sft_file.name}")

    try:
        sft_count, _, _ = convert_jsonl_to_sft(
            input_jsonl_path=raw_jsonl_file,
            output_sft_path=sft_file,
            dedup_mode=args.dedup_mode,
        )
        print(f"[OK] SFT 변환 완료: {sft_file.name} (samples={sft_count})")

    except Exception as e:
        print(f"[ERROR] {raw_jsonl_file.name} 변환 실패: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("\n모든 변환 작업이 완료되었습니다.")
