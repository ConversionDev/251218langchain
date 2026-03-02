"""
메일 수신·AI 처리 상태 전이 (단일 소스).

- 수신 직후:
  - Resolver 성공 → status=RECEIVED, ai_status=PENDING, folder=inbox
  - Resolver 실패 → status=REJECTED, ai_status=NULL, folder=NULL, spam_score=NULL
- 워커:
  1. SELECT FOR UPDATE SKIP LOCKED 로 PENDING 1건 조회
  2. ai_status=PROCESSING, processed_at=now() 후 commit
  3. AI 실행 (classify_spam)
  4. SUCCESS or FAILED + spam_score/folder 반영 후 commit
  - FAILED 시: retry_count+=1, last_failed_at, ai_result_raw 저장
"""
