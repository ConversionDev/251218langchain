"""
LangGraph 기반의 추론 상태 및 흐름도

스팸 감지 도메인의 LangGraph 워크플로우를 정의합니다.
규칙/정책 기반 분기 구조를 사용합니다.

아키텍처 원칙:
- LLaMA: 리더기 역할 + 규칙/정책 판단 + 규칙 기반 최종 결정
- 규칙 기반: LLaMA 결과를 최종 결정으로 직접 사용
- 정책 기반: Policy Service (EXAONE 사용) → EXAONE 결과를 최종 결정으로 사용
"""

from typing import Any

# Orchestrator에서 checkpointer import
from domain.v1.chat.orchestrator.checkpointer import (
    get_checkpointer,  # type: ignore
)
from domain.v1.spam.models.state_model import (
    SpamDetectionState,  # type: ignore
)
from langgraph.graph import END, StateGraph

# 도메인 노드들 import (모든 노드를 nodes/에서 통합 import)
# Gateway 노드 import (같은 폴더)
from .gateway_node import gateway_node  # type: ignore

# 도메인 노드들은 nodes/에서 import
from .nodes import (  # type: ignore
    final_decision_node,
    policy_node,
)


def routing_decision(state: SpamDetectionState) -> str:
    """라우팅 결정 함수.

    Gateway에서 규칙/정책 기반으로 분기합니다.

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름 ("final_decision" 또는 "policy_service")
    """
    routing_strategy = state.get("routing_strategy")

    if routing_strategy == "rule":
        # 규칙 기반: LLaMA 결과를 최종 결정으로 직접 사용
        return "final_decision"
    elif routing_strategy == "policy":
        # 정책 기반: EXAONE을 사용하여 분석
        return "policy_service"
    else:
        # 기본값: 정책 기반 (안전한 선택)
        print(
            f"[WARNING] routing_strategy가 없거나 알 수 없는 값: {routing_strategy}. 정책 기반으로 진행합니다."
        )
        return "policy_service"


def build_spam_detection_graph():
    """스팸 감지 Graph 빌드 (규칙/정책 분기 구조).

    Gateway → [규칙/정책 분기] → Final Decision 구조를 사용합니다.
    - 규칙 기반: LLaMA 결과를 최종 결정으로 직접 사용
    - 정책 기반: Policy Service (EXAONE 사용) → EXAONE 결과를 최종 결정으로 사용

    Returns:
        컴파일된 StateGraph (checkpointer 포함)
    """
    checkpointer = get_checkpointer()
    g = StateGraph(SpamDetectionState)

    # 노드 추가
    g.add_node("gateway", gateway_node)  # Gateway Node (LLaMA 리더기 + 규칙/정책 판단)
    g.add_node("policy_service", policy_node)  # 정책 기반 처리 노드 (EXAONE 사용)
    g.add_node("final_decision", final_decision_node)  # 최종 결정

    # 엣지 설정
    g.set_entry_point("gateway")

    # Gateway → 규칙/정책 분기 (조건부 엣지)
    g.add_conditional_edges(
        "gateway",
        routing_decision,
        {
            "final_decision": "final_decision",  # 규칙 기반: 바로 Final Decision
            "policy_service": "policy_service",  # 정책 기반: Policy Service 거쳐서
        },
    )

    # 정책 기반 경로: Policy Service → Final Decision
    g.add_edge("policy_service", "final_decision")

    # 최종 결정 → END
    g.add_edge("final_decision", END)

    # checkpointer와 함께 컴파일
    return g.compile(checkpointer=checkpointer)


# 스팸 감지 그래프 인스턴스 캐시
_spam_detection_graph: Any = None


def get_spam_detection_graph():
    """스팸 감지 그래프 인스턴스 반환 (lazy loading).

    Returns:
        컴파일된 StateGraph
    """
    global _spam_detection_graph
    if _spam_detection_graph is None:
        _spam_detection_graph = build_spam_detection_graph()
    return _spam_detection_graph


def run_spam_detection_graph(email_metadata: dict) -> dict:
    """스팸 감지 그래프를 실행합니다.

    Args:
        email_metadata: 이메일 메타데이터
            - subject: 제목
            - sender: 발신자
            - body: 본문 (선택)
            - recipient: 수신자 (선택)
            - date: 날짜 (선택)
            - attachments: 첨부파일 목록 (선택)
            - headers: 이메일 헤더 (선택)

    Returns:
        스팸 감지 결과
            - action: 최종 액션
            - reason_codes: 이유 코드
            - user_message: 사용자 메시지
            - confidence: 신뢰도
            - spam_prob: 스팸 확률
            - llama_result: LLaMA 결과
            - exaone_result: EXAONE 결과 (정책 기반인 경우)
            - routing_path: 라우팅 경로
    """
    import uuid

    # 그래프 가져오기
    graph = get_spam_detection_graph()

    # 초기 상태 구성
    initial_state: SpamDetectionState = {
        "email_metadata": email_metadata,
        "llama_result": None,
        "exaone_result": None,
        "routing_strategy": None,
        "routing_path": "",
        "messages": [],
    }

    # 그래프 실행 (thread_id 자동 생성)
    config = {"configurable": {"thread_id": f"spam_{uuid.uuid4().hex[:8]}"}}

    try:
        result = graph.invoke(initial_state, config=config)

        # final_decision 딕셔너리에서 결과 추출
        final_decision = result.get("final_decision", {})

        # 결과 반환
        return {
            "action": final_decision.get("action", "deliver"),
            "reason_codes": final_decision.get("reason_codes", []),
            "user_message": final_decision.get("user_message", ""),
            "confidence": final_decision.get("confidence", "low"),
            "spam_prob": final_decision.get("spam_prob", 0.0),
            "llama_result": result.get("llama_result", {}),
            "exaone_result": result.get("exaone_result"),
            "routing_strategy": result.get("routing_strategy"),  # 라우팅 전략 추가
            "routing_path": result.get("routing_path", ""),
        }
    except Exception as e:
        print(f"[ERROR] 스팸 감지 그래프 실행 실패: {e}")
        return {
            "action": "deliver",
            "reason_codes": ["GRAPH_ERROR"],
            "user_message": f"스팸 감지 처리 중 오류 발생: {str(e)}",
            "confidence": "low",
            "spam_prob": 0.0,
            "llama_result": {},
            "exaone_result": None,
            "routing_strategy": None,
            "routing_path": "Error",
        }
