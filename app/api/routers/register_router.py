"""
게이트웨이 라우트 등록.

역할:
- /api 하위 REST 라우터 등록 (chat, email, soccer)
- /mcp 하위 FastMCP 중앙 허브 마운트
- /internal 하위 hub/mcp Llama·ExaOne·Soccer HTTP 서비스 (spokes가 호출)
"""

from fastapi import FastAPI


def register_routes(
    app: FastAPI,
    mcp_app,
    *,
    chat_router,
    disclosure_router,
    email_router,
    soccer_router,
) -> None:
    """REST 라우터와 MCP 앱을 앱에 등록합니다."""
    # Fast MCP 통일: /mcp/health + /mcp/server 한 앱으로 마운트
    app.mount("/mcp", mcp_app)

    # 통합 API: prefix /api 로 일원화
    app.include_router(chat_router, prefix="/api")  # /api/agent/...
    app.include_router(disclosure_router, prefix="/api")  # /api/disclosure/...
    app.include_router(email_router, prefix="/api")  # /api/mail/...
    app.include_router(soccer_router, prefix="/api")  # /api/soccer/...

    # Hub MCP: Llama·ExaOne 호출 수신 (spokes가 HTTP로 호출)
    from api.routers.hub_llm_router import router as hub_llm_router  # type: ignore
    from api.routers.soccer_router import internal_soccer_router  # type: ignore

    app.include_router(hub_llm_router)
    app.include_router(internal_soccer_router)
