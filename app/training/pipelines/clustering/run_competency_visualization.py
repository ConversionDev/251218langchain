"""
Competency 클러스터링 결과 2D 시각화 (UMAP + Plotly).

클러스터링 결과(assignments, centroids)와 FAISS 인덱스를 읽어
클러스터별로 샘플을 뽑고, UMAP으로 2차원 축소 후 Plotly HTML로 저장.
무거우므로 필요할 때만 실행.

의존성: pip install umap-learn plotly

사용:
  cd app && python -m training.pipelines.clustering.run_competency_visualization
  cd app && python -m training.pipelines.clustering.run_competency_visualization --max-per-cluster 30 --output my_map.html
"""

import argparse
import pickle as pkl
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np  # type: ignore
from scipy.spatial import ConvexHull  # type: ignore

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_clustering_dir, get_faiss_dir  # type: ignore  # noqa: E402

# unique_id 출처 키 → 원본 파일명 (범례에 "원본 데이터" 명시용)
SOURCE_TO_FILENAME = {
    "대인관계능력_01_교수자용": "대인관계능력_01_교수자용.pdf",
    "문제해결능력_01_교수자용": "문제해결능력_01_교수자용.pdf",
    "의사소통능력_01_교수자용": "의사소통능력_01_교수자용.pdf",
    "자기개발능력_01_교수자용": "자기개발능력_01_교수자용.pdf",
    "Abilities": "Abilities.xlsx",
    "Task Statements": "Task Statements.xlsx",
    "Technology Skills": "Technology Skills.xlsx",
    "Work Styles": "Work Styles.xlsx",
}


def _source_from_unique_id(uid: str) -> str:
    """unique_id에서 출처 부분만 추출 (예: 대인관계능력_01_교수자용_ncs_0 → 대인관계능력_01_교수자용)."""
    for sep in ("_ncs_", "_onet_"):
        if sep in uid:
            return uid.split(sep)[0]
    return uid


def _cluster_display_name(cid: int, id_map: list, sampled_indices: list, sampled_cluster_ids: list) -> str:
    """군집 cid에 속한 샘플의 출처 과반수 → 원본 파일명으로 범례 표시 (Cluster N (file.xlsx))."""
    uids = [id_map[i] for j, i in enumerate(sampled_indices) if sampled_cluster_ids[j] == cid]
    if not uids:
        return f"Cluster {cid + 1}"
    sources = [_source_from_unique_id(uid) for uid in uids]
    most_common_key = Counter(sources).most_common(1)[0][0]
    filename = SOURCE_TO_FILENAME.get(most_common_key, most_common_key[:24] + "…" if len(most_common_key) > 24 else most_common_key)
    return f"Cluster {cid + 1} ({filename})"


def main() -> None:
    parser = argparse.ArgumentParser(description="클러스터링 2D 시각화 (UMAP + Plotly)")
    parser.add_argument(
        "--max-clusters",
        type=int,
        default=7,
        help="시각화에 사용할 최대 군집 수 (기본 7)",
    )
    parser.add_argument(
        "--max-per-cluster",
        type=int,
        default=10,
        help="군집당 최대 샘플 수 (기본 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="competency_map.html",
        help="출력 HTML 파일명 (기본 competency_map.html)",
    )
    parser.add_argument(
        "--no-hull",
        action="store_true",
        help="군집 볼록 껍질(영역 표시) 생략",
    )
    parser.add_argument(
        "--no-centroids",
        action="store_true",
        help="군집 중심점(별) 표시 생략",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="클러스터 내 샘플 랜덤 시드",
    )
    args = parser.parse_args()

    try:
        import faiss  # type: ignore
    except ImportError:
        print("[ERROR] faiss 필요: pip install faiss-cpu")
        sys.exit(1)
    try:
        import umap  # type: ignore
    except ImportError:
        print("[ERROR] umap-learn 필요: pip install umap-learn")
        sys.exit(1)
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        print("[ERROR] plotly 필요: pip install plotly")
        sys.exit(1)

    out_dir = get_clustering_dir()
    faiss_dir = get_faiss_dir()
    index_path = faiss_dir / "competency_anchors.index"
    assignments_path = out_dir / "competency_cluster_assignments.pkl"
    centroids_path = out_dir / "competency_centroids.npy"

    for p in (index_path, assignments_path, centroids_path):
        if not p.exists():
            print(f"[ERROR] 파일 없음: {p}")
            print("  먼저 run_competency_clustering.py 와 inspect 단계를 실행하세요.")
            sys.exit(1)

    print("[INFO] FAISS 인덱스 로드 중...")
    index = faiss.read_index(str(index_path))
    ntotal = index.ntotal

    print("[INFO] 클러스터링 결과 로드 중...")
    with assignments_path.open("rb") as f:
        data = pkl.load(f)
    assignments_list = data.get("assignments_list", [])
    id_map = data.get("id_map", [])
    if len(assignments_list) != ntotal or len(id_map) != ntotal:
        print(f"[WARNING] assignments/id_map 길이({len(assignments_list)},{len(id_map)}) != ntotal({ntotal})")

    centroids = np.load(centroids_path).astype(np.float32)
    n_clusters = centroids.shape[0]

    # 시각화할 군집 수 제한 (몇 개만 보이게)
    n_show = min(args.max_clusters, n_clusters)

    # 클러스터별로 인덱스 수집 후, 상위 n_show개 군집만 사용
    cluster_to_indices = defaultdict(list)
    for i in range(ntotal):
        cluster_to_indices[int(assignments_list[i])].append(i)

    random.seed(args.seed)
    sampled_indices = []
    sampled_cluster_ids = []
    for cid in range(n_show):
        indices = cluster_to_indices[cid]
        n_take = min(args.max_per_cluster, len(indices))
        if n_take > 0:
            chosen = random.sample(indices, n_take)
            sampled_indices.extend(chosen)
            sampled_cluster_ids.extend([cid] * n_take)

    print(f"[INFO] 시각화용 샘플: {len(sampled_indices)}점 (군집 {n_show}개, 군집당 최대 {args.max_per_cluster})")

    # 벡터 복원 (연속 구간이 아니므로 한 번에 전체 로드 후 인덱싱)
    print("[INFO] 벡터 복원 중...")
    all_vectors = index.reconstruct_n(0, ntotal)
    sampled_vectors = all_vectors[np.array(sampled_indices, dtype=np.int64)].astype(np.float32)
    del all_vectors

    # UMAP 2D — min_dist를 올려 클러스터가 덜 붙어 보이게
    print("[INFO] UMAP 차원 축소 중...")
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=12,
        min_dist=0.25,
        metric="cosine",
        random_state=args.seed,
    )
    embedding_2d = reducer.fit_transform(sampled_vectors)

    # 중심점 2D (기본 표시, --no-centroids 시 생략)
    centroid_2d = None
    if not args.no_centroids and n_show > 0:
        cen = np.ascontiguousarray(centroids[:n_show].astype(np.float32))
        if cen.ndim == 1:
            cen = cen.reshape(1, -1)
        faiss.normalize_L2(cen)
        centroid_2d = reducer.transform(cen)

    # 군집별 범례: 원본 데이터 파일명으로 표시 (Cluster N (file.xlsx/pdf))
    cluster_names = [
        _cluster_display_name(cid, id_map, sampled_indices, sampled_cluster_ids)
        for cid in range(n_show)
    ]

    # 군집별 색: 점은 진한 색, 영역(볼록껍질)은 파스텔로 구분 (사진처럼)
    CLUSTER_COLORS = [
        "#7C3AED", "#059669", "#EA580C", "#2563EB", "#CA8A04", "#DB2777",
        "#0891B2", "#4F46E5", "#0D9488", "#DC2626", "#65A30D", "#7C2D12",
        "#5B21B6", "#0F766E",
    ]
    CLUSTER_PASTEL = [
        "rgba(167, 139, 250, 0.35)",   # 보라 파스텔
        "rgba(52, 211, 153, 0.35)",     # 초록 파스텔
        "rgba(251, 146, 60, 0.35)",     # 주황 파스텔
        "rgba(96, 165, 250, 0.35)",     # 파랑 파스텔
        "rgba(253, 224, 71, 0.4)",      # 노랑 파스텔
        "rgba(244, 114, 182, 0.35)",    # 핑크 파스텔
        "rgba(34, 211, 238, 0.35)",     # 시안 파스텔
        "rgba(129, 140, 248, 0.35)",    # 인디고 파스텔
        "rgba(45, 212, 191, 0.35)",     # 틸 파스텔
        "rgba(248, 113, 113, 0.35)",    # 빨강 파스텔
        "rgba(163, 230, 53, 0.4)",      # 라임 파스텔
        "rgba(251, 191, 36, 0.4)",      # 앰버 파스텔
        "rgba(139, 92, 246, 0.35)",     # 바이올렛 파스텔
        "rgba(20, 184, 166, 0.35)",     # 틸 진한 파스텔
    ]
    colors = [CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i in range(n_show)]
    pastels = [CLUSTER_PASTEL[i % len(CLUSTER_PASTEL)] for i in range(n_show)]
    # 참고 형식: 군집마다 색 + 마커 모양 구분 (circle, square, triangle-up, diamond, ...)
    CLUSTER_SYMBOLS = [
        "circle", "square", "triangle-up", "diamond", "pentagon", "hexagon", "star",
    ]
    symbols = [CLUSTER_SYMBOLS[i % len(CLUSTER_SYMBOLS)] for i in range(n_show)]

    sampled_cids = np.array(sampled_cluster_ids)
    hover_texts = [
        f"역량 고유ID: {id_map[i]}<br>군집: {cluster_names[sampled_cluster_ids[j]]}"
        for j, i in enumerate(sampled_indices)
    ]

    fig = go.Figure()
    # 1) 볼록 껍질(군집 영역) — 파스텔 채우기 + 테두리로 구분 (사진처럼)
    if not args.no_hull:
        for cid in range(n_show):
            mask = sampled_cids == cid
            pts = embedding_2d[mask]
            if len(pts) >= 3:
                try:
                    hull = ConvexHull(pts)
                    vert_idx = np.append(hull.vertices, hull.vertices[0])
                    x_hull = pts[vert_idx, 0].tolist()
                    y_hull = pts[vert_idx, 1].tolist()
                    fig.add_trace(
                        go.Scatter(
                            x=x_hull,
                            y=y_hull,
                            mode="lines",
                            line=dict(color=colors[cid], width=2, dash="solid"),
                            fill="toself",
                            fillcolor=pastels[cid],
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )
                except Exception:
                    pass
    # 2) 군집별 데이터 점 — 참고 형식: 색 + 마커 모양(동그라미/네모/삼각형/다이아몬드 등) 구분
    for cid in range(n_show):
        mask = sampled_cids == cid
        x_c = embedding_2d[mask, 0]
        y_c = embedding_2d[mask, 1]
        texts_c = [t for j, t in enumerate(hover_texts) if sampled_cids[j] == cid]
        fig.add_trace(
            go.Scatter(
                x=x_c,
                y=y_c,
                mode="markers",
                marker=dict(
                    size=10,
                    symbol=symbols[cid],
                    color=colors[cid],
                    opacity=0.9,
                    line=dict(width=1.2, color="rgba(255,255,255,0.8)"),
                ),
                text=texts_c,
                hoverinfo="text",
                name=cluster_names[cid],
                showlegend=True,
            )
        )
    # 3) 중심점 — 작게 별로 표시 (기본 켜짐)
    if centroid_2d is not None:
        for cid in range(n_show):
            fig.add_trace(
                go.Scatter(
                    x=[centroid_2d[cid, 0]],
                    y=[centroid_2d[cid, 1]],
                    mode="markers",
                    marker=dict(
                        size=8,
                        symbol="star",
                        color=colors[cid],
                        opacity=1,
                        line=dict(width=1, color="rgba(0,0,0,0.5)"),
                    ),
                    text=[f"{cluster_names[cid]} 중심"],
                    hoverinfo="text",
                    name=f"{cluster_names[cid]} ★",
                    showlegend=False,
                )
            )
    # 차트: 한 화면에 들어가도록 높이 제한, 여백 축소
    fig.update_layout(
        title=None,
        xaxis_title="UMAP 축 1",
        yaxis_title="UMAP 축 2",
        template="plotly_white",
        height=560,
        showlegend=True,
        legend=dict(title="cluster (original data)", yanchor="top", y=0.99, xanchor="left", x=1.02),
        margin=dict(t=24, b=24, l=48, r=20),
    )

    out_path = out_dir / args.output
    fig.write_html(
        str(out_path),
        config=dict(responsive=True, displayModeBar=True),
    )
    print(f"[OK] 시각화 저장: {out_path}")
    print("  브라우저에서 열어 확인하세요.")


if __name__ == "__main__":
    main()
