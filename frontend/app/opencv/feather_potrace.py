"""
PNG → 비트맵 → Potrace → SVG 파이프라인.

1. PNG 로드 (한글 경로 지원)
2. 그레이스케일 후 역치로 1비트 비트맵 (검정=깃털, 흰색=배경; 워터마크는 역치로 제거)
3. 임시 BMP 저장 (Potrace 입력 형식)
4. potrace 호출 → SVG 출력

사용 전에 Potrace 설치 필요:
  - Windows: Chocolatey에 패키지 없음. https://potrace.sourceforge.net/ 에서
    potrace-1.16.win64.zip (또는 win32) 다운로드 → 압축 해제 후 potrace.exe 를
    PATH 폴더에 두거나, 실행 시 --potrace-exe "C:\\path\\to\\potrace.exe" 로 지정.
  - macOS: brew install potrace

사용법 (frontend 폴더에서):
  python -m app.opencv.feather_potrace
  python -m app.opencv.feather_potrace --image2 -o app/opencv/feather_potrace.svg
"""
import argparse
import os
import subprocess
import sys

import cv2
import numpy as np


def _imread_unicode(path: str) -> np.ndarray | None:
    """한글 경로 PNG 로드."""
    try:
        with open(path, "rb") as f:
            buf = np.frombuffer(f.read(), dtype=np.uint8)
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)
    except Exception:
        return None


def png_to_bitmap(image_path: str, threshold: int = 200) -> np.ndarray | None:
    """
    PNG를 1비트 비트맵으로 변환.
    Potrace 규약: 검정(0)=추적 대상(깃털), 흰색(255)=배경.
    threshold 미만 픽셀 → 검정(깃털), 이상 → 흰색(워터마크·배경 제거).
    """
    img = _imread_unicode(image_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # BMP: 검정(0)=전경(깃털), 흰색(255)=배경 (Potrace 규약)
    _, bitmap = cv2.threshold(gray, threshold - 1, 255, cv2.THRESH_BINARY)
    return bitmap


def run_potrace(
    bitmap_path: str,
    output_svg_path: str,
    potrace_exe: str = "potrace",
    turnpolicy: str = "black",
) -> bool:
    """potrace 실행. bitmap_path는 ASCII 경로(임시 파일)."""
    cmd = [
        potrace_exe,
        bitmap_path,
        "-s",  # SVG 출력
        "-o", output_svg_path,
        f"--turnpolicy={turnpolicy}",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except FileNotFoundError:
        print("potrace를 찾을 수 없습니다. Windows는 수동 설치 후 --potrace-exe 로 경로 지정.", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"potrace 실패: {e.stderr}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="PNG → bitmap → Potrace → SVG")
    parser.add_argument("--image", "-i", default=None, help="입력 PNG")
    parser.add_argument("--image2", action="store_true", help="app/opencv/깃털2.png 사용")
    parser.add_argument("--svg", "-o", default=None, help="출력 SVG 경로")
    parser.add_argument("--threshold", "-t", type=int, default=200, help="이진화 역치 (기본 200, 워터마크 제거)")
    parser.add_argument("--keep-bmp", action="store_true", help="임시 BMP 파일 삭제하지 않음")
    parser.add_argument("--potrace-exe", default=None, help="potrace 실행 파일 경로 (Windows 수동 설치 시 예: C:\\tools\\potrace.exe)")
    args = parser.parse_args()

    opencv_dir = os.path.dirname(os.path.abspath(__file__))
    if args.image2:
        default_image = os.path.join(opencv_dir, "깃털2.png")
    else:
        default_image = os.path.join(opencv_dir, "깃털.png")
    image_path = os.path.abspath(args.image or default_image)

    if not os.path.isfile(image_path):
        print(f"이미지를 찾을 수 없습니다: {image_path}", file=sys.stderr)
        sys.exit(1)

    bitmap = png_to_bitmap(image_path, threshold=args.threshold)
    if bitmap is None:
        print("이미지 로드 실패.", file=sys.stderr)
        sys.exit(1)

    # Potrace는 한글 경로를 못 읽을 수 있으므로 ASCII 임시 파일 사용
    temp_bmp = os.path.join(opencv_dir, "temp_potrace_input.bmp")
    if not cv2.imwrite(temp_bmp, bitmap):
        print("비트맵 저장 실패.", file=sys.stderr)
        sys.exit(1)

    out_svg = args.svg or os.path.join(opencv_dir, "feather_potrace.svg")
    potrace_exe = args.potrace_exe or "potrace"
    try:
        if not run_potrace(temp_bmp, out_svg, potrace_exe=potrace_exe):
            sys.exit(1)
        print(f"SVG 저장: {out_svg}")
    finally:
        if not args.keep_bmp and os.path.isfile(temp_bmp):
            try:
                os.remove(temp_bmp)
            except OSError:
                pass


if __name__ == "__main__":
    main()
