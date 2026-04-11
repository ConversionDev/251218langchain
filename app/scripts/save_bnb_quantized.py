"""EXAONE bitsandbytes NF4 사전 양자화 저장 스크립트.

한 번 실행하면 NF4 양자화된 가중치(~4 GB)가 로컬에 저장됩니다.
이후 서버 시작 시 re-quantization(FP16 → NF4 변환) 없이 바로 로드하므로
7-shard 로딩 시간이 약 46 초 → 10~15 초로 단축됩니다.

사용법:
    cd C:\\dev\\RAG\\app
    python scripts/save_bnb_quantized.py

저장 경로 커스텀:
    set EXAONE_PREQUANTIZED_DIR=D:\\models\\exaone-bnb4
    python scripts/save_bnb_quantized.py

주의사항:
    - GPU(CUDA) 환경에서만 실행 가능합니다 (bitsandbytes 4-bit는 CPU 미지원).
    - 저장 중 약 10~20 GB의 추가 VRAM/RAM 사용이 발생할 수 있습니다.
    - 이미 저장된 경우 재실행하면 덮어쓰기 여부를 묻습니다.
"""

import os
import shutil
import sys
from pathlib import Path

# app/ 가 Python path에 없으면 추가 (스크립트 단독 실행 시)
_app_root = Path(__file__).parent.parent.resolve()
if str(_app_root) not in sys.path:
    sys.path.insert(0, str(_app_root))

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "true"

import torch  # noqa: E402


# ---------------------------------------------------------------------------
# 저장 경로 결정
# ---------------------------------------------------------------------------

def _resolve_save_dir() -> Path:
    """환경변수 EXAONE_PREQUANTIZED_DIR 또는 settings, 또는 기본 경로를 반환."""
    env_val = os.environ.get("EXAONE_PREQUANTIZED_DIR", "").strip()
    if env_val:
        return Path(env_val)

    # settings 에서 읽기 (있으면 우선)
    try:
        from core.config import settings  # type: ignore
        if settings.exaone_prequantized_dir:
            return Path(settings.exaone_prequantized_dir)
    except Exception:
        pass

    # 기본: artifacts/fine_tuned/exaone/prequantized_bnb4
    try:
        from core.paths import get_output_dir  # type: ignore
        return get_output_dir() / "exaone" / "prequantized_bnb4"
    except Exception:
        return _app_root / "artifacts" / "fine_tuned" / "exaone" / "prequantized_bnb4"


# ---------------------------------------------------------------------------
# HF 캐시에서 모델 코드 파일(.py) 복사
# ---------------------------------------------------------------------------

def _copy_model_code_files(model_id: str, revision: str, save_dir: Path) -> None:
    """HF 캐시 snapshot 에서 .py 파일을 save_dir 로 복사.

    trust_remote_code=True 모델은 커스텀 .py 파일이 필요합니다.
    save_dir 에서 from_pretrained 할 때 해당 파일을 참조합니다.
    """
    try:
        from huggingface_hub import snapshot_download  # type: ignore

        snapshot_dir = Path(
            snapshot_download(
                repo_id=model_id,
                revision=revision,
                local_files_only=True,
            )
        )
        py_files = list(snapshot_dir.glob("*.py"))
        if not py_files:
            print("[WARN] HF 캐시에서 .py 파일을 찾지 못했습니다. trust_remote_code 로드가 실패할 수 있습니다.")
            return
        for src in py_files:
            dst = save_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
        print(f"[OK] 모델 코드 파일 복사 완료: {[f.name for f in py_files]}")
    except Exception as e:
        print(f"[WARN] 모델 코드 파일 복사 실패 (무시 가능): {e}")


# ---------------------------------------------------------------------------
# 메인 로직
# ---------------------------------------------------------------------------

def main() -> None:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig  # type: ignore

    MODEL_ID = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"
    REVISION = "0ff6b5e"

    save_dir = _resolve_save_dir()
    marker = save_dir / "config.json"

    print("=" * 60)
    print("EXAONE bitsandbytes NF4 사전 양자화 저장")
    print(f"저장 경로: {save_dir}")
    print("=" * 60)

    if not torch.cuda.is_available():
        print("[ERROR] CUDA를 사용할 수 없습니다. GPU 환경에서 실행해 주세요.")
        sys.exit(1)

    if marker.exists():
        ans = input(f"\n[?] 이미 저장된 모델이 있습니다 ({save_dir}).\n    덮어쓰시겠습니까? [y/N] ").strip().lower()
        if ans != "y":
            print("[OK] 취소합니다.")
            return
        shutil.rmtree(save_dir)
        print(f"[INFO] 기존 디렉터리 삭제 완료: {save_dir}")

    save_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 4-bit 양자화 설정 ----------
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    print(f"\n[INFO] 모델 로드 중 (FP16 → NF4 변환 포함, 약 1~3분): {MODEL_ID}")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=REVISION,
        torch_dtype=torch.float16,
        device_map="cuda:0",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        attn_implementation="sdpa",
        use_safetensors=True,
        local_files_only=True,
        quantization_config=bnb_config,
    )

    print("[INFO] 토크나이저 로드 중...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        revision=REVISION,
        trust_remote_code=True,
        use_fast=True,
        local_files_only=True,
    )

    # ---------- NF4 양자화 가중치 저장 ----------
    print(f"[INFO] NF4 양자화 가중치 저장 중: {save_dir}")
    print("       (safetensors 포맷, 약 4 GB — 저장 시간 2~5분)")
    model.save_pretrained(save_dir, safe_serialization=True)
    tokenizer.save_pretrained(save_dir)

    # ---------- trust_remote_code 용 .py 파일 복사 ----------
    _copy_model_code_files(MODEL_ID, REVISION, save_dir)

    print(f"\n{'=' * 60}")
    print(f"[OK] 저장 완료: {save_dir}")
    print()
    print("다음 서버 시작부터 사전 양자화된 모델을 자동으로 로드합니다.")
    print("(재변환 없이 ~4 GB 읽기만 하므로 로딩이 훨씬 빠릅니다)")
    print()
    print("경로를 변경하고 싶다면 .env 에 다음을 추가하세요:")
    print(f"  EXAONE_PREQUANTIZED_DIR={save_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
