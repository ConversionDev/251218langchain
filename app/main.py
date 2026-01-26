"""
메인 진입점 - FastAPI 서버 실행.

FastAPI 서버를 실행합니다.
V10 도메인 초기화는 server.py의 lifespan에서 처리됩니다.
"""

import logging
import sys
from pathlib import Path

# 프로젝트 진입점: app/ 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Logging 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# 설정 로드
from core.config import get_settings  # type: ignore

settings = get_settings()

# FastAPI 서버 실행
logging.info("Starting FastAPI server...")
import server  # noqa: E402
import uvicorn  # noqa: E402

uvicorn.run(server.app, host=settings.host, port=settings.port)
