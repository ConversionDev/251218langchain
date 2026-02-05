"""
Upstash Redis + JWT access token + BullMQ 연동 (단일 파일).

- UPSTASH_REDIS_REST_URL, UPSTASH_REDIS_REST_TOKEN: Redis 클라이언트 및 BullMQ(Node)와 동일 인스턴스 공유.
- Soccer 임베딩 job 상태: soccer:embedding:status:{job_id} (create_embedding_job_inline + BackgroundTasks)
"""

import os
import time
import uuid
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Upstash Redis
# ---------------------------------------------------------------------------

_redis: Optional[Any] = None

EMBEDDING_STATUS_KEY_PREFIX = "soccer:embedding:status:"
EMBEDDING_STATUS_TTL = 86400


def get_redis():
    """Upstash Redis 클라이언트. 설정(.env) 또는 env 없으면 None."""
    global _redis
    if _redis is not None:
        return _redis
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        try:
            from core.config import get_settings  # type: ignore
            s = get_settings()
            url = url or getattr(s, "upstash_redis_rest_url", None)
            token = token or getattr(s, "upstash_redis_rest_token", None)
        except Exception:
            pass
    if not url or not token:
        return None
    try:
        from upstash_redis import Redis  # type: ignore
        _redis = Redis(url=url, token=token)
        return _redis
    except Exception:
        return None


def is_redis_token_valid() -> bool:
    """UPSTASH_REDIS_REST_URL·TOKEN 유효 시 True."""
    r = get_redis()
    if r is None:
        return False
    try:
        r.ping()
        return True
    except Exception:
        try:
            r.set("_ping", "1", ex=10)
            r.get("_ping")
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Soccer 임베딩 job 큐·상태
# ---------------------------------------------------------------------------

def create_embedding_job_inline(entities: Optional[list] = None) -> Optional[str]:
    """큐에 넣지 않고 job_id만 생성·상태를 processing으로 등록. API 백그라운드 태스크용."""
    r = get_redis()
    if r is None:
        return None
    job_id = uuid.uuid4().hex
    try:
        import json as _json
        r.set(
            EMBEDDING_STATUS_KEY_PREFIX + job_id,
            _json.dumps({"status": "processing", "job_id": job_id}),
            ex=EMBEDDING_STATUS_TTL,
        )
        return job_id
    except Exception:
        return None


def set_embedding_job_status(job_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> bool:
    """job 상태 저장. status: waiting | processing | completed | failed."""
    r = get_redis()
    if r is None:
        return False
    try:
        import json as _json
        data: Dict[str, Any] = {"status": status, "job_id": job_id}
        if result is not None:
            data["result"] = result
        r.set(EMBEDDING_STATUS_KEY_PREFIX + job_id, _json.dumps(data), ex=EMBEDDING_STATUS_TTL)
        return True
    except Exception:
        return False


def get_embedding_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """job 상태 조회."""
    r = get_redis()
    if r is None:
        return None
    try:
        import json as _json
        raw = r.get(EMBEDDING_STATUS_KEY_PREFIX + job_id)
        if raw is None:
            return None
        return _json.loads(raw)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# BullMQ(Node)와 같은 Redis 쓰기 위한 설정
# ---------------------------------------------------------------------------

def get_bullmq_connection_config() -> dict:
    """BullMQ 워커가 같은 Upstash Redis를 쓰기 위한 설정 (Node에서 동일 env 사용)."""
    return {
        "url": os.getenv("UPSTASH_REDIS_REST_URL", ""),
        "token": os.getenv("UPSTASH_REDIS_REST_TOKEN", ""),
    }


# ---------------------------------------------------------------------------
# JWT access token (로그인 시 사용)
# ---------------------------------------------------------------------------

def create_access_token(subject: str, expires_delta_minutes: Optional[int] = None) -> str:
    """로그인 성공 시 JWT access token 생성. subject는 user_id 등."""
    try:
        import jwt  # type: ignore
    except ImportError:
        raise RuntimeError("PyJWT 필요: pip install PyJWT")
    secret = os.getenv("JWT_SECRET", "change-me-in-production")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    minutes = expires_delta_minutes
    if minutes is None:
        minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    payload = {"sub": subject, "exp": int(time.time()) + minutes * 60, "iat": int(time.time())}
    return jwt.encode(payload, secret, algorithm=algorithm)


def verify_access_token(token: str) -> Optional[dict]:
    """Bearer token 검증 후 payload 반환. 실패 시 None."""
    try:
        import jwt  # type: ignore
    except ImportError:
        return None
    secret = os.getenv("JWT_SECRET", "change-me-in-production")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except Exception:
        return None


def set_session(key: str, value: str, ttl_seconds: int = 3600) -> bool:
    """Redis에 세션/토큰 저장 (선택)."""
    r = get_redis()
    if r is None:
        return False
    try:
        r.set(key, value, ex=ttl_seconds)
        return True
    except Exception:
        return False


def get_session(key: str) -> Optional[str]:
    """Redis에서 세션/토큰 조회."""
    r = get_redis()
    if r is None:
        return None
    try:
        return r.get(key)
    except Exception:
        return None
