"""
공통 모듈 패키지.

애플리케이션 전체에서 사용하는 공통 유틸리티, 설정, 경로 관리 등을 제공합니다.

모듈:
- paths: 경로 유틸리티
- config: 애플리케이션 설정 (Pydantic BaseSettings)
- database: 데이터베이스 연결 관리
- logging_config: 로깅 설정
"""

from core.paths import (  # type: ignore
    get_app_root,
    get_artifacts_dir,
    get_base_models_dir,
    get_data_dir,
    get_fine_tuned_dir,
    get_output_dir,
    get_project_root,
)
from core.config import get_settings, settings, Settings  # type: ignore

__all__ = [
    # paths
    "get_app_root",
    "get_artifacts_dir",
    "get_base_models_dir",
    "get_data_dir",
    "get_fine_tuned_dir",
    "get_output_dir",
    "get_project_root",
    # config
    "get_settings",
    "settings",
    "Settings",
]
