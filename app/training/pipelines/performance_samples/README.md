# 성과 샘플: JSONL 정규화 → performance_records 적재

재생성(ExaOne 호출) 없이 **기존 JSONL만 수정** 후 통합 테이블에 넣습니다.

## 1. JSONL 목표 형식으로 수정

- `successDna` 제거 (AI가 나중에 텍스트 기반으로 채움)
- employeeId별 300명 고유 name·email 부여

```bash
cd app
python -m training.pipelines.performance_samples.normalize_performance_jsonl --file data/performance/samples/performance_samples_20260221_1141.jsonl --in-place
```

미지정 시 samples 폴더에서 최신 `performance_samples_*.jsonl` 사용. `--in-place` 없으면 `_normalized.jsonl` 로 저장.

## 2. DB 마이그레이션 (최초 1회)

```bash
cd app
alembic upgrade head
```

## 3. performance_records 테이블에 적재

```bash
cd app
python -m training.pipelines.performance_samples.run_import_performance_samples
```

`--file` 로 파일 지정 가능. `--no-skip` 이면 id 중복 시 에러.
