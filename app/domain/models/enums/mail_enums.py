"""메일 도메인 Enum: 수신 상태·AI 처리 상태.

- status (MailReceiveStatus): 수신 도메인 상태 (RECEIVED | REJECTED)
- ai_status (AiStatus): AI 처리 상태 (PENDING | PROCESSING | SUCCESS | FAILED)
DB/마이그레이션에는 .value(문자열)로 저장. 코드에서는 Enum만 사용해 오타 방지.
"""

from enum import Enum


class AiStatus(str, Enum):
    """AI 처리 상태. 워커가 PENDING → PROCESSING → SUCCESS | FAILED."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class MailReceiveStatus(str, Enum):
    """수신 도메인 상태. Resolver 성공/실패."""

    RECEIVED = "RECEIVED"
    REJECTED = "REJECTED"
