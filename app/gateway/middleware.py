"""
게이트웨이 미들웨어.

역할:
- CORS (진입부 허용)
- (추후) 요청 정규화, 인증, Rate Limit 등
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI) -> None:
    """CORS 미들웨어 등록. 모든 요청 진입부에 적용."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
