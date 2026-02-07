# Alembic 마이그레이션 (통합 관리)

Soccer 도메인 + 임베딩 테이블을 **단일 스쿼시 마이그레이션**으로 관리합니다.

## 현재 구조

- **`versions/001_initial_squashed.py`**: 통합 초기 마이그레이션 (revision: `001_initial`)
  - pgvector 확장, stadiums, teams, players, schedules, player/team/schedule/stadium_embeddings (vector 1024)

## 사용법

### 새 환경 / 테이블 전부 제거한 DB

```bash
cd app
alembic upgrade head
```

한 번에 전체 스키마가 적용됩니다.

### 이미 테이블이 있는 DB (수동으로 스키마 맞춘 경우)

```bash
alembic stamp 001_initial
```

적용 없이 현재 리비전만 `001_initial`로 표시합니다.

### 스키마 변경 시 (앞으로 추가 마이그레이션)

```bash
cd app
alembic revision --autogenerate -m "설명 메시지"
alembic upgrade head
```

- 서버 기동 시에는 **upgrade만** 실행되며, 새 마이그레이션 파일은 생성하지 않습니다.
- 변경이 있을 때만 위처럼 수동으로 `revision --autogenerate` 후 적용하세요.

## 주요 명령어

- `alembic upgrade head`: 최신까지 적용
- `alembic current`: 현재 적용된 리비전 확인
- `alembic history`: 마이그레이션 목록
- `alembic revision --autogenerate -m "메시지"`: 모델 차이로 새 마이그레이션 생성
- `alembic downgrade -1`: 마지막 1개 롤백

## 참고

- **기존 DB**에서 `alembic_version`에 이전 리비전이 남아 있으면, 통합 전환 시 `alembic stamp 001_initial`로 맞춘 뒤 필요 시 스키마를 수동 정리하세요.
- 프로덕션 적용 전에는 마이그레이션 파일을 검토하고, 필요 시 백업 후 적용하세요.
