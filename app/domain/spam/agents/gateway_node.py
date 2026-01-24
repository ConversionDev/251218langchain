"""
Gateway 노드

단일 진입점으로 요청을 수신하고 LLaMA 리더기를 통해 텍스트 정제/추출을 수행.
"""

from typing import Any, Dict, Optional

from .reader.llma_reader import LLaMAReader


# LLaMA 리더기 싱글톤
_llama_reader: Optional[LLaMAReader] = None


def _get_llama_reader() -> LLaMAReader:
    """LLaMA 리더기 싱글톤 인스턴스 반환."""
    global _llama_reader
    if _llama_reader is None:
        _llama_reader = LLaMAReader()
    return _llama_reader


class GatewayNode:
    """Gateway 노드 클래스.

    외부 요청을 수신하고 리더기를 통해 텍스트 정제/추출을 수행합니다.
    """

    @staticmethod
    def process(state: Dict[str, Any]) -> Dict[str, Any]:
        """Gateway 노드 처리.

        Args:
            state: 워크플로우 상태 (email_metadata 포함)

        Returns:
            업데이트된 상태 (llama_result 포함)
        """
        email_metadata = state.get("email_metadata", {})
        routing_path = state.get("routing_path", "Start")

        try:
            # LLaMA 리더기로 텍스트 정제/추출
            print("[DEBUG] Gateway 노드: LLaMA 리더기 가져오기 시작")
            reader = _get_llama_reader()
            print("[DEBUG] Gateway 노드: LLaMA 리더기 가져오기 완료, read() 호출 시작")
            result = reader.read(email_metadata)
            print(f"[DEBUG] Gateway 노드: read() 완료, routing_strategy={result.get('routing_strategy')}")

            new_routing_path = routing_path + " -> Gateway(LLaMA)"

            return {
                "email_metadata": result["email_metadata"],
                "llama_result": result["llama_result"],
                "routing_strategy": result.get("routing_strategy"),  # "rule" or "policy"
                "routing_path": new_routing_path,
            }
        except Exception as e:
            print(f"[ERROR] Gateway 노드 오류: {str(e)}")
            import traceback
            traceback.print_exc()

            # 오류 발생 시 기본값 반환
            return {
                "llama_result": {
                    "spam_prob": 0.5,
                    "confidence": "low",
                    "label": "UNCERTAIN",
                },
                "routing_path": routing_path + " -> Gateway(ERROR)",
            }


# LangGraph 노드 호환 함수
def gateway_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph용 Gateway 노드 함수."""
    return GatewayNode.process(state)
