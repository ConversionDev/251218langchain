"""
게이트웨이 라우트 등록.

역할:
- /api 하위 REST 라우터 등록 (chat, email, soccer)
- /mcp 하위 FastMCP 중앙 허브 마운트
- /internal 하위 hub/mcp Llama·ExaOne·Soccer HTTP 서비스 (spokes가 호출)
- /static/clustering: 클러스터 시각화 HTML (데이터 지도)
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles


def register_routes(
    app: FastAPI,
    mcp_app,
    *,
    chat_router,
    disclosure_router,
    document_router,
    email_router,
    employee_router,
    resume_router,
    soccer_router,
) -> None:
    """REST 라우터와 MCP 앱을 앱에 등록합니다."""
    # Fast MCP 통일: /mcp/health + /mcp/server 한 앱으로 마운트
    app.mount("/mcp", mcp_app)

    # Chat MCP / Chat Spoke 동일 프로세스 마운트 (기본 설정으로 9011/9012 없이 동작)
    from domain.spokes.chat.mcp.chat_server import (  # type: ignore
        get_chat_mcp_http_app,
        get_chat_spoke_http_app,
    )
    app.mount("/internal/mcp/chat", get_chat_mcp_http_app())
    app.mount("/internal/mcp/chat-spoke", get_chat_spoke_http_app())

    # 통합 API: prefix /api 로 일원화
    app.include_router(chat_router, prefix="/api")  # /api/agent/...
    app.include_router(disclosure_router, prefix="/api")  # /api/disclosure/...
    app.include_router(document_router, prefix="/api")  # /api/document/...
    app.include_router(email_router, prefix="/api")  # /api/mail/...
    app.include_router(employee_router, prefix="/api")  # /api/employees
    app.include_router(resume_router, prefix="/api")  # /api/resume/...
    app.include_router(soccer_router, prefix="/api")  # /api/soccer/...

    # Hub MCP: Llama·ExaOne 호출 수신 (spokes가 HTTP로 호출)
    from api.routers.hub_llm_router import router as hub_llm_router  # type: ignore
    from api.routers.soccer_router import internal_soccer_router  # type: ignore

    app.include_router(hub_llm_router)
    app.include_router(internal_soccer_router)

    # 클러스터 시각화 HTML (데이터 지도): iframe 삽입 허용 헤더로 서빙
    from core.paths import get_clustering_dir  # type: ignore
    clustering_dir = get_clustering_dir()
    map_path = clustering_dir / "competency_map.html"

    @app.get("/api/clustering/map")
    async def serve_clustering_map():
        """데이터 지도 HTML. iframe에서 보이도록 frame-ancestors 허용."""
        if not map_path.exists():
            raise HTTPException(status_code=404, detail="competency_map.html not found. Run run_competency_visualization first.")
        body = map_path.read_bytes()
        return Response(
            content=body,
            media_type="text/html; charset=utf-8",
            headers={"Content-Security-Policy": "frame-ancestors *"},
        )

    if clustering_dir.exists():
        app.mount("/static/clustering", StaticFiles(directory=str(clustering_dir)), name="clustering_static")
