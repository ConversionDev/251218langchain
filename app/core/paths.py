"""
경로 유틸리티 모듈.

애플리케이션 전체에서 사용하는 경로 관련 유틸리티를 제공합니다.
"""

from pathlib import Path


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 경로 반환.

    Returns:
        프로젝트 루트 디렉토리 경로 (RAG/)
    """
    # paths.py -> core/ -> app/ -> RAG/
    return Path(__file__).parent.parent.parent


def get_app_root() -> Path:
    """App 루트 디렉토리 경로 반환.

    Returns:
        app/ 디렉토리 경로
    """
    # common/paths.py -> common/ -> app/
    return Path(__file__).parent.parent


def get_artifacts_dir() -> Path:
    """Artifacts 디렉토리 경로 반환.

    Returns:
        app/artifacts/ 디렉토리 경로
    """
    return get_app_root() / "artifacts"


def get_base_models_dir() -> Path:
    """Base 모델 디렉토리 경로 반환.

    Returns:
        app/artifacts/base_models/ 디렉토리 경로
    """
    return get_artifacts_dir() / "base_models"


def get_fine_tuned_dir() -> Path:
    """Fine-tuning된 모델 디렉토리 경로 반환.

    Returns:
        app/artifacts/fine_tuned/ 디렉토리 경로
    """
    return get_artifacts_dir() / "fine_tuned"


def get_data_dir() -> Path:
    """데이터 디렉토리 경로 반환.

    Returns:
        app/data/ 디렉토리 경로
    """
    return get_app_root() / "data"


def get_output_dir() -> Path:
    """출력 디렉토리 경로 반환.

    Returns:
        app/artifacts/fine_tuned/ 디렉토리 경로
    """
    return get_fine_tuned_dir()


def get_resource_manager_dir() -> Path:
    """Resource Manager 디렉토리 경로 반환.

    Returns:
        app/core/resource_manager/ 디렉토리 경로
    """
    return get_app_root() / "core" / "resource_manager"


def get_unsloth_cache_dir() -> Path:
    """Unsloth 컴파일 캐시 디렉토리 경로 반환.

    Returns:
        app/core/resource_manager/unsloth_compiled_cache/ 디렉토리 경로
    """
    cache_dir = get_resource_manager_dir() / "unsloth_compiled_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
