"""Gemini용 LangChain Chat 모델 (배포 CHAT_LLM=gemini 채팅).

배포(EC2 CPU): EXAONE CPU 추론 지연을 피하려 채팅 최종 답변을 Gemini로 생성한다.
핵심은 '토큰 스트리밍'이다 — 채팅 오케스트레이터는 graph.astream_events의
on_chat_model_stream 이벤트로 토큰을 클라이언트에 흘린다. 그 이벤트는 LangChain
모델의 _stream()이 run_manager.on_llm_new_token을 호출할 때만 발생한다.
raw gemini_complete(blocking)은 이벤트를 못 내보내 한 덩어리로 도착했다.

그래서 google.generativeai(stream=True)를 감싸 _stream()을 구현한 얇은 BaseChatModel을
둔다. 새 의존성(langchain-google-genai → langchain-core 업그레이드) 없이
기존 GGUF/EXAONE 커스텀 모델과 동일한 경로(.stream())로 동작한다.

도구 호출은 LLM 네이티브 function-calling이 아니라 graph_orchestrator의 키워드 기반
강제 도구(_build_forced_tool_calls)로 처리하므로, bind_tools는 도구를 무시하고 self를
돌려준다(최종 답변 턴은 도구 결과를 텍스트로 받아 답변만 스트리밍).
"""

from __future__ import annotations

import logging
import warnings
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

logger = logging.getLogger(__name__)


def _lc_messages_to_gemini(messages: List[BaseMessage]) -> tuple[str, List[Dict[str, Any]]]:
    """LangChain 메시지 → (system_instruction, Gemini contents).

    - SystemMessage: system_instruction으로 합침
    - HumanMessage: role 'user'
    - AIMessage: role 'model' (내용 없으면 생략; tool_calls만 있는 메시지는 건너뜀)
    - ToolMessage: role 'user'로 '[도구 결과] name: content' 주입
    연속 동일 role은 parts를 합쳐 Gemini의 역할 교대 제약을 피한다.
    """
    system_parts: List[str] = []
    contents: List[Dict[str, Any]] = []

    def _push(role: str, text: str) -> None:
        if not text:
            return
        if contents and contents[-1]["role"] == role:
            contents[-1]["parts"].append(text)
        else:
            contents.append({"role": role, "parts": [text]})

    for msg in messages:
        if isinstance(msg, SystemMessage):
            if str(msg.content).strip():
                system_parts.append(str(msg.content))
        elif isinstance(msg, HumanMessage):
            _push("user", str(msg.content))
        elif isinstance(msg, AIMessage):
            _push("model", str(msg.content))
        elif isinstance(msg, ToolMessage):
            name = getattr(msg, "name", "") or "tool"
            _push("user", f"[도구 결과] {name}: {msg.content}")

    # Gemini는 첫 content가 'user'여야 안정적 → model로 시작하면 빈 user 삽입
    if contents and contents[0]["role"] == "model":
        contents.insert(0, {"role": "user", "parts": ["(대화 시작)"]})
    return "\n\n".join(system_parts), contents


class GeminiChatModel(BaseChatModel):
    """google.generativeai(stream=True)를 감싼 스트리밍 LangChain Chat 모델."""

    _model_id: str = ""
    _api_key: str = ""
    _temperature: float = 0.7
    _max_tokens: int = 2048

    def __init__(
        self,
        model_id: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        super().__init__()
        object.__setattr__(self, "_model_id", model_id)
        object.__setattr__(self, "_api_key", api_key)
        object.__setattr__(self, "_temperature", temperature)
        object.__setattr__(self, "_max_tokens", max_tokens)

    def bind_tools(
        self,
        tools: Sequence[Union[BaseTool, Dict[str, Any]]],
        *,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> "GeminiChatModel":
        # 도구는 키워드 기반 강제 라우팅으로 처리 → 모델은 텍스트 답변만 스트리밍.
        return self

    def _build_model(self, system_instruction: str) -> Any:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            import google.generativeai as genai  # type: ignore

        genai.configure(api_key=self._api_key)
        kwargs: Dict[str, Any] = {}
        if system_instruction.strip():
            kwargs["system_instruction"] = system_instruction
        return genai.GenerativeModel(self._model_id, **kwargs)

    def _gen_config(self, **kwargs: Any) -> Dict[str, Any]:
        return {
            "temperature": float(kwargs.get("temperature", self._temperature)),
            "max_output_tokens": int(kwargs.get("max_tokens") or self._max_tokens),
        }

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        system_instruction, contents = _lc_messages_to_gemini(messages)
        model = self._build_model(system_instruction)
        response = None
        try:
            response = model.generate_content(
                contents,
                stream=True,
                generation_config=self._gen_config(**kwargs),
            )
            for chunk in response:
                piece = getattr(chunk, "text", None) or ""
                if piece:
                    cg = ChatGenerationChunk(message=AIMessageChunk(content=piece))
                    if run_manager:
                        run_manager.on_llm_new_token(piece, chunk=cg)
                    yield cg
        except Exception as e:
            logger.warning("[GEMINI-CHAT] 스트리밍 실패: %s", e)
            raise
        finally:
            if response is not None and hasattr(response, "close"):
                try:
                    response.close()
                except Exception:
                    pass

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_instruction, contents = _lc_messages_to_gemini(messages)
        model = self._build_model(system_instruction)
        resp = model.generate_content(
            contents,
            generation_config=self._gen_config(**kwargs),
        )
        text = (getattr(resp, "text", None) or "").strip()
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    @property
    def _llm_type(self) -> str:
        return "gemini_chat"
