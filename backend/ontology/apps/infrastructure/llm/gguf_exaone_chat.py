"""EXAONE 역량 GGUF(llama.cpp)용 LangChain Chat 모델.

배포(EC2 CPU): merge된 EXAONE+LoRA를 GGUF로 변환한 단일 파일을 로드합니다.
도구 호출은 exaone_model.ExaoneLangChainWrapper와 동일하게 JSON 프롬프트 기반으로 처리합니다.
"""

from __future__ import annotations

import json
import threading
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.tools import BaseTool

from infrastructure.llm.exaone_hf_model import (  # type: ignore
    TOOL_CALLING_SYSTEM_PROMPT,
    _extract_json_from_response,
    _format_tool_description,
    _parse_tool_calls,
)


def _lc_messages_to_llama_cpp(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """LangChain 메시지 → llama_cpp create_chat_completion 형식."""
    out: List[Dict[str, str]] = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            out.append({"role": "system", "content": str(msg.content)})
        elif isinstance(msg, HumanMessage):
            out.append({"role": "user", "content": str(msg.content)})
        elif isinstance(msg, AIMessage):
            content = str(msg.content)
            if getattr(msg, "tool_calls", None):
                tcs = msg.tool_calls or []
                tool_calls_json = [
                    {"name": tc["name"], "arguments": tc.get("args", {})} for tc in tcs
                ]
                content = (
                    json.dumps(tool_calls_json[0], ensure_ascii=False)
                    if len(tool_calls_json) == 1
                    else json.dumps(tool_calls_json, ensure_ascii=False)
                )
            out.append({"role": "assistant", "content": content})
        elif isinstance(msg, ToolMessage):
            name = getattr(msg, "name", "") or "tool"
            out.append({"role": "user", "content": f"[도구 결과] {name}: {msg.content}"})
    return out


class GgufCompetencyChatModel(BaseChatModel):
    """GGUF 파일 + llama_cpp.Llama. EXAONE 채팅 템플릿은 GGUF 메타데이터에 포함된 것을 사용."""

    _llama: Any = None
    _tools: List[BaseTool] = []
    _tool_choice: Optional[str] = None

    def __init__(
        self,
        llama: Any,
        tools: Optional[List[BaseTool]] = None,
        tool_choice: Optional[str] = None,
    ):
        super().__init__()
        object.__setattr__(self, "_llama", llama)
        object.__setattr__(self, "_tools", tools or [])
        object.__setattr__(self, "_tool_choice", tool_choice)

    def bind_tools(
        self,
        tools: Sequence[Union[BaseTool, Dict[str, Any]]],
        *,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> "GgufCompetencyChatModel":
        base_tools = [t for t in tools if isinstance(t, BaseTool)]
        return GgufCompetencyChatModel(
            llama=self._llama,
            tools=base_tools,
            tool_choice=tool_choice,
        )

    def _create_tool_system_prompt(self) -> str:
        if not self._tools:
            return ""
        tools_desc = "\n".join([_format_tool_description(t) for t in self._tools])
        return TOOL_CALLING_SYSTEM_PROMPT.format(tools_description=tools_desc)

    def _inject_tool_prompt(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        if not self._tools:
            return list(messages)
        tool_prompt = self._create_tool_system_prompt()
        has_system = any(isinstance(m, SystemMessage) for m in messages)
        if has_system:
            new_messages: List[BaseMessage] = []
            for msg in messages:
                if isinstance(msg, SystemMessage):
                    new_messages.append(
                        SystemMessage(content=f"{msg.content}\n\n{tool_prompt}")
                    )
                else:
                    new_messages.append(msg)
            return new_messages
        return [SystemMessage(content=tool_prompt)] + list(messages)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        msgs = self._inject_tool_prompt(messages)
        chat = _lc_messages_to_llama_cpp(msgs)
        max_tokens = int(kwargs.get("max_tokens") or kwargs.get("max_new_tokens") or 2048)
        temperature = float(kwargs.get("temperature", 0.7))

        resp = self._llama.create_chat_completion(
            messages=chat,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False,
        )
        text = (resp.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        text = str(text).strip()

        tool_calls: List[Dict[str, Any]] = []
        content = text
        if self._tools and text:
            json_data = _extract_json_from_response(text)
            if json_data:
                tool_calls = _parse_tool_calls(json_data)
                if tool_calls:
                    content = ""

        msg = AIMessage(content=content, tool_calls=tool_calls) if tool_calls else AIMessage(content=content)
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        msgs = self._inject_tool_prompt(messages)
        chat = _lc_messages_to_llama_cpp(msgs)
        max_tokens = int(kwargs.get("max_tokens") or kwargs.get("max_new_tokens") or 2048)
        temperature = float(kwargs.get("temperature", 0.7))

        generated = ""
        stream = self._llama.create_chat_completion(
            messages=chat,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            try:
                delta = (chunk.get("choices") or [{}])[0].get("delta", {})
                piece = delta.get("content") or ""
            except Exception:
                piece = ""
            if piece:
                generated += piece
                cg = ChatGenerationChunk(message=AIMessageChunk(content=piece))
                if run_manager:
                    run_manager.on_llm_new_token(piece, chunk=cg)
                yield cg

        if self._tools and generated.strip():
            json_data = _extract_json_from_response(generated.strip())
            if json_data:
                tool_calls = _parse_tool_calls(json_data)
                if tool_calls:
                    yield ChatGenerationChunk(
                        message=AIMessageChunk(content="", tool_calls=tool_calls)
                    )

    @property
    def _llm_type(self) -> str:
        return "gguf_exaone_competency"


_gguf_singleton: Any = None
_gguf_singleton_path: Optional[str] = None
_gguf_lock = threading.Lock()


def load_gguf_llama_singleton(model_path: str, n_ctx: int = 8192) -> Any:
    """GGUF 경로당 한 번만 Llama 인스턴스 로드."""
    global _gguf_singleton, _gguf_singleton_path
    resolved = str(model_path)
    with _gguf_lock:
        if _gguf_singleton is not None and _gguf_singleton_path == resolved:
            return _gguf_singleton
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as e:
            raise ImportError(
                "llama-cpp-python이 필요합니다. pip install llama-cpp-python"
            ) from e
        print(f"[INFO] GGUF 로드 중 (CPU, n_ctx={n_ctx}): {resolved}")
        inst = Llama(
            model_path=resolved,
            n_gpu_layers=0,
            n_ctx=n_ctx,
            verbose=False,
        )
        _gguf_singleton = inst
        _gguf_singleton_path = resolved
        print("[OK] GGUF 로드 완료")
        return inst


def reset_gguf_singleton() -> None:
    """테스트·캐시 초기화 시 Llama 인스턴스 해제."""
    global _gguf_singleton, _gguf_singleton_path
    with _gguf_lock:
        _gguf_singleton = None
        _gguf_singleton_path = None
