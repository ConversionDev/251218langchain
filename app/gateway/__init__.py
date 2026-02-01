"""게이트웨이: CORS·라우트 등록 등 진입부 설정."""

from .middleware import add_cors_middleware
from api.routers.register_router import register_routes  # noqa: E402

__all__ = ["add_cors_middleware", "register_routes"]
