"""
메인 진입점 - FastAPI 서버 실행.

FastAPI 서버를 실행합니다.
"""

import logging
import sys
from pathlib import Path

# 프로젝트 진입점: app/ 디렉토리를 Python 경로에 추가
# 이렇게 하면 `from api import ...` 형태의 절대 경로 import가 작동합니다
# 참고: main.py는 프로젝트 진입점이므로 이 sys.path.insert는 필요합니다
current_dir = Path(__file__).parent  # app/ 디렉토리
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Logging 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # 콘솔 출력
    ],
)

# FastAPI 서버 실행
logging.info("Starting FastAPI server...")
import server
import uvicorn
from core.config import get_settings  # type: ignore

settings = get_settings()
uvicorn.run(server.app, host=settings.host, port=settings.port)
