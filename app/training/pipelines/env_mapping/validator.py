"""
검증 스텁: 공식 DB 대조·배터리 용어 검증.

현재: ExaOne 후보를 그대로 'ExaOne후보' 상태로 반환.
추후: PubChem/ECHA/화학물질통합정보 API 연동 시 여기서 상태를 '공식DB일치' 등으로 갱신.
"""

import logging
from typing import Any

from .config import STATUS_EXAONE_CANDIDATE, STATUS_OFFICIAL_MATCH, STATUS_UNVERIFIED

logger = logging.getLogger(__name__)


def validate_substance(
    cas: str,
    name_en: str,
    lang_code: str,
    candidate_name: str,
    candidate_synonyms: list[str],
) -> str:
    """
    물질·언어별 후보 명칭 검증.

    Returns:
        검증 상태: 공식DB일치 | ExaOne후보 | 미검증
    """
    # 스텁: 공식 API 미연동 시 모두 ExaOne후보
    if not candidate_name and not candidate_synonyms:
        return STATUS_UNVERIFIED
    # TODO: PubChem/ECHA 등으로 CAS+언어 조회 후 일치 시 STATUS_OFFICIAL_MATCH
    _ = (cas, name_en, lang_code)
    return STATUS_EXAONE_CANDIDATE
