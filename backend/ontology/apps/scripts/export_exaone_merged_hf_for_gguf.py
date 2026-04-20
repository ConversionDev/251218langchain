"""EXAONE NF4 사전 양자화 + 역량 LoRA 병합 → HF 디렉터리 저장 (이후 GGUF 변환용).

로컬 GPU에서 1회 실행합니다. 출력은 float 가중치(병합 결과)이므로 디스크는 ~15GB 수준일 수 있습니다.
이 디렉터리를 llama.cpp 의 convert_hf_to_gguf.py 로 Q4_K_M 등으로 변환한 뒤,
단일 .gguf 파일만 EC2에 올리면 됩니다.

사용법:
    cd backend/ontology/apps
    python scripts/export_exaone_merged_hf_for_gguf.py

환경변수:
    EXAONE_MERGED_EXPORT_DIR — 출력 디렉터리 (기본: artifacts/fine_tuned/exaone/merged_hf_for_gguf)

다음 단계 (로컬에서 llama.cpp 클론 후):
    python convert_hf_to_gguf.py <EXPORT_DIR> --outfile exaone_competency_q4_k_m.gguf --outtype q4_k_m

EXAONE 아키텍처는 llama.cpp 최신 빌드에서 지원 여부를 확인하세요.
"""

import os
import shutil
import sys
from pathlib import Path

_app_root = Path(__file__).parent.parent.resolve()
if str(_app_root) not in sys.path:
    sys.path.insert(0, str(_app_root))

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TOKENIZERS_PARALLELISM"] = "true"

import torch  # noqa: E402


def _prequantized_dir() -> Path:
    env_val = os.environ.get("EXAONE_PREQUANTIZED_DIR", "").strip()
    if env_val:
        return Path(env_val)
    try:
        from core.paths import get_output_dir  # type: ignore

        return get_output_dir() / "exaone" / "prequantized_bnb4"
    except Exception:
        return _app_root / "artifacts" / "fine_tuned" / "exaone" / "prequantized_bnb4"


def _adapter_dir() -> Path:
    try:
        from core.paths import get_output_dir  # type: ignore

        return get_output_dir() / "exaone" / "competency_adapters"
    except Exception:
        return _app_root / "artifacts" / "fine_tuned" / "exaone" / "competency_adapters"


def _export_dir() -> Path:
    env_val = os.environ.get("EXAONE_MERGED_EXPORT_DIR", "").strip()
    if env_val:
        return Path(env_val)
    try:
        from core.paths import get_output_dir  # type: ignore

        return get_output_dir() / "exaone" / "merged_hf_for_gguf"
    except Exception:
        return _app_root / "artifacts" / "fine_tuned" / "exaone" / "merged_hf_for_gguf"


def main() -> None:
    from peft import PeftModel  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

    if not torch.cuda.is_available():
        print("[ERROR] CUDA 필요 (병합 시 VRAM ~14–20GB 권장).")
        sys.exit(1)

    base_dir = _prequantized_dir()
    adapter = _adapter_dir()
    out_dir = _export_dir()

    if not (base_dir / "config.json").exists():
        print(f"[ERROR] 사전 양자화 디렉터리 없음: {base_dir}")
        sys.exit(1)
    if not (adapter / "adapter_config.json").exists():
        print(f"[ERROR] 역량 어댑터 없음: {adapter}")
        sys.exit(1)

    print("=" * 60)
    print("EXAONE NF4 + competency_adapters → 병합 HF보내기 (GGUF 변환 전 단계)")
    print(f"  베이스: {base_dir}")
    print(f"  어댑터: {adapter}")
    print(f"  출력:  {out_dir}")
    print("=" * 60)

    if out_dir.exists():
        ans = input(f"\n[?] 출력 디렉터리가 이미 있습니다.\n    삭제 후 진행할까요? [y/N] ").strip().lower()
        if ans != "y":
            print("[OK] 취소합니다.")
            return
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n[INFO] 베이스(NF4) 로드 중…")
    model = AutoModelForCausalLM.from_pretrained(
        str(base_dir),
        trust_remote_code=True,
        device_map="cuda:0",
        low_cpu_mem_usage=True,
        local_files_only=True,
    )
    tok = AutoTokenizer.from_pretrained(
        str(base_dir),
        trust_remote_code=True,
        local_files_only=True,
    )

    print("[INFO] LoRA 결합 중…")
    model = PeftModel.from_pretrained(model, str(adapter))  # type: ignore[assignment]

    print("[INFO] merge_and_unload() — VRAM 사용량이 크게 늘 수 있습니다…")
    try:
        merged = model.merge_and_unload()  # type: ignore[operator]
    except Exception as e:
        print(f"[ERROR] merge_and_unload 실패: {e}")
        sys.exit(1)

    print("[INFO] bnb Linear4bit 레이어 dequantize → float16 (llama.cpp 변환 호환)…")
    import bitsandbytes as bnb
    from bitsandbytes.functional import dequantize_4bit

    replacements: dict = {}
    for full_name, module in merged.named_modules():
        if not isinstance(module, bnb.nn.Linear4bit):
            continue
        w = dequantize_4bit(
            module.weight.data,
            module.weight.quant_state,
            quant_type="nf4",
        ).to(torch.float16)
        new_lin = torch.nn.Linear(
            module.in_features,
            module.out_features,
            bias=module.bias is not None,
            dtype=torch.float16,
        )
        new_lin.weight = torch.nn.Parameter(w)
        if module.bias is not None:
            new_lin.bias = torch.nn.Parameter(module.bias.to(torch.float16))
        replacements[full_name] = new_lin

    for full_name, new_lin in replacements.items():
        parts = full_name.split(".")
        parent = merged
        for p in parts[:-1]:
            parent = getattr(parent, p)
        setattr(parent, parts[-1], new_lin)

    print(f"[INFO] dequantize 완료: {len(replacements)}개 레이어 변환")

    print(f"[INFO] 저장 중: {out_dir}")
    if hasattr(merged.config, "quantization_config"):
        del merged.config.quantization_config

    # torch.dtype 객체 → 문자열 변환 (JSON 직렬화 호환)
    for key, val in list(vars(merged.config).items()):
        if isinstance(val, torch.dtype):
            setattr(merged.config, key, str(val).replace("torch.", ""))

    merged.save_pretrained(str(out_dir), safe_serialization=True, max_shard_size="4GB")
    tok.save_pretrained(str(out_dir))

    print("\n" + "=" * 60)
    print("[OK] 병합 HF 저장 완료.")
    print("\n다음: llama.cpp 저장소에서 convert_hf_to_gguf.py 실행 예시:")
    print(
        f'  python convert_hf_to_gguf.py "{out_dir.resolve()}" '
        f"--outfile exaone_competency_q4_k_m.gguf --outtype q4_k_m"
    )
    print("\n생성된 .gguf 를 artifacts/fine_tuned/exaone/gguf/ 에 두고 EC2에 rsync 하세요.")
    print("=" * 60)


if __name__ == "__main__":
    main()
