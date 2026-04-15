"""
메일건 API를 이용한 발송.

외부 수신자에게만 사용. 직원/사내 주소는 DB inbox 생성으로 처리.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

MAILGUN_API_BASE = "https://api.mailgun.net/v3"


def send_email(
    api_key: str,
    domain: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    text: str,
    *,
    timeout: float = 10.0,
) -> bool:
    """
    메일건 API로 메일 1건 발송.

    Args:
        api_key: Mailgun API Key (Mail 권한).
        domain: 발송 도메인 (예: mg.kanggyeonggu.store).
        from_addr: 발신 주소 (예: noreply@mg.kanggyeonggu.store).
        to_addr: 수신 주소.
        subject: 제목.
        text: 본문 (plain text).
        timeout: 요청 타임아웃(초).

    Returns:
        성공 시 True, 실패 시 False (로그 출력).
    """
    if not api_key or not domain or not from_addr or not to_addr:
        logger.warning("send_email: api_key/domain/from/to 중 누락")
        return False
    url = f"{MAILGUN_API_BASE}/{domain.strip()}/messages"
    data = {
        "from": from_addr,
        "to": to_addr,
        "subject": subject or "(제목 없음)",
        "text": text or "",
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                url,
                auth=("api", api_key.strip()),
                data=data,
            )
        if resp.status_code in (200, 201):
            return True
        logger.warning("Mailgun send failed: status=%s body=%s", resp.status_code, resp.text[:500])
        return False
    except Exception as e:
        logger.exception("Mailgun send error: %s", e)
        return False
