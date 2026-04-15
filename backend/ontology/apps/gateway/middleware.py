"""
게이트웨이 미들웨어.

역할:
- CORS (진입부 허용). CORS_ORIGINS 환경 변수로 허용 도메인 제한 가능.
- (추후) 요청 정규화, 인증, Rate Limit 등
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings  # type: ignore


def add_cors_middleware(app: FastAPI) -> None:
    """CORS 미들웨어 등록. CORS_ORIGINS가 설정되면 해당 도메인만 허용, 없으면 * (전체 허용)."""
    settings = get_settings()
    if settings.cors_origins and settings.cors_origins.strip():
        origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    else:
        origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
