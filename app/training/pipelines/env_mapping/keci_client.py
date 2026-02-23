"""KECI(화학물질안전관리정보) 공공데이터 API로 CAS별 물질명(영문/국문) 조회. 환경변수: KECI_SERVICE_KEY 또는 DATA_GO_KR_SERVICE_KEY."""

import logging
import os
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)
BASE_URL = "https://apis.data.go.kr/1480802/iciskischem/kischemlist"
DEFAULT_DELAY = 0.2


def _normalize_cas(cas: str) -> str:
    return re.sub(r"\s+", "", (cas or "").strip())


def get_service_key() -> str:
    return (os.environ.get("KECI_SERVICE_KEY") or os.environ.get("DATA_GO_KR_SERVICE_KEY") or "").strip()


def get_names_for_cas(cas: str, service_key: str | None = None, delay_seconds: float = DEFAULT_DELAY) -> dict[str, str]:
    """CAS로 KECI 조회 → {"name_en": str, "name_ko": str}."""
    cas = _normalize_cas(cas)
    if not cas:
        return {}
    key = service_key or get_service_key()
    if not key:
        log = logging.getLogger(__name__)
        log.debug("KECI: ServiceKey 없음.")
        return {}
    qs = urlencode({"serviceKey": key, "numOfRows": 10, "pageNo": 1, "casNo": cas})
    url = f"{BASE_URL}?{qs}"
    try:
        req = Request(url, headers={"Accept": "application/xml"})
        with urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
    except Exception as e:
        logger.debug("KECI 조회 실패 cas=%s: %s", cas, e)
        time.sleep(delay_seconds)
        return {}
    try:
        root = ET.fromstring(data)
        items = root.find(".//items")
        if items is None:
            for el in root.iter():
                if el.tag.endswith("}items") or el.tag == "items":
                    items = el
                    break
        if items is None:
            time.sleep(delay_seconds)
            return {}
        item = items.find("item")
        if item is None:
            for el in items.iter():
                if el.tag.endswith("}item") or el.tag == "item":
                    item = el
                    break
        if item is None:
            time.sleep(delay_seconds)
            return {}
        def _text(el):
            if el is None:
                return ""
            return (el.text or "").strip()
        chem_en = item.find("chemEn") or next((c for c in item if "chemEn" in (c.tag or "")), None)
        chem_ko = item.find("chemKo") or next((c for c in item if "chemKo" in (c.tag or "")), None)
        name_en = _text(chem_en)
        name_ko = _text(chem_ko)
        time.sleep(delay_seconds)
        return {"name_en": name_en, "name_ko": name_ko}
    except Exception as e:
        logger.debug("KECI 파싱 실패 cas=%s: %s", cas, e)
    return {}
