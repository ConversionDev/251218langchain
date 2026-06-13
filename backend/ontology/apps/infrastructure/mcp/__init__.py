"""MCP 아웃바운드 어댑터 + 공유 유틸 (domain/hub/mcp 에서 이동, Phase 5b).

- http_client: hub HTTP 엔드포인트 호출 클라이언트 (exaone_generate, chat_call, spam_call 등)
- mcp_utils: call_tool 결과 파싱·MCP URL 빌더 (Hub·Spoke 공용)
인바운드 MCP 서버(central_control_server)는 api/mcp 로 분리.
"""
