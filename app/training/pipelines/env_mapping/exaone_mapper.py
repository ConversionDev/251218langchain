"""
ExaOne으로 CAS·물질당 언어별 물질명·동의어(완전 동의어) 생성.
"""

import json
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _parse_json_from_response(text: str) -> dict[str, Any] | None:
    """응답 텍스트에서 JSON 블록 추출."""
    text = (text or "").strip()
    for start in ("{", "["):
        i = text.find(start)
        if i < 0:
            continue
        depth = 0
        for j in range(i, len(text)):
            if text[j] in "{[":
                depth += 1
            elif text[j] in "}]":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[i : j + 1])
                    except json.JSONDecodeError:
                        break
    return None


def get_names_for_language(
    cas: str,
    name_en: str,
    name_ko: str,
    lang_code: str,
    lang_label: str,
) -> dict[str, Any]:
    """
    한 언어에 대해 물질명 1개 + 동의어 리스트 생성.
    Returns: {"name": str, "synonyms": list[str]}
    """
    prompt = f"""You are a chemical substance naming expert. For the SAME substance (one CAS number), give the official or common name and EXACT SYNONYMS in the target language only. Same CAS = same substance; synonyms must refer to the identical chemical.

Substance: CAS {cas}, English: {name_en}, Korean: {name_ko}.
Target language: {lang_label} ({lang_code}).

Respond with a single JSON object only, no other text:
{{"name": "<one official or common name in {lang_label}>", "synonyms": ["<synonym1>", "<synonym2>", ...]}}

Rules: Include only exact synonyms (same substance). No explanations."""
    try:
        from domain.hub.llm.exaone_adapter import generate_text  # type: ignore

        raw = generate_text(prompt, max_tokens=512, temperature=0.3)
        obj = _parse_json_from_response(raw)
        if not obj or not isinstance(obj, dict):
            return {"name": "", "synonyms": []}
        name = (obj.get("name") or "").strip()
        syns = obj.get("synonyms") or []
        if isinstance(syns, list):
            syns = [str(s).strip() for s in syns if s and str(s).strip()]
        return {"name": name, "synonyms": syns}
    except Exception as e:
        logger.warning("ExaOne get_names_for_language %s %s: %s", cas, lang_code, e)
        return {"name": "", "synonyms": []}
