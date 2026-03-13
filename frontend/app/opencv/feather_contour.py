"""
깃털.png 같은 단일 오브젝트 PNG에서 윤곽선을 추출해 SVG path 문자열로 출력합니다.
OpenCV findContours 사용 — __init__.py의 Face/Lena는 bounding box 인식,
여기서는 윤곽(contour)으로 정확한 형태를 뽑아 FeatherPenSVG에 넣을 수 있게 합니다.

사용법 (frontend 폴더에서):
  python -m app.opencv.feather_contour
  python -m app.opencv.feather_contour -i app/opencv/깃털.png -o feather_out.svg
"""
import argparse
import os
import sys

import cv2
import numpy as np


def _project_to_viewbox(pts: np.ndarray, view_width: float = 100, view_height: float = 36) -> np.ndarray:
    """contour 좌표를 (x_min..x_max, y_min..y_max) → (0..view_width, 0..view_height) 로 선형 매핑."""
    if len(pts) == 0:
        return pts
    pts = np.array(pts, dtype=np.float64)
    x, y = pts[:, 0], pts[:, 1]
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()
    if x_max - x_min < 1e-6:
        x_max = x_min + 1
    if y_max - y_min < 1e-6:
        y_max = y_min + 1
    x_new = (x - x_min) / (x_max - x_min) * view_width
    y_new = (y - y_min) / (y_max - y_min) * view_height
    return np.column_stack([x_new, y_new])


def contour_to_svg_path(contour: np.ndarray, view_width: float = 100, view_height: float = 36) -> str:
    """단일 contour를 viewBox 크기로 정규화한 뒤 SVG d 경로 문자열로 변환."""
    pts = _project_to_viewbox(contour.reshape(-1, 2), view_width, view_height)
    if len(pts) < 2:
        return ""
    parts = [f"M {pts[0, 0]:.2f} {pts[0, 1]:.2f}"]
    for i in range(1, len(pts)):
        parts.append(f"L {pts[i, 0]:.2f} {pts[i, 1]:.2f}")
    parts.append("Z")
    return " ".join(parts)


def _imread_unicode(path: str) -> np.ndarray | None:
    """한글 등 비ASCII 경로에서도 이미지 로드 (Windows OpenCV imread 한계 우회)."""
    try:
        with open(path, "rb") as f:
            buf = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def find_main_contour(image_path: str) -> np.ndarray | None:
    """이미지에서 가장 큰 외곽선 하나 반환 (흰 배경 + 검은 선 가정)."""
    img = _imread_unicode(image_path)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def run(
    image_path: str,
    view_width: float = 100,
    view_height: float = 36,
    out_svg_path: str | None = None,
    epsilon_approx: float | None = None,
) -> str:
    """PNG에서 메인 contour → viewBox 정규화 SVG path. epsilon_approx로 단순화 가능."""
    contour = find_main_contour(image_path)
    if contour is None:
        return ""
    if epsilon_approx is not None and epsilon_approx > 0:
        contour = cv2.approxPolyDP(contour, epsilon_approx, closed=True)
    assert contour is not None
    path_d = contour_to_svg_path(contour, view_width, view_height)
    if out_svg_path:
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_width} {view_height}"><path fill="none" stroke="#333" stroke-width="1" d="{path_d}"/></svg>'
        with open(out_svg_path, "w", encoding="utf-8") as f:
            f.write(svg)
    return path_d


def main() -> None:
    parser = argparse.ArgumentParser(description="PNG 윤곽선 추출 → SVG path")
    parser.add_argument("--image", "-i", default=None, help="입력 PNG (기본: app/opencv/깃털.png)")
    parser.add_argument("--image2", action="store_true", help="app/opencv/깃털2.png 사용 (한글 경로 우회)")
    parser.add_argument("--view-width", type=float, default=100)
    parser.add_argument("--view-height", type=float, default=36)
    parser.add_argument("--svg", "-o", default=None, help="출력 SVG 파일")
    parser.add_argument("--epsilon", type=float, default=None, help="approxPolyDP epsilon")
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

    path_d = run(
        image_path,
        view_width=args.view_width,
        view_height=args.view_height,
        out_svg_path=args.svg,
        epsilon_approx=args.epsilon,
    )
    if not path_d:
        print("윤곽선을 찾지 못했습니다.", file=sys.stderr)
        sys.exit(1)
    print(path_d)
    if args.svg:
        print(f"SVG 저장: {args.svg}", file=sys.stderr)


if __name__ == "__main__":
    main()
