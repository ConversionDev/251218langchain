"""ORM 모델 (SQLAlchemy). domain/models/bases 에서 이동 (Phase 1).

각 모델은 개별 모듈(`*_orm.py`)에서 직접 import 한다.
※ 이 __init__ 에서 모델을 일괄 import 하지 않는다 — 그러면 서브모듈 하나만 import 해도
   7개 전부가 Base.metadata 에 등록되어, alembic autogenerate 대상 집합이 바뀌기 때문.
   metadata 등록 대상은 alembic/env.py 의 명시적 import 가 결정한다.
"""
