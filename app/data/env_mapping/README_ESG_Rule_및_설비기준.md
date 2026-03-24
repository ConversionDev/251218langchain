# ESG 전력 — 6가지 Rule & 설비·단위전력 기준

**통합 문서** (기존 `README_6가지_Rule_현황.md` + `README_설비정격_공정별기대전력_출처.md`).  
**코드 연동**: `run_generate_measurements._load_rule4_from_readme_rated()`가 **이 파일**에서 `RULE4_THRESHOLD_KWH_PER_KWH` 및 폴백 패턴(`28.3~34.6`, `30~35`)을 파싱합니다.  
**함께 쓰는 문서**: `README_ESG_맥락_및_현황.md`, `README_배터리_손실량_폐기물_통상참고치.md`.

---

## 1. 6가지 Rule 현황

시계열 이상치 탐지용 **Rule 1~6** 기준·데이터·구현 상태를 한눈에 보는 문서입니다.  
**원칙**: 기준·참고는 **가급적 최근**(2024~2025) 우선. 맥락은 `README_ESG_맥락_및_현황.md` 참고.

### 구현·스키마 갱신 (더미 파이프라인)

- **`measurements.csv`**: `training.pipelines.esg_dummy.run_generate_measurements` 출력에 **`hour`(1~24)** 컬럼 포함 (`noticedate` 다음). 시계열·이동평균·시간대 조인은 **`noticedate` + `hour` + `process` + `line`** 기준 정렬 권장. 예전에 생성한 CSV에는 `hour`가 없을 수 있음 → 동일 스크립트로 **재생성** (`app/training/pipelines/esg_dummy/README.md`).
- **`labeled_slots.csv`**: 기존과 같이 `noticedate`, `hour`, …, `label` 유지. 시간 정보가 필요하면 **우선 본 파일** 사용 가능.
- **`verify_esg_dummy_data.py`**: `measurements` 안 **CONTRACT_EXCEED 의도 행**(usage가 shift별 정상 상한 `u_hi`의 약 **1.09배 초과**)은 프로파일 usage 밴드 및 Rule 2/4/5 **정상 구간 검증에서 제외**.

---

## 요약 표

| Rule | 내용 | 기준/임계치 출처 | 데이터 보유 | 상태 |
|------|------|-----------------|-------------|------|
| **1** | 음수 전력 | 고정 (usage < 0) | 불필요 | ✅ 준비됨 |
| **2** | 설비 정격 초과 | 설비별 정격(kW) | README에 정리 (MTI, 켐시스템) | ✅ 기준 확보, 테이블화 대기 |
| **3** | 계약 전력 초과 | 계약 상한(kW) | **2025년 1월 시행 전기요금표 PDF** | ✅ 기준 확보, 테이블화 대기 |
| **4** | 생산량 대비 전력 이상 | 단위 생산당 전력(kWh/kWh) | **MDPI 2025** (28.3~34.6 kWh/kWhprod) | ✅ 기준 확보, 테이블화 대기 |
| **5** | 설비 가동 대비 전력 이상 | usage/equipment_ct 상한 | 공장 입력·프로파일로 설정 | ⚠️ 공개 기준 없음, 설정값으로 운영 |
| **6** | 시간대(shift) 대비 이상 | shift별 정상 usage 범위 | 전력수요 CSV·프로파일로 baseline | ⚠️ 주기성 데이터로 baseline 설계 필요 |

---

## Rule별 상세

### Rule 1 — 음수 전력

- **판단**: `usage < 0` → 이상 (센서 오류 등 의심).
- **기준**: 고정. 별도 테이블/문서 불필요.
- **상태**: ✅ 그대로 적용 가능.

---

### Rule 2 — 설비 정격 초과

- **판단**: `usage`(측정 전력) > 해당 설비 **정격(kW)** → 이상.
- **기준 출처**: 아래 **§2 설비 정격 및 Rule 4 출처**
  - 슬롯다이 코터: 1.5 kW, 2.1 kW (MTI)  
  - 건조기: 1.1~220 kW 구간 (켐시스템/Yanming)  
  - 실험실용 진공건조 오븐: 0.4~2.8 kW  
- **데이터**: README에 표로 정리됨. `equipment_rated_power` 테이블/CSV로 옮기면 Rule 2 검증에 바로 사용 가능.
- **상태**: ✅ 기준 확보. 테이블(또는 설정) 구현만 하면 됨.

---

### Rule 3 — 계약 전력 초과

- **판단**: **동일 noticedate**(같은 시간대)에 여러 (process, line)의 `usage` **합계** > **계약 전력 상한** → 이상.
- **기준 출처**: **2025년도 1월 1일 시행 전기요금표(종합).pdf**  
  - 300 kW / 1,000 kW 등 구간별 계약 전력 확인 가능.
- **데이터**: `app/data/env_mapping/2025년도+01월+01일+시행+전기요금표(종합).pdf` 보유.
- **상태**: ✅ 기준 확보. 계약 전력값을 설정/테이블로 넣으면 Rule 3 검증 가능.

---

### Rule 4 — 생산량 대비 전력 이상

- **판단**: `usage / production`(단위 생산당 전력) > **기준 상한** → 이상.
- **기준 출처**: **MDPI 2025** (2024–2025년 기준)  
  - **28.3~34.6 kWh/kWhprod** (또는 구간 **30–35 kWh/kWh**).  
  - 상한을 이 범위 위로 두고(예: 35~40) threshold 설정.
- **데이터**: 본 문서 §2에 수치·URL 정리됨.
- **상태**: ✅ 2025 기준 확보. baseline/threshold 테이블에 반영하면 됨.

---

### Rule 5 — 설비 가동 대비 전력 이상

- **판단**: `usage / equipment_ct` > **설정 상한** → 이상 (`error_type` = `EQUIPMENT_RATIO`).
- **기준(문헌·공개 데이터)**: **공정별 “설비 1대당 허용 usage”를 적어 둔 공개 표준 데이터는 없음.** MDPI 논문 등도 Rule 4(생산 대비 에너지) 중심이며, **Rule 5와 1:1 대응하는 외부 테이블은 사용하지 않음.**
- **데이터셋(이 프로젝트에서 값이 나오는 곳)**  
  - **임계치 `rule5_usage_per_equipment_max`**: 코드 기본값 **`DEFAULT_PROFILE` → 95** (`run_generate_measurements.py`). `app/data/env_mapping/profile_source.json`에 키를 넣으면 **`profile.json` 생성 시 덮어쓰기** 가능.  
  - **행마다 `equipment_ct`**: (process, line)별 **정수 구간** — 역시 **`DEFAULT_PROFILE`의 `process_line[].equipment_ct`** (예: 4~6대). 설계 의도·시나리오는 **`docs/esg-dummy-data-strategy.md`** (Rule 5 예시: threshold=95 등).  
  - **실무**: 현장 MES/설비 가동 집계가 쌓이면 **자사 데이터로 분위수·평균+σ** 등으로 상한을 다시 잡는 것이 일반적 (본 문서 §1 하단 Rule 5·6 절차 참고).
- **코드에서의 구현 (`run_generate_measurements.py`)**  
  - **정상 행**: `cap5 = equipment_ct * rule5_max` 로 `usage` 상한을 걸어 **`usage / equipment_ct ≤ rule5_max`** 가 되도록 자름(Rule 4 상한 `cap4`와 함께 `min` 적용).  
  - **이상 주입**: Rule 5가 뽑히면 `usage = equipment_ct * rule5_max * (1.1 ~ 1.4)` 로 올려 **`validation_logs.csv`** 에 `EQUIPMENT_RATIO` 기록, **`labeled_slots.csv`** 에 동일 라벨. **`measurements.csv`에는 Rule 5 이상 행을 넣지 않음**(정상·일부 CONTRACT 행만 measurements).  
  - **검증**: `verify_esg_dummy_data.py`가 `measurements`에 대해 Rule 5 위반 여부 검사(단, 위 “CONTRACT 의도 행”은 제외).

- **상태**: ⚠️ 공개 단일 기준 없음. **프로파일·설정값(95)** 으로 더미·룰 검증 가능. 현장 데이터로 갱신 권장.

---

### Rule 6 — 시간대(shift) 대비 이상

- **판단**: (process, line, **shift**)별 **정상 usage 범위** 밖 → 이상.  
  - 예: night shift인데 usage가 day 수준으로 높음, 또는 그 반대.
- **기준**:  
  - **전력수요 CSV**(한국전력거래소 시간별 전국 전력수요량 2024, 2025 등)로 시간대·요일·계절별 **주기성** 참고.  
  - 공정·라인·shift별 **정상 프로파일**(day/night 범위)을 정의해 baseline으로 사용.
- **데이터**:  
  - `한국전력거래소_시간별 전국 전력수요량_*.csv` 보유.  
  - “정상 범위”는 더미 전략의 프로파일처럼 (process, line, shift)별 min~max로 정의 필요.
- **상태**: ⚠️ **baseline 설계 필요**. CSV로 주기성 참고 → 프로파일/설정 테이블에 shift별 범위 넣으면 Rule 6 적용 가능.

---

## Rule 5·6 — “임의 지정”이 아닌, 통상적인 진행 방식

Rule 5(설비 가동 대비 전력), Rule 6(시간대 대비 이상)처럼 **상한·정상 범위를 외부에서 정해주는 공개 자료는 거의 없습니다.**  
대신 업계·표준에서 **통상 어떻게 진행하는지**만 정리하면 아래와 같습니다.

### 1. 외부에서 “이렇게 지정하라”는 정보가 없는 이유

- **공정별·설비 단위당·shift별** 세부 기준을 **업종/공장 공통으로 제시한 공개 표준·가이드**는 찾기 어렵습니다.
- **에너지공단·에너지총조사** 등은 산업 전체·국가 단위 통계(에너지원단위 등)만 제공하며, “이 공정은 이 범위” 같은 수치는 없습니다.
- **ISO 50001**(에너지 경영시스템)은 **EnPI(에너지 성과 지표)·Energy Baseline** 사용을 권장하지만, **어떤 변수로 정규화할지, 상한을 얼마로 할지**는 **조직이 스스로 정한다**고만 되어 있습니다. (표준이 구체 수치를 정해 주지 않음.)

### 2. 통상적인 진행 방식 — “자사 과거 데이터로 baseline”

- **실무·연구**에서는 **자사(동일 사업장) 과거 데이터**로 **통계적 baseline·정상 범위**를 만드는 방식을 씁니다.
  - **Rule 5 (usage/equipment_ct)**: 과거 정상 구간의 평균·표준편차(또는 분위수)로 “정상 비율”과 상한(예: 평균+2σ, 95% 분위) 설정.
  - **Rule 6 (shift별 범위)**: (process, line, shift)별 과거 usage의 **이동평균·회귀·분위수**로 “해당 shift의 정상 min~max” 설정.
- **SPC(통계적 공정 관리)** 를 에너지에 적용한 사례도 같은 논리입니다.  
  - 실제 소비를 **예상값(회귀, PLS, 이동평균 등)** 과 비교하고, **CUSUM·3-sigma·관리한계** 등으로 이상 탐지.  
  - 여기서 “예상값·한계”는 **해당 사이트 역사 데이터**에서 추정합니다.
- 요약하면: **“임의로 숫자만 고르는 것”이 아니라, “과거 정상 데이터로 통계적 범위를 추정해 그걸 기준으로 둔다”**가 통상입니다.

### 3. 우리가 할 수 있는 선택지

| 방법 | 설명 |
|------|------|
| **당장** | 공장 입력·프로파일로 **설정값(상한, shift별 범위)** 을 두고 Rule 5·6 적용. 이후 measurements가 쌓이면 아래로 전환. |
| **데이터 쌓인 후** | **자사 measurements**로 (process, line, shift)별·usage/equipment_ct별 **평균·σ·분위수** 계산 → 그걸 baseline/threshold로 갱신. |
| **참고만** | 전력수요 CSV(시간대·요일 주기성)로 “낮/밤 대략적 비율” 참고. 절대값은 사업장마다 다르므로, 범위 설정은 자사 데이터 기반이 맞음. |

**정리**: Rule 5·6에 대해 **“통상적으로 이렇게 진행한다”는 정보를 외부 문서에서 찾는 것은 사실상 어렵고**, **실제로는 “자사 과거 데이터로 통계적 baseline을 만드는 것”이 일반적인 방법**입니다.  
그래서 지금은 설정값으로 운영하고, 데이터가 쌓이면 **같은 measurements로 baseline을 추정·갱신**하는 흐름을 두면 됩니다.

---

## 다음에 할 수 있는 작업

1. **기준 테이블/설정 구현**  
   - Rule 2: `equipment_rated_power` (설비–정격 kW)  
   - Rule 3: 계약 전력 상한 (kW)  
   - Rule 4: 공정별 또는 전역 단위 생산당 전력 상한 (28.3~34.6 또는 30–35 기준으로 상한 설정)  
   - Rule 6: (process, line, shift)별 정상 usage 범위

2. **measurements 더미 데이터 생성**  
   - `esg-dummy-data-strategy.md`대로 정상 + 6가지 이상 시나리오 생성 → validation 로그와 함께 검증.

3. **Rule 5**  
   - 당분간 설정값(usage/equipment_ct 상한)으로 운영하고, 실제 데이터 쌓이면 baseline 갱신.

---

## 예측까지 고려 시 추가 테이블

지금 설계만으로 **시계열·이상치·예측** 모두 입력 데이터는 **measurements**로 충분합니다.  
다만 예측 **결과를 저장·비교**하려면 아래를 두는 편이 좋습니다.

| 테이블 | 용도 | 필수 여부 |
|--------|------|-----------|
| **measurements** | 시계열 입력·이상치 판단·예측 학습용 | ✅ 기존 설계 |
| **validation** | Rule 위반 에러 로그 | ✅ 기존 설계 |
| **기준/설정 테이블** (Rule 2~6) | 설비 정격, 계약 전력, 공정별 상한, shift별 범위 등 | ✅ 이미 “다음 작업”에 포함 |
| **usage_forecasts** (예측 결과) | 예측값 저장 → 실제와 비교, “예측 대비 이탈” 이상치 | ⭐ 예측 단계에서 권장 |

### usage_forecasts 예시 (선택)

예측 결과를 남겨서 **실제(measurements) vs 예측** 비교·대시보드·백테스트에 쓰려면 예시 스키마는 아래처럼 둘 수 있습니다.

| 컬럼 | 설명 |
|------|------|
| forecast_id | PK |
| noticedate | 예측 대상 시점 (또는 생성 시각) |
| process, line | measurements와 동일 |
| horizon_hours | 예측 수평선 (예: 1, 24) |
| predicted_usage | 예측 전력 (kWh) |
| predicted_lower, predicted_upper | (선택) 구간 예측 시 하한·상한 |
| model_version | 모델/버전 식별 |
| created_at | 예측 생성 시각 |

→ **실제 usage**는 `measurements`에서 조인.  
→ “실제가 predicted_upper 초과” 등으로 **예측 기반 이상치** 규칙을 추가할 수 있음.

**정리**:  
- **없어도 되는 것**: measurements만으로 예측 모델은 학습·실행 가능.  
- **있으면 좋은 것**: `usage_forecasts`처럼 **예측 결과 전용 테이블** 하나 두면, 예측 저장·실제와 비교·예측 기반 이상 탐지까지 한 구조로 갈 수 있음.  
- **calendar/외부 요인**: 요일·휴일은 `noticedate`에서 파생 가능. 날씨·요금 등 별도 수집 시에만 `external_factors` 같은 테이블을 추가하면 됨.

---

## 참고 문서

| 문서 | 용도 |
|------|------|
| 본 문서 §2 | Rule 2 설비 정격, Rule 4 공정별 기대 전력(2025 기준) |
| `docs/esg-dummy-data-strategy.md` | 6 Rule 더미 생성 전략, validation 예시 |
| 전기요금표 PDF, 전력수요 CSV | Rule 3 계약 전력, Rule 6 시간대 baseline 참고 |

위 상태를 기준으로 **Rule 1~4는 기준 확보**, **Rule 5·6은 설정/프로파일로 보완**하면 6가지 전부 흐름에 올릴 수 있습니다.

---

## 2. 설비 정격 & 공정별 기대 전력 — 출처 및 수치

Rule 2(설비 정격 초과), Rule 4(생산량 대비 전력 이상)용 기준 데이터를 **어디서 찾았는지**, **어떤 수치를 쓸 수 있는지** 정리한 문서입니다.  
**원칙**: 출처 URL이 확인된 수치만 수록. 불명확한 수치는 제외.  
**확인 기준**: 2025-03 직접 접속 확인.

---

## Rule 2 — 설비 정격 초과 기준

> `usage > 설비 정격(kW)` → 이상 판정 (`RATED_EXCEED`)  
> 아래 설비별 정격을 `equipment_rated_power` 테이블/설정에 넣고 사용.

### 2-1. 슬롯다이 코터 (Slot-die Coater)

배터리 전극 슬러리를 집전체(알루미늄·동박)에 코팅하는 설비.

| 설비명 | 정격 전력 | 출처 URL | 확인 상태 | 스펙 원문 |
|--------|-----------|----------|-----------|-----------|
| **MSK-AFA-H500SD** (Sheet-to-Sheet, 300mm 폭, 진공척 가열) | **3.0 kW** | https://www.premier-sols.com/partners/item/300mm-wide-slot-die-sheet-to-sheet-coater-w-ss316-heating-vacuum-chuck-150%C2%B0c-400-w-%C3%97-500mm-l-msk-afa-h500sd.html | ✅ 2025-03 직접 확인 | "3000W, 110V or 208-240V AC, 50/60Hz" |
| **MSK-AFA-SD200-LD** (Roll-to-Roll, 160mm 폭) | **2.1 kW** | https://www.premier-sols.com/partners/item/small-roll-to-roll-slot-die-coating-system-max-160-mm-w-with-slurry-feeder-msk-afa-sd200-ld.html | ✅ 2025-03 직접 확인 | "Power: 2.1 KW (15A Air breaker required), 208-240 VAC, 50/60 Hz" |

- **출처**: Premier Sols (MTI 싱가포르 공식 대리점, https://www.premier-sols.com)
- **스케일**: 실험·파일럿 규모 장비 기준. 양산 라인 코터는 이보다 훨씬 큼.
- **MTI 본사 스토어**: https://www.mtixtl.com (mti-kjgroup.com 일부 URL 404 발생 — mtixtl.com 사용 권장)

---

### 2-2. 건조기 (배터리 전극·소재용)

전극 코팅 후 용매(NMP 등)를 제거하는 설비. 출처: Yanming/켐시스템 한국어 공식 페이지 (리튬 배터리 소재용 건조기 전문, 2025-03 직접 확인).

| 설비 유형 | 정격 전력 범위 | 출처 URL | 확인 상태 | 스펙 원문 |
|-----------|----------------|----------|-----------|-----------|
| **회전 트레이 건조기** | **1.1 ~ 18.5 kW** | http://chemsystem-kr.com/1-1-rotary-tray-dryer.html | ✅ 2025-03 직접 확인 | "건조 구역 3.3-168m², 전력 1.1-18.5kW" |
| **패들 건조기** | **1.5 ~ 220 kW** | http://chemsystem-kr.com/1-2-paddle-dryer.html | ✅ 2025-03 직접 확인 | "열교환 면적 1-300m², 모터 출력 1.5-220kW" |
| **스핀 플래시 건조기** | **1.1 ~ 55 kW** | http://chemsystem-kr.com/1-3-spin-flash-dryer.html | ✅ 2025-03 직접 확인 | "전력 1.1-55kW" |
| **유동층 건조기** | **5.5 × 2 kW** | http://chemsystem-kr.com/1-4-fluid-bed-dryer.html | ✅ 2025-03 직접 확인 | "진동 모터 출력 5.5×2kW" |
| **수직 리본 진공 건조기** | **1.5 ~ 22 kW** | http://chemsystem-kr.com/1-5-vertical-ribbon-vacuum-dryer.html | ✅ 2025-03 직접 확인 | "내경 500-2300mm, 전력 1.5-22kW" |

- **목록 페이지**: http://chemsystem-kr.com/1-dryers.html
- **스케일 주의**: 위 수치는 파일럿~중형 장비 기준. 양산 라인 건조 오븐은 수백 kW급이므로, Rule 2 threshold 설정 시 실제 공정 규모에 맞게 조정 필요.

---

### 2-3. 제외된 항목

| 항목 | 제외 이유 |
|------|-----------|
| 실험실용 진공 건조 오븐 (8L~430L) | 출처 URL 없음. "검색 결과 요약"으로만 기록된 수치로 원본 추적 불가. |

---

## Rule 4 — 생산량 대비 전력 이상 기준

> `usage / production > threshold` → 이상 판정 (`PRODUCTION_RATIO`)  
> 단위 생산당 전력(kWh/kWhprod) 기준으로 상한 설정.

### 4-1. 공장 전체 단위 생산당 전력 (우선 사용)

| 출처 | 기준 연도 | 수치 | 비고 |
|------|-----------|------|------|
| **MDPI Environments (2025)** — Samsung SDI Göd | 2023년 연간 에너지 보고서 | **28.3 kWh/kWhprod** | 본문 §3.2.1: 연간 보고서 기반 계산. 원문·보조자료: [MDPI 논문](https://www.mdpi.com/2076-3298/12/1/24) / [Supplementary (Excel)](https://www.mdpi.com/article/10.3390/environments12010024/s1) |
| **MDPI Environments (2025)** — SK Innovation Iváncsa | 2024년 가동 | **29.4 kWh/kWhprod** | 본문 §3.3.1: natural gas 기반 계산(전력 포함 시 증감 가능). 원문·보조자료: [MDPI 논문](https://www.mdpi.com/2076-3298/12/1/24) / [Supplementary (Excel)](https://www.mdpi.com/article/10.3390/environments12010024/s1) |
| **MDPI Environments (2025)** — CATL Debrecen | 2024년 환경허가 추정 | **34.6 kWh/kWhprod** | 본문 §3.1.1: 허가·추정치 포함(상한 참고용). 원문·보조자료: [MDPI 논문](https://www.mdpi.com/2076-3298/12/1/24) / [Supplementary (Excel)](https://www.mdpi.com/article/10.3390/environments12010024/s1) |
| **MDPI Environments (2025)** — 3공장 종합 구간 | 2024–2025 | **30–35 kWh/kWh** | threshold 설계 기준 구간. 원문: [MDPI 논문](https://www.mdpi.com/2076-3298/12/1/24) |
- **원문·보조자료(세부 출처)**  
- Samsung SDI (Göd): Uniform Environmental Permit (ref.17 in Supplementary) 및 연간 에너지 리포트(2023) — https://samsungsdi.hu/upload/eves_szakreferensi_riport_2023_hu.pdf  
- CATL (Debrecen): Uniform Environmental Permit / 허가 문서 (ref.16 in Supplementary). 상세 수치는 Supplementary `Battery factories impact.xlsx` 참조 — https://www.mdpi.com/article/10.3390/environments12010024/s1  
- SK ON / SK Innovation (Iváncsa): Uniform Environmental Permit (ref.19 in Supplementary). 상세 수치는 Supplementary 참조 — https://www.mdpi.com/article/10.3390/environments12010024/s1
- **논문(원문)**: "Energy Use and Environmental Impact of Three Lithium-Ion Battery Factories with a Total Annual Capacity of 100 GWh"  
- **논문 웹페이지(확인용)**: https://www.mdpi.com/2076-3298/12/1/24  
- **논문 PDF (직접 다운)**: https://www.mdpi.com/2076-3298/12/1/24/pdf  
- **Supplementary (엑셀 등 보조자료)**: https://www.mdpi.com/article/10.3390/environments12010024/s1  
- **데이터 성격/주의**: 본문은 "around 30–35 kWh per kWh"로 요약하며, 세 공장별 상세 수치와 표는 Supplementary 엑셀(`Battery factories impact.xlsx`)에 수록되어 있습니다. SK 값은 natural gas만 기반 계산된 항목이므로 전력 포함 여부 확인 권장, CATL 값은 일부 추정치입니다.

### 4-2. Rule 4 threshold 명시값 (코드 파싱 기준) — 어댑터 재활용 시 수정 필요

> 코드(`_load_rule4_from_readme_rated`)는 **`README_ESG_Rule_및_설비기준.md`** 에서 아래 `RULE4_THRESHOLD_KWH_PER_KWH` 값을 직접 읽어 사용한다.  
> 엑셀 자동 파싱 대신 이 값을 우선 적용해 오파싱을 방지한다.

```
RULE4_THRESHOLD_KWH_PER_KWH = 39.8
```

- **산출 근거**: MDPI 2025 실측 상한 **34.565 kWh/kWh** (CATL Debrecen, `Battery factories impact.xlsx` `Factories_sum` 시트 row 3) × **1.15** (안전 마진) = **39.75 → 39.8**
- **엑셀 오파싱 주의**: 동 엑셀에 CATL 용량 **40 GWh/year** 값이 있어, 코드가 25~50 범위 숫자를 무차별 스캔하면 40을 에너지 소비값으로 혼동해 `40 × 1.15 = 46.0`으로 잘못 설정됨. 이 명시값으로 덮어쓴다.
- **갱신 시**: 실제 공장 데이터가 쌓이면 이 값만 수정하면 됨.

**→ 적용값**: `rule4_usage_per_production_max = 39.8`

---

### ✅ 수정 완료 (2026-03-16)

> **이전 상태**: 더미 데이터는 `rule4_usage_per_production_max = 46.0` (오파싱값)으로 생성됨.  
> **현재 상태**: `profile_source.json`에 `39.8` 고정값 설정 완료. 다음 데이터 재생성 시 자동 적용.

**수정 내용**:
- `app/data/env_mapping/profile_source.json` 생성 → `rule4_usage_per_production_max = 39.8` 명시
- `DEFAULT_PROFILE` 기본값도 `39.8`로 수정 (`run_generate_measurements.py`)
- Rule 3 `contract_kwh_per_hour` 도 동시 수정: `10020 → 5500` (PDF 오파싱 수정)

**재학습 체크리스트**:
- [x] `profile_source.json` 수정 완료
- [ ] `run_generate_measurements.py` 재실행으로 더미 데이터 재생성
- [ ] 재생성된 데이터로 어댑터 재학습 (`run_esg_sft_training.py`)
- [ ] Rule 4 이상 탐지 정확도 39.8~46.0 구간 집중 검증

---

### 4-3. 제외된 항목

| 항목 | 제외 이유 |
|------|-----------|
| 공정별 에너지 비율 76% (코팅·건조·성형·건조실) | "LCA 연구"라고만 기재, 특정 논문·URL 없음. Rule 4 threshold 세분화 시 별도 출처 확인 필요. |
| GHG 약 10 kgCO2eq/kWh | Rule 4와 무관한 참고용 수치. |

---

## 추후 반영 예정

| 항목 | 내용 | URL |
|------|------|-----|
| **EU PBG BREF** (배터리 거대공장 BAT 문서) | 2025년 12월 기술작업반 시작. 초안 공개 후 설비 정격·공정별 기준 반영 가능. | https://eipie.eu/the-sevilla-process/brefs/production-of-batteries-in-giga-factories-pbg-bref/ |

---

## 확인 상태 범례

| 기호 | 의미 |
|------|------|
| ✅ | 2025-03 직접 접속 확인, 스펙 원문 대조 완료 |
| ⏳ | 미발행 — 공개 후 반영 예정 |