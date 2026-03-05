"""PubChem PUG REST API로 CAS별 동의어 조회."""

import json
import logging
import re
import time
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
DEFAULT_DELAY = 0.2


def _normalize_cas(cas: str) -> str:
    s = (cas or "").strip()
    return re.sub(r"\s+", "", s)


def get_synonyms_for_cas(cas: str, delay_seconds: float = DEFAULT_DELAY) -> list[str]:
    """CAS로 PubChem 동의어 조회. 실패 시 빈 리스트."""
    cas = _normalize_cas(cas)
    if not cas:
        return []
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/synonyms/JSON"
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        syns = data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
        if isinstance(syns, list):
            seen = set()
            out = []
            for s in syns:
                x = (s and str(s)).strip()
                if x and x.lower() not in seen:
                    seen.add(x.lower())
                    out.append(x)
            time.sleep(delay_seconds)
            return out
    except Exception as e:
        logger.debug("PubChem synonyms cas=%s: %s", cas, e)
    time.sleep(delay_seconds)
    return []


def get_synonyms_for_cas_via_cid(cas: str, delay_seconds: float = DEFAULT_DELAY) -> list[str]:
    """CAS → CID 검색 후 동의어 조회 (fallback)."""
    cas = _normalize_cas(cas)
    if not cas:
        return []
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/cids/JSON"
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cids = data.get("IdentifierList", {}).get("CID", [])
        if not cids:
            time.sleep(delay_seconds)
            return []
        cid = cids[0]
        time.sleep(delay_seconds)
        url2 = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
        req2 = Request(url2, headers={"Accept": "application/json"})
        with urlopen(req2, timeout=12) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
        syns = data2.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
        if isinstance(syns, list):
            seen = set()
            out = []
            for s in syns:
                x = (s and str(s)).strip()
                if x and x.lower() not in seen:
                    seen.add(x.lower())
                    out.append(x)
            time.sleep(delay_seconds)
            return out
    except Exception as e:
        logger.debug("PubChem via CID cas=%s: %s", cas, e)
    time.sleep(delay_seconds)
    return []


def get_ec_number_for_cas(cas: str, delay_seconds: float = DEFAULT_DELAY) -> str:
    """CAS로 PubChem 조회 후 EC 번호(유럽 공동체 번호) 반환. 없으면 빈 문자열."""
    ec, _ = get_ec_and_cid_for_cas(cas, delay_seconds=delay_seconds)
    return ec


def get_ec_and_cid_for_cas(cas: str, delay_seconds: float = DEFAULT_DELAY) -> tuple[str, str]:
    """CAS로 PubChem 조회 후 (EC 번호, CID) 반환. 없으면 ('', '')."""
    cas = _normalize_cas(cas)
    if not cas:
        return ("", "")
    try:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/cids/JSON"
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cids = data.get("IdentifierList", {}).get("CID", [])
        if not cids:
            time.sleep(delay_seconds)
            return ("", "")
        cid = cids[0]
        cid_str = str(cid).strip() if cid is not None else ""
        time.sleep(delay_seconds)
        url2 = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/ECNumber/JSON"
        req2 = Request(url2, headers={"Accept": "application/json"})
        with urlopen(req2, timeout=12) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
        props = data2.get("PropertyTable", {}).get("Properties", [])
        if not props:
            time.sleep(delay_seconds)
            return ("", cid_str)
        ec = props[0].get("ECNumber")
        if ec is None:
            time.sleep(delay_seconds)
            return ("", cid_str)
        if isinstance(ec, list):
            ec = next((x for x in ec if x and str(x).strip()), None) or ""
        s = str(ec).strip()
        time.sleep(delay_seconds)
        return (s, cid_str)
    except Exception as e:
        logger.debug("PubChem EC/CID cas=%s: %s", cas, e)
    time.sleep(delay_seconds)
    return ("", "")
