# -*- coding: utf-8 -*-
"""수신→분류 기능 점검용 메일 주입 스크립트.

워커(`python -m workers.mail_pending`)가 떠 있는 상태에서 별도 터미널로 실행하면,
스팸/정상 샘플을 PENDING으로 DB에 넣는다. 워커가 이를 집어 classify_spam → folder(spam/inbox)를 정한다.

사용 (apps 디렉터리에서):
  python -m scripts.test_mail_flow            # 등록된 직원 1명을 수신자로 자동 선택
  python -m scripts.test_mail_flow me@corp.com  # 특정 수신자 지정(직원/주소록에 있어야 함)

검증: 실행 후 워커 터미널 로그에서 "메일 처리 완료: ... folder=spam / folder=inbox" 확인.
주의: 수신자가 employees.email(또는 internal_addresses)과 일치해야 PENDING 저장됨. 아니면 REJECTED → 분류 안 됨.
"""

import sys
from datetime import datetime, timezone

# Windows 콘솔(cp949)에서 한글/기호 출력 깨짐·크래시 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

from core.database import SessionLocal  # type: ignore
from application.mail.mail_service import MailService  # type: ignore
from infrastructure.persistence.models.employee_orm import Employee  # type: ignore

# (label, subject, sender, body) — 라마 스팸 어댑터가 한글 내용을 보고 판정
SAMPLES = [
    (
        "스팸(기대: spam)",
        "[광고] 무료 대출 100% 당첨! 지금 즉시 클릭",
        "promo@cheap-loan.ru",
        "축하합니다! 귀하는 무이자 대출 대상자로 선정되셨습니다. 지금 클릭: http://bit.ly/win-now 한정 이벤트!",
    ),
    (
        "정상(기대: inbox)",
        "내일 오후 3시 팀 회의 일정 공유",
        "minji.kim@corp.example.com",
        "안녕하세요. 내일 오후 3시 2층 회의실에서 분기 리뷰 미팅 진행합니다. 자료 미리 확인 부탁드립니다.",
    ),
]


def _pick_recipient(db) -> str:
    """argv로 받은 수신자, 없으면 등록된 직원 중 이메일 있는 첫 명을 자동 선택."""
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    emp = (
        db.query(Employee)
        .filter(Employee.email.isnot(None), Employee.email != "")
        .first()
    )
    if not emp:
        raise SystemExit(
            "등록된 직원 이메일이 없습니다. 수신자를 인자로 지정하세요: "
            "python -m scripts.test_mail_flow you@corp.com"
        )
    return emp.email


def main() -> None:
    db = SessionLocal()
    try:
        recipient = _pick_recipient(db)
        print(f"수신자(메일함 소유자) = {recipient}\n")
        for i, (label, subject, sender, body) in enumerate(SAMPLES):
            record, folder, code, already = MailService(db).receive_inbound(
                to_email=recipient,
                from_display=sender.split("@")[0],
                from_email=sender,
                subject=subject,
                body=body,
                message_id=f"<test-{label}-{datetime.now(timezone.utc).timestamp()}-{i}>",
                received_at=datetime.now(timezone.utc),
            )
            db.commit()
            ai_status = record.get("aiStatus")  # 반환 dict는 camelCase 키
            ok = "[OK]  " if (ai_status == "PENDING" and folder == "inbox") else "[WARN]"
            print(
                f"{ok} {label}\n"
                f"    저장폴더={folder} ai_status={ai_status} 중복저장={already} (code={code})\n"
                f"    -> ai_status=PENDING 이어야 워커가 집어감. REJECTED/None이면 수신자 미등록.\n"
            )
        print(
            "이제 워커 터미널 로그를 보세요:\n"
            '  "메일 처리 완료: id=... folder=spam"  ← 스팸 샘플\n'
            '  "메일 처리 완료: id=... folder=inbox" ← 정상 샘플\n'
            "둘 다 기대대로면 수신→저장→분류→폴더배치 기능 정상."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
