# 기능별 구현 상태 (Implementation Status)

이 문서는 **Gemini 등 AI가 프로젝트의 기능별 구현 상태를 정확히 인식**할 수 있도록, 백엔드·프론트엔드·도메인별로 상태를 정의한 것입니다.

**상태 정의**
- **구현됨**: API·로직·UI가 실제 동작하며, DB/외부 연동 포함.
- **부분 구현**: 핵심만 동작하거나, 조건부·데이터 의존이 있음.
- **스텁**: 엔드포인트/함수는 있으나 실제 처리 없이 고정 응답 또는 no-op.
- **미구현**: 코드 없음 또는 명시적으로 "아직 구현되지 않음" 응답.

**프론트 연동**
- **연동됨**: 프론트에서 해당 API를 호출하여 사용 중.
- **미연동**: 백엔드만 구현되었고 프론트에서 호출하지 않음.

---

## 1. 직원 (Employees)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 직원 목록 조회 (GET /api/employees) | 구현됨 | 연동됨 | 페이지네이션, employmentType 필터. DB employees 테이블. |
| 직원 단건 조회 (GET /api/employees/{id}) | 구현됨 | 연동됨 | |
| 직원 생성 (POST /api/employees) | 구현됨 | 연동됨 | camelCase 페이로드, 409 시 기존 직원 안내. |
| 직원 수정 (PUT /api/employees/{id}) | 구현됨 | 연동됨 | |
| 직원 삭제 (DELETE /api/employees/{id}) | 구현됨 | 연동됨 | 204 허용. |
| 다음 ID 조회 (GET /api/employees/next-id) | 구현됨 | 연동됨 | 신규 등록 시 ID 부여용. |
| 이력서 해시 중복 확인 (GET /api/employees/check-resume-hash) | 구현됨 | 연동됨 | 동일 이력서 파일 재등록 방지. |
| 직원별 이력서 분석 (POST /api/employees/{id}/analyze) | 구현됨 | 연동됨 | 기존 직원 레코드에 이력서 재분석 반영. |
| 직원 임베딩 갱신 (POST /api/employees/embedding) | 구현됨 | 연동됨 | 전체 또는 지정 id. RAG 검색용 pgvector 갱신. |
| 직원 프로필 백필 (POST /api/employees/profile-backfill) | 구현됨 | 연동됨 | dryRun, seed 옵션. 누락 프로필 필드 채움. |
| 감사 로그 기록 | 구현됨 | (내부) | 직원 생성/수정/삭제 시 audit_log_repository에 기록. x-actor 헤더 지원. |

**의존성**: employee_repository, performance_record_repository(일부), audit_log_repository, resume_analyzer 서비스, disclosure embedding 모델(임베딩 갱신 시).

---

## 2. 성과 활동 (Activity Records)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 활동 목록 (GET /api/activity-records) | 구현됨 | 연동됨 | period, grade, textType 필터, limit. performance_records 테이블. |
| 직원별 활동 (GET /api/activity-records/by-employee/{id}) | 구현됨 | 연동됨 | |
| 활동 단건 (GET /api/activity-records/{record_id}) | 구현됨 | 연동됨 | |
| 내 활동 목록 (GET /api/activity-records/my) | 구현됨 | 연동됨 | employeeId 필수. 워크스페이스 "제출함"용. |
| 업무 제출 (POST /api/activity-records/submit) | 구현됨 | 연동됨 | meeting/report/email, content, period, tags. DB 저장. |

**의존성**: performance_record_repository, PerformanceRecord ORM.

---

## 3. 채팅 (Agent / LangGraph)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 파일 업로드 (POST /api/agent/upload) | 구현됨 | 연동됨 | 이미지·문서(PDF/TXT/Word/Excel). file_ids 반환. upload_store 사용. |
| 스트리밍 채팅 (POST /api/agent/chat/stream) | 구현됨 | 연동됨 | SSE. run_agent_stream, RAG·도구·멀티모달(이미지) 지원. |
| 스레드 이력 (GET /api/agent/threads/{thread_id}/history) | 구현됨 | 연동됨 | 체크포인터 기반. |
| 스레드 삭제 (DELETE /api/agent/threads/{thread_id}) | 구현됨 | 연동됨 | |
| 프로바이더 목록 (GET /api/agent/providers) | 구현됨 | (선택) | exaone 등, supports_tool_calling 포함. |
| 도구 목록 (GET /api/agent/tools) | 구현됨 | (선택) | search_documents, get_hr_summary, get_employee_info 등. |
| 에이전트 헬스 (GET /api/agent/health) | 구현됨 | (선택) | current_provider, checkpointer_enabled 등. |

**도메인**: chat_orchestrator.run_agent_stream, graph_orchestrator(TOOLS, build_agent_graph). RAG는 disclosures, competency_anchors, employees 벡터 검색. ExaOne 기본, Gemini 멀티모달 지원.

**의존성**: domain.hub.orchestrators.chat_orchestrator, domain.hub.llm, domain.hub.repositories(disclosure, competency_anchor, employee, performance_record), FAISS 또는 pgvector.

---

## 4. 이력서 분석 (Resume)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 이력서 분석 (POST /api/resume/analyze) | 구현됨 | 연동됨 | PDF/TXT/Word/HWP. 텍스트 추출 → LLM 분석 → name, jobTitle, department, email, successDna 등 반환. |

**의존성**: api.services.resume_analyzer.analyze_resume_file, document_extract, LLM(get_llm). Core 신입 관리에서 이력서 업로드 시 호출.

---

## 5. 감사 로그 (Audit)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 감사 로그 조회 (GET /api/audit/logs) | 구현됨 | 연동됨 | entityType, entityId, action, actor, fromAt, toAt, limit. audit_logs 테이블. |

**의존성**: audit_log_repository.list_logs.

---

## 6. 공시 (Disclosure)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 적재 상태 (GET /api/disclosure/status) | 구현됨 | 미연동 가능 | document_count, embedded_count, embedding_ratio. |
| 공시 기여도 예측 동기 (POST /api/disclosure/check) | 구현됨 | 미연동 가능 | 이름·직급·부서 등 → RAG+LLM → suitable, message, suggestions. DB SessionLocal 직접 사용. |
| 공시 기여도 예측 비동기 (POST /api/disclosure/check → GET /api/disclosure/check/result/{job_id}) | 구현됨 | 미연동 가능 | BackgroundTasks로 job_id 반환, 폴링으로 결과 조회. |
| 공시 임베딩 실행 (POST /api/disclosure/embedding/run) | 구현됨 | (관리) | prepared 디렉터리 기반으로 disclosures 테이블 임베딩 채움. |
| 공시 문서 적재 (disclosure ingest 파이프라인) | 구현됨 | (CLI/수동) | disclosure_orchestrator, JSONL/ prepared 경로. API가 아닌 별도 실행. |

**참고**: 프론트에서 disclosure API를 직접 호출하는 화면은 별도 확인 필요. 백엔드는 전부 구현됨.

---

## 7. 문서 (Document)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 지원 확장자 (GET /api/document/supported-extensions) | 구현됨 | (선택) | text, excel, all. document_extract 단일 소스와 동기화. |

채팅 업로드·이력서 분석에서 사용하는 확장자와 동일 소스.

---

## 8. 이메일 / 메일 (Mail)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 수신 (POST /api/mail/receive) | 구현됨 | 미연동 | Webhook. external_id 중복→409, Resolver(To→owner_employee_id) 실패→4xx, 스팸 판정→folder=inbox/spam 저장. |
| 수신 메일 AI 분석 (비동기) | 구현됨 | — | inbox 저장 후 BackgroundTasks로 성과/5대 역량 분류 → performance_records·역량 태깅. |
| 스팸 필터 (POST /api/mail/filter) | 구현됨 | 미연동 | run_spam_detection. action, routing_strategy, reason_codes, user_message 등 반환. |
| 이메일 전송 (POST /api/mail/send) | 스텁 | 미연동 | 메타데이터만 mail_items에 저장. 실제 SMTP 등 발송 미구현. |
| 워크스페이스 메일 UI (/workspace/mail) | 부분 구현 | 미연동 | 프론트는 샘플 데이터만 사용. 백엔드 receive/list/스팸은 구현됨. |

**정리**: 수신·스팸·AI 분석 연결 구현됨. send는 스텁. 워크스페이스 메일 페이지는 아직 백엔드와 연동되지 않음.

---

## 9. 데이터 지도 (Clustering Map)

| 항목 | 상태 | 프론트 연동 | 설명 |
|------|------|-------------|------|
| 지도 HTML 서빙 (GET /api/clustering/map) | 구현됨 | 연동됨 | competency_map.html. theme=dark 시 다크 스타일 주입. iframe용 frame-ancestors * 헤더. |
| competency_map.html 생성 | 부분 구현 | — | **수동 실행 필요.** `python -m training.pipelines.clustering.run_competency_visualization` 으로 생성. 미실행 시 404. |

**의존성**: core.paths.get_clustering_dir(), 역량 임베딩·UMAP·K-Means 등. 사전에 스크립트 실행 후 HTML이 있어야 /api/clustering/map 이 200 반환.

---

## 10. 내부 API (Hub LLM)

| 항목 | 상태 | 호출 주체 | 설명 |
|------|------|-----------|------|
| Llama 스팸 분류 (POST /internal/llama/classify_spam) | 구현됨 | Spokes·email_router | domain.hub.llm.classify_spam. |
| ExaOne 생성 (POST /internal/exaone/generate) | 구현됨 | Spokes | |
| ExaOne 이메일 분석 (POST /internal/exaone/analyze_email) | 구현됨 | Spokes | |
| Chat MCP / Chat Spoke | 구현됨 | Hub | 동일 프로세스 /internal/mcp/chat, /internal/mcp/chat-spoke 마운트. |

프론트는 직접 호출하지 않음. MCP·스팸 플로우 내부용.

---

## 11. MCP (Central Hub)

| 항목 | 상태 | 설명 |
|------|------|------|
| /mcp 마운트 | 구현됨 | FastMCP 앱. health, /server 프로토콜. |
| Chat MCP 위임 (generate_with_exaone, classify_then_generate 등) | 구현됨 | 채팅은 ExaOne만 사용, LLaMA 제거. get_chat_mcp_url → call_tool. |
| Spam MCP 위임 (analyze_email, classify_spam) | 구현됨 | get_spam_mcp_url → call_tool. |

Soccer MCP는 제거됨. 현재 Chat / Spam 만 존재.

---

## 12. 임베딩 동기화 (Embedding Sync)

| 항목 | 상태 | 설명 |
|------|------|------|
| run_embedding_sync_task (api.shared.embedding_sync) | 스텁 | Redis에 job 상태만 "completed"로 설정. 실제 임베딩 갱신 로직 없음. (과거 soccer 용도 제거 후 호환용.) |

**호출처**: 없음 (이전 soccer_router 제거로 호출하는 코드 없음).

---

## 13. 기타·인프라

| 항목 | 상태 | 설명 |
|------|------|------|
| CORS | 구현됨 | gateway.add_cors_middleware. CORS_ORIGINS 없으면 * 허용. |
| DB 마이그레이션 (Alembic) | 구현됨 | AUTO_MIGRATE=true 시 기동 시 upgrade head. |
| RAG 초기화 (ensure_rag_initialized) | 구현됨 | Embedding(BGE-m3), FAISS 인덱스(선택), disclosure·competency 준비. |
| GET /, GET /health | 구현됨 | API 상태, local_embeddings 여부. |

---

## 14. 프론트엔드 화면별 요약

| 화면/경로 | 백엔드 연동 | 비고 |
|-----------|-------------|------|
| /dashboard, 전사 현황 | 연동됨 | 직원·활동 등 API 사용. |
| /chat, AI 질의 | 연동됨 | /api/agent/upload, /api/agent/chat/stream, threads. |
| /core/new-hires, 신입 관리 | 연동됨 | /api/resume/analyze, /api/employees. |
| /core/employees, 기존 직원 | 연동됨 | /api/employees 전부. |
| /performance/activities | 연동됨 | /api/activity-records. |
| /risk, 감사 로그 | 연동됨 | /api/audit/logs. |
| /data-map, 데이터 지도 | 연동됨 | /api/clustering/map. (HTML 사전 생성 필요) |
| /workspace, 직원 서비스 | 연동됨 | 업무 제출 → /api/activity-records/submit, 내 활동 → /api/activity-records/my. |
| /workspace/mail | 미연동 | 프론트 샘플만. 백엔드 /api/mail/receive·list·filter 구현됨. |
| /apply, 이력서 지원 | 연동됨 | 이력서 제출·저장 등. |
| /resumes, 지원내역 | 연동됨 | 이름·이메일 조회 등. |

---

## 15. AI(Gemini) 인식용 요약 문장

- **직원·성과 활동·채팅·이력서 분석·감사 로그·데이터 지도·공시(disclosure)·문서 지원 확장자**: 백엔드 구현됨. 직원/활동/채팅/감사/지도/워크스페이스 업무제출·내활동은 프론트와 연동됨. 공시 API는 프론트 직접 호출 여부 별도 확인.
- **이메일**: 수신(receive)·스팸 판정·inbox 저장 후 AI 분석(성과/역량) 구현됨. 스팸 필터 구현됨. 전송(send)은 스텁. 워크스페이스 메일 페이지는 프론트 미연동(샘플만).
- **임베딩 동기화**: 스텁. 호출처 없음.
- **데이터 지도**: 지도 HTML은 수동 스크립트 실행으로 생성해야 하며, 생성 후 /api/clustering/map 으로 서빙됨.

이 문서를 업데이트할 때는 위 상태 정의(구현됨/부분 구현/스텁/미구현)와 프론트 연동(연동됨/미연동)을 유지하면, Gemini 등이 현재 프로젝트의 기능별 구현 상태를 일관되게 인식할 수 있다.
