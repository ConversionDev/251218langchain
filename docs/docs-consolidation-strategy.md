# docs 통합 전략

불필요하게 여러 파일로 나뉜 문서를 **역할별 대문서 몇 개**로 묶어 관리하기 위한 전략입니다.

---

## 1. 현재 상태 (22개 → 목표 8~9개)

| 구분 | 현재 파일 | 문제 |
|------|-----------|------|
| 목차 | README.md | 유지 |
| 핵심 | project-context, implementation-status, backend, runbook, issues-and-resolutions | 5개 유지하면 찾기 쉬움 |
| 전략 | vision-and-goals, mail-strategy, chat-rag-strategy, rag-and-vector, llama-spam-management | **5개 → 1개**로 통합 가능 |
| 기술 | technologies, db-and-migrations, extraction-and-data, exaone-tool-calling-design | **4개 → backend에 흡수** 또는 1개 |
| 프론트 | frontend.md, frontend-flow-and-status, frontend-backend-api-mapping | **리다이렉트 2개 삭제** (frontend.md만 유지) |
| 설계안 | mail-performance-integration, internal-address-book, disclosure-metrics, apply-form | **4개 → 1개** designs.md로 통합 |

---

## 2. 통합 후 목표 구조 (8개)

| 파일 | 역할 | 흡수·정리 내용 |
|------|------|----------------|
| **README.md** | 목차 + "아래 문서만 보면 됨" | 현재 유지, 목차만 통합 구조에 맞게 수정 |
| **project.md** | 프로젝트 맥락·비전·실행 한 번에 | **project-context** + **vision-and-goals** + **runbook** (개요·목표·데이터/실행) |
| **backend.md** | 백엔드·DB·기술·RAG 한 번에 | 현재 backend.md + **db-and-migrations** + **technologies** + **rag-and-vector** (진입점·API·도메인·DB·마이그레이션·기술스택·RAG) |
| **frontend.md** | 프론트 전부 | 현재 유지. **frontend-flow-and-status.md**, **frontend-backend-api-mapping.md** 파일 삭제 (이미 리다이렉트만 있음) |
| **status.md** | 기능별 구현 상태 (AI 인식용) | **implementation-status.md** 이름만 변경 또는 유지 |
| **issues-and-resolutions.md** | 과거 문제·해결 | 유지 |
| **strategy.md** | 도메인별 전략·설계 한 번에 | **mail-strategy** + **chat-rag-strategy** + **llama-spam-management** (+ 필요 시 rag-and-vector 요약). exaone-tool-calling은 "채팅 품질" 하위 섹션 또는 strategy에 짧게 요약 |
| **designs.md** | 확장·설계안 참고용 | **mail-performance-integration-design** + **internal-address-book-design** + **disclosure-metrics-design** + **extraction-and-data** + **exaone-tool-calling-design** + **apply-form** → 한 문서에 섹션으로 구분 |

---

## 3. 적용 순서 (리스크 낮은 순)

1. **리다이렉트 제거**  
   `frontend-flow-and-status.md`, `frontend-backend-api-mapping.md` 삭제. README와 내부 링크는 `frontend.md`만 가리키도록 이미 정리됨.

2. **설계안 통합**  
   `designs.md` 신규 생성 후 위 6개 설계 문서 내용을 섹션으로 이전. 기존 6개 파일은 "→ [designs.md](designs.md) §N 참고" 한 줄만 남기거나 삭제.

3. **전략 통합**  
   `strategy.md` 신규 생성 후 mail-strategy, chat-rag-strategy, llama-spam-management (및 rag-and-vector 요약) 이전. 기존 파일은 리다이렉트 또는 삭제.

4. **project.md 생성**  
   project-context + vision-and-goals + runbook을 하나로 합침. 기존 3개는 리다이렉트 또는 삭제.

5. **backend 확장**  
   backend.md에 db-and-migrations, technologies, rag-and-vector 내용을 섹션으로 추가. 기존 3개 파일 삭제 또는 리다이렉트.

6. **README 정리**  
   최종 8개(또는 9개) 구조에 맞게 목차만 수정.

---

## 4. 통합 시 유의사항

- **긴 문서**: backend.md, strategy.md, designs.md가 길어지므로 **목차(##, ###)** 를 명확히 두고, README에서 "§N 참고" 링크 가능하게 하면 됨.
- **외부/코드 링크**: 다른 repo나 코드에서 `mail-strategy.md` 등 **기존 경로**를 참조할 수 있으므로, 통합 후에는 **기존 파일을 삭제하지 않고 "이 문서는 strategy.md §메일 로 통합되었습니다"** 한 줄만 두는 방식**으로 하면 링크 깨짐을 방지할 수 있음.
- **implementation-status**: AI(Gemini 등)가 기능 상태 인식용으로 쓰므로 **파일명·위치 유지**하거나, status.md로 바꿀 경우 기존 경로에 짧은 리다이렉트 남기기.

---

## 5. 요약

| 전 | 후 |
|----|-----|
| 22개 md | **8개** (README + project + backend + frontend + status + issues-and-resolutions + strategy + designs) |
| 전략 5개·기술 4개·설계안 6개 흩어짐 | **strategy 1개** + **designs 1개** + **backend에 DB/기술/RAG** |
| 프론트 3개 (실질 1개+리다이렉트 2개) | **frontend 1개**, 리다이렉트 파일 삭제 |

이 순서대로 적용하면 "불필요하게 여러 부분으로 나뉜" 문서를 **역할별 대문서**로 통합해 관리할 수 있습니다.
