# 신입 샘플 생성·검증·적재·테스트

## 1. 300개 샘플 생성

`app` 디렉터리에서 실행:

```bash
cd C:\dev\RAG\app
python -m training.pipelines.resume_samples.run_generate_new_hire_samples
```

- 기본 300건 생성.
- **GPU 16GB (예: RTX 4060 Ti)**: `--batch 16 --delay 0.2` 권장 (호출 약 20회, 약 10~14분). OOM 나면 `--batch 12`로 낮추기.
- **GPU 8~12GB**: 기본값(batch 8) 유지 또는 `--batch 5`.
- 결과: `app/data/resume/samples/new_hire_samples_YYYYMMDD_HHMM.jsonl`

## 2. 검증 (dry-run)

JSONL 줄 수·필수 필드 검증만 하고 DB에는 넣지 않음:

```bash
python -m training.pipelines.resume_samples.run_import_new_hire_samples --file data/resume/samples/new_hire_samples_YYYYMMDD_HHMM.jsonl --dry-run
```

`--file` 생략 시 `data/resume/samples/` 에서 가장 최신 `new_hire_samples_*.jsonl` 사용.

## 3. DB 적재

검증 통과한 JSONL을 employees 테이블에 넣기:

```bash
python -m training.pipelines.resume_samples.run_import_new_hire_samples --file data/resume/samples/new_hire_samples_YYYYMMDD_HHMM.jsonl
```

- id가 이미 있으면 해당 건은 스킵 (재실행 시 중복 에러 방지).
- `--no-skip`: id 중복이면 에러로 종료.

## 4. UI에서 테스트

1. **백엔드 서버 실행**  
   - FastAPI 서버 기동 (예: `uvicorn fastapi_server:app` 등).

2. **프론트 실행**  
   - 대시보드/프론트엔드 기동.

3. **신입 관리 페이지**  
   - `/core/new-hires` 접속.
   - `employmentType === 'new_hire'` 인 직원만 **신입 목록**에 표시되는지 확인.
   - 300건 적재했다면 이 목록에서 수백 건이 보여야 함.

4. **기존 직원 페이지**  
   - `/core/employees` 에서는 신입이 제외된 목록(또는 전체)으로 동작하는지 확인.

5. **단건 상세**  
   - 신입 목록/기존 직원 목록에서 한 명 선택 시 상세(Success DNA, 이력서 등)가 올바르게 나오는지 확인.

## 5. API로 검증 (선택)

```bash
# 직원 목록 (Neon)
curl http://localhost:8000/api/employees

# 신입만 필터는 프론트에서 하므로, DB에 new_hire이 300건 있는지 목록 개수로 확인 가능
```

## 요약

| 단계 | 명령 | 비고 |
|------|------|------|
| 생성 | `run_generate_new_hire_samples` | 기본 300건, 15~25분 |
| 검증 | `run_import_new_hire_samples --dry-run` | 파일만 검사 |
| 적재 | `run_import_new_hire_samples` | DB insert |
| UI 테스트 | 브라우저 `/core/new-hires`, `/core/employees` | 신입/기존 분리 확인 |
