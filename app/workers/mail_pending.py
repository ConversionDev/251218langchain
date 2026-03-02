"""
메일 PENDING 워커 — Store-then-Process 4단계.

동작:
  1. list_pending_for_worker(db, 1) 로 PENDING 1건 조회 (FOR UPDATE SKIP LOCKED)
  2. ai_status=PROCESSING, processed_at=now() 설정 후 즉시 commit
  3. LLaMA classify_spam 호출 (타임아웃 기본 180초, 워밍업 시 로딩 선행). 성공 시 spam_score, folder(inbox/spam) 반영
  4. 실패/타임아웃 시: ai_status=FAILED, retry_count+=1, last_failed_at, ai_result_raw 기록
  5. PENDING 0건이면 time.sleep(poll_interval) 후 재조회

실행 (프로젝트 루트에서):
  PYTHONPATH=app python -m workers.mail_pending
"""

import logging
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from core.database import SessionLocal  # type: ignore
from domain.hub.repositories.mail_item_repository import (  # type: ignore
    list_pending_for_worker,
    update as mail_item_update,
)
from domain.models.enums.mail_enums import AiStatus  # type: ignore

logger = logging.getLogger(__name__)

# 유휴 시 폴링 간격(초). env MAIL_WORKER_POLL_INTERVAL_SEC, 기본 1
POLL_INTERVAL_SEC = float(os.environ.get("MAIL_WORKER_POLL_INTERVAL_SEC", "1"))
# AI 분류 타임아웃(초). env MAIL_WORKER_CLASSIFY_TIMEOUT_SEC. 기본 180 (LLaMA 로딩+첫 추론 여유)
CLASSIFY_TIMEOUT_SEC = float(os.environ.get("MAIL_WORKER_CLASSIFY_TIMEOUT_SEC", "180"))
# 시작 시 LLaMA 워밍업(로드 선행). 1이면 워밍업 후 루프 진입. env MAIL_WORKER_WARMUP_LLAMA, 기본 1
WARMUP_LLAMA = os.environ.get("MAIL_WORKER_WARMUP_LLAMA", "1").strip().lower() in ("1", "true", "yes")
# spam_prob >= 이 값이거나 label==SPAM 이면 folder=spam
SPAM_THRESHOLD = 0.5


def _row_to_email_metadata(row: dict) -> dict:
    """메일 row → classify_spam용 email_metadata."""
    return {
        "subject": row.get("subject") or "",
        "sender": row.get("fromEmail") or row.get("fromDisplay") or "",
        "body": (row.get("body") or "")[:5000],
        "recipient": row.get("toEmail") or "",
    }


def _classify_spam_with_timeout(email_metadata: dict) -> dict:
    """classify_spam을 CLASSIFY_TIMEOUT_SEC 안에 실행. 초과 시 TimeoutError."""
    from domain.hub.llm import classify_spam  # type: ignore

    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(classify_spam, email_metadata)
        return future.result(timeout=CLASSIFY_TIMEOUT_SEC)


def _warmup_llama() -> None:
    """시작 시 LLaMA 한 번 호출해 모델 로딩. 첫 메일 처리 시 타임아웃 방지."""
    logger.info("LLaMA 워밍업 중 (최대 300초)...")
    dummy = {"subject": "", "sender": "", "body": "", "recipient": ""}
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            from domain.hub.llm import classify_spam  # type: ignore

            future = ex.submit(classify_spam, dummy)
            future.result(timeout=300)
        logger.info("LLaMA 워밍업 완료.")
    except Exception as e:
        logger.warning("LLaMA 워밍업 실패 (첫 메일에서 로드 시도): %s", e)


def _folder_from_result(result: dict) -> Tuple[str, float]:
    """classify_spam 결과 → (folder, spam_score). ham → 받은편지함(inbox), spam → 스팸함(spam)."""
    label = (result.get("label") or "").strip().upper()
    spam_prob = float(result.get("spam_prob", 0.5))
    is_spam = label == "SPAM" or spam_prob >= SPAM_THRESHOLD
    if is_spam:
        return "spam", spam_prob  # 스팸 → 스팸함
    return "inbox", spam_prob  # 햄 → 받은편지함


def _process_one(db: Session, row: dict) -> None:
    """PENDING 1건 처리: PROCESSING commit → classify_spam → SUCCESS/FAILED."""
    mid = row.get("id") or row.get("mail_id")
    if not mid:
        logger.warning("메일 id 없음, 스킵: %s", row)
        return

    # 1) PROCESSING + processed_at 설정 후 즉시 commit
    now = datetime.now(timezone.utc)
    mail_item_update(
        db,
        mid,
        ai_status=AiStatus.PROCESSING.value,
        processed_at=now,
    )
    db.commit()
    logger.info("메일 처리 시작: id=%s", mid)

    # 2) LLaMA classify_spam (타임아웃 적용) → folder, spam_score 반영
    try:
        email_metadata = _row_to_email_metadata(row)
        result = _classify_spam_with_timeout(email_metadata)
        # 오분류 디버깅: 모델이 준 raw 값 로그
        logger.debug(
            "classify_spam raw: id=%s label=%s spam_prob=%s",
            mid,
            result.get("label"),
            result.get("spam_prob"),
        )
        folder, spam_score = _folder_from_result(result)
        mail_item_update(
            db,
            mid,
            folder=folder,
            spam_score=spam_score,
            ai_status=AiStatus.SUCCESS.value,
        )
        db.commit()
        logger.info(
            "메일 처리 완료: id=%s folder=%s spam_score=%s (스팸이면 스팸함에만 표시)",
            mid,
            folder,
            spam_score,
        )
    except FuturesTimeoutError:
        db.rollback()
        err_msg = f"classify_spam timeout ({CLASSIFY_TIMEOUT_SEC}s)"
        retry_count = (row.get("retryCount") or 0) + 1
        try:
            mail_item_update(
                db,
                mid,
                ai_status=AiStatus.FAILED.value,
                retry_count=retry_count,
                last_failed_at=now,
                ai_result_raw=err_msg,
            )
            db.commit()
            logger.warning("메일 처리 타임아웃: id=%s retry_count=%s", mid, retry_count)
        except Exception as commit_err:
            logger.exception("FAILED 상태 저장 실패: %s", commit_err)
            db.rollback()
    except Exception as e:
        db.rollback()
        err_msg = traceback.format_exc()
        if len(err_msg) > 4000:
            err_msg = err_msg[:4000]
        retry_count = (row.get("retryCount") or 0) + 1
        try:
            mail_item_update(
                db,
                mid,
                ai_status=AiStatus.FAILED.value,
                retry_count=retry_count,
                last_failed_at=now,
                ai_result_raw=err_msg,
            )
            db.commit()
            logger.warning("메일 처리 실패 기록: id=%s retry_count=%s %s", mid, retry_count, e)
        except Exception as commit_err:
            logger.exception("FAILED 상태 저장 실패: %s", commit_err)
            db.rollback()


def run_worker_loop() -> None:
    """무한 루프: PENDING 조회 → 1건 처리 또는 sleep."""
    while True:
        db: Session = SessionLocal()
        try:
            rows = list_pending_for_worker(db, limit=1)
            if not rows:
                db.close()
                # 유휴 시 부하 방지
                time.sleep(POLL_INTERVAL_SEC)
                continue
            for row in rows:
                _process_one(db, row)
        except Exception as e:
            logger.exception("워커 루프 예외: %s", e)
            if db:
                try:
                    db.rollback()
                except Exception:
                    pass
        finally:
            try:
                db.close()
            except Exception:
                pass


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info(
        "메일 PENDING 워커 시작 (poll_interval=%s초, classify_timeout=%s초, warmup=%s)",
        POLL_INTERVAL_SEC,
        CLASSIFY_TIMEOUT_SEC,
        WARMUP_LLAMA,
    )
    if WARMUP_LLAMA:
        _warmup_llama()
    run_worker_loop()
