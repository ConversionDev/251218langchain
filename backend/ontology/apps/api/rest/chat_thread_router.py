"""LangGraph 스레드 관리 API.

GET    /agent/threads/{thread_id}/history  대화 기록 조회
DELETE /agent/threads/{thread_id}          대화 기록 삭제
"""

from typing import Any, Dict

from fastapi import APIRouter

from application.chat.chat_service import ChatService  # type: ignore

router = APIRouter(tags=["LangGraph Agent"])


@router.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str) -> Dict[str, Any]:
    """스레드 대화 기록 조회."""
    history = ChatService().get_thread_history(thread_id)
    return {"thread_id": thread_id, "messages": history, "message_count": len(history)}


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str) -> Dict[str, Any]:
    """스레드 대화 기록 삭제."""
    if ChatService().clear_thread(thread_id):
        return {"status": "deleted", "thread_id": thread_id}
    return {
        "status": "not_found",
        "thread_id": thread_id,
        "message": "스레드를 찾을 수 없거나 이미 삭제되었습니다.",
    }
