"""
MCP (Model Control Protocol) Router

모델 제어 관련 API 엔드포인트를 제공합니다.
참고: 스팸 감지 API는 /mail/filter로 이동되었습니다.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["MCP"])


# =============================================================================
# 엔드포인트
# =============================================================================


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트."""
    return {"status": "ok", "service": "MCP Router"}
