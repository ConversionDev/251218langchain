"""
패키지 import 테스트 스크립트

Mock 제거 후 정상적으로 작동하는지 확인합니다.
"""

import sys
from pathlib import Path

# app 디렉토리를 Python 경로에 추가
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

print("=" * 60)
print("패키지 Import 테스트")
print("=" * 60)

# 1. 기본 패키지 테스트
print("\n[1] 기본 패키지 테스트")
try:
    import torch
    print(f"  [OK] torch: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"     CUDA available: {cuda_available}")
    if cuda_available:
        print(f"     CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"     CUDA version: {torch.version.cuda}")
    else:
        print("     [WARN] CUDA가 사용 불가능합니다. GPU가 필요합니다.")
        print("     [WARN] PyTorch가 CPU 버전으로 인식되고 있습니다.")
        print("     [WARN] CUDA 버전 PyTorch를 설치해야 합니다:")
        print("            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
except ImportError as e:
    print(f"  [FAIL] torch: {e}")

try:
    import transformers
    print(f"  [OK] transformers: {transformers.__version__}")
except ImportError as e:
    print(f"  [FAIL] transformers: {e}")

try:
    import numpy
    print(f"  [OK] numpy: {numpy.__version__}")
except ImportError as e:
    print(f"  [FAIL] numpy: {e}")

# 2. XFormers/FlashAttention 테스트
print("\n[2] XFormers/FlashAttention 테스트")
try:
    import xformers
    print(f"  [OK] xformers: {xformers.__version__}")
except ImportError:
    print("  [WARN] xformers: 설치되지 않음 (Unsloth 자체 최적화 사용)")

try:
    import flash_attn
    print(f"  [OK] flash_attn: {flash_attn.__version__}")
except ImportError:
    print("  [WARN] flash_attn: 설치되지 않음 (Unsloth 자체 최적화 사용)")

# 3. ML 라이브러리 테스트
print("\n[3] ML 라이브러리 테스트")
try:
    import peft
    print(f"  [OK] peft: {peft.__version__}")
except ImportError as e:
    print(f"  [FAIL] peft: {e}")

try:
    import bitsandbytes
    print(f"  [OK] bitsandbytes: {bitsandbytes.__version__}")
except ImportError as e:
    print(f"  [FAIL] bitsandbytes: {e}")

try:
    # Unsloth는 GPU가 필요하므로 먼저 확인
    import torch
    if torch.cuda.is_available():
        import unsloth
        print(f"  [OK] unsloth: {unsloth.__version__}")
    else:
        print("  [SKIP] unsloth: GPU가 없어서 스킵 (CUDA 필요)")
except ImportError as e:
    print(f"  [FAIL] unsloth: {e}")
except NotImplementedError as e:
    print(f"  [FAIL] unsloth: {e}")
    print("     [INFO] GPU가 필요합니다. CUDA 버전 PyTorch를 설치하세요.")

try:
    import trl
    print(f"  [OK] trl: {trl.__version__}")
except ImportError as e:
    print(f"  [FAIL] trl: {e}")

# 4. LangChain 테스트
print("\n[4] LangChain 테스트")
try:
    import langchain
    print(f"  [OK] langchain: {langchain.__version__}")
except ImportError as e:
    print(f"  [FAIL] langchain: {e}")

try:
    from langchain_core.messages import HumanMessage
    print("  [OK] langchain_core.messages")
except ImportError as e:
    print(f"  [FAIL] langchain_core.messages: {e}")

# 5. FastAPI 테스트
print("\n[5] FastAPI 테스트")
try:
    import fastapi
    print(f"  [OK] fastapi: {fastapi.__version__}")
except ImportError as e:
    print(f"  [FAIL] fastapi: {e}")

# 6. LLaMA Gate 모듈 테스트 (Mock 제거 후)
print("\n[6] LLaMA Gate 모듈 테스트 (Mock 제거 후)")
try:
    # GPU 확인
    import torch
    if not torch.cuda.is_available():
        print("  [SKIP] LLaMAGate: GPU가 없어서 스킵 (CUDA 필요)")
    else:
        from core.llm.providers.llama.llama_gate import LLaMAGate
        print("  [OK] LLaMAGate import 성공")
        print("     (실제 모델 로드는 시간이 걸리므로 여기서는 import만 확인)")
except Exception as e:
    print(f"  [FAIL] LLaMAGate import 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)
