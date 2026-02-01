#!/usr/bin/env python3
"""
soccer_embeddings.py 생성 실행 스크립트

엑사원(ExaOne)으로 domain/models/bases/soccer_embeddings.py 를 생성합니다.
app 디렉터리에서 실행: python -m scripts.generate_soccer_embeddings
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# app 디렉터리를 path에 넣어 domain 등 import 가능하게 함
_app_dir = Path(__file__).resolve().parent.parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))


def main() -> int:
    # embedding_generator_service.py 직접 로드 (services __init__.py 의존 없음)
    _embedding_service_path = (
        _app_dir
        / "domain"
        / "spokes"
        / "soccer"
        / "services"
        / "embedding_generator_service.py"
    )
    _spec = importlib.util.spec_from_file_location(
        "embedding_generator_service", _embedding_service_path
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    result = _mod.generate_and_write_soccer_embeddings()
    print(result)
    if result.get("success"):
        print(f"\n저장 경로: {result.get('path')}")
        return 0
    print(f"\n오류: {result.get('error', '알 수 없음')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
