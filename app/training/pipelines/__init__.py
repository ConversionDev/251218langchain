"""
학습 공통 파이프라인

애매한 케이스 필터 등 학습 전처리.
"""
# eager import 제거 — ambiguous_case_filter가 core.llm.providers 등에 의존해
# ingest만 실행할 때 ModuleNotFoundError 방지
__all__ = ["filter_training_data", "filter_ambiguous_cases"]
