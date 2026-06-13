"""감사 로그 유스케이스 — entity_type 파라미터화로 Employee/Mail/Disclosure 공용."""

import logging
from typing import Any, Dict, Optional

from fastapi import Request
from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from domain.hub.repositories.audit_log_repository import create_log as repo_create_audit_log  # type: ignore

logger = logging.getLogger(__name__)


def _resolve_actor(request: Request) -> str:
    actor = (request.headers.get("x-actor") or "").strip()
    return actor if actor else "system"


def write_audit_log(
    db: Session,
    *,
    request: Request,
    entity_type: str,
    entity_id: str,
    action: str,
    before_data: Optional[Dict[str, Any]] = None,
    after_data: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
) -> None:
    try:
        repo_create_audit_log(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=_resolve_actor(request),
            reason=reason,
            before_data=before_data,
            after_data=after_data,
        )
    except Exception as e:
        logger.warning("감사로그 저장 실패 entity_type=%s action=%s entity_id=%s err=%s", entity_type, action, entity_id, e)
