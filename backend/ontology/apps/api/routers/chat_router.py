"""LangGraph 에이전트 라우터.

LangGraph 기반 에이전트 API 엔드포인트를 제공합니다.
- POST /agent/upload: 멀티파트 → file_ids 반환.
- POST /agent/chat/stream: JSON (message, file_ids 등) → SSE 스트리밍.
"""

import base64
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.config import get_settings  # type: ignore
from api.shared.upload_store import (  # type: ignore
    delete_upload_file,
    load_upload_file,
    load_upload_files_as_base64,
    save_upload_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["LangGraph Agent"])


class MessageItem(BaseModel):
    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")


class AgentRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지")
    provider: Optional[str] = Field(None, description="LLM 제공자 (exaone)")
    use_rag: bool = Field(True, description="RAG 사용 여부")
    system_prompt: Optional[str] = Field(None, description="커스텀 시스템 프롬프트")
    chat_history: Optional[List[MessageItem]] = Field(None, description="이전 대화 기록")
    thread_id: Optional[str] = Field(None, description="대화 스레드 ID")
    images: Optional[List[str]] = Field(None, description="첨부 이미지 base64 문자열 배열 (data URL 제외)")


class ProviderInfo(BaseModel):
    name: str
    supports_tool_calling: bool
    is_current: bool


async def _parse_chat_payload(request: Request) -> Dict[str, Any]:
    """JSON body만 파싱해 채팅 페이로드 반환."""
    body = await request.json()
    ch = body.get("chat_history")
    chat_history = None
    if isinstance(ch, list):
        try:
            chat_history = [MessageItem(**m) for m in ch]
        except (TypeError, ValueError):
            pass
    return {
        "message": body.get("message", ""),
        "use_rag": body.get("use_rag", True),
        "chat_history": chat_history,
        "thread_id": body.get("thread_id"),
        "provider": body.get("provider"),
        "system_prompt": body.get("system_prompt"),
        "images": body.get("images"),
        "file_ids": body.get("file_ids"),
        "file_names": body.get("file_names"),
    }


_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def _resolve_file_ids_to_payload(payload: Dict[str, Any]) -> None:
    """file_ids(+ file_names)를 로드해 이미지는 base64로, 문서(PDF/TXT/Word/Excel)는 텍스트 추출 후 메시지에 주입."""
    file_ids = payload.get("file_ids")
    if not file_ids or payload.get("images") is not None:
        return
    if not isinstance(file_ids, list):
        return
    ids = [str(x) for x in file_ids if x]
    if not ids:
        return
    file_names: List[str] = payload.get("file_names") or []
    if len(file_names) != len(ids):
        file_names = [""] * len(ids)

    # 파일명이 없으면 기존 동작: 전부 이미지로 처리 (하위 호환)
    if not any(file_names):
        payload["images"] = load_upload_files_as_base64(ids, delete_after=True)
        payload.pop("file_ids", None)
        payload.pop("file_names", None)
        return

    from domain.shared.document_extract import (  # type: ignore
        SUPPORTED_EXCEL_EXTENSIONS,
        SUPPORTED_TEXT_EXTENSIONS,
        extract_text_from_document,
        extract_excel_from_document,
    )

    images_b64: List[str] = []
    document_texts: List[str] = []
    for i, fid in enumerate(ids):
        data = load_upload_file(fid)
        if not data:
            continue
        name = (file_names[i] or "").strip()
        ext = (name.rsplit(".", 1)[-1].lower() if "." in name else "")
        ext = f".{ext}" if ext else ""

        try:
            if ext in _IMAGE_EXTENSIONS:
                images_b64.append(base64.b64encode(data).decode("utf-8"))
            elif ext in SUPPORTED_TEXT_EXTENSIONS:
                text = extract_text_from_document(data=data, filename=name or f"doc{i}.txt")
                if text.strip():
                    document_texts.append(f"[첨부 문서: {name or '문서'}]\n{text[:30000]}")
            elif ext in SUPPORTED_EXCEL_EXTENSIONS:
                rows = extract_excel_from_document(data=data, filename=name or f"sheet{i}.xlsx")
                if rows:
                    lines = ["\t".join(str(v) for v in row.values()) for row in rows[:500]]
                    document_texts.append(f"[첨부 문서: {name or '엑셀'}]\n" + "\n".join(lines))
            # else: 알 수 없는 확장자는 무시
        except Exception as e:
            logger.warning("첨부 파일 처리 실패 %s: %s", name or fid, e)
        finally:
            delete_upload_file(fid)

    if images_b64:
        payload["images"] = images_b64
    if document_texts:
        base_msg = payload.get("message") or ""
        payload["message"] = base_msg + "\n\n" + "\n\n".join(document_texts)
    payload.pop("file_ids", None)
    payload.pop("file_names", None)


@router.post("/upload")
async def agent_upload(files: List[UploadFile] = File(default=[], description="업로드할 파일들")):
    """채팅 첨부용 파일 업로드. 용량·개수 제한 적용 후 임시 저장, file_ids 반환. (BP)"""
    files = files or []
    settings = get_settings()
    max_count = getattr(settings, "upload_max_files", 5)
    max_bytes = int(getattr(settings, "upload_max_file_size_mb", 5) * 1024 * 1024)

    if len(files) > max_count:
        raise HTTPException(
            status_code=400,
            detail=f"최대 {max_count}개까지 업로드 가능합니다.",
        )

    file_ids: List[str] = []
    for f in files:
        data = await f.read()
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"파일 '{f.filename or '?'}' 크기가 제한({max_bytes // (1024*1024)}MB)을 초과합니다.",
            )
        if data:
            file_ids.append(save_upload_file(data))

    return {"file_ids": file_ids}


@router.post("/chat/stream")
async def agent_chat_stream(request: Request):
    payload = await _parse_chat_payload(request)
    _resolve_file_ids_to_payload(payload)
    message = payload.get("message", "")
    try:
        import importlib
        import sys

        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        from domain.hub.llm import get_provider_name  # type: ignore

        provider = payload.get("provider") or get_provider_name()

        if "domain.hub.orchestrators.chat_orchestrator" in sys.modules:
            graph_module = sys.modules["domain.hub.orchestrators.chat_orchestrator"]
        else:
            graph_module = importlib.import_module("domain.hub.orchestrators.chat_orchestrator")
        run_agent_stream = graph_module.run_agent_stream

        chat_history = None
        if payload.get("chat_history"):
            chat_history = []
            for msg in payload["chat_history"]:
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    chat_history.append(AIMessage(content=msg.content))
                elif msg.role == "system":
                    chat_history.append(SystemMessage(content=msg.content))

        async def generate():
            try:
                async for chunk in run_agent_stream(
                    user_text=message,
                    provider=provider,
                    system_prompt=payload.get("system_prompt"),
                    chat_history=chat_history,
                    thread_id=payload.get("thread_id"),
                    images=payload.get("images"),
                ):
                    if isinstance(chunk, dict):
                        yield f"data: {json.dumps(chunk)}\n\n"
                    elif chunk:
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                error_msg = f"스트리밍 오류: {str(e)}"
                logger.error("%s", error_msg, exc_info=True)
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 오류: {str(e)}")


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
    from domain.hub.llm import get_provider_name, list_providers as _list_providers, supports_tool_calling  # type: ignore
    current_provider = get_provider_name()
    return [
        ProviderInfo(name=name, supports_tool_calling=supports_tool_calling(name), is_current=(name == current_provider))
        for name in _list_providers()
    ]


@router.get("/tools")
async def list_tools():
    import importlib
    import sys
    if "domain.hub.orchestrators" in sys.modules:
        graph_module = sys.modules["domain.hub.orchestrators"]
    else:
        graph_module = importlib.import_module("domain.hub.orchestrators")
    TOOLS = graph_module.TOOLS
    return {"tools": [{"name": t.name, "description": t.description} for t in TOOLS]}


@router.get("/health")
async def agent_health():
    from domain.hub.llm import get_provider_name, list_providers, supports_tool_calling  # type: ignore
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


@router.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str):
    import importlib
    import sys
    if "domain.hub.orchestrators.chat_orchestrator" in sys.modules:
        graph_module = sys.modules["domain.hub.orchestrators.chat_orchestrator"]
    else:
        graph_module = importlib.import_module("domain.hub.orchestrators.chat_orchestrator")
    messages = graph_module.get_thread_history(thread_id)
    history = []
    for msg in messages:
        msg_type = type(msg).__name__
        role = "user" if msg_type == "HumanMessage" else ("assistant" if msg_type == "AIMessage" else ("system" if msg_type == "SystemMessage" else "tool"))
        history.append({"role": role, "content": str(msg.content) if hasattr(msg, "content") else str(msg), "type": msg_type})
    return {"thread_id": thread_id, "messages": history, "message_count": len(history)}


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    import importlib
    import sys
    if "domain.hub.orchestrators.chat_orchestrator" in sys.modules:
        graph_module = sys.modules["domain.hub.orchestrators.chat_orchestrator"]
    else:
        graph_module = importlib.import_module("domain.hub.orchestrators.chat_orchestrator")
    success = graph_module.clear_thread_history(thread_id)
    if success:
        return {"status": "deleted", "thread_id": thread_id}
    return {"status": "not_found", "thread_id": thread_id, "message": "스레드를 찾을 수 없거나 이미 삭제되었습니다."}
