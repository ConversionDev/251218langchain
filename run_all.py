"""
통합 개발 서버 실행 스크립트.

모든 서비스(게이트웨이, 백엔드, 프론트)를 한 번에 실행합니다.
사용: python run_all.py

각 서비스는 별도 프로세스에서 실행되며, Ctrl+C로 모두 종료합니다.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# 실행할 서비스들 (이름, 디렉터리, 명령어)
SERVICES = [
    ("Gateway (Spring Boot 8080)", PROJECT_ROOT / "backend" / "gateway", "gradlew.bat bootRun" if sys.platform == "win32" else "./gradlew bootRun"),
    ("Backend (FastAPI 8000)", PROJECT_ROOT / "backend" / "ontology" / "apps", f"{sys.executable} main.py"),
    ("Frontend (Next.js 3000)", PROJECT_ROOT / "frontend", "pnpm dev"),
]

processes = []


def run_service(name: str, cwd: Path, cmd: str) -> subprocess.Popen:
    """서비스를 별도 프로세스에서 실행."""
    print(f"\n🚀 {name} 시작 중...")
    print(f"   디렉터리: {cwd}")
    print(f"   명령어: {cmd}")

    try:
        if sys.platform == "win32":
            # Windows: cmd /k로 실행해서 창을 유지
            proc = subprocess.Popen(
                ["cmd.exe", "/k", cmd],
                cwd=str(cwd),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        else:
            # Linux/macOS
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

        processes.append((name, proc))
        print(f"✅ {name} 시작됨 (PID: {proc.pid})")
        return proc
    except Exception as e:
        print(f"❌ {name} 시작 실패: {e}")
        return None


def cleanup(sig=None, frame=None):
    """모든 프로세스 종료."""
    print("\n\n" + "=" * 60)
    print("🛑 모든 서비스 종료 중...")
    print("=" * 60)

    for name, proc in processes:
        if proc and proc.poll() is None:
            try:
                print(f"  ⏹️  {name} 종료 중...")
                proc.terminate()
                proc.wait(timeout=5)
                print(f"  ✅ {name} 종료됨")
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  {name} 강제 종료")
                proc.kill()
            except Exception as e:
                print(f"  ❌ {name} 종료 실패: {e}")

    print("\n✅ 모든 서비스 종료 완료")
    sys.exit(0)


def main():
    """메인 함수."""
    print("=" * 60)
    print("🚀 통합 개발 서버 실행")
    print("=" * 60)
    print("\n모든 서비스를 시작합니다:")
    for name, cwd, cmd in SERVICES:
        print(f"  • {name}")

    print("\n" + "=" * 60)
    print("Ctrl+C를 누르면 모든 서비스가 종료됩니다.")
    print("=" * 60)

    # 신호 핸들러 등록 (Ctrl+C)
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 모든 서비스 시작
    for name, cwd, cmd in SERVICES:
        if not cwd.exists():
            print(f"\n❌ 디렉터리 없음: {cwd}")
            continue

        run_service(name, cwd, cmd)
        time.sleep(2)  # 서비스 시작 간격

    if not processes:
        print("\n❌ 시작된 서비스가 없습니다.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ 모든 서비스 시작 완료!")
    print("=" * 60)
    print("\n📍 서비스 URL:")
    print("   • 프론트: http://localhost:3000")
    print("   • 게이트웨이: http://localhost:8080")
    print("   • 백엔드 API: http://localhost:8000")
    print("\n로그를 확인하려면 각 터미널 창을 참조하세요.")
    print("=" * 60)

    # 프로세스 모니터링
    while True:
        time.sleep(1)

        # 종료된 프로세스 확인
        for name, proc in processes:
            if proc and proc.poll() is not None:
                print(f"\n⚠️  {name} 프로세스가 종료되었습니다. (코드: {proc.returncode})")

        # 모든 프로세스가 종료되었는지 확인
        if all(proc.poll() is not None for _, proc in processes):
            print("\n⚠️  모든 프로세스가 종료되었습니다.")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        cleanup()
        sys.exit(1)
