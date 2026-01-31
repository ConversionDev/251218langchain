"""
v10 soccer 임베딩 모듈 생성 서비스

엑사원(ExaOne)으로 player/team/schedule/stadium용 *_embeddings.py 파일 내용을 생성하고
domain/v10/soccer/models/bases/ 에 저장합니다.

테스트: USE_EXAONE_EMBEDDING_GENERATOR=0 이면 fallback(data_loader) 코드 사용.
"""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict

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

EMBEDDING_MODULE_PATHS: Dict[str, str] = {
    "player": "domain/v10/soccer/models/bases/player_embeddings.py",
    "team": "domain/v10/soccer/models/bases/team_embeddings.py",
    "schedule": "domain/v10/soccer/models/bases/schedule_embeddings.py",
    "stadium": "domain/v10/soccer/models/bases/stadium_embeddings.py",
}


def _get_app_root() -> Path:
    from core.paths import get_app_root as _get  # type: ignore
    return _get()


def _get_exaone_llm():
    from domain.v1.hub.llm import get_llm  # type: ignore
    return get_llm()


def _build_prompt(entity_type: str) -> str:
    if entity_type not in ENTITY_SCHEMAS:
        raise ValueError(f"지원하지 않는 entity_type: {entity_type}")
    schema = ENTITY_SCHEMAS[entity_type]
    filename = EMBEDDING_MODULE_PATHS[entity_type]
    return f"""다음 규칙에 맞게 Python 모듈 코드만 작성하세요. 설명이나 마크다운 없이 코드만 출력하세요.

파일 경로: {filename}

요구사항:
1. 함수 하나만 정의: def to_embedding_text(record: dict) -> str
2. record는 딕셔너리이며, 다음 스키마를 가집니다:

{schema}

3. 반환값: RAG/벡터 검색에 넣을 한 줄 자연어 문자열 (한국어). None 값은 제외.
4. 모듈 상단에 docstring으로 "{{entity_type}} 임베딩용 텍스트 변환" 한 줄 설명.
5. 타입 힌트 사용 (from typing import Dict, Any 필요 시).
6. 코드만 출력 (```python 제거)."""


def _extract_code_from_response(raw: str) -> str:
    raw = raw.strip()
    m = re.search(r"```(?:python)?\s*\n?(.*?)```", raw, re.DOTALL)
    if m:
        return m.group(1).strip()
    return raw


def _is_valid_embedding_code(code: str) -> bool:
    if not code or not code.strip():
        return False
    if len(code.strip()) < 80:
        return False
    if "def to_embedding_text" not in code:
        return False
    return True


def _validate_code_syntax(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _get_fallback_embedding_code(entity_type: str) -> str:
    from domain.v10.shared.data_loader import (  # type: ignore
        player_to_text,
        schedule_to_text,
        stadium_to_text,
        team_to_text,
    )
    fn_map = {
        "player": ("player_to_text", player_to_text.__name__),
        "team": ("team_to_text", team_to_text.__name__),
        "schedule": ("schedule_to_text", schedule_to_text.__name__),
        "stadium": ("stadium_to_text", stadium_to_text.__name__),
    }
    fn_import, fn_name = fn_map[entity_type]
    return f'''"""{entity_type} 임베딩용 텍스트 변환 (data_loader fallback)."""
from typing import Any, Dict

from domain.v10.shared.data_loader import {fn_import}  # type: ignore


def to_embedding_text(record: Dict[str, Any]) -> str:
    """record를 RAG/벡터 검색용 자연어 문자열로 변환합니다."""
    return {fn_name}(record)
'''


def generate_embedding_module_code(entity_type: str) -> str:
    if os.environ.get("USE_EXAONE_EMBEDDING_GENERATOR", "1") == "0":
        return _get_fallback_embedding_code(entity_type)
    try:
        from langchain_core.messages import HumanMessage  # type: ignore
        prompt = _build_prompt(entity_type)
        llm = _get_exaone_llm()
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        content = getattr(response, "content", None) or str(response)
        code = _extract_code_from_response(content)
        if not _is_valid_embedding_code(code):
            return _get_fallback_embedding_code(entity_type)
        return code
    except Exception:
        return _get_fallback_embedding_code(entity_type)


def write_embedding_file(entity_type: str, code: str) -> Path:
    if entity_type not in EMBEDDING_MODULE_PATHS:
        raise ValueError(f"지원하지 않는 entity_type: {entity_type}")
    rel = EMBEDDING_MODULE_PATHS[entity_type]
    path = _get_app_root() / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return path


def generate_and_write_embedding_module(entity_type: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "success": False,
        "path": None,
        "error": None,
        "code_valid": False,
    }
    if entity_type not in ENTITY_SCHEMAS:
        result["error"] = f"지원하지 않는 entity_type: {entity_type}"
        return result
    try:
        code = generate_embedding_module_code(entity_type)
        if not _is_valid_embedding_code(code):
            code = _get_fallback_embedding_code(entity_type)
        result["code_valid"] = _validate_code_syntax(code)
        if not result["code_valid"]:
            result["error"] = "생성된 코드 문법 검사 실패"
            return result
        path = write_embedding_file(entity_type, code)
        result["success"] = True
        result["path"] = str(path)
    except Exception as e:
        result["error"] = str(e)
    return result
