# 공시 지표(Disclosure Metrics) 설계

여러 공시 표준(ISO 30414, IFRS S1/S2 등)의 지표를 **추적 가능하게** 저장하기 위한 구조와 규칙입니다.

## 1. 문제: 단순 키-값의 한계

`disclosure_metrics`에 `{ "training_hours": 40 }`처럼 숫자만 넣으면:

- 어떤 기준(표준·항목)으로 집계된 수치인지 불명확
- 단위·측정 시점·근거가 없어 감사/공시 시 신뢰도 저하

## 2. 해결: 지표 객체 구조 (JSONB)

**한 지표 = 하나의 객체**로 저장합니다. 컬럼 타입은 그대로 JSONB이며, **내부 구조만 규칙**을 둡니다.

### 2.1 단일 지표 객체: `DisclosureMetricItem`

| 필드 | 타입 | 설명 |
|------|------|------|
| `standard` | string | 기준 표준 (예: `"ISO 30414"`, `"IFRS S1"`, `"IFRS S2"`) |
| `code` | string | 표준 내 항목 코드 (예: `"4.7.1"`, `"B14"`). 구 데이터: `categoryCode` |
| `name` | string? | 지표명 (예: "Total training hours"). 구 데이터: `description` |
| `value` | number | 수치 값 |
| `unit` | string | 단위 (예: `"hours"`, `"percent"`, `"ratio"`) |
| `status` | string? | 검증 상태 (예: `"verified"`) |
| `source_id` | string? | 추출 근거(원문) — 파일명·문서 ID (예: `survey_2025_01`) |
| `measuredAt` | string? | 측정/기준일 (YYYY-MM-DD) |

기존 필드명과의 대응: `categoryCode` → `code`, `description` → `name`, `source` → `source_id`. 하위 호환을 위해 구 필드명도 읽을 수 있음.

예시:

```json
{
  "items": [
    {
      "standard": "ISO 30414",
      "code": "4.7.1",
      "name": "Total training hours",
      "value": 40,
      "unit": "hours",
      "status": "verified"
    },
    {
      "standard": "IFRS S2",
      "code": "B14",
      "name": "Employee engagement",
      "value": 85,
      "unit": "percent",
      "source_id": "survey_2025_01"
    }
  ]
}
```

### 2.2 저장 형태 (호환)

- **레거시**: `{ "transitionReadyScore": 82, "skillGap": 18, "humanCapitalROI": 2.2 }` — 기존 UI/API와 호환.
- **신규(권장)**: `{ "items": [ DisclosureMetricItem, ... ] }` — 여러 표준·항목 추가 시 스키마 변경 없이 확장.

프론트에서는 `getIfrsMetricsView(disclosureMetrics)`로 레거시 3개 지표(transitionReadyScore, skillGap, humanCapitalROI) 뷰를 얻고, 확장 지표는 `getDisclosureMetric(payload, standard, code)`로 조회합니다.

## 3. ISO 30414 11개 영역(참고)

지표를 넣을 때 **어느 영역에 해당하는지** 분류해 두면 애매함이 줄어듭니다. LLM(엑사원 등)으로 이력서/문서에서 지표를 뽑을 때 "ISO 30414 11개 영역 중 해당하는 영역을 표시해 넣어라"라고 프롬프트할 수 있습니다.

| 영역(영문) | 예시 지표 |
|------------|-----------|
| Compliance | 윤리 교육 이수율 등 |
| Costs | 총 인건비, 채용당 비용 등 |
| Diversity | 성별 비율, 연령대 분포 등 |
| Leadership | 리더십 신뢰도 등 |
| Productivity | 직원당 수익 등 |
| … | (나머지 영역은 ISO 30414 본문 참고) |

`standard`: `"ISO 30414"`, `code`: 해당 절 번호(예: `"4.7.1"`)로 저장하면 보고서 출력 시 코드만으로 챕터 제목을 매핑할 수 있습니다.

## 4. 추적 가능성 (Source Mapping)

- **지표가 어디서 나왔는지**를 `source_id`에 남깁니다. (예: `"2025_education_log.xlsx"`, `survey_2025_01`)
- 엑사원이 이력서/사내 문서에서 지표를 생성할 때는, **어떤 문장의 어느 부분을 근거로 이 지표를 만들었는지**를 `source_id`(및 필요 시 `status: "verified"`)와 함께 JSONB에 넣도록 프롬프트하는 것을 권장합니다.

## 5. 지표 정의서와의 연동

- **disclosures 테이블 / `app/data/disclosure/`**: ISO 30414·IFRS 등 **지표 정의와 계산법(교과서)** 를 RAG용으로 저장.
- **분석 단계**: 엑사원이 이력서를 읽을 때 disclosures에서 해당 지표 정의(예: "훈련 시간 4.7.1")를 조회.
- **저장 단계**: 조회한 정의에 맞춰 값을 산출하고, 위 **지표 객체 구조**로 `employees.disclosure_metrics`에 저장.

이렇게 하면 **공시 기준(표준) — 원천(이력서/문서) — 지표(결과)** 가 연결되어 데이터의 애매함을 줄일 수 있습니다.

## 6. DB/마이그레이션

- `employees` 테이블은 007에서 한 번에 생성됩니다. `disclosure_metrics`(JSONB), RAG용 `embedding_content`·`embedding`(vector 1024)·HNSW 인덱스 포함. 직원 벡터 검색은 Neon pgvector(HNSW)만 사용(FAISS 미사용).

## 7. 레거시 3개 지표와 code 매핑

UI 뷰(대시보드 등)용으로 다음 `code`(또는 구 필드 `categoryCode`)가 레거시 필드와 매핑됩니다.

| 레거시 필드 | code 예시 |
|-------------|-----------|
| transitionReadyScore | `transition_ready`, `ifrs_s2_transition_ready` |
| skillGap | `skill_gap` |
| humanCapitalROI | `human_capital_roi` |

`getIfrsMetricsView()`가 `items[]`에서 위 코드를 찾아 레거시 뷰를 만듭니다.
