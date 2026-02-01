"""
Soccer 임베딩 모듈 생성 서비스 (ExaOne)

엑사원(ExaOne)으로 player/team/schedule/stadium용 to_embedding_text 로직을 생성해
domain/models/bases/soccer_embeddings.py 한 파일에 저장합니다.
USE_EXAONE_EMBEDDING_GENERATOR=0 이면 fallback(domain.hub.shared.data_loader) 사용.
"""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List

SOCCER_EMBEDDINGS_PATH = "domain/models/bases/soccer_embeddings.py"

ENTITY_TYPES: List[str] = ["player", "team", "schedule", "stadium"]

ENTITY_SCHEMAS: Dict[str, str] = {
    "player": """
record 키: id, team_id, player_name, e_player_name, nickname, join_yyyy, position, back_no, nation, birth_date, solar, height, weight
- position: GK(골키퍼), DF(수비), MF(미드필더), FW(공격)
- RAG/검색에 쓸 자연어 문장으로 변환 (한국어, ". "로 구분 가능)
""".strip(),
    "team": """
record 키: id, stadium_id, team_code, region_name, team_name, e_team_name, orig_yyyy, zip_code1, zip_code2, address, ddd, tel, fax, homepage, owner
- RAG/검색에 쓸 자연어 문장으로 변환 (한국어)
""".strip(),
    "schedule": """
record 키: id, stadium_id, hometeam_id, awayteam_id, stadium_code, sche_date(YYYYMMDD), gubun(Y/N), hometeam_code, awayteam_code, home_score, away_score
- sche_date는 20240115 형태. 읽기 쉽게 포맷 가능
- gubun: Y=정규리그, N=컵대회 등
- RAG/검색에 쓸 자연어 문장으로 변환 (한국어)
""".strip(),
    "stadium": """
record 키: id, stadium_code, statdium_name(오타 유지), hometeam_id, hometeam_code, seat_count, address, ddd, tel
- RAG/검색에 쓸 자연어 문장으로 변환 (한국어)
""".strip(),
}


def _get_app_root() -> Path:
    """app 루트: 이 파일 기준으로 고정 (실행 CWD/import 경로와 무관하게 soccer_embeddings.py 위치 일치)."""
    # embedding_generator_service.py -> services -> soccer -> spokes -> domain -> app
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def _get_exaone_llm():
    from domain.hub.llm import get_llm  # type: ignore
    return get_llm()


def _build_prompt(entity_type: str) -> str:
    if entity_type not in ENTITY_SCHEMAS:
        raise ValueError(f"지원하지 않는 entity_type: {entity_type}")
    schema = ENTITY_SCHEMAS[entity_type]
    fn_name = f"{entity_type}_to_embedding_text"
    return f"""다음 규칙에 맞게 Python 함수 코드만 작성하세요. 설명이나 마크다운 없이 코드만 출력하세요.

요구사항:
1. 함수 정의: def {fn_name}(record: dict) -> str
2. record는 딕셔너리이며, 다음 스키마를 가집니다:

{schema}

3. 반환값: RAG/벡터 검색에 넣을 한 줄 자연어 문자열 (한국어). None 값은 제외.
4. 타입 힌트 사용 (from typing import Dict, Any 필요 시 함수 내부나 인라인).
5. 코드만 출력 (```python 제거). 함수 하나만 작성."""


def _extract_code_from_response(raw: str) -> str:
    raw = raw.strip()
    m = re.search(r"```(?:python)?\s*\n?(.*?)```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    return raw


def _is_valid_entity_snippet(code: str, entity_type: str) -> bool:
    if not code or not code.strip():
        return False
    if len(code.strip()) < 50:
        return False
    fn_name = f"{entity_type}_to_embedding_text"
    if f"def {fn_name}" not in code:
        return False
    return True


def _validate_code_syntax(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _get_fallback_soccer_embeddings_content() -> str:
    """domain.hub.shared.data_loader 기반 fallback 전체 모듈 내용."""
    from domain.hub.shared.data_loader import (  # type: ignore
        player_to_text,
        schedule_to_text,
        stadium_to_text,
        team_to_text,
    )
    return '''"""Soccer 임베딩용 텍스트 변환 (player, team, schedule, stadium). Fallback: data_loader."""

from typing import Any, Dict

from domain.hub.shared.data_loader import (
    player_to_text,
    schedule_to_text,
    stadium_to_text,
    team_to_text,
)


def player_to_embedding_text(record: Dict[str, Any]) -> str:
    """선수 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return player_to_text(record)


def team_to_embedding_text(record: Dict[str, Any]) -> str:
    """팀 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return team_to_text(record)


def schedule_to_embedding_text(record: Dict[str, Any]) -> str:
    """경기 일정 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return schedule_to_text(record)


def stadium_to_embedding_text(record: Dict[str, Any]) -> str:
    """경기장 record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return stadium_to_text(record)


def to_embedding_text(record: Dict[str, Any], entity_type: str) -> str:
    """entity_type에 따라 해당 변환 함수를 호출합니다."""
    if entity_type == "player":
        return player_to_embedding_text(record)
    if entity_type == "team":
        return team_to_embedding_text(record)
    if entity_type == "schedule":
        return schedule_to_embedding_text(record)
    if entity_type == "stadium":
        return stadium_to_embedding_text(record)
    raise ValueError(f"지원하지 않는 entity_type: {entity_type!r}")
'''


def _generate_one_snippet(entity_type: str) -> str:
    """엑사원으로 entity_type별 함수 코드 한 개 생성. 실패 시 fallback 조각."""
    if os.environ.get("USE_EXAONE_EMBEDDING_GENERATOR", "1") == "0":
        return ""
    try:
        from langchain_core.messages import HumanMessage  # type: ignore
        prompt = _build_prompt(entity_type)
        llm = _get_exaone_llm()
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        content = getattr(response, "content", None) or str(response)
        code = _extract_code_from_response(content)
        if _is_valid_entity_snippet(code, entity_type) and _validate_code_syntax(code):
            return code.strip()
    except Exception:
        pass
    return ""


def _strip_import_lines(code: str) -> str:
    """스니펫에서 from typing / import 단독 라인 제거 (상단 모듈에서 이미 import)."""
    lines = code.strip().split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if s.startswith("from typing import") or s == "import typing":
            continue
        out.append(line)
    return "\n".join(out).strip()


def _build_soccer_embeddings_module(snippets: Dict[str, str]) -> str:
    """4개 스니펫을 합쳐 soccer_embeddings.py 전체 내용 생성."""
    header = '''"""Soccer 임베딩용 텍스트 변환 (player, team, schedule, stadium). ExaOne 생성."""

from typing import Any, Dict

'''
    parts = [header]
    for entity_type in ENTITY_TYPES:
        code = snippets.get(entity_type, "").strip()
        if code:
            parts.append(_strip_import_lines(code))
            parts.append("\n\n")
    parts.append("""
def to_embedding_text(record: Dict[str, Any], entity_type: str) -> str:
    '''entity_type에 따라 해당 변환 함수를 호출합니다.'''
    if entity_type == "player":
        return player_to_embedding_text(record)
    if entity_type == "team":
        return team_to_embedding_text(record)
    if entity_type == "schedule":
        return schedule_to_embedding_text(record)
    if entity_type == "stadium":
        return stadium_to_embedding_text(record)
    raise ValueError(f"지원하지 않는 entity_type: {entity_type!r}")
""")
    return "".join(parts).strip() + "\n"


def generate_and_write_soccer_embeddings() -> Dict[str, Any]:
    """
    엑사원으로 player/team/schedule/stadium용 함수 4개를 생성해
    domain/models/bases/soccer_embeddings.py 한 파일에 저장합니다.
    """
    result: Dict[str, Any] = {
        "success": False,
        "path": None,
        "error": None,
        "code_valid": False,
    }
    snippets: Dict[str, str] = {}
    for entity_type in ENTITY_TYPES:
        snippet = _generate_one_snippet(entity_type)
        if snippet:
            snippets[entity_type] = snippet
    if len(snippets) < 4:
        content = _get_fallback_soccer_embeddings_content()
        result["used_fallback"] = True
    else:
        content = _build_soccer_embeddings_module(snippets)
        result["used_fallback"] = False
    result["code_valid"] = _validate_code_syntax(content)
    if not result["code_valid"]:
        result["error"] = "생성된 코드 문법 검사 실패"
        return result
    try:
        path = _get_app_root() / SOCCER_EMBEDDINGS_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        result["success"] = True
        result["path"] = str(path)
    except Exception as e:
        result["error"] = str(e)
    return result


def generate_embedding_module_code(entity_type: str) -> str:
    """entity_type별 코드 스니펫 생성 (generate_and_write_soccer_embeddings 사용 권장)."""
    if entity_type not in ENTITY_SCHEMAS:
        raise ValueError(f"지원하지 않는 entity_type: {entity_type}")
    return _generate_one_snippet(entity_type) or ""


def generate_and_write_embedding_module(entity_type: str) -> Dict[str, Any]:
    """soccer_embeddings.py 전체 생성 (entity_type 무시, 하위 호환용)."""
    return generate_and_write_soccer_embeddings()
