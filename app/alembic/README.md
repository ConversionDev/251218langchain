# V10 Alembic 마이그레이션 가이드

V10 도메인의 데이터베이스 스키마 변경을 관리하는 Alembic 마이그레이션 시스템입니다.

## 초기 설정 (최초 1회)

### 1. Alembic 설치
```bash
pip install alembic
```

### 2. 초기 마이그레이션 생성
```bash
cd app
alembic revision --autogenerate -m "Initial migration for V10 domain"
```

## 일상적인 사용

### 모델 변경 후 마이그레이션 생성
```bash
cd app
alembic revision --autogenerate -m "설명 메시지"
```

예시:
```bash
alembic revision --autogenerate -m "Add email column to players table"
```

### 마이그레이션 적용
```bash
cd app
alembic upgrade head
```

### 현재 마이그레이션 버전 확인
```bash
cd app
alembic current
```

## 서버 시작 시 자동 마이그레이션

`python main.py` 실행 시 자동으로 최신 마이그레이션이 적용됩니다.

## 주요 명령어

- `alembic revision --autogenerate -m "메시지"`: 모델 변경사항 자동 감지하여 마이그레이션 생성
- `alembic upgrade head`: 모든 마이그레이션을 최신 버전으로 적용
- `alembic downgrade -1`: 마지막 마이그레이션 1개 롤백
- `alembic history`: 마이그레이션 히스토리 확인
- `alembic current`: 현재 적용된 마이그레이션 버전 확인

## 주의사항

1. **프로덕션 환경**: 마이그레이션 파일을 항상 검토한 후 적용하세요.
2. **데이터 백업**: 중요한 변경 전에는 데이터를 백업하세요.
3. **FK 관계**: FK가 있는 테이블의 경우 순서에 주의하세요 (Alembic이 자동 처리).
