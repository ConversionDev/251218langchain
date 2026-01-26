"""
LangGraph 노드 모듈 (일반 에이전트용)

일반 에이전트 워크플로우에서 사용하는 공통 노드들을 export합니다.

구조:
- base.py: 공통 헬퍼 함수 (LangChain LLM 관리)
- agent_nodes.py: 일반 에이전트 노드 (RAG, Model, Tool)

참고: 도메인별 노드는 각 도메인 내부에 있습니다.
예: 스팸 감지 노드는 domains/spam/agents/nodes/에 있습니다.

모든 노드는 LangGraph 노드 인터페이스를 구현합니다:
- 입력: State (AgentState 또는 SpamDetectionState)
- 출력: Dict[str, Any] (State 업데이트)

일부 노드는 내부적으로 LangChain 컴포넌트를 사용합니다:
- BaseChatModel: LLM 인터페이스
- ToolMessage: 툴 실행 결과 변환
- PGVector: 벡터 스토어 검색
"""

# 일반 에이전트 노드
from .agent_nodes import model_node, rag_node, tool_node

__all__ = [
    # 일반 에이전트 노드
    "model_node",
    "tool_node",
    "rag_node",
]
