"""스팸 감지 모듈 import 및 기본 동작 테스트"""

import sys
import traceback

def test_imports():
    """필수 모듈 import 테스트"""
    print("=" * 60)
    print("스팸 감지 모듈 Import 테스트")
    print("=" * 60)

    errors = []

    # 1. 기본 패키지 확인
    print("\n[1/4] 기본 패키지 확인...")
    try:
        import torch
        print(f"  ✅ torch: {torch.__version__}")
        print(f"     CUDA available: {torch.cuda.is_available()}")
    except Exception as e:
        errors.append(f"torch: {e}")
        print(f"  ❌ torch: {e}")

    # 2. Transformers 확인
    print("\n[2/4] Transformers 확인...")
    try:
        import transformers
        print(f"  ✅ transformers: {transformers.__version__}")
        import tokenizers
        print(f"  ✅ tokenizers: {tokenizers.__version__}")
    except Exception as e:
        errors.append(f"transformers/tokenizers: {e}")
        print(f"  ❌ transformers/tokenizers: {e}")
        traceback.print_exc()

    # 3. Unsloth 확인
    print("\n[3/4] Unsloth 확인...")
    try:
        import unsloth
        print(f"  ✅ unsloth: {unsloth.__version__}")
        from unsloth import FastLanguageModel
        print(f"  ✅ FastLanguageModel import 성공")
    except Exception as e:
        errors.append(f"unsloth: {e}")
        print(f"  ❌ unsloth: {e}")
        traceback.print_exc()

    # 4. LLaMA Gate 확인
    print("\n[4/4] LLaMA Gate 확인...")
    try:
        from core.llm.providers.llama import LLaMAGate
        print(f"  ✅ LLaMAGate import 성공")

        # 실제 초기화는 하지 않음 (모델 다운로드 시간 소요)
        print(f"  ℹ️  모델 초기화는 실제 사용 시 수행됩니다")
    except Exception as e:
        errors.append(f"LLaMAGate: {e}")
        print(f"  ❌ LLaMAGate: {e}")
        traceback.print_exc()

    # 결과 요약
    print("\n" + "=" * 60)
    if errors:
        print("❌ 테스트 실패")
        print("\n오류 목록:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return False
    else:
        print("✅ 모든 import 테스트 통과!")
        print("\n스팸 감지 기능이 정상적으로 작동할 것으로 예상됩니다.")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
