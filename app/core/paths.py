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
    return Path(__file__).parent.parent


def get_artifacts_dir() -> Path:
    """Artifacts 디렉토리 경로 반환.

    Returns:
        app/artifacts/ 디렉토리 경로
    """
    return get_app_root() / "artifacts"


def get_fine_tuned_dir() -> Path:
    """Fine-tuning된 모델 디렉토리 경로 반환.

    학습된 모델은 이 경로 아래에서 관리합니다.

    Returns:
        app/artifacts/fine_tuned/ 디렉토리 경로
    """
    return get_artifacts_dir() / "fine_tuned"


def get_faiss_dir() -> Path:
    """FAISS 인덱스·id_map 저장 디렉토리. artifacts/faiss/."""
    d = get_artifacts_dir() / "faiss"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_clustering_dir() -> Path:
    """K-Means 클러스터링 결과 저장 디렉토리. artifacts/clustering/.
    cluster_assignments, centroids, 요약 등 저장."""
    d = get_artifacts_dir() / "clustering"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_data_dir() -> Path:
    """데이터 디렉토리 경로 반환.

    Returns:
        app/data/ 디렉토리 경로
    """
    return get_app_root() / "data"


def get_resume_data_dir() -> Path:
    """입사지원서/이력서 관련 데이터. templates, samples 등. app/data/resume/"""
    d = get_data_dir() / "resume"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_resume_templates_dir() -> Path:
    """입사지원서 템플릿 디렉터리. app/data/resume/templates/"""
    d = get_resume_data_dir() / "templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_resume_samples_dir() -> Path:
    """생성된 신입 샘플(JSONL 등) 저장. app/data/resume/samples/"""
    d = get_resume_data_dir() / "samples"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_performance_data_dir() -> Path:
    """성과 관련 데이터. 회의록/보고서/이메일 샘플 등. app/data/performance/"""
    d = get_data_dir() / "performance"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_performance_samples_dir() -> Path:
    """성과 샘플(JSONL) 저장. app/data/performance/samples/"""
    d = get_performance_data_dir() / "samples"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_env_mapping_data_dir() -> Path:
    """환경 데이터 매핑(다국어·배터리 물질) 입출력. app/data/env_mapping/"""
    d = get_data_dir() / "env_mapping"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_esg_dummy_dir() -> Path:
    """ESG 전력·손실량·폐기물 더미 데이터셋 출력. app/data/esg_dummy/"""
    d = get_data_dir() / "esg_dummy"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_spam_data_dir() -> Path:
    """스팸 SFT 데이터 (ExaOne 합성·실제 레이블). app/data/spam/"""
    d = get_data_dir() / "spam"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_spam_sft_dir() -> Path:
    """스팸 SFT JSONL 저장. app/data/spam/sft/"""
    d = get_spam_data_dir() / "sft"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_llama_adapters_dir() -> Path:
    """LLaMA 스팸 분류 LoRA 어댑터 저장 경로. exaone/competency_adapters와 같이 역할별 이름 사용.

    Returns:
        app/artifacts/fine_tuned/llama/spam_adapters/
    """
    return get_fine_tuned_dir() / "llama" / "spam_adapters"


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
