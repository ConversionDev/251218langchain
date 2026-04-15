"""
Unsloth 캐시 관리자

Unsloth 컴파일 캐시를 통합 관리합니다.

환경 변수 전략:
- UNSLOTH_CACHE_DIR: 프로젝트 주 환경 변수 (기본 캐시 루트)
  - Unsloth의 컴파일된 Trainer 파일들 저장
- HF_HOME, TRITON_CACHE_DIR: 설정하지 않음 (시스템 기본 경로 사용)

Best Practice:
- UNSLOTH_CACHE_DIR만 프로젝트 내에서 관리
- Hugging Face 모델/토크나이저 캐시는 시스템 기본 경로 사용
- Triton 커널 캐시는 시스템 기본 경로 사용 (한글 경로 문제 방지)
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from core.paths import get_app_root, get_unsloth_cache_dir  # type: ignore

# 환경 변수 이름 상수 (중앙 관리)
UNSLOTH_CACHE_DIR_ENV = "UNSLOTH_CACHE_DIR"


class UnslothCacheManager:
    """Unsloth 캐시 관리자.

    캐시 초기화, 환경 변수 설정, 마이그레이션, 관리 기능을 제공합니다.
    """

    # 싱글톤 인스턴스
    _instance: Optional["UnslothCacheManager"] = None
    _initialized = False

    def __new__(cls):
        """싱글톤 패턴으로 인스턴스 생성."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Unsloth 캐시 관리자 초기화."""
        if not self._initialized:
            self._cache_dir: Optional[Path] = None
            self._setup_cache()
            UnslothCacheManager._initialized = True

    def _migrate_existing_caches(self, target_dir: Path) -> None:
        """기존 분산된 캐시를 통합 위치로 마이그레이션 후 삭제.

        방법 1 적용 후에는 작업 디렉토리가 리소스 매니저로 변경되므로
        새로운 잘못된 위치 캐시는 생성되지 않지만, 기존 캐시 마이그레이션은 유지.

        Args:
            target_dir: 통합 캐시 디렉토리 경로
        """
        app_root = get_app_root()

        # 기존 분산 캐시 위치들
        legacy_cache_locations = [
            app_root / "unsloth_compiled_cache",
            app_root / "training" / "unsloth_compiled_cache",
        ]

        migrated = False
        migrated_dirs = []

        for legacy_cache_dir in legacy_cache_locations:
            if not legacy_cache_dir.exists():
                continue

            # 캐시 파일이 있는지 확인 (숨김 파일 제외)
            cache_files = list(legacy_cache_dir.rglob("*"))
            cache_files = [
                f for f in cache_files if f.is_file() and not f.name.startswith(".")
            ]

            if not cache_files:
                # 파일이 없어도 디렉토리가 존재하면 삭제
                if legacy_cache_dir != target_dir:
                    shutil.rmtree(legacy_cache_dir)
                continue

            # 통합 위치로 파일 복사
            for source_file in cache_files:
                relative_path = source_file.relative_to(legacy_cache_dir)
                target_file = target_dir / relative_path

                target_file.parent.mkdir(parents=True, exist_ok=True)

                if target_file.exists():
                    continue

                shutil.copy2(source_file, target_file)

            migrated = True
            migrated_dirs.append(legacy_cache_dir)

        # 마이그레이션된 디렉토리 삭제
        for migrated_dir in migrated_dirs:
            if migrated_dir != target_dir:
                shutil.rmtree(migrated_dir)

        if migrated:
            print("[INFO] 기존 캐시가 통합 위치로 마이그레이션되었습니다.")

    def _normalize_cache_path(self, cache_dir: Path) -> str:
        """캐시 경로를 절대 경로 문자열로 정규화 (Windows 경로 처리 강화).

        Args:
            cache_dir: 캐시 디렉토리 경로

        Returns:
            정규화된 절대 경로 문자열
        """
        # 절대 경로로 변환 (작업 디렉토리 변경에 영향받지 않도록)
        cache_dir_abs = cache_dir.resolve()

        # Windows 경로 구분자 정규화
        # 백슬래시를 슬래시로 변환하여 일관성 보장
        # Windows에서도 슬래시가 작동하므로 통일
        cache_dir_str = str(cache_dir_abs).replace("\\", "/")

        # 절대 경로인지 확인 (상대 경로가 아닌지 검증)
        if not os.path.isabs(cache_dir_str.replace("/", os.sep)):
            # 상대 경로인 경우 다시 절대 경로로 변환
            cache_dir_str = str(Path(cache_dir_str).resolve()).replace("\\", "/")

        return cache_dir_str

    def _set_cache_environment_variables(self, cache_dir: Path) -> None:
        """캐시 디렉토리를 환경 변수로 설정 (절대 경로 보장).

        UNSLOTH_CACHE_DIR만 설정하여 Unsloth 캐시를 통합 관리합니다.
        HF_HOME, TRITON_CACHE_DIR은 설정하지 않아 시스템 기본 경로를 사용합니다.

        Args:
            cache_dir: 캐시 디렉토리 경로
        """
        # 경로 정규화 (Windows 경로 처리 강화)
        cache_dir_str = self._normalize_cache_path(cache_dir)

        # 주 환경 변수 설정 (프로젝트 표준)
        os.environ[UNSLOTH_CACHE_DIR_ENV] = cache_dir_str

        # HF_HOME: 설정하지 않음 → Hugging Face가 시스템 기본 경로 사용
        # - 모델, 토크나이저, 데이터셋 캐시는 시스템 기본 경로에 저장
        # - 프로젝트 관리 범위 밖 (용량 관리 필요 시 별도 처리)

        # TRITON_CACHE_DIR: 설정하지 않음 → Triton이 시스템 기본 경로 사용
        # - Triton 커널 컴파일 캐시는 ~/.triton/cache에 저장
        # - 한글 경로 문제 방지 및 시스템 기본 경로 사용


    def ensure_cache_environment_variables(self) -> None:
        """환경 변수를 절대 경로로 재확인 및 강제 설정.

        방법 1 적용 후에는 작업 디렉토리가 리소스 매니저로 변경되므로
        환경 변수 재확인은 선택적입니다.
        """
        # 현재 설정된 캐시 경로 확인
        current_cache = os.environ.get(UNSLOTH_CACHE_DIR_ENV)

        if current_cache:
            cache_path = Path(current_cache)
            if not cache_path.is_absolute():
                cache_path = cache_path.resolve()
            self._set_cache_environment_variables(cache_path)
        else:
            default_cache_dir = get_unsloth_cache_dir()
            self._set_cache_environment_variables(default_cache_dir)

    def _setup_cache(self) -> None:
        """Unsloth 캐시 경로를 리소스 매니저로 설정 및 초기화."""
        # 1. UNSLOTH_CACHE_DIR 환경 변수 확인 (사용자 지정 경로)
        if UNSLOTH_CACHE_DIR_ENV in os.environ:
            user_cache_dir = Path(os.environ[UNSLOTH_CACHE_DIR_ENV]).resolve()
            user_cache_dir.mkdir(parents=True, exist_ok=True)

            # 환경 변수 설정 (절대 경로 보장)
            self._set_cache_environment_variables(user_cache_dir)
            self._cache_dir = user_cache_dir
            print(f"[INFO] Unsloth 캐시 경로 설정 (사용자 지정): {user_cache_dir}")
            return

        # 2. 통합 캐시 디렉토리 확인/생성
        unsloth_cache_dir = get_unsloth_cache_dir().resolve()
        unsloth_cache_dir.mkdir(parents=True, exist_ok=True)

        # 3. 기존 분산 캐시 마이그레이션 (초기 설정 시에만, 방법 1 적용 후에는 불필요하지만 호환성 유지)
        self._migrate_existing_caches(unsloth_cache_dir)

        # 4. 환경 변수 설정 (절대 경로 보장)
        self._set_cache_environment_variables(unsloth_cache_dir)

        self._cache_dir = unsloth_cache_dir
        print(f"[INFO] Unsloth 캐시 경로 설정: {unsloth_cache_dir}")

    @property
    def cache_dir(self) -> Path:
        """Unsloth 캐시 디렉토리 경로 반환.

        Returns:
            app/core/resource_manager/unsloth_compiled_cache/ 디렉토리 경로
        """
        if self._cache_dir is None:
            self._cache_dir = get_unsloth_cache_dir()
        return self._cache_dir


# 전역 인스턴스 (자동 초기화)
_global_manager: Optional[UnslothCacheManager] = None


def get_unsloth_cache_manager() -> UnslothCacheManager:
    """Unsloth 캐시 관리자 인스턴스를 반환 (싱글톤).

    Returns:
        UnslothCacheManager 인스턴스
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = UnslothCacheManager()
    return _global_manager


def setup_unsloth_cache() -> Path:
    """Unsloth 캐시 경로를 리소스 매니저로 설정 (호환성 함수).

    이 함수는 기존 코드와의 호환성을 위해 제공됩니다.
    내부적으로 UnslothCacheManager를 사용합니다.

    Returns:
        Unsloth 캐시 디렉토리 경로 (절대 경로)
    """
    manager = get_unsloth_cache_manager()
    return manager.cache_dir


def ensure_unsloth_cache_environment() -> None:
    """환경 변수를 절대 경로로 재확인 및 강제 설정.

    방법 1 적용 후에는 작업 디렉토리가 리소스 매니저로 변경되므로
    이 함수는 선택적으로 사용됩니다.

    사용 예시:
        setup_unsloth_cache()  # 초기 설정
        ensure_unsloth_cache_environment()  # 환경 변수 재확인 (선택적)
        import unsloth         # 언슬로스 import
    """
    manager = get_unsloth_cache_manager()
    manager.ensure_cache_environment_variables()


# 모듈 import 시 자동으로 캐시 경로 설정
_setup_done = False

if not _setup_done:
    get_unsloth_cache_manager()  # 자동 초기화
    _setup_done = True
