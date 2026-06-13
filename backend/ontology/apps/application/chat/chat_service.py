"""채팅 유스케이스 — LangGraph 오케스트레이터 위임."""

import importlib
import sys
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageItem(BaseModel):
    """채팅 히스토리 메시지 1건."""

    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")


def _to_lc_messages(chat_history: Optional[List[MessageItem]]) -> Optional[List[Any]]:
    """MessageItem 리스트 → LangChain 메시지 리스트 변환."""
    if not chat_history:
        return None
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # type: ignore

    result = []
    for msg in chat_history:
        if msg.role == "user":
            result.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            result.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            result.append(SystemMessage(content=msg.content))
    return result


class ChatService:
    """LangGraph 오케스트레이터·LLM 팩토리 위임. 직접 비즈니스 로직 없는 얇은 퍼사드."""

    @staticmethod
    def _get_orchestrator() -> Any:
        """sys.modules 캐시 우선, 없으면 importlib 로드."""
        key = "infrastructure.orchestration.chat_orchestrator"
        if key in sys.modules:
            return sys.modules[key]
        return importlib.import_module(key)

    @staticmethod
    def _get_orchestrators_pkg() -> Any:
        key = "infrastructure.orchestration"
        if key in sys.modules:
            return sys.modules[key]
        return importlib.import_module(key)

    # ------------------------------------------------------------------ 스트리밍

    def stream(
        self,
        user_text: str,
        provider: Optional[str],
        system_prompt: Optional[str],
        chat_history: Optional[List[MessageItem]],
        thread_id: Optional[str],
        images: Optional[List[str]],
    ) -> AsyncIterator[Any]:
        """run_agent_stream 반환. chat_history를 LangChain 메시지로 변환."""
        from infrastructure.llm import get_provider_name  # type: ignore

        resolved_provider = provider or get_provider_name()
        lc_history = _to_lc_messages(chat_history)

        return self._get_orchestrator().run_agent_stream(
            user_text=user_text,
            provider=resolved_provider,
            system_prompt=system_prompt,
            chat_history=lc_history,
            thread_id=thread_id,
            images=images,
        )

    # ------------------------------------------------------------------ 메타

    def list_providers(self) -> List[Dict[str, Any]]:
        from infrastructure.llm import get_provider_name, list_providers, supports_tool_calling  # type: ignore

        current = get_provider_name()
        return [
            {
                "name": name,
                "supports_tool_calling": supports_tool_calling(name),
                "is_current": name == current,
            }
            for name in list_providers()
        ]

    def list_tools(self) -> List[Dict[str, str]]:
        tools = self._get_orchestrators_pkg().TOOLS
        return [{"name": t.name, "description": t.description} for t in tools]

    def get_health(self) -> Dict[str, Any]:
        from infrastructure.llm import get_provider_name, list_providers, supports_tool_calling  # type: ignore

        try:
            provider = get_provider_name()
            return {
                "status": "healthy",
                "current_provider": provider,
                "supports_tool_calling": supports_tool_calling(provider),
                "available_providers": list_providers(),
                "checkpointer_enabled": True,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ------------------------------------------------------------------ 스레드

    def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        messages = self._get_orchestrator().get_thread_history(thread_id)
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
        return history

    def clear_thread(self, thread_id: str) -> bool:
        return self._get_orchestrator().clear_thread_history(thread_id)
