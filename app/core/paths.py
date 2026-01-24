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


def get_model_dir() -> Path:
    """모델 디렉토리 경로 반환.

    Returns:
        app/artifacts/base_models/ 디렉토리 경로
    """
    return get_base_models_dir()


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


def get_llama_model_dir() -> Path:
    """LLaMA 모델 디렉토리 경로 반환.

    Returns:
        app/artifacts/base_models/llama/ 디렉토리 경로
    """
    return get_base_models_dir() / "llama"


def get_exaone_model_dir() -> Path:
    """EXAONE 모델 디렉토리 경로 반환.

    Returns:
        app/artifacts/base_models/exaone/ 디렉토리 경로
    """
    return get_base_models_dir() / "exaone"


def get_fine_tuned_llama_dir() -> Path:
    """Fine-tuned LLaMA 디렉토리 경로 반환.

    Returns:
        app/artifacts/fine_tuned/llama/ 디렉토리 경로
    """
    return get_fine_tuned_dir() / "llama"


def get_fine_tuned_exaone_dir() -> Path:
    """Fine-tuned EXAONE 디렉토리 경로 반환.

    Returns:
        app/artifacts/fine_tuned/exaone/ 디렉토리 경로
    """
    return get_fine_tuned_dir() / "exaone"
