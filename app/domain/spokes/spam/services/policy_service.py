"""
정책 기반 서비스

정책 기반 판단을 수행합니다.
- PG Vector에서 정책 조회
- EXAONE으로 분석
- LLM 생성 결과 반환
"""

import json
from typing import Any, Dict, Optional

from domain.spokes.spam.repositories.policy_repository import (  # type: ignore
    PolicyRepository,
)


class PolicyService:
    """정책 기반 서비스.

    정책 기반 판단을 수행하며, EXAONE을 사용합니다.
    """

    def __init__(
        self,
        policy_repository: Optional[PolicyRepository] = None,
        exaone_provider: str = "exaone",
    ):
        """초기화.

        Args:
            policy_repository: 정책 저장소 (None이면 새로 생성)
            exaone_provider: EXAONE 프로바이더 이름
        """
        self._repository = policy_repository or PolicyRepository()
        self._exaone_provider = exaone_provider

    def process(
        self, email_metadata: Dict[str, Any], use_existing_policy: bool = True
    ) -> Dict[str, Any]:
        """정책 기반 처리.

        Args:
            email_metadata: 이메일 메타데이터
                - subject: 제목
                - sender: 발신자
                - body: 본문
                - attachments: 첨부파일 목록
            use_existing_policy: 기존 정책 사용 여부 (True면 PG Vector에서 조회)

        Returns:
            정책 기반 처리 결과
            {
                "is_spam": Optional[bool],
                "action": str,  # "reject", "allow", "quarantine", etc.
                "reason_codes": List[str],
                "confidence": str,  # "high", "medium", "low"
                "analysis": str,  # EXAONE 분석 내용
                "policy_id": Optional[str],
            }
        """
        # 1. 기존 정책 조회 (선택적)
        policies = []
        if use_existing_policy:
            query = self._format_email_query(email_metadata)
            policies = self._repository.search_policy(query, top_k=3)

        # 2. EXAONE으로 분석
        exaone_result = self._analyze_with_exaone(email_metadata, policies)

        # 3. 결과 파싱 및 반환
        return self._parse_exaone_result(exaone_result, policies)

    def _format_email_query(self, email_metadata: Dict[str, Any]) -> str:
        """이메일 메타데이터를 검색 쿼리로 변환.

        Args:
            email_metadata: 이메일 메타데이터

        Returns:
            검색 쿼리 문자열
        """
        subject = email_metadata.get("subject", "")
        sender = email_metadata.get("sender", "")
        body = email_metadata.get("body", "")[:500]  # 본문 일부만 사용

        return f"제목: {subject}\n발신자: {sender}\n내용: {body}"

    def _analyze_with_exaone(
        self, email_metadata: Dict[str, Any], policies: list
    ) -> Dict[str, Any]:
        """Spam MCP를 통해 EXAONE으로 이메일 분석."""
        try:
            from domain.spokes.spam.mcp.spam_server import _analyze_email_impl  # type: ignore

            policy_text = None
            if policies:
                policy_text = "\n".join([
                    f"- {policy.get('content', '')}" for policy in policies
                ])

            tool_result_json = _analyze_email_impl(
                subject=email_metadata.get("subject", ""),
                sender=email_metadata.get("sender", ""),
                body=email_metadata.get("body"),
                recipient=email_metadata.get("recipient"),
                date=email_metadata.get("date"),
                attachments=email_metadata.get("attachments"),
                headers=email_metadata.get("headers"),
                policy_context=policy_text,
            )

            tool_result = json.loads(tool_result_json)

            # 기존 형식으로 변환
            raw_output = tool_result.get("raw_output", "")
            parsed = tool_result.get("parsed", {})
            risk_codes = tool_result.get("risk_codes", [])

            # 정책 정보가 있으면 분석 내용에 추가
            if policies and parsed.get("analysis"):
                policy_summary = f"\n\n[참고 정책: {len(policies)}개]"
                parsed["analysis"] = parsed["analysis"] + policy_summary

            return {
                "raw_output": raw_output,
                "success": True,
                "parsed": parsed,
                "risk_codes": risk_codes,
            }
        except Exception as e:
            return {
                "raw_output": "",
                "success": False,
                "error": str(e),
            }


    def _parse_exaone_result(
        self, exaone_result: Dict[str, Any], policies: list
    ) -> Dict[str, Any]:
        """EXAONE 툴 결과 파싱.

        Args:
            exaone_result: EXAONE 툴 분석 결과 (이미 파싱된 형식)
            policies: 관련 정책 리스트

        Returns:
            파싱된 결과
        """
        if not exaone_result.get("success", False):
            return {
                "is_spam": None,
                "action": "ask_user_confirm",
                "reason_codes": ["EXAONE_ERROR"],
                "confidence": "low",
                "analysis": f"EXAONE 툴 분석 실패: {exaone_result.get('error', 'Unknown error')}",
                "policy_id": policies[0].get("policy_id") if policies else None,
            }

        # 툴 결과에서 파싱된 정보 가져오기
        parsed = exaone_result.get("parsed", {})
        raw_output = exaone_result.get("raw_output", "")
        risk_codes = exaone_result.get("risk_codes", [])

        # 결과 구성
        is_spam = parsed.get("is_spam")
        confidence = parsed.get("confidence", "medium")
        analysis = parsed.get("analysis", raw_output)

        # reason_codes는 risk_codes를 사용하거나 parsed에서 가져오기
        reason_codes = risk_codes if risk_codes else parsed.get("reason_codes", [])

        # action 결정
        if is_spam is True:
            action = "reject" if confidence == "high" else "quarantine"
        elif is_spam is False:
            action = "allow"
        else:
            action = "ask_user_confirm"

        return {
            "is_spam": is_spam,
            "action": action,
            "reason_codes": reason_codes,
            "confidence": confidence,
            "analysis": analysis,
            "policy_id": policies[0].get("policy_id") if policies else None,
        }

    def _heuristic_parse(self, text: str) -> Dict[str, Any]:
        """휴리스틱 파싱 (JSON 파싱 실패 시).

        Args:
            text: 파싱할 텍스트

        Returns:
            파싱된 딕셔너리
        """
        result = {
            "is_spam": None,
            "confidence": "medium",
            "reason_codes": [],
            "analysis": text,
        }

        text_lower = text.lower()

        # 스팸 키워드 확인
        spam_keywords = ["spam", "스팸", "피싱", "phishing", "의심"]
        if any(keyword in text_lower for keyword in spam_keywords):
            result["is_spam"] = True
            result["reason_codes"] = ["HEURISTIC_SPAM_DETECTED"]

        # 정상 키워드 확인
        normal_keywords = ["normal", "정상", "safe", "안전"]
        if any(keyword in text_lower for keyword in normal_keywords):
            result["is_spam"] = False

        return result
