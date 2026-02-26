"""이메일 라우터.

메일함(받은/보낸/임시보관/휴지통) CRUD, 전송, 스팸 필터링, 메일 분류(성과/5대 역량) API.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from core.database import get_db  # type: ignore
from domain.hub.orchestrators import run_email_classify_and_record, run_spam_detection  # type: ignore
from domain.hub.repositories.mail_item_repository import (  # type: ignore
    create as mail_item_create,
    get_by_id as mail_item_get,
    list_by_folder as mail_item_list,
    move_to_trash as mail_item_trash,
    update as mail_item_update,
)
from domain.models import EmailRequest, EmailResponse  # type: ignore

email_router = APIRouter(prefix="/mail", tags=["mail"])


# ---------------------------------------------------------------------------
# 메일 분류 (성과 / 5대 역량) 요청·응답
# ---------------------------------------------------------------------------


class ClassifyEmailRequest(BaseModel):
    """메일 1건 분류 요청. 학습된 모델이 성과·5대 역량 동시 판단."""

    subject: str = Field("", description="메일 제목")
    body: Optional[str] = Field(None, description="메일 본문")
    employeeId: str = Field(..., description="발신 직원 ID (성과 기록 시 사용)")
    period: Optional[str] = Field(None, description="분기 (예: 2025-Q1). 없으면 현재 분기")


class ClassifyEmailResponse(BaseModel):
    """메일 분류 결과."""

    classification: Dict[str, Any] = Field(..., description="is_performance, competency_labels")
    performance_record_id: Optional[str] = Field(None, description="성과로 기록한 경우 레코드 ID")
    raw_response: str = Field("", description="모델 원시 응답 일부 (디버깅용)")


@email_router.post("/classify", response_model=ClassifyEmailResponse)
def classify_email(
    payload: ClassifyEmailRequest,
    db: Session = Depends(get_db),
) -> ClassifyEmailResponse:
    """메일 1건을 분류: 학습된 모델(ExaOne)이 성과 관련·5대 역량 관련 동시 판단 후, 성과로 판단되면 performance_records에 자동 기록."""
    try:
        result = run_email_classify_and_record(
            db,
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
# 메일함 공통 (mail_items: 받은/보낸/임시보관/휴지통)
# ---------------------------------------------------------------------------

class MailRecipientBody(BaseModel):
    """수신자 정보 (주소록 1건)."""
    id: str = Field(..., description="주소록 ID (직원 또는 internal_address)")
    displayName: str = Field("", description="표시명")
    email: Optional[str] = Field(None, description="이메일")


class SendMailBody(BaseModel):
    """메일 발송 요청. 저장 후 folder=sent."""
    senderEmployeeId: str = Field(..., description="발신 직원 ID")
    to: MailRecipientBody = Field(..., description="수신자 (주소록 1건)")
    subject: str = Field("", description="제목")
    body: Optional[str] = Field(None, description="본문")


class DraftMailBody(BaseModel):
    """임시보관 저장 요청."""
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
    """폴더별 메일 목록. 받은/보낸/임시보관/휴지통 공통."""
    if folder not in ("inbox", "sent", "draft", "trash"):
        raise HTTPException(status_code=400, detail="folder must be inbox, sent, draft, or trash")
    return mail_item_list(db, folder=folder, owner_employee_id=ownerEmployeeId, limit=limit, offset=offset)


@email_router.get("/{mail_id}", response_model=Dict[str, Any])
def get_mail(
    mail_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 단건 조회."""
    item = mail_item_get(db, mail_id)
    if not item:
        raise HTTPException(status_code=404, detail="Mail not found")
    return item


@email_router.post("/send", response_model=Dict[str, Any])
def send_mail_api(
    body: SendMailBody,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 발송 후 mail_items에 저장 (folder=sent)."""
    now = datetime.now(timezone.utc)
    record = mail_item_create(
        db,
        folder="sent",
        owner_employee_id=body.senderEmployeeId,
        from_employee_id=body.senderEmployeeId,
        from_display="me",
        from_email=None,
        to_address_id=body.to.id,
        to_display=body.to.displayName or body.to.id,
        to_email=body.to.email,
        subject=body.subject or "",
        body=body.body,
        sent_at=now,
        is_starred=False,
        is_unread=False,
    )
    return {"status": "success", "mail": record}


@email_router.post("/draft", response_model=Dict[str, Any])
def save_draft(
    body: DraftMailBody,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """임시보관 저장. id 있으면 수정, 없으면 신규."""
    if body.id:
        row = mail_item_get(db, body.id)
        if row and row.get("folder") == "draft":
            updated = mail_item_update(
                db,
                body.id,
                subject=body.subject,
                body=body.body,
                to_display=body.to.displayName if body.to else None,
                to_email=body.to.email if body.to else None,
                to_address_id=body.to.id if body.to else None,
            )
            return {"status": "saved", "mail": updated}
    record = mail_item_create(
        db,
        folder="draft",
        owner_employee_id=body.ownerEmployeeId,
        from_display="me",
        to_address_id=body.to.id if body.to else None,
        to_display=body.to.displayName if body.to else None,
        to_email=body.to.email if body.to else None,
        subject=body.subject or "",
        body=body.body,
        sent_at=None,
        is_unread=True,
    )
    return {"status": "saved", "mail": record}


@email_router.put("/{mail_id}", response_model=Dict[str, Any])
def update_mail(
    mail_id: str,
    isStarred: Optional[bool] = Query(None),
    isUnread: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 수정 (중요/읽음 플래그 등)."""
    item = mail_item_get(db, mail_id)
    if not item:
        raise HTTPException(status_code=404, detail="Mail not found")
    updated = mail_item_update(db, mail_id, is_starred=isStarred, is_unread=isUnread)
    return updated or item


@email_router.delete("/{mail_id}", status_code=200)
def delete_mail(
    mail_id: str,
    permanent: bool = Query(False, description="true면 물리 삭제(복구 불가)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """메일 삭제. 기본은 휴지통으로 이동, permanent=true면 물리 삭제."""
    from domain.hub.repositories.mail_item_repository import delete_permanently  # type: ignore

    if permanent:
        if not delete_permanently(db, mail_id):
            raise HTTPException(status_code=404, detail="Mail not found")
        return {"status": "deleted"}
    item = mail_item_trash(db, mail_id)
    if not item:
        raise HTTPException(status_code=404, detail="Mail not found")
    return {"status": "moved_to_trash", "mail": item}


# ---------------------------------------------------------------------------
# 스팸 필터
# ---------------------------------------------------------------------------

@email_router.post("/filter", response_model=EmailResponse)
async def spam_mail_filter(email: EmailRequest):
    try:
        email_metadata = email.email_metadata.model_dump()
        result = run_spam_detection(email_metadata)
        routing_path = result.get("routing_path", "")
        routing_strategy = result.get("routing_strategy", "policy")
        from domain.models import ExaoneResult  # type: ignore
        from domain.models import LLaMAResult  # type: ignore

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
