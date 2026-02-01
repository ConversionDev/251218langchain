"""
통합 API 라우터

채팅, 이메일, 축구 등 도메인별 API를 한 곳에서 관리합니다.
"""

from .chat_router import router as chat_router
from .email_router import email_router
from .soccer_router import router as soccer_router

__all__ = [
    "chat_router",
    "email_router",
    "soccer_router",
    "register_router"
]
