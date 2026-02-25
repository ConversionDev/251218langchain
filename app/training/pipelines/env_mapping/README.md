# 환경 데이터 매핑 파이프라인 (다국어·배터리)

전략: 베이스 환경 데이터 + 배터리 물질 → ExaOne 12개 언어 물질명·동의어 → PubChem/KECI/ECHA 보강 → Excel.

## 디렉터리
- `app/data/env_mapping/`: battery_substances.csv, 원본 Excel, mapping_*.xlsx, 출력

## 실행 (app 디렉터리에서)

### 0) 한 번에 실행

#### 0-1) 기존 데이터만으로 빠르게 재생성 (권장: 이미 매핑 파일이 있을 때)
원본 + **이미 있는** 매핑 Excel만 사용해 CAS·MSDS 기준명을 채우고, **EC 번호가 비어 있으면 PubChem API로 조회해 채웁니다.** (동의어용 PubChem/KECI/ECHA 호출은 생략)

```bash
# app 디렉터리에서 실행. 매핑 파일 미지정 시 data/env_mapping/ 내 최신 mapping_*.xlsx 자동 사용
python -m training.pipelines.env_mapping.rebuild_from_existing
```
또는 `run_full_strategy`에 플래그만 추가:
```bash
python -m training.pipelines.env_mapping.run_full_strategy --use-existing-mapping
```
- 옵션: `--original`, `--mapping`, `--output`, `--battery-csv`, `--no-ec-api` (EC 번호 API 생략 시)

#### 0-2) 전략 전체 (원본 CAS 추출 → ExaOne 매핑 → 보강)
```bash
# app 디렉터리에서 실행. 인자 없으면 기본 경로 사용 (원본·출력 모두 data/env_mapping/ 기준)
python -m training.pipelines.env_mapping.run_full_strategy
```
경로 지정 시:
```bash
python -m training.pipelines.env_mapping.run_full_strategy --original "data/env_mapping/환경 데이터 매핑 테이블.xlsx" --output data/env_mapping/환경데이터_매핑_보강.xlsx
```
- **1단계**: 원본에서 유니크 CAS 추출 → `base_for_mapping.csv`
- **2단계**: `run_mapping` (73개+배터리, ExaOne 12개 언어) → `mapping_full_YYYYMMDD_HHMM.xlsx` (30분~1시간 소요 가능)
- **3단계**: `vocabulary_builder` (.env 로드 → PubChem·KECI 포함) → 보강 Excel 저장
- 옵션: `--no-pubchem`, `--no-keci`, `--use-existing-mapping`, `--stage 1|2|3`, `--delay 0.5`, `--pubchem-delay 0.2`, `--keci-service-key`

### 1) 매핑 Excel 생성 (ExaOne 12개 언어)
```bash
# 배터리 CSV만 사용
python -m training.pipelines.env_mapping.run_mapping

# 원본 73개 CAS 포함하려면: 먼저 원본에서 CAS 추출
python -m training.pipelines.env_mapping.export_original_cas_for_mapping --original "data/env_mapping/환경 데이터 매핑 테이블.xlsx" --output data/env_mapping/base_for_mapping.csv
python -m training.pipelines.env_mapping.run_mapping --input data/env_mapping/base_for_mapping.csv --output data/env_mapping/mapping_YYYYMMDD_HHMM.xlsx
```

### 2) 전체 보강 (원본 + 12개 언어 + EC 번호 API + PubChem + KECI + ECHA)
```bash
python -m training.pipelines.env_mapping.vocabulary_builder --original "data/env_mapping/환경 데이터 매핑 테이블.xlsx" --mapping data/env_mapping/mapping_20260223_2138.xlsx --output data/env_mapping/환경데이터_매핑_보강.xlsx
```
- **EC 번호**: 원본/매핑에 없으면 CAS 기준으로 PubChem API에서 조회해 채움. `--no-ec-api`로 생략 가능.
- KECI: 프로젝트 루트 `.env`에 `KECI_SERVICE_KEY=발급받은키` 넣으면 자동 로드. 또는 `--keci-service-key` 로 전달. (공공데이터포털 → 화학물질안전관리정보 API 활용신청 후 일반 인증키 발급)
- ECHA: 공개 API 없음. `ECHA_API_URL` 설정 시에만 동작. 없으면 `--no-echa` 또는 그냥 스킵
- 옵션: `--no-ec-api`, `--no-pubchem`, `--no-keci`, `--no-echa`, `--pubchem-delay 0.2`

### 3) 넓은 형식 통합 (원본 행 수 유지, 12개 언어 컬럼만 추가)
```bash
python -m training.pipelines.env_mapping.merge_with_original --original "..." --mapping "..." --output "..."
```

## 언어 단계
| stage | 언어 |
|-------|------|
| 1 | 영·한·중·일 |
| 2 | 1 + 독·프·스·포 |
| 3 | 2 + 베트남·태국·인도네시아·아랍 |

전략 상세: `app/data/env_mapping/전략_환경데이터_매핑_보강.md`
