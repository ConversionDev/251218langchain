"""
LangGraph 도구 정의

에이전트가 사용할 수 있는 도구들을 정의합니다.
"""

import json
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool


@tool
def analyze_with_exaone(
    subject: str,
    sender: str,
    body: Optional[str] = None,
    recipient: Optional[str] = None,
    date: Optional[str] = None,
    attachments: Optional[List[str]] = None,
    headers: Optional[Dict[str, Any]] = None,
    _policy_context: Optional[str] = None,
) -> str:
    """EXAONE을 사용하여 이메일을 분석합니다.

    스팸 여부를 판단하고 위험 요소를 분석합니다.

    Args:
        subject: 이메일 제목
        sender: 발신자
        body: 이메일 본문 (선택)
        recipient: 수신자 (선택)
        date: 날짜 (선택)
        attachments: 첨부파일 목록 (선택)
        headers: 이메일 헤더 (선택)
        _policy_context: 정책 컨텍스트 (내부용)

    Returns:
        JSON 형식의 분석 결과
    """
    try:
        # EXAONE 모델 가져오기
        from core.resource_manager.exaone_manager import ExaoneManager  # type: ignore

        exaone_manager = ExaoneManager()
        exaone_model = exaone_manager.get_base_model()

        # 분석 프롬프트 구성
        email_text = f"제목: {subject}\n발신자: {sender}"
        if body:
            email_text += f"\n본문: {body}"
        if recipient:
            email_text += f"\n수신자: {recipient}"
        if attachments:
            email_text += f"\n첨부파일: {', '.join(attachments)}"

        policy_info = ""
        if _policy_context:
            policy_info = f"\n정책: {_policy_context}"

        # 최적화된 프롬프트 (명확한 기준 제시)
        prompt = f"""이메일 스팸 분석:
{email_text}{policy_info}

판단 기준:
- 스팸: 피싱, 사기, 광고성 링크, 개인정보 요청
- 정상: 일반 업무, 개인 소통, 일정 안내

confidence 기준:
- high: 명확한 스팸 또는 명확한 정상
- medium: 일부 의심 요소 있음
- low: 판단 어려움

JSON만 답변:
{{"is_spam": false, "confidence": "high", "risk_codes": [], "analysis": "분석내용"}}"""

        # EXAONE 호출 (max_new_tokens 256으로 최적화)
        response = exaone_model.invoke(prompt, max_new_tokens=256, temperature=0.3)
        raw_output = response if isinstance(response, str) else str(response)

        # JSON 파싱 시도
        try:
            # JSON 블록 추출
            import re

            json_match = re.search(r"\{[\s\S]*\}", raw_output)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = {
                    "is_spam": False,
                    "confidence": "low",
                    "risk_level": "low",
                    "risk_codes": [],
                    "analysis": raw_output,
                    "recommendation": "추가 검토 필요",
                }
        except json.JSONDecodeError:
            parsed = {
                "is_spam": False,
                "confidence": "low",
                "risk_level": "low",
                "risk_codes": [],
                "analysis": raw_output,
                "recommendation": "추가 검토 필요",
            }

        result = {
            "raw_output": raw_output,
            "parsed": parsed,
            "risk_codes": parsed.get("risk_codes", []),
        }

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "raw_output": f"EXAONE 분석 오류: {str(e)}",
            "parsed": {
                "is_spam": False,
                "confidence": "low",
                "risk_level": "low",
                "risk_codes": [],
                "analysis": f"분석 실패: {str(e)}",
                "recommendation": "수동 검토 필요",
            },
            "risk_codes": [],
        }
        return json.dumps(error_result, ensure_ascii=False)


@tool
def search_documents(query: str) -> str:
    """문서에서 관련 정보를 검색합니다.

    Args:
        query: 검색 쿼리

    Returns:
        검색 결과
    """
    # TODO: 실제 문서 검색 로직 구현
    return f"'{query}'에 대한 검색 결과가 없습니다."


@tool
def get_current_time() -> str:
    """현재 시간을 반환합니다.

    Returns:
        현재 시간 문자열
    """
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """수학 표현식을 계산합니다.

    Args:
        expression: 계산할 수학 표현식

    Returns:
        계산 결과
    """
    try:
        # 안전한 계산을 위해 eval 대신 제한된 평가
        allowed_chars = set("0123456789+-*/().% ")
        if not all(c in allowed_chars for c in expression):
            return "허용되지 않은 문자가 포함되어 있습니다."
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"계산 오류: {str(e)}"


# 사용 가능한 도구 목록
TOOLS = [
    analyze_with_exaone,
    search_documents,
    get_current_time,
    calculate,
]

# 도구 이름으로 빠른 접근을 위한 맵
TOOL_MAP: Dict[str, Any] = {tool.name: tool for tool in TOOLS}
