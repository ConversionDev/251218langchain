"""LangGraph 스레드 관리 API.

GET    /agent/threads/{thread_id}/history  대화 기록 조회
DELETE /agent/threads/{thread_id}          대화 기록 삭제
"""

import importlib
import sys
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["LangGraph Agent"])


def _get_chat_orchestrator() -> Any:
    """chat_orchestrator 모듈을 반환. 이미 로드된 경우 sys.modules 재사용."""
    key = "domain.hub.orchestrators.chat_orchestrator"
    if key in sys.modules:
        return sys.modules[key]
    return importlib.import_module(key)


@router.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str) -> Dict[str, Any]:
    """스레드 대화 기록 조회."""
    module = _get_chat_orchestrator()
    messages = module.get_thread_history(thread_id)
    history = []
    for msg in messages:
        msg_type = type(msg).__name__
        if msg_type == "HumanMessage":
            role = "user"
        elif msg_type == "AIMessage":
            role = "assistant"
        elif msg_type == "SystemMessage":
            role = "system"
        else:
            role = "tool"
        history.append({
            "role": role,
            "content": str(msg.content) if hasattr(msg, "content") else str(msg),
            "type": msg_type,
        })
    return {"thread_id": thread_id, "messages": history, "message_count": len(history)}


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str) -> Dict[str, Any]:
    """스레드 대화 기록 삭제."""
    module = _get_chat_orchestrator()
    success = module.clear_thread_history(thread_id)
    if success:
        return {"status": "deleted", "thread_id": thread_id}
    return {
        "status": "not_found",
        "thread_id": thread_id,
        "message": "스레드를 찾을 수 없거나 이미 삭제되었습니다.",
    }
