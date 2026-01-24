"""
로깅 설정 모듈.

애플리케이션 전체에서 일관된 로깅 설정을 제공합니다.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """로깅 설정.

    Args:
        level: 로깅 레벨 (기본값: INFO)
        format_string: 로깅 포맷 (None이면 기본값 사용)
        log_file: 로그 파일 경로 (None이면 파일 로깅 안 함)

    Returns:
        설정된 로거
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
    )

    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """명명된 로거 반환.

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)
