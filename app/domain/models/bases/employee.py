"""
직원(Employee) 도메인 ORM — employees 단일 테이블.

Core 직원 등록/수정/삭제 및 직무 처리(부서 매칭 등)용.
프론트 Employee 타입과 필드 매핑 (snake_case 컬럼).
"""

import pgvector.sqlalchemy  # type: ignore[import-untyped]
from sqlalchemy import Column, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base  # type: ignore
from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore


class Employee(Base):  # type: ignore[misc]
    """직원 한 건. 이력서·Success DNA·IFRS 지표 등 포함."""

    __tablename__ = "employees"

    id = Column(String(64), primary_key=True, comment="직원 ID (예: E001)")
    name = Column(String(256), nullable=False, comment="이름")
    job_title = Column(String(256), nullable=False, server_default="", comment="직급")
    department = Column(String(256), nullable=False, server_default="", comment="부서")
    email = Column(String(512), nullable=True, comment="이메일")
    application_date = Column(DateTime(timezone=True), nullable=True, comment="지원서 제출일시 (UTC, 시분초 포함)")
    joined_at = Column(String(32), nullable=True, comment="입사일 YYYY-MM-DD (입사 확정 후 설정)")
    status = Column(String(32), nullable=True, comment="채용 상태: pending(미검토)|screening(심사 중)|hired(합격)|rejected(탈락)")
    success_dna = Column(JSONB(), nullable=True, comment="Success DNA 5대 역량")
    success_dna_reason = Column(Text(), nullable=True, comment="AI 평가 근거 (점수 산정 이유, ATS 관리자 표시용)")
    rejection_reason = Column(Text(), nullable=True, comment="탈락 사유 (ATS 관리자 입력, 이의 제기·감사 대응용)")
    behavioral_dna = Column(JSONB(), nullable=True, comment="비정형 분석 기반 역량")
    behavioral_source = Column(Text(), nullable=True, comment="behavioralDna 출처 요약")
    behavioral_source_items = Column(JSONB(), nullable=True, comment="회의록/이메일 등 원문 목록")
    disclosure_metrics = Column(
        JSONB(), nullable=True, comment="공시 지표(다중 표준). IFRS/ISO 30414 등. docs/disclosure-metrics-design.md"
    )
    gender = Column(String(32), nullable=True, comment="성별 (남/여/미기입)")
    age = Column(Integer(), nullable=True, comment="연령(만 나이). 연령대는 age로 파생.")
    employment_type = Column(String(32), nullable=True, comment="고용 형태")
    training_hours = Column(Integer(), nullable=True, comment="연간 교육훈련 시간")
    resume = Column(JSONB(), nullable=True, comment="이력서 학력·경력·스킬·자격증")
    resume_text = Column(Text(), nullable=True, comment="이력서 원본 추출 텍스트 (ATS AI 분석용 원문 보존)")
    resume_file_hash = Column(String(64), nullable=True, comment="이력서 파일 SHA-256, 동일 이력서 중복 방지")
    matched_department = Column(String(256), nullable=True, comment="추천 부서")
    embedding_content = Column(Text(), nullable=True, comment="RAG 임베딩용 텍스트")
    embedding = Column(pgvector.sqlalchemy.Vector(BGE_M3_DENSE_DIM), nullable=True, comment="BGE-m3 1024차원, RAG 검색용")  # type: ignore[var-annotated]
    created_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="생성 시각")
    updated_at = Column(DateTime(), server_default=text("now()"), nullable=True, comment="수정 시각")
