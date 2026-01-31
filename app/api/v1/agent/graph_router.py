"""LangGraph 에이전트 라우터.

LangGraph 기반 에이전트 API 엔드포인트를 제공합니다.
"""

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/agent", tags=["LangGraph Agent"])


# =============================================================================
# Request/Response 모델
# =============================================================================
class MessageItem(BaseModel):
    """대화 메시지 아이템."""

    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")


class AgentRequest(BaseModel):
    """에이전트 요청 모델."""

    message: str = Field(..., description="사용자 메시지")
    provider: Optional[str] = Field(
        None, description="LLM 제공자 (exaone, ollama). None이면 환경 변수 사용"
    )
    use_rag: bool = Field(True, description="RAG 사용 여부")
    system_prompt: Optional[str] = Field(None, description="커스텀 시스템 프롬프트")
    chat_history: Optional[List[MessageItem]] = Field(
        None, description="이전 대화 기록"
    )
    thread_id: Optional[str] = Field(
        None, description="대화 스레드 ID (checkpointer를 통한 상태 관리용)"
    )


class AgentResponse(BaseModel):
    """에이전트 응답 모델."""

    response: str = Field(..., description="에이전트 응답")
    provider: str = Field(..., description="사용된 LLM 제공자")
    used_rag: bool = Field(..., description="RAG 사용 여부")
    thread_id: Optional[str] = Field(None, description="사용된 대화 스레드 ID")
    semantic_action: Optional[str] = Field(
        None, description="시멘틱 분류 결과: BLOCK, RULE_BASED, POLICY_BASED"
    )


class ProviderInfo(BaseModel):
    """LLM 제공자 정보."""

    name: str
    supports_tool_calling: bool
    is_current: bool


# =============================================================================
# 엔드포인트
# =============================================================================
# 시멘틱 분류 시 BLOCK 응답 메시지
_BLOCK_MESSAGE = (
    "해당 질문은 서비스 범위 밖입니다. "
    "축구/선수/경기 관련 질문만 답변해 드립니다."
)


@router.post("/chat", response_model=AgentResponse)
async def agent_chat(request: AgentRequest):
    """LangGraph 에이전트와 대화합니다.

    Args:
        request: 에이전트 요청

    Returns:
        에이전트 응답
    """
    semantic_action: Optional[str] = None
    try:
        import importlib
        import sys

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        from domain.v1.hub.llm import get_provider_name  # type: ignore

        provider = request.provider or get_provider_name()

        # 시멘틱 분류: BLOCK이면 에이전트 호출 없이 고정 응답
        try:
            from domain.v1.hub.orchestrators import (
                classify,
                is_classifier_available,
            )
            if is_classifier_available():
                semantic_action = classify(request.message)
                msg_preview = (request.message[:80] + "…") if len(request.message) > 80 else request.message
                logger.info("[시멘틱 분류] 질문: %s → %s", msg_preview, semantic_action)
                if semantic_action == "BLOCK":
                    return AgentResponse(
                        response=_BLOCK_MESSAGE,
                        provider=provider,
                        used_rag=request.use_rag,
                        thread_id=request.thread_id,
                        semantic_action=semantic_action,
                    )
        except Exception:
            pass  # 분류 실패 시 기존 플로우 유지

        if "domain.v10.soccer.hub.orchestrators.chat_orchestrator" in sys.modules:
            graph_module = sys.modules["domain.v10.soccer.hub.orchestrators.chat_orchestrator"]
        else:
            graph_module = importlib.import_module(
                "domain.v10.soccer.hub.orchestrators.chat_orchestrator"
            )
        run_agent = graph_module.run_agent

        # 대화 기록 변환
        chat_history = None
        if request.chat_history:
            chat_history = []
            for msg in request.chat_history:
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    chat_history.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    chat_history.append(SystemMessage(content=msg.content))

        # 에이전트 실행 (시멘틱 분류 결과 전달 → 답변과 UI 태그 일치)
        response = run_agent(
            user_text=request.message,
            provider=provider,
            use_rag=request.use_rag,
            system_prompt=request.system_prompt,
            chat_history=chat_history,
            thread_id=request.thread_id,
            semantic_action=semantic_action,
        )

        return AgentResponse(
            response=response,
            provider=provider,
            used_rag=request.use_rag,
            thread_id=request.thread_id,
            semantic_action=semantic_action,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에이전트 실행 오류: {str(e)}")


@router.post("/chat/stream")
async def agent_chat_stream(request: AgentRequest):
    """LangGraph 에이전트와 스트리밍 대화합니다.

    Args:
        request: 에이전트 요청

    Returns:
        SSE 스트리밍 응답
    """
    try:
        import importlib
        import sys

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        from domain.v1.hub.llm import get_provider_name  # type: ignore

        provider = request.provider or get_provider_name()

        # 시멘틱 분류: BLOCK이면 스트리밍 없이 고정 메시지 한 번 전송 후 [DONE]
        stream_semantic_action: Optional[str] = None
        try:
            from domain.v1.hub.orchestrators import (
                classify,
                is_classifier_available,
            )
            if is_classifier_available():
                action = classify(request.message)
                msg_preview = (request.message[:80] + "…") if len(request.message) > 80 else request.message
                logger.info("[시멘틱 분류] 질문: %s → %s", msg_preview, action)
                if action == "BLOCK":
                    async def block_stream():
                        yield f"data: {json.dumps({'semantic_action': action})}\n\n"
                        yield f"data: {_BLOCK_MESSAGE}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        block_stream(),
                        media_type="text/event-stream",
                        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
                    )
                stream_semantic_action = action
        except Exception:
            pass

        # 지연 import (v10 채팅 오케스트레이터)
        if "domain.v10.soccer.hub.orchestrators.chat_orchestrator" in sys.modules:
            graph_module = sys.modules["domain.v10.soccer.hub.orchestrators.chat_orchestrator"]
        else:
            graph_module = importlib.import_module(
                "domain.v10.soccer.hub.orchestrators.chat_orchestrator"
            )
        run_agent_stream = graph_module.run_agent_stream

        # 대화 기록 변환
        chat_history = None
        if request.chat_history:
            chat_history = []
            for msg in request.chat_history:
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    chat_history.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    chat_history.append(SystemMessage(content=msg.content))

        async def generate():
            try:
                if stream_semantic_action:
                    yield f"data: {json.dumps({'semantic_action': stream_semantic_action})}\n\n"
                async for chunk in run_agent_stream(
                    user_text=request.message,
                    provider=provider,
                    use_rag=request.use_rag,
                    system_prompt=request.system_prompt,
                    chat_history=chat_history,
                    thread_id=request.thread_id,
                    semantic_action=stream_semantic_action,
                ):
                    if chunk:  # 빈 청크는 전송하지 않음
                        yield f"data: {chunk}\n\n"
                # 스트리밍 완료 신호
                yield "data: [DONE]\n\n"
            except Exception as e:
                import traceback

                error_msg = f"스트리밍 오류: {str(e)}"
                logger.error("%s", error_msg, exc_info=True)
                traceback.print_exc()
                # 오류 발생 시에도 클라이언트에 알림
                yield f"data: [ERROR] {error_msg}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 오류: {str(e)}")


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
    """사용 가능한 LLM 제공자 목록을 반환합니다.

    Returns:
        LLM 제공자 목록
    """
    from domain.v1.hub.llm import (  # type: ignore
        get_provider_name,
        list_providers as _list_providers,
        supports_tool_calling,
    )

    current_provider = get_provider_name()
    providers = []

    for name in _list_providers():
        providers.append(
            ProviderInfo(
                name=name,
                supports_tool_calling=supports_tool_calling(name),
                is_current=(name == current_provider),
            )
        )

    return providers


@router.get("/tools")
async def list_tools():
    """사용 가능한 도구 목록을 반환합니다.

    Returns:
        도구 목록
    """
    import importlib
    import sys

    if "domain.v1.hub.orchestrators" in sys.modules:
        graph_module = sys.modules["domain.v1.hub.orchestrators"]
    else:
        graph_module = importlib.import_module("domain.v1.hub.orchestrators")
    TOOLS = graph_module.TOOLS

    tools = []
    for tool in TOOLS:
        tools.append(
            {
                "name": tool.name,
                "description": tool.description,
            }
        )

    return {"tools": tools}


@router.get("/health")
async def agent_health():
    """에이전트 상태 확인.

    Returns:
        에이전트 상태
    """
    from domain.v1.hub.llm import (  # type: ignore
        get_provider_name,
        list_providers,
        supports_tool_calling,
    )

    try:
        provider = get_provider_name()
        supports_tools = supports_tool_calling(provider)

        return {
            "status": "healthy",
            "current_provider": provider,
            "supports_tool_calling": supports_tools,
            "available_providers": list_providers(),
            "checkpointer_enabled": True,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str):
    """특정 스레드의 대화 기록을 조회합니다.

    Args:
        thread_id: 대화 스레드 ID

    Returns:
        대화 기록
    """
    import importlib
    import sys

    if "domain.v10.soccer.hub.orchestrators.chat_orchestrator" in sys.modules:
        graph_module = sys.modules["domain.v10.soccer.hub.orchestrators.chat_orchestrator"]
    else:
        graph_module = importlib.import_module(
            "domain.v10.soccer.hub.orchestrators.chat_orchestrator"
        )

    get_history = graph_module.get_thread_history
    messages = get_history(thread_id)

    # 메시지를 직렬화 가능한 형태로 변환
    history = []
    for msg in messages:
        msg_type = type(msg).__name__
        role = (
            "user"
            if msg_type == "HumanMessage"
            else (
                "assistant"
                if msg_type == "AIMessage"
                else ("system" if msg_type == "SystemMessage" else "tool")
            )
        )
        history.append(
            {
                "role": role,
                "content": str(msg.content) if hasattr(msg, "content") else str(msg),
                "type": msg_type,
            }
        )

    return {
        "thread_id": thread_id,
        "messages": history,
        "message_count": len(history),
    }


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """특정 스레드의 대화 기록을 삭제합니다.

    Args:
        thread_id: 대화 스레드 ID

    Returns:
        삭제 결과
    """
    import importlib
    import sys

    if "domain.v10.soccer.hub.orchestrators.chat_orchestrator" in sys.modules:
        graph_module = sys.modules["domain.v10.soccer.hub.orchestrators.chat_orchestrator"]
    else:
        graph_module = importlib.import_module(
            "domain.v10.soccer.hub.orchestrators.chat_orchestrator"
        )

    clear_history = graph_module.clear_thread_history
    success = clear_history(thread_id)

    if success:
        return {
            "status": "deleted",
            "thread_id": thread_id,
        }
    else:
        return {
            "status": "not_found",
            "thread_id": thread_id,
            "message": "스레드를 찾을 수 없거나 이미 삭제되었습니다.",
        }
