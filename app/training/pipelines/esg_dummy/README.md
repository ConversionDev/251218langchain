# ESG 전력·손실량·폐기물 더미 데이터셋

엑사원 학습용 2년치 17~18만 건 데이터셋 생성.  
**최종 전략**: `docs/esg-exaone-learning-final-strategy.md`

## 입력

- `app/data/env_mapping/` — 전력 수요 CSV, 전기요금표, mdpI 엑셀·PDF 등
- `README_ESG_Rule_및_설비기준.md` — Rule 4 `RULE4_THRESHOLD_KWH_PER_KWH` 등 파싱
- `README_배터리_손실량_폐기물_통상참고치.md` §3.2 — 공정별 scrap/waste **비율 표**(빌드 시 파싱 → `profile.json` 절대 구간)
- `README_ESG_맥락_및_현황.md` — 폴더 맥락·파이프라인 입력 요약(파싱 대상 아님)
- `docs/esg-dummy-data-strategy.md` — 프로파일·전략 참고
- (선택) `app/data/esg_dummy/profile_source.json` — 계약·Rule 등 수동 보정 시 `build_profile`에서 병합

## 출력

- `app/data/esg_dummy/` — `measurements.csv`(정상 + **CONTRACT_EXCEED** 해당 행만), `validation_logs.csv`, `profile.json`; `--output-labeled` 시 `labeled_slots.csv`  
  (경로: `core.paths.get_esg_dummy_dir()`)
- **`measurements.csv` 컬럼**: `noticedate`, **`hour`**(1~24), `process`, `line`, `usage`, `production`, `equipment_ct`, `shift`, `scrap`, `waste` — 시계열·이동평균은 `hour` 기준으로 정렬해 사용. (이전에 생성한 파일에는 `hour`가 없을 수 있음 → 재생성 권장)

## 실행 순서

1. 프로파일·기준 정리 → profile.json 생성
2. 전력 수요 패턴 테이블 생성
3. `run_generate_measurements.py` — 정상 + 이상 생성

## 다변량 이상(멀티 타입) — 5종

라벨: `MULTIVARIATE_EFFICIENCY_DROP`, `MULTIVARIATE_IDLE_POWER`, `MULTIVARIATE_BASE_LOAD`, `MULTIVARIATE_SINGLE_EQUIPMENT_LOW`, `MULTIVARIATE_SCRAP_WASTE_DEVIATION`. **이상 슬롯** 중 기본 **약 35%**에서 균등 선택(나머지는 단일 Rule 1·2·4·5·6). **행은 `measurements.csv`에 넣지 않고** `validation_logs`·라벨 파일에만 기록.

`generate_multivariate_row_and_validation`에서 **Rule4·Rule5** 및 공정별 `production`/`usage` 밴드를 쓴다. 단일 Rule과 겹치지 않도록 `usage`는 **Rule4·Rule5 직전(마진 0.05)**으로 클립. `SCRAP_WASTE_DEVIATION`은 scrap/waste **프로파일 상한 대비** 약 **1.12~1.38 / 1.10~1.32배**(production 대비 물리 캡은 생략, 라벨 분리 우선).

## 실행 예

**반드시 `app` 디렉터리에서 실행** (프로젝트 루트에서 하면 `No module named 'training'` 발생):

```bash
cd C:\dev\RAG\app
python -m training.pipelines.esg_dummy.run_generate_measurements --dry-run
python -m training.pipelines.esg_dummy.run_generate_measurements --years 2
```
