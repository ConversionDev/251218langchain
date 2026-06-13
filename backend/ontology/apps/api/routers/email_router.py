"""이메일 라우터.

메일함(받은/보낸/임시보관/휴지통) CRUD, 전송, 스팸 필터링, 메일 분류(성과/5대 역량) API.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from application.mail.mail_service import MailService  # type: ignore
from core.database import SessionLocal, get_db  # type: ignore
from domain.hub.mail import MailgunProvider  # type: ignore
from infrastructure.orchestration import run_spam_detection  # type: ignore
from domain.models import EmailRequest, EmailResponse  # type: ignore
from domain.models import ExaoneResult, LLaMAResult  # type: ignore

email_router = APIRouter(prefix="/mail", tags=["mail"])

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 메일 분류 (성과 / 5대 역량)
# ---------------------------------------------------------------------------

class ClassifyEmailRequest(BaseModel):
    subject: str = Field("", description="메일 제목")
    body: Optional[str] = Field(None, description="메일 본문")
    employeeId: str = Field(..., description="발신 직원 ID (성과 기록 시 사용)")
    period: Optional[str] = Field(None, description="분기 (예: 2025-Q1). 없으면 현재 분기")


class ClassifyEmailResponse(BaseModel):
    classification: Dict[str, Any] = Field(..., description="is_performance, competency_labels")
    performance_record_id: Optional[str] = Field(None, description="성과로 기록한 경우 레코드 ID")
    raw_response: str = Field("", description="모델 원시 응답 일부 (디버깅용)")


@email_router.post("/classify", response_model=ClassifyEmailResponse)
def classify_email(
    payload: ClassifyEmailRequest,
    db: Session = Depends(get_db),
) -> ClassifyEmailResponse:
    """메일 1건을 분류: 성과 관련·5대 역량 동시 판단 후, 성과로 판단되면 performance_records에 자동 기록."""
    try:
        result = MailService(db).classify(
            subject=payload.subject,
            body=payload.body,
            employee_id=payload.employeeId,
            period=payload.period,
        )
        return ClassifyEmailResponse(
            classification=result["classification"],
            performance_record_id=result.get("performance_record_id"),
            raw_response=result.get("raw_response", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메일 분류 중 오류: {str(e)}")


# ---------------------------------------------------------------------------
# 메일함 공통
# ---------------------------------------------------------------------------

class MailRecipientBody(BaseModel):
    id: str = Field(..., description="주소록 ID (직원 또는 internal_address)")
    displayName: str = Field("", description="표시명")
    email: Optional[str] = Field(None, description="이메일")


class SendMailBody(BaseModel):
    senderEmployeeId: str = Field(..., description="발신 직원 ID")
    to: MailRecipientBody = Field(..., description="수신자 (주소록 1건)")
    subject: str = Field("", description="제목")
    body: Optional[str] = Field(None, description="본문")


class DraftMailBody(BaseModel):
    ownerEmployeeId: str = Field(..., description="메일함 소유자(직원 ID)")
    id: Optional[str] = Field(None, description="기존 draft id (수정 시)")
    to: Optional[MailRecipientBody] = Field(None, description="수신자")
    subject: str = Field("", description="제목")
    body: Optional[str] = Field(None, description="본문")


@email_router.get("", response_model=List[Dict[str, Any]])
def list_mail(
    folder: str = Query(..., description="inbox | sent | draft | trash"),
    ownerEmployeeId: str = Query(..., description="메일함 소유자(직원 ID)"),
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """폴더별 메일 목록."""
    if folder not in ("inbox", "sent", "draft", "trash", "spam"):
        raise HTTPException(status_code=400, detail="folder must be inbox, sent, draft, trash, or spam")
    return MailService(db).list_folder(folder, ownerEmployeeId, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# 수신 (Webhook) — Store-then-Process
# ---------------------------------------------------------------------------

class ReceiveMailBody(BaseModel):
    to_email: str = Field(..., min_length=1, description="수신자 To 주소")
    from_display: str = Field("", description="발신자 표시명")
    from_email: Optional[str] = Field(None, description="발신자 이메일")
    subject: str = Field("", description="제목")
    body: Optional[str] = Field(None, description="본문")
    message_id: Optional[str] = Field(None, description="Message-ID (external_id). 중복 시 200 OK 멱등")
    received_at: Optional[str] = Field(None, description="수신 시각 ISO8601. 없으면 now()")


@email_router.post("/receive")
def receive_mail_api(
    body: ReceiveMailBody,
    db: Session = Depends(get_db),
):
    """수신 메일 1건 저장 (Store-then-Process). external_id 중복 시 200 OK. Resolver 실패 시 REJECTED 저장 후 200."""
    received_at = datetime.now(timezone.utc)
    if body.received_at and body.received_at.strip():
        try:
            received_at = datetime.fromisoformat(body.received_at.replace("Z", "+00:00"))
        except ValueError:
            pass
    record, folder, status_code, already = MailService(db).receive_inbound(
        to_email=body.to_email.strip(),
        from_display=body.from_display or "",
        from_email=body.from_email,
        subject=body.subject or "",
        body=body.body,
        message_id=body.message_id,
        received_at=received_at,
    )
    return JSONResponse(
        status_code=status_code,
        content={"status": "received", "mail": record, "folder": folder, "already_stored": already},
    )


def _save_mailgun_inbound_background(
    to_email: str,
    from_display: str,
    from_email: Optional[str],
    subject: str,
    body: Optional[str],
    message_id: Optional[str],
    received_at: datetime,
) -> None:
    """백그라운드에서 메일건 수신 1건 저장. 전용 세션 사용."""
    db = SessionLocal()
    try:
        MailService(db).receive_inbound(
            to_email=to_email,
            from_display=from_display,
            from_email=from_email,
            subject=subject,
            body=body,
            message_id=message_id,
            received_at=received_at,
        )
        db.commit()
    except Exception as e:
        logger.exception("Mailgun webhook background save failed: %s", e)
        db.rollback()
    finally:
        db.close()


@email_router.post("/receive/webhook/mailgun")
async def receive_mailgun_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Mailgun Webhook. 검증 후 즉시 200, 저장은 백그라운드."""
    form = await request.form()
    payload = {}
    for k, v in form.items():
        if hasattr(v, "read"):
            continue
        if isinstance(v, bytes):
            payload[k] = v.decode("utf-8", errors="replace")
        else:
            payload[k] = v
    try:
        normalized = MailgunProvider().parse_and_verify(payload)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    received_at = normalized.received_at or datetime.now(timezone.utc)
    background_tasks.add_task(
        _save_mailgun_inbound_background,
        to_email=normalized.to_email,
        from_display=normalized.from_display or "",
        from_email=normalized.from_email,
        subject=normalized.subject or "",
        body=normalized.body,
        message_id=normalized.message_id,
        received_at=received_at,
    )
    return JSONResponse(
        status_code=200,
        content={"status": "accepted", "message": "Webhook received; storage in progress."},
    )


# ---------------------------------------------------------------------------
# 메일 단건 조회·수정·재처리
# ---------------------------------------------------------------------------

@email_router.post("/{mail_id}/retry", response_model=Dict[str, Any])
def retry_mail_processing(
    mail_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """FAILED 메일을 PENDING으로 되돌려 워커가 재분류하도록 함. retry_count <= 3 인 경우만."""
    try:
        return MailService(db).retry_failed(mail_id)
    except ValueError as e:
        msg = str(e)
        status = 404 if "not found" in msg.lower() else 400
        raise HTTPException(status_code=status, detail=msg)


@email_router.get("/{mail_id}", response_model=Dict[str, Any])
def get_mail(
    mail_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 단건 조회."""
    item = MailService(db).get(mail_id)
    if not item:
        raise HTTPException(status_code=404, detail="Mail not found")
    return item


@email_router.post("/send", response_model=Dict[str, Any])
def send_mail_api(
    body: SendMailBody,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 발송: 직원/사내 주소면 DB만(보낸함+받은함), 외부 주소면 메일건 API 발송 후 보낸함 저장."""
    return MailService(db).send(
        sender_employee_id=body.senderEmployeeId,
        to_id=body.to.id,
        to_email=(body.to.email or "").strip(),
        to_display=body.to.displayName or body.to.id,
        subject=body.subject or "",
        body=body.body,
    )


@email_router.post("/draft", response_model=Dict[str, Any])
def save_draft(
    body: DraftMailBody,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """임시보관 저장. id 있으면 수정, 없으면 신규."""
    return MailService(db).save_draft(
        owner_employee_id=body.ownerEmployeeId,
        draft_id=body.id,
        to_id=body.to.id if body.to else None,
        to_display=body.to.displayName if body.to else None,
        to_email=body.to.email if body.to else None,
        subject=body.subject or "",
        body=body.body,
    )


@email_router.put("/{mail_id}", response_model=Dict[str, Any])
def update_mail(
    mail_id: str,
    isStarred: Optional[bool] = Query(None),
    isUnread: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 수정 (중요/읽음 플래그 등)."""
    svc = MailService(db)
    item = svc.get(mail_id)
    if not item:
        raise HTTPException(status_code=404, detail="Mail not found")
    updated = svc.update_flags(mail_id, is_starred=isStarred, is_unread=isUnread)
    return updated or item


@email_router.delete("/{mail_id}", status_code=200)
def delete_mail(
    mail_id: str,
    permanent: bool = Query(False, description="true면 물리 삭제(복구 불가)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 삭제. 기본은 휴지통으로 이동, permanent=true면 물리 삭제."""
    try:
        return MailService(db).delete(mail_id, permanent=permanent)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# 스팸 필터
# ---------------------------------------------------------------------------

@email_router.post("/filter", response_model=EmailResponse)
async def spam_mail_filter(email: EmailRequest):
    try:
        result = run_spam_detection(email.email_metadata.model_dump())
        routing_path = result.get("routing_path", "")
        routing_strategy = result.get("routing_strategy", "policy")

        llama_result_dict = result.get("llama_result", {})
        exaone_result_dict = result.get("exaone_result")
        llama_result = (
            LLaMAResult(**llama_result_dict)
            if llama_result_dict
            else LLaMAResult(spam_prob=0.5, confidence="low", label="UNCERTAIN")
        )
        exaone_result = ExaoneResult(**exaone_result_dict) if exaone_result_dict else None

        return EmailResponse(
            action=result.get("action", "ask_user_confirm"),
            routing_strategy=routing_strategy,
            reason_codes=result.get("reason_codes", []),
            user_message=result.get("user_message", "처리 완료"),
            confidence=result.get("confidence", "medium"),
            spam_prob=result.get("spam_prob", 0.5),
            llama_result=llama_result,
            exaone_result=exaone_result,
            routing_path=routing_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스팸 필터링 중 오류가 발생했습니다: {str(e)}")
