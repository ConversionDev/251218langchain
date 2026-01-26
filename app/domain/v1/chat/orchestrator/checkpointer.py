"""
LangGraph 체크포인터

대화 상태를 관리하는 메모리 기반 체크포인터.
"""

from typing import Any, Dict, List, Optional

from langgraph.checkpoint.memory import MemorySaver

# 전역 체크포인터 인스턴스
_checkpointer: Optional[MemorySaver] = None


def get_checkpointer() -> MemorySaver:
    """체크포인터 인스턴스를 반환합니다.

    Returns:
        MemorySaver 인스턴스 (싱글톤)
    """
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def get_thread_config(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """스레드 설정을 반환합니다.

    Args:
        thread_id: 대화 스레드 ID

    Returns:
        LangGraph 설정 딕셔너리
    """
    if thread_id:
        return {"configurable": {"thread_id": thread_id}}
    return {}
