# ESG 전력 이상치 탐지 — 더미 데이터 생성 전략

> 목표: **measurements**(검증 완료 시계열) + **validation**(에러 로그) 구조와 6개 Rule을 기준으로,  
> “정상 베이스라인”과 “의도된 이상치”를 모두 갖춘 더미 데이터를 설계·생성하기 위한 전략.

---

## 1. 전제 정리

- **measurements**: 검증을 통과한 **확정 데이터**만 저장. (원본 raw가 아님)
- **validation**: 엑셀 행 단위로 검증 실패 시 **에러 유형·값·임계치** 기록.
- **플로우**: 엑셀 업로드/키인 → Save → Validation Rule 실행 → 정상만 measurements, 비정상은 validation_error_log → 이후 시계열 분석은 measurements만 사용.

따라서 더미 생성 시:

1. **정상 데이터** → Rule을 만족하는 행만 생성해 `measurements`에 넣을 수 있게 설계.
2. **이상 데이터** → 6가지 Rule별로 “걸리도록” 만든 행은 **measurements에 넣지 않고**, 대신 `validation`에 해당하는 에러 로그를 생성.
3. **시나리오 검증**을 위해 “정상만 있는 배치”와 “1~6번 각각/복합으로 실패한 배치”를 나눠 만들 수 있음.

---

## 2. 정상 베이스라인 정의

이상치가 “이상”으로 보이려면, **정상이 무엇인지** 먼저 정의해야 함.

### 2.1 공정·라인별 정상 프로파일 (시드/설정)

| process | line | 설비 정격(kW) | 정상 usage 범위(kWh) | 정상 production | 정상 equipment_ct | day 범위 | night 범위 | usage/production | usage/equipment_ct |
|---------|------|----------------|----------------------|-----------------|-------------------|----------|------------|------------------|---------------------|
| mixing  | L1   | 600            | 350~500              | 80~120          | 4~6               | 350~500  | 60~100     | 4.5~5.5          | 70~95               |
| plate   | L1   | 500            | 280~420              | 100~150         | 3~5               | 280~420  | 50~80      | 2.8~3.2          | 75~95               |
| cell    | L2   | 700            | 400~600              | 60~100          | 5~8               | 400~600  | 70~120     | 6.0~7.0          | 65~85               |
| module  | L1   | 550            | 300~450              | 40~70           | 3~5               | 300~450  | 40~70      | 6.5~7.5          | 75~95               |
| pack    | L1   | 450            | 250~380              | 30~50           | 2~4               | 250~380  | 30~60      | 7.5~8.5          | 90~110              |

- **설비 정격**: Rule 2 임계치.
- **정상 usage 범위**: Rule 6 (shift별 정상 범위) 및 Rule 2 미달 확인용.
- **usage/production, usage/equipment_ct**: Rule 4, 5 임계치 설정용 (예: 상한 1.2배를 threshold로).
- **계약 전력**: Rule 3용. 예: “동일 시간대 전체 라인 합계” 상한 2000 kWh 등.

이 프로파일을 **설정(JSON/DB/상수)** 으로 두고, 정상 행 생성 시 이 범위 안에서만 샘플링.

### 2.2 시간 축 설계

- **기간**: 예) 2024-01 ~ 2025-12 (24개월) → YoY 비교 가능.
- **시간 간격**: 1시간 단위 `noticedate`.
- **shift**: 06:00~18:00 = `day`, 18:00~06:00 = `night`.
- **선택**: 주말/공휴일은 `production` 0 또는 극소, `usage`는 기저(야간 범위)만 — 시계열 다양성 확보.

---

## 3. measurements용 정상 데이터 대량 생성

- **단위**: `noticedate` 1시간마다, (process, line) 조합별 1행.
- **로직 요약**:
  - 위 프로파일에서 (process, line, shift)별 정상 범위 조회.
  - `usage`: 해당 범위 내에서 **가우시안 랜덤** (평균=중간값, σ=범위의 약 1/6 등).
  - `production`, `equipment_ct`: 정상 범위에서 랜덤.
  - `usage/production`이 Rule 4 임계치 미만, `usage/equipment_ct`가 Rule 5 임계치 미만이 되도록 보정하거나, 아예 범위를 그렇게 설계.
- **계절성(선택)**:
  - 여름(7~8월): 기저 usage 5~10% 상승.
  - 겨울(12~1월): 난방/가열 반영으로 usage 소폭 상승.
- **예상 규모**: 5공정 × 2라인 가정 시, 24시간 × 365일 × 2년 ≈ 8만 행 이상 가능. 시계열 분석·차트에 충분.

생성 시 **Rule 3(계약 전력)** 만 유의: “동일 noticedate”에 대한 **전체 라인 합산**이 계약 상한 미만이어야 함.  
→ 시간 슬라이스 단위로 먼저 “이 시간대 합계 상한”을 두고, 공정/라인별로 쪼개서 usage를 부여하는 순서가 안전.

---

## 4. 이상치 시나리오와 validation 로그 생성

6개 Rule에 **1:1 대응**하는 이상 시나리오를 만들고, 각각에 대해 **measurements에는 넣지 않고** `validation` 테이블에만 기록하는 더미를 생성.

| Rule | 이상 유형           | 더미 생성 방식 | validation 예시 (error_type, value, threshold) |
|------|--------------------|----------------|-----------------------------------------------|
| 1️⃣   | 음수 전력           | 특정 (process, line, noticedate)의 usage를 -10 ~ -50으로 설정한 “행” 준비 | error_type=`NEGATIVE_POWER`, value=-25, threshold=0 |
| 2️⃣   | 설비 정격 초과      | usage를 해당 공정 정격의 110~130%로 설정한 행 준비 | error_type=`RATED_EXCEED`, value=820, threshold=700 |
| 3️⃣   | 계약 전력 초과      | **동일 noticedate**에 여러 (process, line) 행의 usage 합이 계약 상한을 넘도록 배치 | error_type=`CONTRACT_EXCEED`, value=2350, threshold=2000 |
| 4️⃣   | 생산량 대비 전력 이상 | production은 유지, usage만 40~60% 상향해 usage/production 비율이 임계치 초과 | error_type=`PRODUCTION_RATIO`, value=7.2, threshold=6.0 |
| 5️⃣   | 설비 가동 대비 전력 이상 | equipment_ct 유지, usage만 상향해 usage/equipment_ct 초과 | error_type=`EQUIPMENT_RATIO`, value=156, threshold=95 |
| 6️⃣   | 시간대 대비 이상    | night 행의 usage를 day 수준으로 올리거나, day를 정격 근처로 올려 “shift별 정상 범위” 이탈 | error_type=`SHIFT_RANGE`, value=320, threshold=100 (night 상한) |

**생성 전략**:

- **정상 배치**: 위 §3만 사용 → 모두 measurements 형태로 저장, validation 건수 0.
- **이상 배치**: “엑셀 행”을 시뮬레이션할 때, 1~6번 각각에 대해 “의도적으로 Rule에 걸리도록” 행을 만들고, Save 시뮬레이션 시:
  - 해당 행은 measurements에 넣지 않음.
  - 대신 `validation`에 (row_number, error_type, error_message, value, threshold, created_at) 삽입.
- **복합 이상**: 한 “행”이 여러 Rule에 동시에 걸리게 할 수 있음 (예: 음수 + 정격 초과). 이 경우 validation에는 Rule별로 1행씩 여러 건 기록.
- **비율**: 전체 더미 중 약 3~5%를 “이상”으로 두면, 대시보드·알림 테스트에 적당함.

---

## 5. validation 테이블 채우기

- **row_number**: “가상 엑셀”에서의 행 번호. 이상치 주입 시나리오마다 1, 2, 3… 또는 실제 엑셀 시트 행과 매핑.
- **error_type**: 1~6번을 코드로 매핑 (예: `NEGATIVE_POWER`, `RATED_EXCEED`, `CONTRACT_EXCEED`, `PRODUCTION_RATIO`, `EQUIPMENT_RATIO`, `SHIFT_RANGE`).
- **error_message**: 예) "usage < 0: 센서 오류 의심", "usage > 설비 정격(700 kWh)", "동일 시간대 계약 전력 초과" 등.
- **value / threshold**: 검증 시 사용한 실제값과 기준값. UI·원인 분석에서 “얼마나 벗어났는지” 보여주기 좋음.
- **created_at**: 검증 실행 시각.

이상치를 주입한 **시나리오 배치**를 “Save” 파이프라인에 넣었을 때, 검증기가 내뱉는 결과를 그대로 validation에 INSERT하는 형태로 시뮬레이션하면, 실제 플로우와 동일한 데이터 구조를 유지할 수 있음.

---

## 6. 구현 방식 제안

| 방식 | 장점 | 적합한 경우 |
|------|------|-------------|
| **Python 스크립트** (pandas + numpy) | 가우시안, 계절성, Rule 3 합산 제어, 6가지 이상 유형 주입 제어 용이 | 시드 데이터를 한 번에 만들고, CSV/DB INSERT로 적재할 때 |
| **SQL 시드** (Supabase 등) | DB 마이그레이션·버전과 함께 관리, 앱에서 바로 조회 | 백엔드가 이미 연결된 상태에서 초기 데이터 세팅 |
| **프론트 인라인 mock** | UI만 먼저 검증할 때 빠름 | DB 없이 차트·테이블·알림 목업만 필요할 때 |
| **엑셀 템플릿 + 업로드 시뮬레이션** | 실제 “엑셀 업로드 → Save → Validation” 플로우를 그대로 테스트 | E2E 검증용 |

권장: **정상 + 이상 시나리오를 Python으로 생성** → CSV/JSON 또는 직접 DB INSERT → 필요 시 동일 스크립트로 “엑셀 시트 형태”도 export해, 실제 업로드 플로우로 validation 로그가 쌓이게 테스트.

---

## 7. 요약

| 단계 | 내용 |
|------|------|
| 1 | 공정·라인·shift별 **정상 프로파일**(usage, production, equipment_ct, 비율, 정격, 계약 상한) 정의 |
| 2 | 이 프로파일과 Rule 3(시간대별 합계)을 만족하는 **정상 measurements** 대량 생성 (가우시안, 계절성·주말 선택) |
| 3 | 6가지 Rule에 **의도적으로 걸리도록** 이상 행 설계 → **measurements에는 넣지 않고**, **validation**에만 (row_number, error_type, value, threshold 등) 기록 |
| 4 | 정상/이상 비율(예: 95:5), 기간·빈도 조절로 시계열·대시보드·알림 검증에 쓸 수 있는 더미 확보 |

이 전략대로면 “검증이 끝난 의미 있는 데이터(measurements)”와 “오류 추적용 validation_error_log” 구조를 그대로 살리면서, 6개 Rule과 플로우를 모두 커버하는 더미 데이터를 형성할 수 있음.
