"""
Competency FAISS 인덱스 K-Means 클러스터링.

FAISS 인덱스에서 벡터를 읽어 K-Means로 100~500개 클러스터 생성 후
app/artifacts/clustering/ 에 결과 저장.

사용:
  cd app && python -m training.pipelines.clustering.run_competency_clustering
  # 클러스터 수 지정 (기본 200):
  cd app && python -m training.pipelines.clustering.run_competency_clustering --n-clusters 300
"""

import argparse
import json
import pickle as pkl
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np  # type: ignore

# app 루트를 경로에 추가
app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_clustering_dir, get_faiss_dir  # type: ignore
from domain.shared.embedding import BGE_M3_DENSE_DIM  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser(description="Competency FAISS K-Means 클러스터링")
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=200,
        help="클러스터 개수 (기본 200, 100~500 권장)",
    )
    parser.add_argument(
        "--niter",
        type=int,
        default=25,
        help="K-Means 반복 횟수",
    )
    parser.add_argument(
        "--nredo",
        type=int,
        default=2,
        help="K-Means 재시작 횟수 (가장 좋은 결과 선택)",
    )
    args = parser.parse_args()

    try:
        import faiss  # type: ignore
    except ImportError:
        print("[ERROR] faiss 설치 필요: pip install faiss-cpu (또는 faiss-gpu)")
        sys.exit(1)

    base = get_faiss_dir()
    idx_path = base / "competency_anchors.index"
    map_path = base / "competency_anchors_id_map.pkl"
    if not idx_path.exists() or not map_path.exists():
        print(f"[ERROR] FAISS 인덱스 없음: {idx_path} / {map_path}")
        print("  먼저 run_competency_ingest 로 적재하세요.")
        sys.exit(1)

    print("[INFO] FAISS 인덱스 로드 중...")
    t0 = time.perf_counter()
    index = faiss.read_index(str(idx_path))
    with map_path.open("rb") as f:
        id_map = pkl.load(f)
    ntotal = index.ntotal
    dim = index.d
    print(f"[INFO] 로드 완료: {ntotal}건, dim={dim}, 소요: {time.perf_counter() - t0:.1f}s")

    if ntotal == 0:
        print("[ERROR] 벡터가 없습니다.")
        sys.exit(1)
    if dim != BGE_M3_DENSE_DIM:
        print(f"[WARNING] dim={dim}, BGE_M3_DENSE_DIM={BGE_M3_DENSE_DIM}")

    # 벡터 전체 복원 (IndexFlatIP는 reconstruct_n 지원)
    print("[INFO] 벡터 복원 중...")
    t0 = time.perf_counter()
    vectors = index.reconstruct_n(0, ntotal)
    vectors = np.ascontiguousarray(vectors.astype(np.float32))
    print(f"[INFO] 복원 완료: shape={vectors.shape}, 소요: {time.perf_counter() - t0:.1f}s")

    n_clusters = min(args.n_clusters, ntotal)
    if n_clusters < 2:
        print("[ERROR] n_clusters >= 2 필요")
        sys.exit(1)

    print(f"[INFO] K-Means 학습 (n_clusters={n_clusters}, niter={args.niter}, nredo={args.nredo})...")
    t0 = time.perf_counter()
    kmeans = faiss.Kmeans(
        d=dim,
        k=n_clusters,
        niter=args.niter,
        nredo=args.nredo,
        gpu=False,
        seed=42,
    )
    kmeans.train(vectors)
    print(f"[INFO] K-Means 완료, 소요: {time.perf_counter() - t0:.1f}s")

    centroids = kmeans.centroids

    # 각 벡터를 가장 가까운 centroid에 할당 (L2 거리)
    print("[INFO] 클러스터 할당 중...")
    t0 = time.perf_counter()
    index_centroids = faiss.IndexFlatL2(dim)
    index_centroids.add(centroids)
    _, labels = index_centroids.search(vectors, 1)
    labels = labels.ravel()
    print(f"[INFO] 할당 완료, 소요: {time.perf_counter() - t0:.1f}s")

    # 저장
    out_dir = get_clustering_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) unique_id -> cluster_id 매핑
    assignments = [int(labels[i]) for i in range(ntotal)]
    uid_to_cid = {id_map[i]: assignments[i] for i in range(ntotal)}
    assignments_path = out_dir / "competency_cluster_assignments.pkl"
    with assignments_path.open("wb") as f:
        pkl.dump({"unique_id_to_cluster": uid_to_cid, "assignments_list": assignments, "id_map": id_map}, f)
    print(f"[OK] 할당 저장: {assignments_path}")

    # 2) centroids
    centroids_path = out_dir / "competency_centroids.npy"
    np.save(centroids_path, centroids)
    print(f"[OK] centroid 저장: {centroids_path}")

    # 3) cluster_summary.json
    cluster_to_uids = defaultdict(list)
    for i, uid in enumerate(id_map):
        cluster_to_uids[int(labels[i])].append(uid)
    clusters_summary = [
        {"id": cid, "size": len(cluster_to_uids[cid]), "sample_unique_ids": cluster_to_uids[cid][:10]}
        for cid in range(n_clusters)
    ]
    summary = {
        "n_vectors": ntotal,
        "n_clusters": n_clusters,
        "dim": dim,
        "clusters": clusters_summary,
    }
    summary_path = out_dir / "competency_cluster_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[OK] 요약 저장: {summary_path}")

    # 통계
    sizes = [len(cluster_to_uids[c]) for c in range(n_clusters)]
    print(f"[INFO] 클러스터 크기: min={min(sizes)}, max={max(sizes)}, mean={np.mean(sizes):.1f}")

    print("[OK] 클러스터링 완료.")


if __name__ == "__main__":
    main()
