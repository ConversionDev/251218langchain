"""
v10 soccer 임베딩 코드 생성 스크립트 (BP: Alembic 최대 활용 + 엑사원 자동화)

[목적 · BP]
- 테이블 생성: Alembic이 전담. alembic upgrade head 로 일반·임베딩 테이블 모두 생성.
- 본 스크립트: ExaOne이 *_embeddings.py (to_embedding_text) 코드만 생성 → domain/v10/soccer/models/bases/

실행: app 디렉터리에서
  python scripts/generate_v10_embedding_modules.py
"""
import sys
from pathlib import Path

# 스크립트 파일 기준 app 루트 (app/scripts/xxx.py → app)
_APP_ROOT = Path(__file__).resolve().parent.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from domain.v10.soccer.spokes.services.embedding_generator_service import (  # type: ignore  # noqa: E402
    generate_and_write_embedding_module,
)

ENTITY_TYPES = ["player", "team", "schedule", "stadium"]


def main() -> None:
    print("=" * 60)
    print("v10 soccer 임베딩 코드 생성 (ExaOne)")
    print("=" * 60)
    print("\n[*] *_embeddings.py (to_embedding_text) 생성 중...")

    for entity_type in ENTITY_TYPES:
        print(f"  [{entity_type}] 생성 중...", end=" ")
        result = generate_and_write_embedding_module(entity_type)
        if result["success"]:
            print(f"OK: {result['path']}")
        else:
            print(f"실패: {result.get('error', 'Unknown')}")

    print("\n완료.")


if __name__ == "__main__":
    main()
