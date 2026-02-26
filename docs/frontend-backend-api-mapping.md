# 프론트엔드–백엔드 API 매핑 검토

검토일: 2026-02-26  
프론트 변경이 많았으므로, 호출 경로·메서드·쿼리/바디·응답 처리 일치 여부를 점검함.

---

## 1. 매핑 요약 (일치함)

| 프론트 호출 | 백엔드 경로 | 메서드 | 비고 |
|------------|-------------|--------|------|
| `modules/core/services.ts` | | | |
| `fetchEmployees()` | `/api/employees` | GET | 일치 |
| `fetchEmployeesPaginated({ page, pageSize, employmentType })` | `/api/employees?page=&pageSize=&employmentType=` | GET | 쿼리명·타입 일치 |
| `fetchNextEmployeeId()` | `/api/employees/next-id` | GET | 응답 `nextId` 사용 |
| `checkResumeHashApi(resumeHash)` | `/api/employees/check-resume-hash?resume_hash=` | GET | 쿼리명 `resume_hash` 일치 |
| `createEmployeeApi(payload)` | `/api/employees` | POST | Body camelCase(Employee), 409 시 existing 처리 |
| `updateEmployeeApi(id, payload)` | `/api/employees/{id}` | PUT | Body에 id 포함 |
| `deleteEmployeeApi(id)` | `/api/employees/{id}` | DELETE | 204 허용 |
| `analyzeEmployeeResumeApi(employeeId)` | `/api/employees/{id}/analyze` | POST | 일치 |
| `refreshEmployeeEmbeddingsApi()` | `/api/employees/embedding` | POST | Body `{}` |
| `backfillEmployeeProfilesApi({ dryRun, seed })` | `/api/employees/profile-backfill` | POST | 일치 |
| `modules/performance/services/activityServices.ts` | | | |
| `fetchActivityRecords({ period, grade, textType, limit })` | `/api/activity-records?period=&grade=&textType=&limit=` | GET | 백엔드 Query alias `textType` 일치 |
| `fetchActivitiesByEmployee(employeeId, params)` | `/api/activity-records/by-employee/{id}?…` | GET | 일치 |
| `fetchActivityById(id)` | `/api/activity-records/{record_id}` | GET | 일치 |
| `fetchMyActivities(employeeId, params)` | `/api/activity-records/my?employeeId=&period=&textType=&limit=` | GET | 쿼리 `employeeId` 일치 |
| `submitActivity({ employeeId, textType, content, period, tags })` | `/api/activity-records/submit` | POST | Body camelCase, 백엔드 SubmitPayload와 일치 |
| `modules/chat/services.ts` | | | |
| `uploadChatFiles(files)` | `/api/agent/upload` | POST | FormData key `files`, 백엔드 `List[UploadFile]` |
| `getThreadHistory(threadId)` | `/api/agent/threads/{thread_id}/history` | GET | 일치 |
| `deleteThread(threadId)` | `/api/agent/threads/{thread_id}` | DELETE | 일치 |
| `sendChatMessageStream(payload)` | `/api/agent/chat/stream` | POST | JSON body, 스트리밍 |
| `modules/core/services/resumeToBaseline.tsx` | | | |
| `analyzeResumeFile(file)` | `/api/resume/analyze` | POST | FormData key `file`, 백엔드 File(...) |
| `app/(dashboard)/risk/page.tsx` | | | |
| 감사 로그 조회 | `/api/audit/logs?limit=&action=&entityId=` | GET | 쿼리명 entityId, action 일치 |
| `app/(dashboard)/data-map/page.tsx` | | | |
| 클러스터 맵 iframe | `/api/clustering/map?theme=` | GET | fastapi_server 직접 등록 경로와 일치 |
| `modules/soccer/services.ts` | | | |
| 업로드/임베딩 | `/api/soccer/player/upload` 등, `/api/soccer/embedding`, `/api/soccer/embedding/status/{jobId}` | POST/GET | soccer_router 경로와 일치 |

---

## 2. API 베이스 URL

- 프론트: `process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"` (각 모듈에서 동일 패턴)
- 백엔드 기본: `localhost:8000`
- 배포 시 `NEXT_PUBLIC_API_URL`만 맞추면 됨.

---

## 3. 백엔드에만 있고 프론트에서 미사용인 API

- `/api/mail/send`, `/api/mail/filter` — 워크스페이스 메일 페이지는 현재 샘플 데이터만 사용, 실제 전송/필터 호출 없음.
- `/api/disclosure/*` — 공시 관련; 프론트에서 직접 호출하는 부분은 별도 확인 필요.

---

## 4. 결론

- **직원(employees), 성과 활동(activity-records), 채팅(agent), 이력서 분석(resume/analyze), 감사 로그(audit/logs), 데이터 지도(clustering/map), soccer**  
  → 경로·메서드·쿼리/바디·응답 필드명(camelCase) 모두 백엔드와 **매핑 일치**. 프론트 변경으로 인한 불일치는 없음.
- **메일(/workspace/mail)**  
  → 현재는 백엔드 연동 없이 UI만 동작. 추후 `/api/mail/send` 등 연동 시 위 표와 동일하게 경로/스펙만 맞추면 됨.
