"""
기본 데이터 구조 (Pydantic)

스팸 도메인의 기본 데이터 모델 정의.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EmailMetadata(BaseModel):
    """이메일 메타데이터 모델."""

    subject: str = Field(..., description="이메일 제목")
    sender: str = Field(..., description="발신자")
    recipient: Optional[str] = Field(default=None, description="수신자")
    body: Optional[str] = Field(default=None, description="이메일 본문")
    attachments: Optional[List[str]] = Field(default=[], description="첨부파일 목록")
    received_at: Optional[str] = Field(default=None, description="수신 일시")
    date: Optional[str] = Field(default=None, description="날짜")
    headers: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {}, description="이메일 헤더"
    )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return self.model_dump()


class LLaMAResult(BaseModel):
    """LLaMA 분류 결과 모델."""

    spam_prob: float = Field(..., description="스팸 확률 (0.0-1.0)")
    confidence: str = Field(..., description="신뢰도 (high, medium, low)")
    label: Optional[str] = Field(default=None, description="예측 라벨")
    raw_output: Optional[str] = Field(default=None, description="원본 출력")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return self.model_dump()



class SpamResult(BaseModel):
    """스팸 분류 결과 모델 (통합)."""

    action: str = Field(
        ...,
        description="최종 액션 (deliver, deliver_with_warning, quarantine, reject, ask_user_confirm)",
    )
    reason_codes: List[str] = Field(..., description="이유 코드 리스트")
    user_message: str = Field(..., description="사용자 메시지")
    confidence: str = Field(..., description="신뢰도 (high, medium, low)")
    spam_prob: float = Field(..., description="스팸 확률")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return self.model_dump()
