"""앱 부트스트랩: FastAPI 앱 조립(CORS 미들웨어·라우트 등록) 진입부 설정.

※ Spring API Gateway(backend/gateway, OAuth/8080)와는 무관한 FastAPI 내부 wiring 모듈.
"""

from .middleware import add_cors_middleware
from api.routers.register_router import register_routes  # noqa: E402

__all__ = ["add_cors_middleware", "register_routes"]
