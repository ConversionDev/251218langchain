"""
메인 진입점 - FastAPI 서버 실행.

FastAPI 서버를 실행합니다.
V10 도메인 초기화는 fastapi_server의 lifespan에서 처리됩니다.

실행: (torch311) PS ...\\backend\\ontology\\apps> python main.py
다른 폴더에서 `python ..\\ontology\\apps\\main.py`처럼 경로만 줄 때도 동작하도록
sys.path·cwd를 apps 디렉터리로 맞춥니다.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

_APPS_ROOT = Path(__file__).resolve().parent


def _ensure_apps_runtime() -> None:
    """import 경로와 cwd를 ontology/apps로 고정한다."""
    root = str(_APPS_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        os.chdir(_APPS_ROOT)
    except OSError as exc:
        logging.warning("chdir to %s failed: %s", _APPS_ROOT, exc)


def main() -> None:
    _ensure_apps_runtime()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    from core.config import get_settings  # noqa: E402

    settings = get_settings()

    logging.info("Starting FastAPI server...")
    import fastapi_server  # noqa: E402
    import uvicorn  # noqa: E402

    uvicorn.run(fastapi_server.app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
