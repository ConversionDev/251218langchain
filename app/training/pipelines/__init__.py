"""
학습 공통 파이프라인

애매한 케이스 필터 등 학습 전처리.
"""

from .ambiguous_case_filter import filter_training_data, filter_ambiguous_cases

__all__ = ["filter_training_data", "filter_ambiguous_cases"]
