"""MCP 인바운드 어댑터 (domain/hub/mcp 에서 이동, Phase 5b).

- central_control_server: FastMCP 중앙 허브 서버. fastapi_server lifespan에서 get_http_app()로 마운트.
아웃바운드 클라이언트·유틸은 infrastructure/mcp 로 분리.
"""
