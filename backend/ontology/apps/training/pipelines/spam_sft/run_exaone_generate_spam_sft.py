"""
ExaOne으로 스팸/햄 합성 SFT 데이터 생성 (스팸 SFT ETL: Extract + Transform + Load).
한국어 스팸 메일 중심.

ETL: ExaOne으로 이메일 추출(Extract) → SFT 형식 변환(Transform) → exaone_synthetic.jsonl 및 train/val.jsonl 저장(Load).
LLaMA 스팸 분류 학습을 위해 ExaOne이 생성한 한국어 이메일(JSON)을
SFT 형식( input + output.action BLOCK/ALLOW )으로 저장합니다.
다양한 스팸 유형(피싱, 당첨, 광고, 가짜 경고 등)과 햄(업무, 개인)을 모두 한국어로 생성합니다.

한국어 참고 데이터셋 (구글 "한국어 스팸 메일 데이터셋" 검색 등):
- 공공데이터포털(data.go.kr): 불법 스팸 URL, 피싱사이트, 상용메일 차단 데이터 등
- GitHub: KoreanSpamDataPool, KOR_phishing_Detect-Dataset 등 공유 데이터·논문용 데이터셋
- 수동 다운로드 후 참고용 예시로 활용 시, 동일한 subject/sender/body 형식으로 정리하면 few-shot에 사용 가능

실행: app/ 에서
  python -m training.pipelines.spam_sft.run_exaone_generate_spam_sft
  python -m training.pipelines.spam_sft.run_exaone_generate_spam_sft --full    # 2,000건 (스팸 1,200 + 햄 800)
  python -m training.pipelines.spam_sft.run_exaone_generate_spam_sft --large   # 3,600건 (스팸 2,400 + 햄 1,200)
  python -m training.pipelines.spam_sft.run_exaone_generate_spam_sft --max      # 5,000건 (스팸 3,000 + 햄 2,000)
  python -m training.pipelines.spam_sft.run_exaone_generate_spam_sft --max --fast   # 5,000건 (참고 데이터 기본 사용)
  python -m training.pipelines.spam_sft.run_exaone_generate_spam_sft --max --no-references  # 참고 데이터 생략 시에만

권장 환경 (RTX 4060 Ti 16GB + i5-8600):
  - GPU 전용·안정성: 아래 env가 스크립트 시작 시 자동 적용됨.
  - 다른 GPU 사용 앱 종료, 전원 옵션 '고성능', 방열 유지 시 장시간 안정.
"""

# ========== GPU 최대 활용·안정성 (모델 로드 전에 적용)
import os
_env = os.environ
_env.setdefault("TOKENIZERS_PARALLELISM", "false")  # 6스레드 CPU에서 토크나이저 충돌 방지
_env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")  # 장시간 실행 시 VRAM 단편화 완화
if "CUDA_VISIBLE_DEVICES" not in _env:
    _env["CUDA_VISIBLE_DEVICES"] = "0"  # 단일 GPU 명시 (4060 Ti만 사용)

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_spam_sft_dir  # type: ignore
from domain.shared.utils import save_jsonl  # type: ignore


# 한국어 스팸 메일 유형 15종 (다양성 극대화, 검증 정확도 82~88%+ 목표)
SPAM_CATEGORIES = [
    ("phishing", "피싱: 비밀번호 확인, 계정 정지 위장, OTP·금융 사기 유도하는 한국어 이메일 한 건"),
    ("lottery", "당첨/이벤트: 무료 당첨, 경품, 쿠폰, 링크 클릭 유도하는 스팸 이메일 한 건"),
    ("marketing", "광고/마케팅: 원치 않는 프로모션, 구독 유도, 할인 광고 이메일 한 건"),
    ("fake_alert", "가짜 경고/지원: 계정 정지 예정, 고객센터 연락 요청 위장 이메일 한 건"),
    ("adult_gambling", "성인/도박: 불법 광고 또는 도박 사이트 유도 이메일 한 건"),
    ("delivery_fake", "택배 사칭: 배송 불가·주소 확인·재배송 신청 위장 이메일 한 건"),
    ("gov_fake", "정부기관 사칭: 국세청·경찰·건강보험·법원 위장 피싱 이메일 한 건"),
    ("loan_finance", "대출/금융: 신용등급 무관 대출·당일 입금·서민대출 유도 이메일 한 건"),
    ("payment_fake", "결제 확인 위장: 해외 결제·이상 거래·결제 취소 위장 피싱 이메일 한 건"),
    ("account_alert", "계정 보안 알림: 비정상 로그인·비밀번호 변경 요청 위장 이메일 한 건"),
    ("investment", "투자 권유: 주식·코인·부동산 고수익 투자 유도 이메일 한 건"),
    ("job_fake", "구직·채용 사칭: 가짜 입사 제안, 이력서 요청, 선입금 유도 이메일 한 건"),
    ("survey_reward", "설문·리워드: 설문 참여 대가 현금·포인트 유도, 개인정보 수집 이메일 한 건"),
    ("friend_fake", "친구·지인 사칭: 급전 요청, 번호 변경 알림, 대리 결제 요청 위장 이메일 한 건"),
    ("other", "기타 스팸: 짧은 문구, 의심스러운 링크·첨부 유도 이메일 한 건"),
]

# 한국어 햄(정상 메일) + Hard Negative(스팸처럼 보이지만 정상)
HAM_CATEGORIES = [
    ("work", "업무: 회의 일정, 보고, 협업 요청 등 정상적인 회사 이메일 한 건"),
    ("personal", "개인: 친구/가족에게 보내는 일반적인 한국어 이메일 한 건"),
    ("newsletter", "뉴스레터: 뉴스·소식 요약 형태의 정상 메일 한 건"),
    ("work_marketing", "업무 마케팅: 회사 내부 프로모션·설문·이벤트 안내(정상) 한 건"),
    ("hr_notice", "인사/IT 공지: 비밀번호 변경·보안 정책 안내 등 회사 공지 한 건"),
    ("delivery_real", "실제 배송: 주문한 택배 배송 시작·도착 알림(정상) 한 건"),
    ("subscription", "구독 뉴스레터: 구독한 서비스의 정기 소식(정상) 한 건"),
]

# BP(Best Practice) 단계별 목표 (총 데이터 + 다양성 15종)
# full: 2,000건  |  large: 3,600건  |  max: 5,000건
PRESETS = {
    "full": {"per_category": 80, "ham_total": 800},   # 15*80=1,200 스팸 + 800 햄 = 2,000
    "large": {"per_category": 160, "ham_total": 1200},  # 15*160=2,400 + 1,200 = 3,600
    "max": {"per_category": 200, "ham_total": 2000},   # 15*200=3,000 + 2,000 = 5,000
}
BP_SPAM_TOTAL = len(SPAM_CATEGORIES) * PRESETS["full"]["per_category"]   # 1,200
BP_HAM_TOTAL = PRESETS["full"]["ham_total"]   # 800
BP_TOTAL = BP_SPAM_TOTAL + BP_HAM_TOTAL       # 2,000

# 예상 건당 소요 시간(초). RTX 4060 Ti 기준 실제 약 15~25초, 보수적으로 20초로 표시
SEC_PER_SAMPLE = 20

# 참고 데이터 few-shot (기본 사용. 학습 정확도 위해 3곳 참고 데이터 무조건 적용)
_FEW_SHOT_CONTEXT: str = ""


def _fmt_elapsed(sec: float) -> str:
    """경과 시간을 'N분 M초' 또는 'N시간 M분' 형식으로."""
    if sec < 60:
        return f"{sec:.0f}초"
    if sec < 3600:
        return f"{int(sec // 60)}분 {int(sec % 60)}초"
    return f"{int(sec // 3600)}시간 {int((sec % 3600) // 60)}분"


def _fmt_remaining(sec: float) -> str:
    """남은 시간을 '약 N분' 또는 '약 N시간 M분' 형식으로."""
    if sec <= 0:
        return "곧 완료"
    if sec < 60:
        return f"약 {sec:.0f}초"
    if sec < 3600:
        return f"약 {int(sec // 60)}분"
    return f"약 {int(sec // 3600)}시간 {int((sec % 3600) // 60)}분"


def _prompt_for_spam(category: str, description: str, few_shot: str = "") -> str:
    base = f"""다음 조건을 만족하는 이메일을 **반드시 JSON 한 개만** 출력하세요. 다른 설명 없이 JSON만 출력합니다.
조건: {description}
JSON 키: "subject" (제목), "sender" (발신자 표시명 또는 이메일), "body" (본문, 2~5문장).
한국어로 작성하세요."""
    if few_shot:
        return few_shot + "\n\n" + base
    return base


def _prompt_for_ham(category: str, description: str, few_shot: str = "") -> str:
    base = f"""다음 조건을 만족하는 **정상(스팸 아님)** 이메일을 **반드시 JSON 한 개만** 출력하세요. 다른 설명 없이 JSON만 출력합니다.
조건: {description}
JSON 키: "subject" (제목), "sender" (발신자 표시명 또는 이메일), "body" (본문, 2~5문장).
한국어로 작성하세요."""
    if few_shot:
        return few_shot + "\n\n" + base
    return base


def _parse_json_from_response(text: str) -> dict | None:
    """응답 텍스트에서 JSON 객체 하나 추출 (마크다운 코드블록 제거)."""
    if not text or not text.strip():
        return None
    s = text.strip()
    # ```json ... ``` 제거
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s)
    if m:
        s = m.group(1).strip()
    # 첫 { 부터 마지막 } 까지
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(s[start : end + 1])
    except json.JSONDecodeError:
        return None


def _generate_one(generate_fn, prompt: str, temperature: float = 0.8) -> dict | None:
    """ExaOne으로 한 건 생성 후 파싱."""
    # max_tokens 256: 제목+발신+본문 2~5문장이면 충분. 품질 유지하면서 속도 확보.
    out = generate_fn(prompt, max_tokens=256, temperature=temperature)
    if not out or "[ExaOne 오류]" in out:
        return None
    obj = _parse_json_from_response(out)
    if not obj:
        return None
    subject = obj.get("subject") or obj.get("제목") or ""
    sender = obj.get("sender") or obj.get("발신자") or ""
    body = obj.get("body") or obj.get("본문") or ""
    return {"subject": subject, "sender": sender, "body": body}


def build_sft_row(input_obj: dict, action: str, category: str) -> dict:
    """SFT 한 줄 생성."""
    return {
        "input": {
            "subject": input_obj.get("subject", ""),
            "sender": input_obj.get("sender", ""),
            "body": input_obj.get("body", ""),
            "attachments": [],
            "received_at": "",
        },
        "output": {"action": action},
        "category": category,
    }


def run(
    per_category: int = 50,
    ham_total: int = 300,
    output_path: Path | None = None,
    generate_fn=None,
    fetch_references: bool = True,
    fast_mode: bool = False,
) -> Path:
    """ExaOne으로 합성 데이터 생성 후 JSONL 저장. 참고 데이터는 기본 사용(학습 정확도)."""
    global _FEW_SHOT_CONTEXT

    # --fast: 품질 유지하면서 속도 우선 (temperature 0.75, few-shot 축소)
    gen_temperature = 0.75 if fast_mode else 0.8
    if fast_mode:
        print("[INFO] --fast: temperature 0.75, 참고 예시 최소화 (품질 유지)")
        print()

    # 참고 데이터 수집 (기본 켜짐. --no-references 시에만 생략)
    if fetch_references:
        try:
            from training.pipelines.spam_sft.reference_fetcher import get_few_shot_examples  # type: ignore
            print("[INFO] 3곳(공공데이터포털, GitHub, KISA)에서 참고 데이터 수집 중...")
            n_s, n_h = (1, 1) if fast_mode else (3, 2)
            _FEW_SHOT_CONTEXT = get_few_shot_examples(n_spam=n_s, n_ham=n_h)
            print("[OK] few-shot 컨텍스트 준비 완료")
            print()
        except Exception as e:
            print(f"[WARNING] 참고 데이터 수집 실패: {e}. few-shot 없이 진행합니다.")
            _FEW_SHOT_CONTEXT = ""
    if generate_fn is None:
        try:
            from infrastructure.llm import generate_text  # type: ignore
            generate_fn = generate_text
        except Exception as e:
            raise RuntimeError(f"ExaOne generate_text 로드 실패: {e}") from e

    if output_path is None:
        output_path = get_spam_sft_dir() / "exaone_synthetic.jsonl"

    expected_spam = per_category * len(SPAM_CATEGORIES)
    expected_total = expected_spam + ham_total
    expected_sec = expected_total * SEC_PER_SAMPLE
    expected_min = expected_sec / 60
    eta = datetime.now() + timedelta(seconds=expected_sec)

    print("=" * 60)
    print("[실행 전] 예상 건수 · 소요 시간 · 완료 예정")
    print("=" * 60)
    print(f"  예상 스팸: {expected_spam}건 (유형 {len(SPAM_CATEGORIES)}종 x {per_category}건)")
    print(f"  예상 햄:   {ham_total}건")
    print(f"  예상 총:   {expected_total}건")
    print(f"  예상 소요: 약 {expected_min:.0f}분 ({expected_sec:.0f}초, 건당 약 {SEC_PER_SAMPLE}초 가정)")
    print(f"  완료 예정: {eta.strftime('%Y-%m-%d %H:%M')} (현재 {datetime.now().strftime('%H:%M')} 기준)")
    print(f"  BP 단계:   full 2,000 / large 3,600 / max 5,000건 (정확도 82~88%%+ 기대)")
    print("=" * 60)
    print("  진행률: 첫 5건은 매 건, 이후 스팸 10건/햄 50건마다 출력. [경과 | 속도 | 남은 시간]")
    print("=" * 60)
    print()

    rows: list[dict] = []
    t_start = time.perf_counter()

    # 스팸 유형별 per_category 건씩
    expected_spam_count = per_category * len(SPAM_CATEGORIES)
    print("[INFO] 스팸 생성 시작... (첫 1~2건은 torch 컴파일 등으로 1~2분 걸릴 수 있음)")
    print()
    t_spam_start = time.perf_counter()
    for cat_id, desc in SPAM_CATEGORIES:
        prompt = _prompt_for_spam(cat_id, desc, few_shot=_FEW_SHOT_CONTEXT)
        for i in range(per_category):
            one = _generate_one(generate_fn, prompt, temperature=gen_temperature)
            if one:
                rows.append(build_sft_row(one, "BLOCK", cat_id))
            n_done = i + 1
            total_spam_done = len(rows)
            if total_spam_done <= 5 or n_done % 10 == 0:
                elapsed = time.perf_counter() - t_spam_start
                rate = (total_spam_done / (elapsed / 60)) if elapsed > 0 else 0
                remaining_sec = ((expected_spam_count - total_spam_done) / rate * 60) if rate > 0 else 0
                print(f"  [spam] {cat_id} {total_spam_done}/{expected_spam_count}  |  경과 {_fmt_elapsed(elapsed)}  |  속도 {rate:.1f}건/분  |  남은 시간 {_fmt_remaining(remaining_sec)}")
    t_spam_elapsed = time.perf_counter() - t_spam_start
    spam_ok = len(rows)
    spam_rate = spam_ok / (t_spam_elapsed / 60) if t_spam_elapsed > 0 else 0
    print(f"[OK] 스팸 합계: {spam_ok}건  (소요 {t_spam_elapsed:.1f}초, 약 {spam_rate:.1f}건/분)")

    # 햄: 유형 돌면서 ham_total 채울 때까지
    print("[INFO] 햄 생성 시작...")
    print()
    t_ham_start = time.perf_counter()
    ham_count = 0
    ham_per_type = max(50, ham_total // len(HAM_CATEGORIES))
    for cat_id, desc in HAM_CATEGORIES:
        prompt = _prompt_for_ham(cat_id, desc, few_shot=_FEW_SHOT_CONTEXT)
        for i in range(ham_per_type):
            if ham_count >= ham_total:
                break
            one = _generate_one(generate_fn, prompt, temperature=gen_temperature)
            if one:
                rows.append(build_sft_row(one, "ALLOW", cat_id))
                ham_count += 1
            if ham_count <= 5 or (ham_count > 0 and ham_count % 50 == 0):
                elapsed = time.perf_counter() - t_ham_start
                rate = (ham_count / (elapsed / 60)) if elapsed > 0 else 0
                remaining_sec = ((ham_total - ham_count) / rate * 60) if rate > 0 else 0
                print(f"  [ham] {cat_id} {ham_count}/{ham_total}  |  경과 {_fmt_elapsed(elapsed)}  |  속도 {rate:.1f}건/분  |  남은 시간 {_fmt_remaining(remaining_sec)}")
        if ham_count >= ham_total:
            break
    t_ham_elapsed = time.perf_counter() - t_ham_start
    ham_rate = ham_count / (t_ham_elapsed / 60) if t_ham_elapsed > 0 else 0
    print(f"[OK] 햄 합계: {ham_count}건  (소요 {t_ham_elapsed:.1f}초, 약 {ham_rate:.1f}건/분)")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_jsonl(rows, output_path)
    print(f"[OK] 저장: {output_path} (총 {len(rows)}건)")

    # train/val 분할 (ExaOne LoRA·파이프라인용)
    out_dir = output_path.parent
    train_path = out_dir / "train.jsonl"
    val_path = out_dir / "val.jsonl"
    shuffled = list(rows)
    random.shuffle(shuffled)
    split = max(1, int(len(shuffled) * 0.9))
    train_rows, val_rows = shuffled[:split], shuffled[split:]
    save_jsonl(train_rows, train_path)
    save_jsonl(val_rows, val_path)
    print(f"[OK] train/val 분할: {train_path.name} {len(train_rows)}건, {val_path.name} {len(val_rows)}건")

    t_total = time.perf_counter() - t_start
    print()
    print("=" * 60)
    print("[완료] 최종 요약")
    print("=" * 60)
    print(f"  총 데이터: {len(rows)}건 (스팸 {spam_ok}건, 햄 {ham_count}건)")
    print(f"  train: {len(train_rows)}건  |  val: {len(val_rows)}건")
    print(f"  총 소요 시간: {t_total:.1f}초 ({t_total / 60:.1f}분)")
    print(f"  BP 목표: 총 {BP_TOTAL}건 (스팸 {BP_SPAM_TOTAL} + 햄 {BP_HAM_TOTAL}) → 검증 정확도 82~88%% 기대")
    print("=" * 60)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="ExaOne으로 한국어 스팸 15종/햄 합성 SFT JSONL (정확도 82~88%%+ 목표)")
    parser.add_argument("--per-category", type=int, default=50, help="스팸 유형당 생성 건수 (기본 50)")
    parser.add_argument("--ham", type=int, default=300, help="햄 총 건수 (기본 300)")
    parser.add_argument("--full", action="store_true", help="2,000건 (스팸 1,200 + 햄 800)")
    parser.add_argument("--large", action="store_true", help="3,600건 (스팸 2,400 + 햄 1,200)")
    parser.add_argument("--max", action="store_true", dest="max_preset", help="5,000건 (스팸 3,000 + 햄 2,000)")
    parser.add_argument("--output", type=str, default=None, help="출력 JSONL 경로 (기본: data/spam/sft/exaone_synthetic.jsonl)")
    parser.add_argument("--no-references", action="store_true", help="참고 데이터 생략 (기본은 3곳 참고 데이터 사용)")
    parser.add_argument("--fast", action="store_true", help="품질 유지하면서 속도 우선 (temperature 0.75, few-shot 축소)")
    args = parser.parse_args()

    if args.max_preset:
        preset = PRESETS["max"]
    elif args.large:
        preset = PRESETS["large"]
    elif args.full:
        preset = PRESETS["full"]
    else:
        preset = None

    per_category = preset["per_category"] if preset else args.per_category
    ham_total = preset["ham_total"] if preset else args.ham

    output_path = Path(args.output) if args.output else None
    run(
        per_category=per_category,
        ham_total=ham_total,
        output_path=output_path,
        fetch_references=not args.no_references,
        fast_mode=args.fast,
    )
    print("완료.")


if __name__ == "__main__":
    main()
