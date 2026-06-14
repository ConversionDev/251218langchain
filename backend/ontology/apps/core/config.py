"""
애플리케이션 설정 모듈.

Pydantic BaseSettings를 사용하여 환경 변수를 타입 안전하게 관리합니다.
순환 의존성을 피하기 위한 중앙 설정 모듈입니다.
"""

from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.paths import get_project_root  # type: ignore


class Settings(BaseSettings):
    """애플리케이션 설정 클래스.

    환경 변수에서 설정을 자동으로 읽어옵니다.
    .env 파일도 자동으로 지원합니다.
    """

    model_config = SettingsConfigDict(
        env_file=str(get_project_root() / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===================
    # 데이터베이스 설정
    # ===================
    database_url: Optional[str] = Field(
        default=None,
        description="DATABASE_URL 환경 변수",
    )

    db_batch_chunk_size: int = Field(
        default=500,
        ge=1,
        le=5000,
        description="DB 배치 저장 시 청크 크기 (성능·메모리 균형)",
    )

    sslmode: str = Field(
        default="require",
        description="SSL 모드",
    )

    postgres_connection_string: Optional[str] = Field(
        default=None,
        description="PostgreSQL 연결 문자열 (fallback)",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def connection_string(self) -> str:
        """PostgreSQL 연결 문자열.

        DATABASE_URL이 있으면 sslmode를 추가하고,
        없으면 POSTGRES_CONNECTION_STRING 또는 기본값을 사용합니다.
        """
        if self.database_url:
            from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
            parsed = urlparse(self.database_url)
            query = parse_qs(parsed.query)
            # channel_binding=require 시 EC2(일부 libpq)에서 invalid value 오류 나는 경우 방지
            query.pop("channel_binding", None)
            if "sslmode" not in query:
                query["sslmode"] = [self.sslmode]
            new_query = urlencode(query, doseq=True)
            clean = urlunparse(parsed._replace(query=new_query))
            return clean

        # POSTGRES_CONNECTION_STRING이 있으면 사용
        if self.postgres_connection_string:
            return self.postgres_connection_string

        raise ValueError(
            "DATABASE_URL 또는 POSTGRES_CONNECTION_STRING 환경 변수가 설정되지 않았습니다. "
            ".env 파일을 확인하세요."
        )

    # ===================
    # LLM 설정
    # ===================
    llm_provider: str = Field(
        default="exaone",
        description="텍스트 채팅 LLM: exaone(GPU) | llama_cpp(CPU GGUF). 이미지는 gemini_adapter 별도.",
    )

    # ===================
    # DB·마이그레이션 설정
    # ===================
    auto_migrate: bool = Field(
        default=True,
        description="Alembic 마이그레이션 자동 실행 여부",
    )

    migration_revision: str = Field(
        default="head",
        description="적용할 마이그레이션 버전 (기본값: head)",
    )

    exaone_model_dir: Optional[str] = Field(
        default=None,
        description="(미사용) EXAONE 베이스/어댑터는 HF 캐시 및 core.paths 출력 경로만 사용",
    )

    # ===================
    # 임베딩 설정
    # ===================
    embedding_device: Optional[str] = Field(
        default=None,
        description="임베딩 디바이스 (cuda, cpu 등)",
    )

    default_embedding_model: str = Field(
        default="BAAI/bge-m3",
        description="RAG·임베딩 공용 모델 (Disclosure 등, FlagEmbedding BGE-m3)",
    )

    # ===================
    # 서버 설정
    # ===================
    host: str = Field(
        default="127.0.0.1",
        description="서버 호스트",
    )

    port: int = Field(
        default=8000,
        description="서버 포트",
    )

    debug_streaming: bool = Field(
        default=False,
        description="스트리밍 디버그 로깅 활성화",
    )

    cors_origins: Optional[str] = Field(
        default=None,
        description="CORS 허용 오리진. 쉼표 구분 (예: https://app.example.com,https://www.example.com). 비어 있으면 * (전체 허용).",
    )

    # ===================
    # EXAONE 최적화 설정
    # ===================
    exaone_use_compile: bool = Field(
        default=False,
        description="torch.compile() 최적화 활성화 (첫 실행 시 컴파일 시간 필요)",
    )

    exaone_use_4bit: bool = Field(
        default=True,
        description="4-bit 양자화 사용 여부",
    )

    exaone_use_competency_adapter: bool = Field(
        default=True,
        description="역량 SFT 어댑터(competency_adapters) 로드 여부. True면 artifacts/fine_tuned/exaone/competency_adapters 사용",
    )

    exaone_prequantized_dir: Optional[str] = Field(
        default=None,
        description=(
            "사전 양자화된 EXAONE 모델 저장 경로. "
            "scripts/save_bnb_quantized.py 를 한 번 실행하면 해당 경로에 NF4 가중치가 저장됨. "
            "이후 서버 시작 시 re-quantization 없이 ~4GB 파일만 읽으므로 로딩 속도가 대폭 개선됨. "
            "비어 있으면 artifacts/fine_tuned/exaone/prequantized_bnb4 를 자동 감지."
        ),
    )

    exaone_gguf_path: Optional[str] = Field(
        default=None,
        description=(
            "LLM_PROVIDER=llama_cpp 일 때 로드할 GGUF 파일 경로. "
            "비어 있으면 EXAONE_GGUF_PATH 환경변수 또는 artifacts/fine_tuned/exaone/gguf/exaone_competency_q4_k_m.gguf"
        ),
    )

    exaone_gguf_n_ctx: int = Field(
        default=8192,
        ge=2048,
        le=131072,
        description="llama.cpp 컨텍스트 길이 (GGUF 추론 시)",
    )

    # ===================
    # LLaMA (스팸 분류)
    # ===================
    llama_model_id: str = Field(
        default="unsloth/Llama-3.2-3B-Instruct",
        description="LLaMA 스팸 분류 베이스 모델 ID (HF). 학습·추론 공통.",
    )
    llama_use_spam_adapter: bool = Field(
        default=True,
        description="스팸 LoRA 어댑터 로드 여부. True면 artifacts/fine_tuned/llama/spam_adapters 사용.",
    )
    spam_classifier: str = Field(
        default="llama",
        description=(
            "스팸 1차 분류기 선택. llama=학습된 LLaMA 어댑터(transformers, 로컬/GPU 권장). "
            "gemini=Gemini API로 분류(배포 권장 — CPU에서 무거운 LLaMA 미로드). "
            "gemini 실패 시 UNCERTAIN으로 안전 처리(LLaMA 폴백 안 함)."
        ),
    )
    spam_agent_escalation: bool = Field(
        default=False,
        description=(
            "애매한 스팸 판정(low confidence/UNCERTAIN 등)을 LLM으로 에스컬레이션할지. "
            "기본 False(결정론 파이프라인만). 실패 시 기존 판정을 유지한다."
        ),
    )
    spam_agent_llm: str = Field(
        default="auto",
        description=(
            "에스컬레이션 판정 LLM 선택. auto=현재 llm_provider 사용(로컬: 학습/로컬 모델). "
            "gemini=Gemini로 판정(배포 권장, CPU에서 견고). exaone|llama_cpp도 지정 가능."
        ),
    )

    # ===================
    # API 키
    # ===================
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API 키",
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Gemini API 키 (멀티모달 채팅용)",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini 모델 ID (예: gemini-2.5-flash, gemini-2.0-flash). 404 시 공식 문서 모델명 확인.",
    )

    # ===================
    # Mailgun (수신 Webhook + 발송)
    # ===================
    mailgun_webhook_signing_key: Optional[str] = Field(
        default=None,
        description="Mailgun Webhook Signing Key (HMAC 검증). 대시보드에서 확인.",
    )
    mailgun_skip_verify: bool = Field(
        default=False,
        description="True면 Mailgun HMAC 검증 생략 (로컬/개발용).",
    )
    mailgun_api_key: Optional[str] = Field(
        default=None,
        description="Mailgun API Key (발송용). 대시보드 API Keys에서 'Mail' 키.",
    )
    mailgun_domain: Optional[str] = Field(
        default=None,
        description="발송 도메인 (예: mg.kanggyeonggu.store). 메일건에 등록된 도메인.",
    )

    # ===================
    # 채팅 첨부 업로드 (BP: /api/agent/upload)
    # ===================
    upload_dir: Optional[str] = Field(
        default=None,
        description="업로드 파일 임시 저장 디렉터리 (비어 있으면 시스템 temp/rag_upload)",
    )
    upload_max_files: int = Field(
        default=5,
        ge=1,
        le=20,
        description="업로드 최대 파일 개수",
    )
    upload_max_file_size_mb: float = Field(
        default=5.0,
        ge=0.5,
        le=20.0,
        description="채팅 첨부 파일당 최대 크기(MB)",
    )
    resume_max_file_size_mb: float = Field(
        default=10.0,
        ge=1.0,
        le=50.0,
        description="이력서 파일 최대 크기(MB)",
    )

    # ===================
    # Upstash Redis (임베딩 job 큐)
    # 단일 URL(UPSTASH_REDIS_URL)에서 REST URL·TOKEN을 자동 추출.
    # 하위호환을 위해 REST 전용 env도 그대로 지원.
    # ===================
    upstash_redis_url: Optional[str] = Field(
        default=None,
        description="UPSTASH_REDIS_URL (rediss://default:TOKEN@HOST:6379) — 단일 연결 URL",
    )
    upstash_redis_rest_url: Optional[str] = Field(
        default=None,
        description="UPSTASH_REDIS_REST_URL (.env에서 로드, 없으면 URL에서 추출)",
    )
    upstash_redis_rest_token: Optional[str] = Field(
        default=None,
        description="UPSTASH_REDIS_REST_TOKEN (.env에서 로드, 없으면 URL에서 추출)",
    )

    # ===================
    # Hub MCP HTTP 서비스 (Fractal Star 아키텍처)
    # hub/mcp = Llama·ExaOne 호출 수신, spokes = hub를 HTTP로 호출
    # ===================
    hub_service_url: str = Field(
        default="http://127.0.0.1:8000",
        description="Hub MCP Base URL (Llama·ExaOne 엔드포인트 호스트)",
    )

    # ===================
    # 도메인 MCP URL (Central → MCP → Spoke, call_tool)
    # 기본값: 동일 프로세스(8000) 마운트. 별도 프로세스는 CHAT_MCP_URL=.../9011/server 등으로 지정.
    # ===================
    chat_mcp_url: str = Field(
        default="http://127.0.0.1:8000/internal/mcp/chat/server",
        description="Chat MCP 서버 URL (Hub가 call_tool로 호출)",
    )
    chat_spoke_mcp_url: str = Field(
        default="http://127.0.0.1:8000/internal/mcp/chat-spoke/server",
        description="Chat Spoke MCP URL (Chat MCP가 call_tool로 호출)",
    )
    spam_mcp_url: str = Field(
        default="http://127.0.0.1:9021/server",
        description="Spam MCP 서버 URL (Central이 call_tool로 호출)",
    )
    spam_spoke_mcp_url: str = Field(
        default="http://127.0.0.1:9022/server",
        description="Spam Spoke MCP URL (Spam MCP가 call_tool로 호출)",
    )


# 전역 설정 인스턴스 (싱글톤)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """설정 싱글톤 반환.

    Returns:
        Settings 인스턴스

    Note:
        지연 초기화를 사용하여 필요할 때만 설정을 로드합니다.
        전역 `settings` 변수는 하위 호환성을 위해 유지됩니다.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# 하위 호환성을 위한 전역 settings 변수
settings = get_settings()
