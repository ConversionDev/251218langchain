"""
😎😎 chat_service_t.py 서빙 관련 서비스

PEFT QLoRA 방식으로 대화하고 학습하는 기능 포함.

세션별 히스토리 관리, 요약, 토큰 절약 전략 등.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from datasets import Dataset
from peft import (
    LoraConfig,
    PeftModel,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    TrainingArguments,
)

try:
    from trl import SFTTrainer
except ImportError:
    from trl.trainer.sft_trainer import SFTTrainer


class ChatServiceQLoRA:
    """QLoRA를 사용한 채팅 및 학습 서비스."""

    def __init__(
        self,
        model_name_or_path: str,
        output_dir: str = "./qlora_output",
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        device_map: str = "auto",
    ):
        """QLoRA 채팅 서비스 초기화.

        Args:
            model_name_or_path: 모델 이름 또는 경로
            output_dir: 학습 결과 저장 디렉토리
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            target_modules: LoRA를 적용할 모듈 목록 (None이면 자동 감지)
            device_map: 디바이스 매핑 ("auto", "cpu", "cuda" 등)
        """
        self.model_name_or_path = model_name_or_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # QLoRA 설정 (4-bit quantization)
        self.bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        # LoRA 설정
        if target_modules is None:
            # 일반적인 모델의 attention 모듈 (Llama, Mistral 등)
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]

        self.lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=target_modules,
            lora_dropout=lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

        # 모델 및 토크나이저 로드
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[Any] = None
        self.peft_model: Optional[PeftModel] = None
        self.device_map = device_map

        # 세션별 대화 히스토리
        self.chat_sessions: Dict[str, List[Dict[str, str]]] = {}

    def load_model(self) -> None:
        """모델 및 토크나이저 로드."""
        print(f"[INFO] 모델 로딩 중: {self.model_name_or_path}")

        # 토크나이저 로드
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name_or_path,
            trust_remote_code=True,
        )

        # pad_token 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id

        self.tokenizer = tokenizer

        # 모델 로드 (4-bit quantization)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name_or_path,
            quantization_config=self.bnb_config,
            device_map=self.device_map,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )

        # PEFT 모델 준비
        model = prepare_model_for_kbit_training(model)

        # LoRA 적용
        peft_model = get_peft_model(model, self.lora_config)
        peft_model.print_trainable_parameters()

        self.model = model
        self.peft_model = peft_model

        print("[OK] 모델 로딩 완료")

    def load_peft_model(self, peft_model_path: str) -> None:
        """학습된 PEFT 모델 로드.

        Args:
            peft_model_path: PEFT 모델 경로
        """
        if self.model is None:
            raise RuntimeError("먼저 load_model()을 호출하세요.")

        print(f"[INFO] PEFT 모델 로딩 중: {peft_model_path}")
        self.peft_model = PeftModel.from_pretrained(
            self.model, peft_model_path, device_map=self.device_map
        )
        print("[OK] PEFT 모델 로딩 완료")

    def chat(
        self,
        message: str,
        session_id: str = "default",
        history: Optional[List[Dict[str, str]]] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """대화 생성.

        Args:
            message: 사용자 메시지
            session_id: 세션 ID
            history: 대화 기록 (None이면 세션 히스토리 사용)
            max_new_tokens: 최대 생성 토큰 수
            temperature: 생성 온도
            top_p: nucleus sampling 파라미터

        Returns:
            생성된 응답
        """
        if self.peft_model is None:
            raise RuntimeError("먼저 load_model() 또는 load_peft_model()을 호출하세요.")

        # 세션 히스토리 가져오기
        if history is None:
            history = self.chat_sessions.get(session_id, [])

        # 대화 형식으로 프롬프트 구성
        prompt = self._format_chat_prompt(message, history)

        # 토크나이징
        if self.tokenizer is None:
            raise RuntimeError("토크나이저가 초기화되지 않았습니다.")

        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=2048
        ).to(self.peft_model.device)

        # 생성
        with torch.no_grad():
            outputs = self.peft_model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
                if self.tokenizer.pad_token_id
                else self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # 디코딩
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 응답만 추출 (프롬프트 제외)
        response = generated_text[len(prompt) :].strip()

        # 히스토리 업데이트
        self.chat_sessions[session_id] = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response},
        ]

        return response

    def _format_chat_prompt(self, message: str, history: List[Dict[str, str]]) -> str:
        """대화 형식으로 프롬프트 구성.

        Args:
            message: 현재 메시지
            history: 대화 기록

        Returns:
            포맷된 프롬프트
        """
        prompt_parts = []

        # 시스템 프롬프트
        prompt_parts.append("당신은 도움이 되는 AI 어시스턴트입니다.")

        # 히스토리 추가
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"사용자: {content}")
            elif role == "assistant":
                prompt_parts.append(f"어시스턴트: {content}")

        # 현재 메시지 추가
        prompt_parts.append(f"사용자: {message}")
        prompt_parts.append("어시스턴트:")

        return "\n".join(prompt_parts)

    def train(
        self,
        training_data: List[Dict[str, str]],
        output_dir: Optional[str] = None,
        num_epochs: int = 3,
        per_device_train_batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 100,
        logging_steps: int = 10,
        save_steps: int = 500,
        max_seq_length: int = 512,
    ) -> str:
        """QLoRA 학습 실행.

        Args:
            training_data: 학습 데이터 ({"instruction": "...", "input": "...", "output": "..."} 형식)
            output_dir: 출력 디렉토리 (None이면 기본값 사용)
            num_epochs: 에폭 수
            per_device_train_batch_size: 배치 크기
            gradient_accumulation_steps: 그래디언트 누적 스텝
            learning_rate: 학습률
            warmup_steps: 워밍업 스텝
            logging_steps: 로깅 스텝
            save_steps: 저장 스텝
            max_seq_length: 최대 시퀀스 길이

        Returns:
            학습된 모델 경로
        """
        if self.peft_model is None:
            raise RuntimeError("먼저 load_model()을 호출하세요.")

        if self.tokenizer is None:
            raise RuntimeError("토크나이저가 초기화되지 않았습니다.")

        output_dir = output_dir or str(
            self.output_dir / f"checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

        # 데이터셋 준비
        def format_prompt(example):
            """프롬프트 포맷팅."""
            instruction = example.get("instruction", "")
            input_text = example.get("input", "")
            output = example.get("output", "")

            if input_text:
                prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
            else:
                prompt = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"

            return {"text": prompt}

        dataset = Dataset.from_list(training_data)
        dataset = dataset.map(format_prompt)

        # 학습 인자 설정
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            save_total_limit=3,
            fp16=False,  # QLoRA는 bfloat16 사용
            bf16=True,
            optim="paged_adamw_8bit",
            lr_scheduler_type="cosine",
            report_to="none",
        )

        # 데이터 콜레이터
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer, mlm=False
        )

        # 트레이너 생성
        trainer_kwargs: Dict[str, Any] = {
            "model": self.peft_model,
            "train_dataset": dataset,
            "peft_config": self.lora_config,
            "tokenizer": self.tokenizer,
            "args": training_args,
            "data_collator": data_collator,
            "max_seq_length": max_seq_length,
        }

        # packing 파라미터는 버전에 따라 선택적
        try:
            trainer = SFTTrainer(**trainer_kwargs, packing=False)  # type: ignore
        except TypeError:
            # packing 파라미터가 없는 경우
            trainer_kwargs.pop("packing", None)
            trainer = SFTTrainer(**trainer_kwargs)  # type: ignore

        # 학습 실행
        print("[INFO] 학습 시작...")
        trainer.train()
        print("[OK] 학습 완료")

        # 모델 저장
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)

        print(f"[OK] 모델 저장 완료: {output_dir}")
        return output_dir

    def train_from_chat_history(
        self,
        session_ids: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        **train_kwargs,
    ) -> str:
        """채팅 히스토리로부터 학습 데이터 생성 및 학습.

        Args:
            session_ids: 학습할 세션 ID 목록 (None이면 모든 세션)
            output_dir: 출력 디렉토리
            **train_kwargs: train() 메서드에 전달할 추가 인자

        Returns:
            학습된 모델 경로
        """
        # 학습 데이터 생성
        training_data = []

        if session_ids is None:
            session_ids = list(self.chat_sessions.keys())

        for session_id in session_ids:
            history = self.chat_sessions.get(session_id, [])
            if len(history) < 2:
                continue

            # 대화 쌍으로 변환
            for i in range(0, len(history) - 1, 2):
                if i + 1 < len(history):
                    user_msg = history[i].get("content", "")
                    assistant_msg = history[i + 1].get("content", "")

                    training_data.append(
                        {
                            "instruction": "다음 대화에 응답하세요.",
                            "input": user_msg,
                            "output": assistant_msg,
                        }
                    )

        if not training_data:
            raise ValueError("학습할 데이터가 없습니다.")

        print(f"[INFO] {len(training_data)}개의 학습 샘플 생성됨")

        # 학습 실행
        return self.train(training_data, output_dir=output_dir, **train_kwargs)

    def save_session(self, session_id: str, file_path: str) -> None:
        """세션 히스토리 저장.

        Args:
            session_id: 세션 ID
            file_path: 저장 경로
        """
        history = self.chat_sessions.get(session_id, [])
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"[OK] 세션 저장 완료: {file_path}")

    def load_session(self, session_id: str, file_path: str) -> None:
        """세션 히스토리 로드.

        Args:
            session_id: 세션 ID
            file_path: 로드 경로
        """
        with open(file_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        self.chat_sessions[session_id] = history
        print(f"[OK] 세션 로드 완료: {file_path}")

    def clear_session(self, session_id: str) -> None:
        """세션 히스토리 삭제.

        Args:
            session_id: 세션 ID
        """
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            print(f"[OK] 세션 삭제 완료: {session_id}")

    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """세션 히스토리 가져오기.

        Args:
            session_id: 세션 ID

        Returns:
            대화 기록 리스트
        """
        return self.chat_sessions.get(session_id, [])
