"""
LLaMAGate - Hub의 스팸 분류 진입점.

Hub 공통 Llama 로더를 쓰는 LLaMAClassifier(Spoke)를 한 번만 로드해 classify_spam / classify_spam_batch 제공.
"""

from typing import Any, Dict, List

_spam_classifier: Any = None


def _get_classifier():
    """LLaMAClassifier 싱글톤 (lazy). LlamaManager 베이스 사용."""
    global _spam_classifier
    if _spam_classifier is None:
        from domain.spokes.spam.services.semantic_classifier import LLaMAClassifier  # type: ignore

        _spam_classifier = LLaMAClassifier()
        _spam_classifier.load_model()
    return _spam_classifier


class LLaMAGate:
    """스팸 분류 게이트. 동일 프로세스에서 Hub LlamaManager 공유."""

    def classify_spam(self, email_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """단건 스팸 분류."""
        return _get_classifier().predict(email_metadata)

    def classify_spam_batch(
        self,
        email_metadata_list: List[Dict[str, Any]],
        batch_size: int = 32,
    ) -> List[Dict[str, Any]]:
        """배치 스팸 분류."""
        return _get_classifier().predict_batch(email_metadata_list)
