"""
LLaMA 스팸 분류 게이트 (training 등 호환용).

Hub domain.hub.llm.llama_classifier.LLaMAGate를 재내보냅니다.
동일 프로세스에서는 LlamaManager 공유.
"""

from domain.hub.llm.llama_classifier import LLaMAGate  # type: ignore

__all__ = ["LLaMAGate"]
