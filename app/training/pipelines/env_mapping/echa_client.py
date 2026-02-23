"""ECHA 동의어 조회. ECHA_API_URL 설정 시에만 동작. 공개 무료 API 없음."""

import logging
import os
import re
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger(__name__)
DEFAULT_DELAY = 0.2


def _normalize_cas(cas: str) -> str:
    return re.sub(r"\s+", "", (cas or "").strip())


def get_synonyms_for_cas(cas: str, api_base_url: str | None = None, delay_seconds: float = DEFAULT_DELAY) -> list[str]:
    """ECHA_API_URL 또는 api_base_url이 있으면 CAS별 동의어 조회. 없으면 []."""
    cas = _normalize_cas(cas)
    if not cas:
        return []
    base = (api_base_url or os.environ.get("ECHA_API_URL") or "").strip()
    if not base:
        return []
    url = f"{base}&cas={cas}" if "?" in base else f"{base}?cas={cas}"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
    except (HTTPError, URLError, OSError) as e:
        logger.debug("ECHA 조회 실패 cas=%s: %s", cas, e)
        time.sleep(delay_seconds)
        return []
    try:
        import json
        obj = json.loads(data)
        syns = []
        if isinstance(obj, list):
            syns = [str(s) for s in obj if s]
        elif isinstance(obj, dict):
            syns = obj.get("synonyms", obj.get("names", []))
            if isinstance(syns, str):
                syns = [syns]
            syns = [str(s).strip() for s in (syns or []) if s and str(s).strip()]
        time.sleep(delay_seconds)
        return syns
    except Exception as e:
        logger.debug("ECHA 파싱 실패 cas=%s: %s", cas, e)
    return []
