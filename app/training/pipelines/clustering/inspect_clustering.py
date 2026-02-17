import argparse
import json
import pickle as pkl
import sys
from pathlib import Path

import faiss  # type: ignore
import numpy as np  # type: ignore

app_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

from core.paths import get_clustering_dir, get_faiss_dir  # type: ignore  # noqa: E402
from training.shared.competency_extract import get_competency_prepared_dir  # type: ignore  # noqa: E402


def load_raw_data():
    """원본 텍스트 데이터를 unique_id를 키로 하는 딕셔너리로 로드"""
    prepared_dir = get_competency_prepared_dir()
    raw_data_path = prepared_dir / "competency_rows.jsonl"
    data_map = {}
    if raw_data_path.exists():
        with raw_data_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                data_map[row["unique_id"]] = row.get("content", "")
    return data_map

def main() -> None:
    parser = argparse.ArgumentParser(description="클러스터링 결과 확인 및 대표 샘플 추출")
    parser.add_argument("--export", type=str, default="assignments.jsonl", help="할당 결과 저장 경로")
    parser.add_argument("--top-n", type=int, default=5, help="클러스터별 대표 샘플 개수")
    args = parser.parse_args()

    out_dir = get_clustering_dir()
    summary_path = out_dir / "competency_cluster_summary.json"
    assignments_path = out_dir / "competency_cluster_assignments.pkl"
    centroids_path = out_dir / "competency_centroids.npy"
    index_path = get_faiss_dir() / "competency_anchors.index"

    if not summary_path.exists():
        print(f"[ERROR] 요약 파일 없음: {summary_path}")
        sys.exit(1)
    if not index_path.exists():
        print(f"[ERROR] FAISS 인덱스 없음: {index_path}")
        sys.exit(1)

    # 1) 기본 요약 출력
    with summary_path.open("r", encoding="utf-8") as f:
        summary = json.load(f)
    print(f"총 벡터 수: {summary['n_vectors']} | 클러스터 수: {summary['n_clusters']}")

    # 2) id_map 로드 (인덱스 번호 -> unique_id)
    with assignments_path.open("rb") as f:
        assign_data = pkl.load(f)
    id_map = assign_data.get("id_map", [])
    if len(id_map) != summary["n_vectors"]:
        print(f"[WARNING] id_map 길이({len(id_map)}) != n_vectors({summary['n_vectors']})")

    # 3) FAISS 인덱스 로드 및 대표 샘플 추출
    print(f"[INFO] FAISS 인덱스 로드 중: {index_path.name}")
    index = faiss.read_index(str(index_path))
    centroids = np.load(centroids_path).astype(np.float32)
    # IndexFlatIP 사용 시 centroid도 L2 정규화 후 검색
    if centroids.ndim == 1:
        centroids = centroids.reshape(1, -1)
    faiss.normalize_L2(centroids)

    print(f"[INFO] 클러스터별 대표 샘플 {args.top_n}개 추출 중...")
    _, neighbor_indices = index.search(centroids, args.top_n)

    raw_data = load_raw_data()
    print(f"[INFO] 원본 텍스트 로드: {len(raw_data)}건")

    # 4) 결과 저장 (제미나이 전송용 교과서): cluster_id별로 unique_id + content
    representative_path = out_dir / "cluster_representatives.jsonl"
    with representative_path.open("w", encoding="utf-8") as f:
        for cluster_id in range(neighbor_indices.shape[0]):
            samples = []
            for idx in neighbor_indices[cluster_id].tolist():
                if idx < 0 or idx >= len(id_map):
                    continue
                uid = id_map[idx]
                content = raw_data.get(uid, "")
                samples.append({"unique_id": uid, "content": content[:500] if len(content) > 500 else content})
            f.write(
                json.dumps({"cluster_id": cluster_id, "representative_samples": samples}, ensure_ascii=False) + "\n"
            )

    print(f"[OK] 제미나이용 샘플 저장 완료: {representative_path}")

    print("\n[TIP] 이제 이 샘플들을 Gemini API에 던져서 라벨링을 시작할 수 있습니다.")

if __name__ == "__main__":
    main()
