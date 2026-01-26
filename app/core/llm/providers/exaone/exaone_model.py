"""EXAONE 3.5 모델 구현체.

EXAONE 3.5는 LG AI Research에서 개발한 한국어 특화 LLM입니다.
JSON Tool Calling을 프롬프트 기반으로 지원합니다.
bitsandbytes 4-bit 양자화로 GPU 메모리 효율적 사용을 지원합니다.
"""

import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

# OpenMP 충돌 방지
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
from core.llm.base import BaseLLM  # type: ignore
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
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
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextIteratorStreamer,
)

# Tool Calling을 위한 시스템 프롬프트 템플릿
TOOL_CALLING_SYSTEM_PROMPT = """당신은 도움이 되는 AI 어시스턴트입니다. 사용자의 요청을 처리하기 위해 다음 도구들을 사용할 수 있습니다.

## 사용 가능한 도구:
{tools_description}

## 도구 호출 규칙:
1. 도구를 호출해야 할 경우, 반드시 다음 JSON 형식으로만 응답하세요:
```json
{{"name": "도구이름", "arguments": {{"인자명": "값"}}}}
```

2. 여러 도구를 호출해야 할 경우:
```json
[{{"name": "도구1", "arguments": {{}}}}, {{"name": "도구2", "arguments": {{}}}}]
```

3. 도구 호출이 필요 없으면 일반 텍스트로 응답하세요.

4. JSON 형식으로 도구를 호출할 때는 다른 텍스트 없이 JSON만 출력하세요.

중요: 도구를 호출할 때는 반드시 위의 JSON 형식만 사용하세요."""


def _format_tool_description(tool: BaseTool) -> str:
    """도구를 설명 문자열로 변환."""
    args_desc = ""
    if hasattr(tool, "args_schema") and tool.args_schema:
        schema = tool.args_schema.schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        args_parts = []
        for name, prop in properties.items():
            arg_type = prop.get("type", "string")
            arg_desc = prop.get("description", "")
            req_marker = "(필수)" if name in required else "(선택)"
            args_parts.append(f"    - {name} ({arg_type}) {req_marker}: {arg_desc}")
        if args_parts:
            args_desc = "\n" + "\n".join(args_parts)

    return f"- **{tool.name}**: {tool.description}{args_desc}"


def _extract_json_from_response(text: str) -> Optional[Union[Dict, List]]:
    """응답에서 JSON을 추출."""
    text = text.strip()

    # 코드 블록 내 JSON 추출
    json_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(json_block_pattern, text)
    if matches:
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

    # 직접 JSON 파싱 시도
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # JSON 객체/배열 패턴 찾기
    json_patterns = [
        r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*\}',  # 단일 객체
        r'\[[^\[\]]*\{[^{}]*"name"[^{}]*\}[^\[\]]*\]',  # 배열
    ]

    for pattern in json_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    return None


def _parse_tool_calls(json_data: Union[Dict, List]) -> List[Dict[str, Any]]:
    """JSON 데이터를 tool_calls 형식으로 변환."""
    tool_calls = []

    if isinstance(json_data, dict):
        # 단일 도구 호출
        if "name" in json_data:
            tool_calls.append(
                {
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "name": json_data["name"],
                    "args": json_data.get("arguments", json_data.get("args", {})),
                }
            )
    elif isinstance(json_data, list):
        # 여러 도구 호출
        for item in json_data:
            if isinstance(item, dict) and "name" in item:
                tool_calls.append(
                    {
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "name": item["name"],
                        "args": item.get("arguments", item.get("args", {})),
                    }
                )

    return tool_calls


def get_adaptive_max_length(input_length: int, max_new_tokens: int = 2048) -> int:
    """입력 길이에 따라 KV 캐시 최대 크기를 동적으로 결정 (메모리 절약).
    
    Args:
        input_length: 입력 토큰 길이
        max_new_tokens: 최대 생성 토큰 수
    
    Returns:
        동적으로 조정된 max_length
    """
    total_needed = input_length + max_new_tokens
    
    # 입력 길이에 따라 KV 캐시 크기 동적 조정
    if input_length <= 256:
        # 매우 짧은 입력: 작은 KV 캐시 (메모리 절약)
        return min(1024, total_needed)
    elif input_length <= 512:
        # 짧은 입력: 중간 KV 캐시
        return min(2048, total_needed)
    elif input_length <= 1024:
        # 중간 입력: 큰 KV 캐시
        return min(3072, total_needed)
    elif input_length <= 2048:
        # 긴 입력: 매우 큰 KV 캐시
        return min(4096, total_needed)
    else:
        # 매우 긴 입력: 최대 허용 크기
        return min(4096, total_needed)


class ExaoneLLM(BaseLLM):
    """EXAONE 3.5 LLM 모델 구현체 (bitsandbytes 4-bit 양자화 GPU 지원)."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        model_id: str = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct",
        device_map: str = "auto",
        torch_dtype: str = "auto",
        trust_remote_code: bool = True,
        use_4bit: Optional[bool] = None,
    ):
        """EXAONE 모델 초기화.

        Args:
            model_path: 로컬 모델 경로 (None이면 model_id 사용)
            model_id: HuggingFace 모델 ID
            device_map: 디바이스 매핑 ("auto", "cuda" 등, GPU 전용)
            torch_dtype: 토치 데이터 타입 ("auto", "float16", "bfloat16", "float32")
            trust_remote_code: 원격 코드 신뢰 여부
            use_4bit: 4-bit 양자화 사용 여부 (None이면 환경변수 EXAONE_USE_4BIT 확인, 기본 True)
        """
        self.model_path = model_path
        self.model_id = model_id
        self.device_map = device_map
        self.torch_dtype = torch_dtype
        self.trust_remote_code = trust_remote_code

        # 4-bit 양자화 설정 (Settings에서 확인, 기본값 True)
        if use_4bit is None:
            from core.config import settings  # type: ignore

            self.use_4bit = settings.exaone_use_4bit
        else:
            self.use_4bit = use_4bit

        # 모델 경로 결정 (우선순위: model_path > EXAONE_MODEL_DIR > model_id)
        if model_path and Path(model_path).exists():
            self._load_path = model_path
        else:
            # EXAONE_MODEL_DIR 설정 확인 (메인 경로)
            from core.config import settings  # type: ignore

            env_model_dir = settings.exaone_model_dir
            if env_model_dir:
                env_path = Path(env_model_dir)
                # 상대 경로인 경우 프로젝트 루트 기준으로 해석
                if not env_path.is_absolute():
                    # __file__ = app/models/exaone_model.py
                    # parent.parent = app/ 디렉토리
                    # parent.parent.parent = 프로젝트 루트 (RAG/)
                    app_dir = Path(__file__).parent.parent  # models -> app
                    project_root = app_dir.parent  # app -> 프로젝트 루트
                    env_path = (project_root / env_path).resolve()

                # app/artifacts 경로만 확인
                if env_path.exists() and (env_path / "config.json").exists():
                    self._load_path = str(env_path)
                    print(
                        f"[INFO] EXAONE_MODEL_DIR 환경 변수에서 모델 경로 사용: {self._load_path}"
                    )
                else:
                    # 경로가 없으면 HuggingFace 모델 ID 사용
                    self._load_path = model_id
            else:
                # 환경 변수가 없으면 HuggingFace 모델 ID 사용
                self._load_path = model_id

        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self._langchain_model: Optional[BaseChatModel] = None

        # 모델 로드
        self._load_model()

    def _load_model(self) -> None:
        """모델 및 토크나이저 로드."""
        try:
            print(f"[INFO] EXAONE 모델 로딩 중: {self._load_path}")

            # CUDA 사용 가능 여부 확인
            cuda_available = torch.cuda.is_available()
            print(f"[INFO] CUDA 사용 가능: {cuda_available}")
            if cuda_available:
                print(f"[INFO] CUDA 디바이스: {torch.cuda.get_device_name(0)}")
                print(
                    f"[INFO] CUDA 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB"
                )

            # CUDA 필수 확인 (GPU 강제 사용)
            if not cuda_available:
                raise RuntimeError(
                    "CUDA가 사용 불가능합니다. GPU가 필요합니다.\n"
                    "torch.cuda.is_available()이 False입니다."
                )

            # 양자화 및 모델 로드 설정 (GPU 전용)
            dtype = torch.float16

            if self.use_4bit:
                # bitsandbytes 4-bit 양자화 (GPU 메모리 절약)
                print("[INFO] bitsandbytes 4-bit 양자화 적용 (GPU 전용)")
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )
                quantization_info = "4-bit (NF4, bitsandbytes)"
            else:
                print("[INFO] GPU FP16 모드로 로딩")
                quantization_config = None
                quantization_info = "없음 (FP16)"

            # 모델 로드 설정 (GPU 강제)
            load_kwargs: Dict[str, Any] = {
                "torch_dtype": dtype,
                "device_map": {"": "cuda:0"},  # GPU 강제 사용
                "trust_remote_code": self.trust_remote_code,
                "low_cpu_mem_usage": True,
                "attn_implementation": "sdpa",  # PyTorch 2.0+ SDPA 최적화
            }

            if quantization_config is not None:
                load_kwargs["quantization_config"] = quantization_config

            self.model = AutoModelForCausalLM.from_pretrained(
                self._load_path,
                **load_kwargs,
            )

            # torch.compile 최적화 (PyTorch 2.0+, 첫 실행 시 컴파일 시간 필요)
            from core.config import settings  # type: ignore

            if settings.exaone_use_compile and hasattr(torch, "compile"):
                print("[INFO] torch.compile() 최적화 적용 중...")
                self.model = torch.compile(self.model, mode="reduce-overhead")
                print("[OK] torch.compile() 적용 완료")

            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self._load_path,
                trust_remote_code=self.trust_remote_code,
            )

            # pad_token 설정 (없으면 eos_token 사용)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            # 디바이스 정보 확인 및 출력
            if hasattr(self.model, "device"):
                device_info = str(self.model.device)
            elif hasattr(self.model, "hf_device_map"):
                device_info = str(self.model.hf_device_map)
            else:
                first_param = next(self.model.parameters(), None)
                device_info = (
                    str(first_param.device) if first_param is not None else "unknown"
                )

            print("[OK] EXAONE 모델 로드 완료")
            print(f"[INFO] 사용 디바이스: {device_info}")
            print(f"[INFO] 데이터 타입: {dtype}")
            print(f"[INFO] 양자화: {quantization_info}")

            if cuda_available and "cuda" in str(device_info):
                print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")
                print(
                    f"[INFO] GPU 메모리 사용량: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB / "
                    f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
                )
        except Exception as e:
            error_msg = f"EXAONE 모델 로드 실패: {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise RuntimeError(error_msg) from e

    def get_langchain_model(self) -> BaseChatModel:
        """LangChain 호환 모델 반환."""
        if self._langchain_model is None:
            self._langchain_model = ExaoneLangChainWrapper(self.model, self.tokenizer)
        return self._langchain_model

    def invoke(self, prompt: str, **kwargs) -> str:
        """프롬프트 실행 및 응답 반환."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("모델이 로드되지 않았습니다.")

        try:
            # EXAONE 채팅 템플릿 사용
            messages = [{"role": "user", "content": prompt}]
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
            ).to(self.model.device)

            # 생성 파라미터
            max_new_tokens = kwargs.get("max_new_tokens", 2048)
            temperature = kwargs.get("temperature", 0.7)
            do_sample = kwargs.get("do_sample", True)

            # 동적 KV 캐시 최적화: 입력 길이에 따라 max_length 조정 (메모리 절약)
            input_length = input_ids.shape[1]
            max_length = kwargs.get("max_length", None)
            if max_length is None:
                # 동적 조정: 입력 길이에 따라 KV 캐시 크기 결정
                max_length = get_adaptive_max_length(input_length, max_new_tokens)
            else:
                # 사용자가 지정한 경우, 동적 조정과 비교하여 작은 값 사용
                adaptive_max = get_adaptive_max_length(input_length, max_new_tokens)
                max_length = min(max_length, adaptive_max)

            # 생성 (메모리 효율적인 옵션 적용)
            with torch.no_grad(), torch.cuda.amp.autocast():
                outputs = self.model.generate(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    max_length=max_length,  # 동적 KV 캐시 최적화
                    temperature=temperature if do_sample else None,
                    do_sample=do_sample,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True,  # KV 캐시 활성화 (속도 향상)
                    num_beams=1,  # 그리디 디코딩 (빠른 생성)
                    # 메모리 효율 옵션 추가
                    output_attentions=False,  # Attention 출력 비활성화 (메모리 절약)
                    output_hidden_states=False,  # Hidden states 출력 비활성화 (메모리 절약)
                    return_dict_in_generate=False,  # Dict 대신 Tensor 반환 (메모리 절약)
                )

            # 디코딩 (입력 부분 제외)
            generated_text = self.tokenizer.decode(
                outputs[0][input_length:], skip_special_tokens=True
            )

            return generated_text.strip()
        except Exception as e:
            error_msg = f"텍스트 생성 실패: {str(e)}"
            raise RuntimeError(error_msg) from e

    def stream(self, prompt: str, **kwargs):
        """스트리밍 응답 생성."""
        response = self.invoke(prompt, **kwargs)
        for chunk in response.split():
            yield chunk + " "

    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환."""
        return {
            "model_type": "exaone",
            "model_path": self._load_path,
            "model_id": self.model_id,
            "device": str(self.model.device) if self.model else None,
            "dtype": str(self.model.dtype) if self.model else None,
        }


class ExaoneLangChainWrapper(BaseChatModel):
    """EXAONE 모델을 LangChain 인터페이스로 래핑 (Tool Calling 지원)."""

    _model: Any = None
    _tokenizer: Any = None
    _tools: List[BaseTool] = []
    _tool_choice: Optional[str] = None

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        tools: Optional[List[BaseTool]] = None,
        tool_choice: Optional[str] = None,
    ):
        super().__init__()
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_tokenizer", tokenizer)
        object.__setattr__(self, "_tools", tools or [])
        object.__setattr__(self, "_tool_choice", tool_choice)

    def bind_tools(
        self,
        tools: Sequence[Union[BaseTool, Dict[str, Any]]],
        *,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> "ExaoneLangChainWrapper":
        """도구를 바인딩한 새 인스턴스 반환.

        Args:
            tools: 바인딩할 도구 목록
            tool_choice: 도구 선택 옵션 ("auto", "any", "none" 등)

        Returns:
            도구가 바인딩된 새 ExaoneLangChainWrapper 인스턴스
        """
        # BaseTool만 필터링 (dict 형식은 지원하지 않음)
        base_tools = [t for t in tools if isinstance(t, BaseTool)]

        return ExaoneLangChainWrapper(
            model=self._model,
            tokenizer=self._tokenizer,
            tools=base_tools,
            tool_choice=tool_choice,
        )

    def _create_tool_system_prompt(self) -> str:
        """도구 설명이 포함된 시스템 프롬프트 생성."""
        if not self._tools:
            return ""

        tools_desc = "\n".join([_format_tool_description(t) for t in self._tools])
        return TOOL_CALLING_SYSTEM_PROMPT.format(tools_description=tools_desc)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """메시지를 기반으로 응답 생성 (Tool Calling 지원)."""
        # 도구가 바인딩되어 있으면 시스템 프롬프트에 추가
        if self._tools:
            tool_prompt = self._create_tool_system_prompt()

            # 기존 시스템 메시지가 있는지 확인
            has_system = any(isinstance(m, SystemMessage) for m in messages)

            if has_system:
                # 기존 시스템 메시지에 도구 프롬프트 추가
                new_messages = []
                for msg in messages:
                    if isinstance(msg, SystemMessage):
                        combined_content = f"{msg.content}\n\n{tool_prompt}"
                        new_messages.append(SystemMessage(content=combined_content))
                    else:
                        new_messages.append(msg)
                messages = new_messages
            else:
                # 새 시스템 메시지 추가
                messages = [SystemMessage(content=tool_prompt)] + list(messages)

        # 메시지를 EXAONE 채팅 형식으로 변환
        chat_messages = self._convert_messages(messages)

        # 채팅 템플릿 적용
        input_ids = self._tokenizer.apply_chat_template(
            chat_messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self._model.device)

        # 생성 파라미터
        max_new_tokens = kwargs.get("max_new_tokens", 2048)
        temperature = kwargs.get("temperature", 0.7)
        do_sample = kwargs.get("do_sample", True)

        # 동적 KV 캐시 최적화: 입력 길이에 따라 max_length 조정 (메모리 절약)
        input_length = input_ids.shape[1]
        max_length = kwargs.get("max_length", None)
        if max_length is None:
            # 동적 조정: 입력 길이에 따라 KV 캐시 크기 결정
            max_length = get_adaptive_max_length(input_length, max_new_tokens)
        else:
            # 사용자가 지정한 경우, 동적 조정과 비교하여 작은 값 사용
            adaptive_max = get_adaptive_max_length(input_length, max_new_tokens)
            max_length = min(max_length, adaptive_max)

        # 생성 (메모리 효율적인 옵션 적용)
        with torch.no_grad(), torch.cuda.amp.autocast():
            outputs = self._model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                max_length=max_length,  # 동적 KV 캐시 최적화
                temperature=temperature if do_sample else None,
                do_sample=do_sample,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
                use_cache=True,  # KV 캐시 활성화 (속도 향상)
                num_beams=1,  # 그리디 디코딩 (빠른 생성)
                # 메모리 효율 옵션 추가
                output_attentions=False,  # Attention 출력 비활성화 (메모리 절약)
                output_hidden_states=False,  # Hidden states 출력 비활성화 (메모리 절약)
                return_dict_in_generate=False,  # Dict 대신 Tensor 반환 (메모리 절약)
            )

        # 디코딩 (입력 부분 제외)
        generated_text = self._tokenizer.decode(
            outputs[0][input_length:], skip_special_tokens=True
        )
        generated_text = generated_text.strip()

        # 도구가 바인딩되어 있으면 JSON 파싱 시도
        tool_calls = []
        content = generated_text

        if self._tools:
            json_data = _extract_json_from_response(generated_text)
            if json_data:
                tool_calls = _parse_tool_calls(json_data)
                if tool_calls:
                    # 도구 호출이 있으면 content는 비움
                    content = ""

        # AIMessage 생성
        if tool_calls:
            message = AIMessage(content=content, tool_calls=tool_calls)
        else:
            message = AIMessage(content=content)

        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """LangChain 메시지를 EXAONE 채팅 형식으로 변환."""
        chat_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                chat_messages.append({"role": "system", "content": str(msg.content)})
            elif isinstance(msg, HumanMessage):
                chat_messages.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                content = str(msg.content)
                # tool_calls가 있으면 JSON으로 변환
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls_json = [
                        {"name": tc["name"], "arguments": tc.get("args", {})}
                        for tc in msg.tool_calls
                    ]
                    if len(tool_calls_json) == 1:
                        content = json.dumps(tool_calls_json[0], ensure_ascii=False)
                    else:
                        content = json.dumps(tool_calls_json, ensure_ascii=False)
                chat_messages.append({"role": "assistant", "content": content})
            elif isinstance(msg, ToolMessage):
                # ToolMessage를 user 메시지로 변환 (도구 결과)
                tool_result = (
                    f"[도구 결과] {msg.name}: {msg.content}"
                    if hasattr(msg, "name")
                    else f"[도구 결과]: {msg.content}"
                )
                chat_messages.append({"role": "user", "content": tool_result})
        return chat_messages

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """메시지를 기반으로 스트리밍 응답 생성.

        TextIteratorStreamer를 사용하여 토큰 단위 스트리밍을 지원합니다.
        """
        # 도구가 바인딩되어 있으면 시스템 프롬프트에 추가
        if self._tools:
            tool_prompt = self._create_tool_system_prompt()
            has_system = any(isinstance(m, SystemMessage) for m in messages)

            if has_system:
                new_messages = []
                for msg in messages:
                    if isinstance(msg, SystemMessage):
                        combined_content = f"{msg.content}\n\n{tool_prompt}"
                        new_messages.append(SystemMessage(content=combined_content))
                    else:
                        new_messages.append(msg)
                messages = new_messages
            else:
                messages = [SystemMessage(content=tool_prompt)] + list(messages)

        # 메시지를 EXAONE 채팅 형식으로 변환
        chat_messages = self._convert_messages(messages)

        # 채팅 템플릿 적용
        input_ids = self._tokenizer.apply_chat_template(
            chat_messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self._model.device)

        # 생성 파라미터
        max_new_tokens = kwargs.get("max_new_tokens", 2048)
        temperature = kwargs.get("temperature", 0.7)
        do_sample = kwargs.get("do_sample", True)

        # 동적 KV 캐시 최적화: 입력 길이에 따라 max_length 조정 (메모리 절약)
        input_length = input_ids.shape[1]
        max_length = kwargs.get("max_length", None)
        if max_length is None:
            # 동적 조정: 입력 길이에 따라 KV 캐시 크기 결정
            max_length = get_adaptive_max_length(input_length, max_new_tokens)
        else:
            # 사용자가 지정한 경우, 동적 조정과 비교하여 작은 값 사용
            adaptive_max = get_adaptive_max_length(input_length, max_new_tokens)
            max_length = min(max_length, adaptive_max)

        # TextIteratorStreamer 설정
        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        # 생성 kwargs (메모리 효율적인 옵션 적용)
        generation_kwargs = {
            "input_ids": input_ids,
            "max_new_tokens": max_new_tokens,
            "max_length": max_length,  # 동적 KV 캐시 최적화
            "temperature": temperature if do_sample else None,
            "do_sample": do_sample,
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
            "streamer": streamer,
            "use_cache": True,  # KV 캐시 활성화 (속도 향상)
            "num_beams": 1,  # 그리디 디코딩 (빠른 생성)
            # 메모리 효율 옵션 추가
            "output_attentions": False,  # Attention 출력 비활성화 (메모리 절약)
            "output_hidden_states": False,  # Hidden states 출력 비활성화 (메모리 절약)
            "return_dict_in_generate": False,  # Dict 대신 Tensor 반환 (메모리 절약)
        }

        # 별도 스레드에서 생성 실행
        def generate_in_thread():
            with torch.no_grad(), torch.cuda.amp.autocast():
                self._model.generate(**generation_kwargs)

        thread = threading.Thread(target=generate_in_thread)
        thread.start()

        # 스트리머에서 토큰 읽어서 yield
        generated_text = ""
        for new_text in streamer:
            if new_text:
                generated_text += new_text
                chunk = ChatGenerationChunk(message=AIMessageChunk(content=new_text))
                if run_manager:
                    run_manager.on_llm_new_token(new_text, chunk=chunk)
                yield chunk

        thread.join()

        # 도구 호출 파싱 (스트리밍 완료 후)
        if self._tools and generated_text:
            json_data = _extract_json_from_response(generated_text)
            if json_data:
                tool_calls = _parse_tool_calls(json_data)
                if tool_calls:
                    # 도구 호출이 감지되면 마지막 청크에 tool_calls 포함
                    final_chunk = ChatGenerationChunk(
                        message=AIMessageChunk(content="", tool_calls=tool_calls)
                    )
                    yield final_chunk

    @property
    def _llm_type(self) -> str:
        return "exaone"


def load_exaone_model(
    model_path: Optional[str] = None,
    model_id: str = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct",
    register: bool = True,
    is_default: bool = False,
) -> ExaoneLLM:
    """EXAONE 모델 로드 및 등록.

    Args:
        model_path: 로컬 모델 경로 (None이면 현재 디렉토리 또는 model_id 사용)
        model_id: HuggingFace 모델 ID
        register: LLMFactory에 등록할지 여부
        is_default: 기본 모델로 설정할지 여부

    Returns:
        ExaoneLLM: 로드된 EXAONE 모델 인스턴스
    """
    # 모델 경로 결정
    if model_path is None:
        current_dir = Path(__file__).parent
        exaone_dir = current_dir / "exaone"
        if exaone_dir.exists() and (exaone_dir / "config.json").exists():
            model_path = str(exaone_dir)
        elif (current_dir / "config.json").exists():
            model_path = str(current_dir)
        else:
            model_path = None  # model_id 사용

    # 모델 생성
    model = ExaoneLLM(
        model_path=model_path,
        model_id=model_id,
        device_map="auto",
        torch_dtype="auto",
        trust_remote_code=True,
    )

    # 등록
    if register:
        from core.llm.factory import LLMFactory  # type: ignore

        LLMFactory.register("exaone", model, is_default=is_default)
        print(
            f"[OK] EXAONE 모델이 LLMFactory에 등록되었습니다. (기본 모델: {is_default})"
        )

    return model
