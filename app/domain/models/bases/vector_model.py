"""
벡터 DB 검색을 위한 스키마

정책 기반 검색을 위한 벡터 검색 모델 정의.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VectorSearchQuery(BaseModel):
    """벡터 검색 쿼리 모델."""

    query: str = Field(..., description="검색 쿼리")
    k: int = Field(default=3, description="반환할 문서 수")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="필터 조건")
    score_threshold: Optional[float] = Field(default=None, description="점수 임계값")


class VectorSearchResult(BaseModel):
    """벡터 검색 결과 모델."""

    documents: List[str] = Field(..., description="검색된 문서 내용")
    scores: List[float] = Field(default=[], description="유사도 점수")
    metadata: List[Dict[str, Any]] = Field(default=[], description="문서 메타데이터")

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return self.model_dump()
