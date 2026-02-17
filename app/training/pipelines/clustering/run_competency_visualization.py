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
import json
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

# unique_id → 시각화용 짧은 출처 이름 (어떤 군집 데이터인지)
SOURCE_LABELS = {
    "대인관계능력_01_교수자용": "대인관계 역량",
    "문제해결능력_01_교수자용": "문제해결 역량",
    "의사소통능력_01_교수자용": "의사소통 역량",
    "자기개발능력_01_교수자용": "자기개발 역량",
    "Abilities": "O*NET Abilities",
    "Task Statements": "O*NET Task",
    "Technology Skills": "O*NET 기술",
    "Work Styles": "O*NET Work",
}


def _source_from_unique_id(uid: str) -> str:
    """unique_id에서 출처 부분만 추출 (예: 대인관계능력_01_교수자용_ncs_0 → 대인관계능력_01_교수자용)."""
    for sep in ("_ncs_", "_onet_"):
        if sep in uid:
            return uid.split(sep)[0]
    return uid


def _cluster_display_name(cid: int, id_map: list, sampled_indices: list, sampled_cluster_ids: list) -> str:
    """군집 cid에 속한 샘플의 출처 과반수로 표시 이름 생성."""
    uids = [id_map[i] for j, i in enumerate(sampled_indices) if sampled_cluster_ids[j] == cid]
    if not uids:
        return f"역량 군집 {cid + 1}"
    sources = [_source_from_unique_id(uid) for uid in uids]
    short = [SOURCE_LABELS.get(s, s[:20] + "…" if len(s) > 20 else s) for s in sources]
    most_common = Counter(short).most_common(1)[0][0]
    return f"역량 군집 {cid + 1} ({most_common})"


def main() -> None:
    parser = argparse.ArgumentParser(description="클러스터링 2D 시각화 (UMAP + Plotly)")
    parser.add_argument(
        "--max-clusters",
        type=int,
        default=14,
        help="시각화에 사용할 최대 군집 수 (기본 14, 빼곡한 느낌)",
    )
    parser.add_argument(
        "--max-per-cluster",
        type=int,
        default=20,
        help="군집당 최대 샘플 수 (기본 20, 보기 좋게)",
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
        help="중심점(X) 표시 생략",
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

    # UMAP 2D
    print("[INFO] UMAP 차원 축소 중...")
    reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, metric="cosine", random_state=args.seed)
    embedding_2d = reducer.fit_transform(sampled_vectors)

    # 중심점 2D (선택, 시각화한 군집만)
    centroid_2d = None
    if not args.no_centroids and n_show > 0:
        cen = np.ascontiguousarray(centroids[:n_show].astype(np.float32))
        if cen.ndim == 1:
            cen = cen.reshape(1, -1)
        faiss.normalize_L2(cen)
        centroid_2d = reducer.transform(cen)

    # 군집별 표시 이름: cluster_labels.json(주제 라벨) 우선, 없으면 출처 과반수
    cluster_names = [
        _cluster_display_name(cid, id_map, sampled_indices, sampled_cluster_ids)
        for cid in range(n_show)
    ]
    labels_path = out_dir / "cluster_labels.json"
    if labels_path.exists():
        try:
            with labels_path.open("r", encoding="utf-8") as f:
                labels_dict = json.load(f)
            for cid in range(n_show):
                if str(cid) in labels_dict and labels_dict[str(cid)].strip():
                    cluster_names[cid] = f"역량 군집 {cid + 1} ({labels_dict[str(cid)].strip()})"
        except Exception:
            pass

    # 군집별 색·모양 (눈에 띄게, 14개까지 순환)
    CLUSTER_COLORS = [
        "#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C",
        "#E91E63", "#00BCD4", "#795548", "#607D8B", "#CDDC39", "#FF5722",
        "#673AB7", "#009688",
    ]
    CLUSTER_SYMBOLS = [
        "circle", "square", "triangle-up", "diamond", "pentagon", "hexagon",
        "star", "cross", "triangle-down", "triangle-left", "triangle-right", "diamond-tall",
        "hourglass", "bowtie",
    ]
    colors = [CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i in range(n_show)]
    symbols = [CLUSTER_SYMBOLS[i % len(CLUSTER_SYMBOLS)] for i in range(n_show)]

    sampled_cids = np.array(sampled_cluster_ids)
    hover_texts = [
        f"역량 고유ID: {id_map[i]}<br>군집: {cluster_names[sampled_cluster_ids[j]]}"
        for j, i in enumerate(sampled_indices)
    ]

    fig = go.Figure()
    # 1) 볼록 껍질(군집 영역) 먼저 그리기
    if not args.no_hull:
        for cid in range(n_show):
            mask = sampled_cids == cid
            pts = embedding_2d[mask]
            if len(pts) >= 3:
                try:
                    hull = ConvexHull(pts)
                    # 껍질 꼭짓점을 순서대로 (닫힌 다각형)
                    vert_idx = np.append(hull.vertices, hull.vertices[0])
                    x_hull = pts[vert_idx, 0].tolist()
                    y_hull = pts[vert_idx, 1].tolist()
                    fig.add_trace(
                        go.Scatter(
                            x=x_hull,
                            y=y_hull,
                            mode="lines",
                            line=dict(color=colors[cid], width=1.5, dash="dot"),
                            fill="toself",
                            fillcolor=colors[cid],
                            opacity=0.15,
                            showlegend=False,
                            hoverinfo="skip",
                        )
                    )
                except Exception:
                    pass
    # 2) 군집별 점 (색+모양 구분)
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
                    size=12,
                    symbol=symbols[cid],
                    color=colors[cid],
                    opacity=0.85,
                    line=dict(width=1, color="white"),
                ),
                text=texts_c,
                hoverinfo="text",
                name=cluster_names[cid],
                showlegend=True,
            )
        )
    # 3) 중심점 (선택)
    if centroid_2d is not None:
        fig.add_trace(
            go.Scatter(
                x=centroid_2d[:, 0],
                y=centroid_2d[:, 1],
                mode="markers",
                marker=dict(size=14, symbol="x", color="black", line=dict(width=2)),
                text=[f"{cluster_names[i]} 중심" for i in range(n_show)],
                hoverinfo="text",
                name="역량 군집 중심",
            )
        )
    # 차트: 제목·주석 없이 시각화만 (설명은 페이지 상단에 배치)
    fig.update_layout(
        title=None,
        xaxis_title="UMAP 축 1",
        yaxis_title="UMAP 축 2",
        template="plotly_white",
        height=800,
        showlegend=True,
        legend=dict(title="역량 군집", yanchor="top", y=0.99, xanchor="left", x=1.02),
        margin=dict(t=40, b=40, l=60, r=20),
    )

    out_path = out_dir / args.output
    fig.write_html(str(out_path))
    print(f"[OK] 시각화 저장: {out_path}")
    print("  브라우저에서 열어 확인하세요.")


if __name__ == "__main__":
    main()
