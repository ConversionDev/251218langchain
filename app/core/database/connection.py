"""
데이터베이스 연결 유틸리티

PostgreSQL 연결 대기 등. (LangChain PGVector 테이블 미사용)
"""

import time

from core.config import get_settings  # type: ignore


def wait_for_postgres(max_retries: int = 30, delay: int = 2) -> None:
    """Neon PostgreSQL이 준비될 때까지 대기.

    Args:
        max_retries: 최대 재시도 횟수
        delay: 재시도 간격 (초)

    Raises:
        ConnectionError: 연결 실패 시
    """
    import psycopg2  # type: ignore[import-untyped]

    settings = get_settings()
    connection_string = settings.connection_string

    print(
        f"[INFO] Neon PostgreSQL 연결 시도 중... (연결 문자열: {connection_string[:50]}...)"
    )

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(connection_string)

            # PGVector 확장 확인
            cur = conn.cursor()
            cur.execute(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
            )
            vector_ext = cur.fetchone()

            if vector_ext:
                print("[OK] Neon PostgreSQL 연결 성공!")
                print(f"[INFO] PGVector 확장 설치됨 (버전: {vector_ext[1]})")
            else:
                print("[OK] Neon PostgreSQL 연결 성공!")
                print("[WARNING] PGVector 확장이 설치되지 않았습니다!")

            conn.close()
            return
        except Exception as e:
            if i < max_retries - 1:
                print(
                    f"[INFO] Neon PostgreSQL 대기 중... ({i + 1}/{max_retries}) - {str(e)[:100]}"
                )
                time.sleep(delay)
            else:
                raise ConnectionError(f"Neon PostgreSQL 연결 실패: {e}")


