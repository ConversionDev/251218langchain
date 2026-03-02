# 확장·설계안 (참고)

메일–성과 연동, 사내 주소록, 공시 지표, 문서 추출·역량 스키마, ExaOne 도구 품질, 입사 지원 페이지 설계를 한 문서에 둡니다.

---

## 1. 메일 발송–성과 활동 연동

- **목표**: 발송한 메일을 선택적으로 performance_records(text_type=email)로 남기기. 기존 업무 제출(activity-records/submit) 유지.
- **권장**: 방식 A — `POST /api/mail/send` 요청에 `save_to_performance: true`, `employee_id`, `period`(선택) 추가. 발송 처리 후 동일 요청 안에서 create_submission 호출.
- **content**: 제목 + 본문 일부(500~1000자). period 없으면 현재 분기. 상세: [strategy.md](strategy.md) Part 1.

---

## 2. 사내 주소록 확장

- **목표**: 수신자를 직원 + 공용 메일함 + 그룹으로 확장. 주소록 전용 페이지·API.
- **타입**: person(employees), shared(공용함), group(메일 그룹). 권장: 직원은 기존 API, 공용/그룹은 `internal_addresses` 테이블 추가 후 **GET /api/address-book**에서 직원+internal_addresses 통합 반환.
- **부서**: "개발·IT" 등 통일. CRUD: 공용/그룹만 /api/address-book/shared 또는 /api/internal-addresses.

---

## 3. 공시 지표 (Disclosure Metrics)

- **문제**: 단순 키-값이면 기준·단위·근거 불명확.
- **구조**: JSONB 내 **지표 객체** — `standard`, `code`, `name`, `value`, `unit`, `status`, `source_id`, `measuredAt`. 레거시 호환: `transitionReadyScore`, `skillGap`, `humanCapitalROI` 유지. 신규는 `items: [ DisclosureMetricItem, ... ]`로 확장.

---

## 4. 문서·역량 추출 및 데이터

- **PDF 전략**: FastExtract(PyMuPDF) — 공시. Structural(pdfplumber) — NCS 역량. Intelligent(LlamaParse) — ESG 등(미구현 시 FastExtract). 라우팅: 파일명/경로 키워드.
- **competency_anchors 스키마**: content, category, level, section_title, source, source_type, metadata. O*NET 4종 xlsx + NCS PDF 4종 동일 스키마 적재. 구현: `domain/shared/strategies/`, `strategy_imples/`.

---

## 5. ExaOne 도구 바인딩 시 답변 품질

- **현상**: bind_tools 시 질문에 직접 답하지 않고 도구 설명·제안 위주 응답.
- **원인**: 도구 프롬프트 비중 과다, "역량 전문가" vs "도구 JSON" 지시 충돌.
- **개선 후보**: 프롬프트에서 "직접 답변 우선, 필요할 때만 도구 사용" 명시. 도구 섹션 축소. 조건부 도구 프롬프트 또는 RAG 경로에서 도구 프롬프트 최소화.

---

## 6. 입사 지원 페이지 (Apply)

- **양식**: `app/data/KPMG_입사지원서_Template.docx`. 추출: `python -m app.scripts.extract_apply_template`.
- **프론트**: `/apply`, 메인과 동일 배경·카드 스타일. 제출 시 createEmployeeApi, Employee·Resume 타입.
