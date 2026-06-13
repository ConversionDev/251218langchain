"""Backward-compat stub — 실제 구현은 infrastructure.orchestration.spam_orchestrator로 이동됨."""
from infrastructure.orchestration.spam_orchestrator import *  # noqa: F401,F403
from infrastructure.orchestration.spam_orchestrator import (  # noqa: F401
    SpamGatewayService,
    build_spam_detection_graph,
    get_spam_detection_graph,
    run_spam_detection,
)
