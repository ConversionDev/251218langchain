"""
통합 API 라우터

채팅, 이메일, 축구 등 도메인별 API를 한 곳에서 관리합니다.
"""

from .activity_router import router as activity_router
from .audit_router import router as audit_router
from .chat_router import router as chat_router
from .disclosure_router import router as disclosure_router
from .document_router import router as document_router
from .email_router import email_router
from .employee_router import router as employee_router
from .resume_router import router as resume_router
from .soccer_router import router as soccer_router

__all__ = [
    "activity_router",
    "audit_router",
    "chat_router",
    "disclosure_router",
    "document_router",
    "email_router",
    "employee_router",
    "resume_router",
    "soccer_router",
    "register_router",
]
