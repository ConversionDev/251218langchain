"""
EXAONE 서비스 모델 정의

EXAONE 분석 결과 및 설정 모델.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExaoneResult(BaseModel):
    """EXAONE 분석 결과 모델."""

    raw_output: str = Field(..., description="EXAONE 모델의 원본 출력")
    parsed: Dict[str, Any] = Field(
        default_factory=dict, description="파싱된 분석 결과"
    )
    risk_codes: List[str] = Field(
        default_factory=list, description="위험 코드 리스트"
    )
    is_spam: Optional[bool] = Field(None, description="스팸 여부")
    confidence: str = Field(
        "medium", description="신뢰도 (high, medium, low)"
    )
    analysis: Optional[str] = Field(None, description="상세 분석 내용")
    error: Optional[str] = Field(None, description="오류 메시지 (있는 경우)")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return self.model_dump()


class ExaoneConfig(BaseModel):
    """EXAONE 설정 모델."""

    model_path: Optional[str] = Field(None, description="모델 경로")
    use_4bit: bool = Field(True, description="4-bit 양자화 사용 여부")
    device: str = Field("cuda", description="사용할 디바이스")
    trust_remote_code: bool = Field(True, description="원격 코드 신뢰 여부")
