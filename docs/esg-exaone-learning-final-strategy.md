# 엑사원 학습 최종 전략 — ESG 전력·손실량·폐기물 데이터셋

**문서 갱신(구현 동기화)**: 2025-03 — `noticedate`+`hour`, scrap/waste README 자동 반영, `measurements` vs validation·다변량 5종 구분 반영.

엑사원(ExaOne)이 **데이터 생성·학습**에 쓸 수 있도록 정리한 **최종 전략** 문서.  
시계열·이상치·예측을 위한 2년치 17~18만 건 데이터셋을 env_mapping 정보 전부를 활용해 만드는 방안.

---

## 1. 목표

- **시계열**: 공정·라인별 전력(usage) 시계열 분석, 추세·주기·시각화.
- **이상치**: 6가지 Rule 기반 검증 + 다변량 패턴(복합 이상) → Rule로 판단 어려운 경우 별도 학습, 정상 범위 이탈 시 원인 미상 또는 **원인 후보·조치 정확도별** 산정.
- **예측**: 전력 수요 예측(다음 1시간/1일/1주). 2년치 + 전력 수요 5년치 참고로 계절성 반영.

**데이터셋**: 손실량(scrap)·산출 폐기물(waste) 포함. **정의된 경우만** 데이터로 만들고, 정의 안 한 경우는 실제에서 나오면 **원인 미상**으로 둠.

---

## 2. 참고 정보 (전부 env_mapping)

| 구분 | 경로/파일 | 용도 |
|------|-----------|------|
| **전력 수요 데이터** | 전력수요 CSV(2022~2025) + 수요관리 CSV(2021) | usage 패턴·스케일, Rule 6 shift baseline, **월/계절** 반영(특정월 온도↑→전력↑는 정상 baseline) |
| **전기요금표** | 2025년 시행 전기요금표 PDF 등 | 계약 전력 상한 → Rule 3 |
| **README_ESG_맥락_및_현황** | app/data/env_mapping | 맥락·현황·파이프라인 입력·참고 데이터셋 요약 |
| **README_ESG_Rule_및_설비기준** | app/data/env_mapping | Rule 1~6, 설비 정격, Rule 4 threshold(`RULE4_THRESHOLD_KWH_PER_KWH` 파싱) |
| **README_배터리_손실량_폐기물_통상참고치** | app/data/env_mapping | §3.2 공정별 비율 표 → `build_profile()` 파싱 후 `profile.json`의 scrap·waste **절대 구간** |
| **esg-dummy-data-strategy 프로파일** | docs | (process, line)별 정상 usage/production/equipment_ct, day/night, scrap/waste |
| **mdpI (MDPI 보조자료)** | app/data/env_mapping/mdpI (Battery factories impact.xlsx, Energy_water_gas_emissions.xlsx) | Rule 4·usage 스케일 검증·보강 |

---

## 3. 데이터 범위 — 정의된 것만 생성

- **정상 (92~95%)**  
  프로파일·통상 참고치 범위. usage는 전력 수요 데이터 패턴 + **월/계절** 반영. 동일 1시간 합계 ≤ 계약 전력. scrap/waste는 통상 참고치 범위.

- **이상 — Rule 1~6 (각 0.5~1%)**  
  각 Rule 위반 행 + validation 로그(error_type, value, threshold).

- **이상 — 다변량 패턴 (MULTIVARIATE_* 5종, 기본 전 슬롯 대략 ~2.1%)**  
  `EFFICIENCY_DROP`, `IDLE_POWER`, `BASE_LOAD`, `SINGLE_EQUIPMENT_LOW`, `SCRAP_WASTE_DEVIATION`. 이상 슬롯 중 **약 35%**에서 균등 선택. **행은 `measurements.csv`에 넣지 않고** `validation_logs`·`labeled_slots`만 증가. Rule4/5 직전 클립·scrap/waste 상한 초과 등은 `training/pipelines/esg_dummy/README.md` 참고.

- **만들지 않음**  
  계측 오류, 점검일, 부분 가동, 시운전, 수요반응 등 **변수·정의 없는 경우** → 데이터셋에 넣지 않음. 실제에서는 **원인 미상**.

---

## 4. 건수·비율

| 항목 | 값 |
|------|-----|
| **기간** | 24개월 (예: 2024-01 ~ 2025-12) |
| **시간 단위** | 1시간 — `noticedate` + **`hour`(1~24)** |
| **공정·라인** | 5 process × 2 line = 10 |
| **measurements 건수** | **17만~18만 건** (2년) — **정상** + **Rule 3(CONTRACT)** 해당 시간대 행만 |
| **정상 슬롯** | 대략 전체의 **94%** 전후(기본 `anomaly-rate=0.06`) |
| **이상 슬롯(검증 로그)** | 대략 **6%**; 그중 다변량 **35%**·단일 Rule **65%**·시간대 CONTRACT는 `rate×0.15` |
| **다변량만** | 전 슬롯 약 **2.1%** (위 기본값 기준; `measurements` 비포함) |

이상 비율을 이렇게 작게 두는 것은 **현실감**(실제 공장도 대부분 정상), **학습·평가** 용이, **알림 과다 방지**를 위함.

---

## 5. 확장성·재학습 불필요

- **Rule 추가**: 프로파일/규칙 테이블에 rule_id·조건·임계치 추가.
- **정상 범위 변경**: 프로파일 min/max·임계치 수정.
- **원인 후보 추가**: 패턴→원인 규칙 테이블에 행 추가.
- **새 지표**: `extra_metrics`(JSON)에 넣고 규칙에서 참조만 추가.

→ **모델 재학습 없이** 설정만으로 확장.

---

## 6. 폴더·경로 매핑

| 구분 | 경로 |
|------|------|
| **입력(기준)** | app/data/env_mapping/ (README, CSV, PDF, **mdpI/** 포함) |
| **출력** | app/data/esg_dummy/ — `measurements.csv`(**정상+CONTRACT**, `hour` 포함), `validation_logs.csv`, `profile.json`; `--output-labeled` 시 `labeled_slots.csv` |
| **경로 함수** | app/core/paths.py 에 `get_esg_dummy_dir()` 추가 |
| **파이프라인** | app/training/pipelines/esg_dummy/ (resume_samples 구조 참고) |

---

## 7. 실행 순서 (시작 시)

1. **프로파일·기준 정리** — env_mapping README + 전기요금표 + mdpI에서 profile.json(또는 동일 역할 설정) 생성.
2. **전력 수요 패턴 테이블** — 전력 수요 데이터 전부 읽어 (날짜, 시간)별 패턴/비율 테이블 생성.
3. **데이터 생성 스크립트** — 정상 + Rule별 이상 + 다변량 이상 생성, 비율 유지, 출력은 esg_dummy/.
4. **1차 생성·검증** — 2년 17~18만 건 생성 후 Rule 1~6·비율·건수 검증.
5. **Rule 엔진·활용** — measurements + validation으로 Rule 엔진 검증, 클러스터링·원인 후보 규칙 테이블 연결.

---

## 8. 전력 측면 보조 정의 (설정 이외 최소화)

- **Shift 경계**: 06:00~17:59 = day, 18:00~05:59 = night 등 **고정**.
- **휴일**: 전력 수요 데이터와 맞춘 휴일 리스트, 해당일은 생산 0·usage 기저만.
- **계약 전력 vs 설비 정격**: 프로파일에 관계 명시.
- **시간 단위**: 1시간 평균 usage만 사용한다고 고정.
- **임계치 경계**: usage = 정격 등 **경계값** 정상/이상 판정 규칙 한 줄 정의.

---

## 9. 참고 문서

- `docs/esg-dummy-data-strategy.md` — 프로파일 표, 정상·이상 시나리오 상세.
- `docs/esg-dataset-scale-and-usage.md` — 규모·활용·확장성 상세.
- `app/data/env_mapping/README_ESG_맥락_및_현황.md`, `README_ESG_Rule_및_설비기준.md`, `README_배터리_손실량_폐기물_통상참고치.md`.

이 문서를 **엑사원 학습·데이터 생성 최종 전략**으로 사용한다.
