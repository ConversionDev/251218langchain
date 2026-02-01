"""
규칙 기반 서비스

규칙 기반 판단을 수행합니다.
- Redis에서 규칙 조회
- 패턴 매칭
- 즉시 결정 반환 (EXAONE 없이)
"""

from typing import Any, Dict, Optional

from domain.spokes.spam.repositories.rule_repository import (  # type: ignore
    RuleRepository,
)
from domain.models import LLaMAResult  # type: ignore


class RuleService:
    """규칙 기반 서비스.

    규칙 기반 판단을 수행하며, EXAONE을 사용하지 않습니다.
    """

    def __init__(self, rule_repository: Optional[RuleRepository] = None):
        """초기화.

        Args:
            rule_repository: 규칙 저장소 (None이면 새로 생성)
        """
        self._repository = rule_repository or RuleRepository()

    def process(self, email_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """규칙 기반 처리.

        Args:
            email_metadata: 이메일 메타데이터
                - subject: 제목
                - sender: 발신자
                - body: 본문
                - attachments: 첨부파일 목록

        Returns:
            규칙 기반 처리 결과
            {
                "is_spam": bool,
                "action": str,  # "reject", "allow", "quarantine", etc.
                "reason_codes": List[str],
                "confidence": str,  # "high", "medium", "low"
                "matched_rule_id": Optional[str],
            }
        """
        # 1. 패턴 매칭
        matched_rule_id = self._repository.match_pattern(email_metadata)

        # 2. 블랙리스트 확인
        blacklist_senders = self._repository.get_blacklist_senders()
        sender = email_metadata.get("sender", "").lower()

        # 3. 규칙 기반 판단
        if matched_rule_id:
            rule = self._repository.get_rule(matched_rule_id)
            if rule:
                action = rule.get("action", "reject")
                reason_codes = rule.get("reason_codes", [matched_rule_id])
                confidence = "high"  # 규칙 매칭은 높은 신뢰도
                is_spam = action in ["reject", "quarantine"]

                return {
                    "is_spam": is_spam,
                    "action": action,
                    "reason_codes": reason_codes,
                    "confidence": confidence,
                    "matched_rule_id": matched_rule_id,
                }

        # 4. 블랙리스트 발신자 확인
        if sender in [s.lower() for s in blacklist_senders]:
            return {
                "is_spam": True,
                "action": "reject",
                "reason_codes": ["BLACKLIST_SENDER"],
                "confidence": "high",
                "matched_rule_id": None,
            }

        # 5. 키워드 패턴 확인
        keyword_patterns = self._repository.get_keyword_patterns()
        subject = email_metadata.get("subject", "").lower()
        body = email_metadata.get("body", "").lower()
        text = f"{subject} {body}"

        for pattern_info in keyword_patterns:
            pattern = pattern_info.get("pattern", "")
            rule_id = pattern_info.get("rule_id", "")
            action = pattern_info.get("action", "reject")

            # 간단한 키워드 매칭 (정규표현식은 나중에 구현)
            if pattern.lower() in text:
                return {
                    "is_spam": action in ["reject", "quarantine"],
                    "action": action,
                    "reason_codes": [rule_id],
                    "confidence": "medium",
                    "matched_rule_id": rule_id,
                }

        # 6. 규칙 매칭 실패 - 정상 메일로 간주
        return {
            "is_spam": False,
            "action": "allow",
            "reason_codes": [],
            "confidence": "medium",
            "matched_rule_id": None,
        }

    def is_rule_based(self, email_metadata: Dict[str, Any]) -> bool:
        """이메일이 규칙 기반으로 처리 가능한지 판단.

        Args:
            email_metadata: 이메일 메타데이터

        Returns:
            규칙 기반 처리 가능 여부
        """
        return self._repository.is_rule_based(email_metadata)
