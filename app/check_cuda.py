"""
CUDA 상태 확인 스크립트
"""
import torch

print("=" * 60)
print("CUDA 상태 확인")
print("=" * 60)

print(f"\nPyTorch 버전: {torch.__version__}")
print(f"CUDA 사용 가능: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA 버전: {torch.version.cuda}")
    print(f"CUDA 디바이스: {torch.cuda.get_device_name(0)}")
    print(f"CUDA 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    print("\n[OK] GPU가 정상적으로 인식되고 있습니다!")
else:
    print("\n[ERROR] CUDA가 사용 불가능합니다!")
    print("다음 사항을 확인하세요:")
    print("1. NVIDIA GPU 드라이버가 설치되어 있는지 확인")
    print("2. CUDA 버전 PyTorch를 설치했는지 확인")
    print("3. nvidia-smi 명령어로 GPU 인식 확인")
    print("\nCUDA 버전 PyTorch 설치:")
    print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")

print("=" * 60)
