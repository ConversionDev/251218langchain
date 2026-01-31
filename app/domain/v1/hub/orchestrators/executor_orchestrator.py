"""
스팸 감지 실행 (v1)

run_spam_detection: 스팸 그래프 실행 진입점.
채팅 실행은 chat_orchestrator에서 직접 사용합니다.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def run_spam_detection(email_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """스팸 감지를 실행합니다.

    Args:
        email_metadata: 이메일 메타데이터

    Returns:
        스팸 감지 결과
    """
    try:
        from domain.v1.spokes.spam.agents.graph import run_spam_detection_graph  # type: ignore

        result = run_spam_detection_graph(email_metadata)
        logger.debug(
            "스팸 감지 완료: action=%s, routing_strategy=%s",
            result.get("action"),
            result.get("routing_strategy"),
        )
        return result
    except ImportError as e:
        logger.exception("스팸 감지 모듈 import 실패: %s", e)
        return {
            "action": "deliver",
            "reason_codes": ["MODULE_NOT_FOUND"],
            "user_message": "스팸 감지 모듈을 찾을 수 없습니다.",
            "confidence": "low",
            "spam_prob": 0.0,
            "llama_result": {
                "spam_prob": 0.0,
                "confidence": "low",
                "label": "HAM",
            },
            "exaone_result": None,
            "routing_strategy": None,
            "routing_path": "Default",
        }
    except Exception as e:
        logger.exception("스팸 감지 실행 중 오류: %s", e)
        return {
            "action": "deliver",
            "reason_codes": ["EXECUTION_ERROR"],
            "user_message": f"스팸 감지 처리 중 오류가 발생했습니다: {str(e)}",
            "confidence": "low",
            "spam_prob": 0.0,
            "llama_result": {
                "spam_prob": 0.0,
                "confidence": "low",
                "label": "UNCERTAIN",
            },
            "exaone_result": None,
            "routing_strategy": None,
            "routing_path": "Error",
        }
