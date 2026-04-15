import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
SAMPLE_PATH = ROOT / "chat_eval_sample.jsonl"
RESULT_PATH = ROOT / "chat_eval_result.json"
API_BASE = "http://127.0.0.1:8000"
CHAT_STREAM_URL = f"{API_BASE}/api/agent/chat/stream"
HEALTH_URL = f"{API_BASE}/api/agent/health"


def _load_samples(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        rows.append(json.loads(raw))
    return rows


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 120) -> str:
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _get_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    req = Request(url, method="GET")
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def _parse_sse(stream_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    answer_parts: List[str] = []
    latest_sources: List[Dict[str, Any]] = []

    for line in stream_text.splitlines():
        if not line.startswith("data: "):
            continue
        payload = line[6:].strip()
        if payload == "[DONE]":
            break
        if not payload:
            continue
        try:
            event = json.loads(payload)
        except Exception:
            continue
        content = event.get("content")
        if content:
            answer_parts.append(str(content))
        if "sources" in event and isinstance(event.get("sources"), list):
            latest_sources = event["sources"]

    return "".join(answer_parts).strip(), latest_sources


def _source_tables(sources: List[Dict[str, Any]], answer: str) -> Set[str]:
    tables: Set[str] = set()
    for s in sources:
        table = s.get("table")
        if isinstance(table, str) and table.strip():
            tables.add(table.strip())
    if "[시스템 안내]" in answer:
        tables.add("system")
    return tables


def _score_case(
    answer: str,
    source_tables: Set[str],
    must_include: List[str],
    must_not_include: List[str],
    expected_sources: List[str],
) -> Tuple[float, float, float, float]:
    include_score = 1.0 if all(token in answer for token in must_include) else 0.0
    exclude_score = 1.0 if all(token not in answer for token in must_not_include) else 0.0
    source_score = 1.0 if set(expected_sources).issubset(source_tables) else 0.0
    # 기존 결과 파일 스코어 체계와 유사하게 include 비중을 높임
    total_score = round((include_score * 0.6) + (exclude_score * 0.2) + (source_score * 0.2), 3)
    return include_score, exclude_score, source_score, total_score


def run() -> int:
    try:
        health = _get_json(HEALTH_URL, timeout=20)
    except (HTTPError, URLError, TimeoutError, OSError) as e:
        print(f"[ERROR] 백엔드 헬스 체크 실패: {e}")
        print("[HINT] app 디렉터리에서 `python main.py`로 서버를 먼저 실행하세요.")
        return 1

    if str(health.get("status", "")).lower() != "healthy":
        print(f"[ERROR] 백엔드 상태 비정상: {health}")
        return 1

    samples = _load_samples(SAMPLE_PATH)
    results: List[Dict[str, Any]] = []

    for sample in samples:
        question = str(sample.get("question", "")).strip()
        if not question:
            continue

        payload = {
            "message": question,
            "use_rag": True,
            "thread_id": f"eval-{uuid.uuid4()}",
        }

        try:
            stream_text = _post_json(CHAT_STREAM_URL, payload, timeout=300)
            answer, sources = _parse_sse(stream_text)
            tables = sorted(_source_tables(sources, answer))
            include_score, exclude_score, source_score, total_score = _score_case(
                answer=answer,
                source_tables=set(tables),
                must_include=list(sample.get("must_include") or []),
                must_not_include=list(sample.get("must_not_include") or []),
                expected_sources=list(sample.get("expected_sources") or []),
            )
            results.append(
                {
                    "id": sample.get("id"),
                    "question": question,
                    "answer": answer,
                    "sources": tables,
                    "include_score": include_score,
                    "exclude_score": exclude_score,
                    "source_score": source_score,
                    "total_score": total_score,
                }
            )
            print(f"[OK] {sample.get('id')} total={total_score}")
        except Exception as e:
            results.append(
                {
                    "id": sample.get("id"),
                    "question": question,
                    "answer": f"[EVAL ERROR] {e}",
                    "sources": [],
                    "include_score": 0.0,
                    "exclude_score": 0.0,
                    "source_score": 0.0,
                    "total_score": 0.0,
                }
            )
            print(f"[ERROR] {sample.get('id')}: {e}")

    avg = round(sum(r["total_score"] for r in results) / max(1, len(results)), 3)
    output = {"average_score": avg, "count": len(results), "results": results}
    RESULT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] 평균 점수: {avg} / 결과 파일: {RESULT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
