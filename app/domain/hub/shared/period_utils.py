"""
분기(period) 유틸 — 현재 분기 문자열 생성.

성과 기록·메일 분류 시 period 자동 설정에 사용.
형식: YYYY-Q1 | YYYY-Q2 | YYYY-Q3 | YYYY-Q4
"""

from datetime import datetime
from typing import Optional


def get_current_period(dt: Optional[datetime] = None) -> str:
    """현재 시점 기준 분기 문자열 반환 (예: 2025-Q1).

    Args:
        dt: 기준 시각. None이면 datetime.now() 사용.

    Returns:
        "YYYY-Qn" (n = 1..4)
    """
    t = dt or datetime.now()
    year = t.year
    month = t.month
    if month <= 3:
        q = 1
    elif month <= 6:
        q = 2
    elif month <= 9:
        q = 3
    else:
        q = 4
    return f"{year}-Q{q}"
