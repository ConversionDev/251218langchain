"""라우터 - API 엔드포인트."""

from .health import router as health_router

__all__ = ["health_router"]

