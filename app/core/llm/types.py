"""LLM 모델 타입 정의."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """LLM 응답 모델."""

    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingResponse(BaseModel):
    """Embedding 응답 모델."""

    embedding: List[float]
    model: str
    dimensions: int
    metadata: Optional[Dict[str, Any]] = None

