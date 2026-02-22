"""
직원(Employee) 저장·조회 — employees 테이블 Neon CRUD.

프론트 Employee 타입과 호환되는 camelCase JSON 반환.
백엔드에서 직원 목록이 필요한 직무 처리(부서 매칭 등)는 이 리포지토리만 사용하면 됨.
RAG: embedding_content·embedding·FAISS/pgvector 검색 지원.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session  # type: ignore[import-untyped]
from tqdm import tqdm

from domain.models.bases.employee import Employee  # type: ignore

_AGE_BAND_BY_AGE = (
    (30, "under30"),
    (40, "30-39"),
    (50, "40-49"),
    (60, "50-59"),
    (999, "60over"),
)


def _age_band_from_age(age: Optional[int]) -> Optional[str]:
    """age(만 나이) → 연령대. age만 저장하고 연령대는 파생."""
    if age is None:
        return None
    for limit, band in _AGE_BAND_BY_AGE:
        if age < limit:
            return band
    return "60over"


def _application_date_to_api(val: Any) -> Optional[str]:
    """DB application_date(datetime | None) → API용 ISO 문자열."""
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val) if val else None


def _parse_application_date(val: Any) -> Optional[datetime]:
    """API/JSONL의 applicationDate(문자열 또는 datetime) → DB 저장용 datetime."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if not isinstance(val, str) or not val.strip():
        return None
    s = val.strip()
    try:
        if "T" in s or " " in s:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _row_to_dict(row: Employee) -> Dict[str, Any]:
    """ORM 행 → 프론트 호환 camelCase dict."""
    return {
        "id": row.id,
        "name": row.name,
        "jobTitle": row.job_title or "",
        "department": row.department or "",
        "email": row.email,
        "applicationDate": _application_date_to_api(getattr(row, "application_date", None)),
        "joinedAt": row.joined_at,
        "successDna": row.success_dna,
        "successDnaReason": getattr(row, "success_dna_reason", None),
        "rejectionReason": getattr(row, "rejection_reason", None),
        "behavioralDna": row.behavioral_dna,
        "behavioralSource": row.behavioral_source,
        "behavioralSourceItems": row.behavioral_source_items,
        "disclosureMetrics": row.disclosure_metrics,
        "gender": row.gender,
        "age": row.age,
        "ageBand": _age_band_from_age(row.age),
        "employmentType": row.employment_type,
        "trainingHours": row.training_hours,
        "resume": row.resume,
        "resumeFileHash": row.resume_file_hash,
        "matchedDepartment": row.matched_department,
        "status": getattr(row, "status", None),
    }


def _apply_payload(row: Employee, data: Dict[str, Any]) -> None:
    """payload(camelCase)를 ORM 행에 반영."""
    mapping = (
        ("name", "name"),
        ("jobTitle", "job_title"),
        ("department", "department"),
        ("email", "email"),
        ("applicationDate", "application_date"),
        ("joinedAt", "joined_at"),
        ("successDna", "success_dna"),
        ("successDnaReason", "success_dna_reason"),
        ("rejectionReason", "rejection_reason"),
        ("behavioralDna", "behavioral_dna"),
        ("behavioralSource", "behavioral_source"),
        ("behavioralSourceItems", "behavioral_source_items"),
        ("disclosureMetrics", "disclosure_metrics"),
        ("gender", "gender"),
        ("age", "age"),
        ("employmentType", "employment_type"),
        ("trainingHours", "training_hours"),
        ("resume", "resume"),
        ("resumeFileHash", "resume_file_hash"),
        ("matchedDepartment", "matched_department"),
        ("status", "status"),
    )
    for key, attr in mapping:
        if key not in data:
            continue
        val = data[key]
        if key == "applicationDate" and attr == "application_date":
            val = _parse_application_date(val) if val is not None else None
        setattr(row, attr, val)


def find_by_resume_hash(db: Session, resume_hash: str) -> Optional[Dict[str, Any]]:
    """이력서 파일 해시로 직원 조회 (동일 이력서 중복 등록 방지)."""
    if not (resume_hash and resume_hash.strip()):
        return None
    row = db.query(Employee).filter(Employee.resume_file_hash == resume_hash.strip()).first()
    return _row_to_dict(row) if row else None


def create(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """직원 생성. data에 id 필수. 동일 이력서(resumeFileHash)가 이미 있으면 DB 추가하지 않음(409)."""
    eid = data.get("id")
    if not eid:
        raise ValueError("id is required")
    existing_by_id = db.query(Employee).filter(Employee.id == eid).first()
    if existing_by_id:
        raise ValueError(f"Employee id already exists: {eid}")
    resume_hash = (data.get("resumeFileHash") or "").strip()
    if resume_hash:
        existing_by_hash = db.query(Employee).filter(Employee.resume_file_hash == resume_hash).first()
        if existing_by_hash:
            raise ValueError("ALREADY_EXISTS")
    # 지원 접수(신입) 시 상태는 항상 미검토. AI 분석 API에서만 screening으로 변경.
    if (data.get("employmentType") or "").strip().lower() == "new_hire":
        data = {**data, "status": "pending"}
    row = Employee(id=eid, name=data.get("name", ""), job_title=data.get("jobTitle", ""), department=data.get("department", ""))
    _apply_payload(row, data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def get_by_id(db: Session, eid: str) -> Optional[Dict[str, Any]]:
    """직원 단건 조회."""
    row = db.query(Employee).filter(Employee.id == eid).first()
    return _row_to_dict(row) if row else None


def find_by_name(db: Session, name_part: str, limit: int = 10) -> List[Dict[str, Any]]:
    """이름에 name_part가 포함된 직원 목록 조회 (부분 일치). 채팅/도구에서 개별 직원 질문 시 사용."""
    if not (name_part and name_part.strip()):
        return []
    pattern = f"%{name_part.strip()}%"
    rows = (
        db.query(Employee)
        .filter(Employee.name.ilike(pattern))
        .order_by(Employee.id)
        .limit(limit)
        .all()
    )
    return [_row_to_dict(r) for r in rows]


def list_all(db: Session) -> List[Dict[str, Any]]:
    """직원 목록 전체 (Neon 데이터만)."""
    rows = db.query(Employee).order_by(Employee.id).all()
    return [_row_to_dict(r) for r in rows]


def list_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    employment_type: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """직원 목록 페이징. employment_type: None(전체), 'regular'(기존직원), 'new_hire'(신입).
    신입: employment_type='new_hire' 이거나 status가 ATS 상태(pending/screening/hired/rejected)인 경우(과거 적재 데이터 호환).
    반환: (해당 페이지 항목 리스트, 전체 개수)."""
    q = db.query(Employee)
    if employment_type == "new_hire":
        q = q.filter(
            (Employee.employment_type == "new_hire")
            | (Employee.status.in_(["pending", "screening", "hired", "rejected"]))
        )
    elif employment_type == "regular":
        # 기존 직원: employment_type이 new_hire가 아닌 경우 (NULL·빈값·regular 등)
        q = q.filter(
            (Employee.employment_type.is_(None))
            | (Employee.employment_type == "")
            | (Employee.employment_type == "regular")
        )
        # ATS 지원자만 제외: pending/screening/rejected. hired(입사 확정)는 기존 직원으로 포함.
        q = q.filter(
            (Employee.status.is_(None))
            | (Employee.status == "")
            | (~Employee.status.in_(["pending", "screening", "rejected"]))
        )
    total = q.count()
    rows = (
        q.order_by(Employee.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_row_to_dict(r) for r in rows], total


def get_next_id(db: Session) -> str:
    """직원 ID 중 숫자 부분 최대값+1로 다음 ID 제안 (예: E001, E002 → E003)."""
    row = (
        db.query(Employee.id)
        .order_by(Employee.id.desc())
        .limit(1)
        .first()
    )
    if not row or not row[0]:
        return "E001"
    s = str(row[0])
    num = 0
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
    return f"E{num + 1:03d}"


def update(db: Session, eid: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """직원 수정. id는 변경 불가."""
    row = db.query(Employee).filter(Employee.id == eid).first()
    if not row:
        return None
    if "id" in data and data["id"] != eid:
        raise ValueError("id cannot be changed")
    _apply_payload(row, data)
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return _row_to_dict(row)


def delete(db: Session, eid: str) -> bool:
    """직원 삭제. 존재하면 True, 없으면 False."""
    row = db.query(Employee).filter(Employee.id == eid).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


# --- RAG: 임베딩용 텍스트·벡터 검색 ---


def build_embedding_content(row: Employee) -> str:
    """직원 행 → RAG 임베딩용 한 덩어리 텍스트.
    검색 품질 향상 시: 엑사원(SFT 어댑터)으로 '직원 역량 페르소나' 요약을 생성해
    embedding_content에 저장한 뒤 임베딩하는 것을 권장. update_one_employee_embedding(..., embedding_content_override=...) 로 반영 가능."""
    parts = [
        f"직원 ID: {row.id}. 이름: {row.name}. 직급: {row.job_title or ''}. 부서: {row.department or ''}.",
    ]
    if row.training_hours is not None:
        parts.append(f"연간 교육훈련 시간: {row.training_hours}시간.")
    if row.disclosure_metrics:
        dm = row.disclosure_metrics
        if isinstance(dm, dict) and "items" in dm and isinstance(dm["items"], list):
            items = dm["items"]
            parts.append("공시 지표: " + ", ".join(
                str(x.get("value", x.get("name", ""))) for x in items[:10] if isinstance(x, dict)
            ) + ".")
        elif isinstance(dm, dict):
            parts.append(
                f"공시 지표: transitionReadyScore={dm.get('transitionReadyScore')}, skillGap={dm.get('skillGap')}, humanCapitalROI={dm.get('humanCapitalROI')}."
            )
    if row.resume and isinstance(row.resume, dict):
        edu = row.resume.get("education") or []
        exp = row.resume.get("experience") or []
        skills = row.resume.get("skills") or []
        if edu:
            parts.append("학력: " + ", ".join(
                (e.get("school") or "") + " " + (e.get("degree") or "") for e in edu[:5] if isinstance(e, dict)
            ) + ".")
        if exp:
            parts.append("경력: " + ", ".join(
                (e.get("company") or "") + " " + (e.get("role") or "") for e in exp[:5] if isinstance(e, dict)
            ) + ".")
        if skills:
            parts.append("기술: " + ", ".join(
                (s.get("name") or str(s)) for s in skills[:15] if isinstance(s, dict)
            ) + ".")
    return " ".join(parts)


def update_one_employee_embedding(
    db: Session,
    eid: str,
    embeddings_model: Any,
    embedding_content_override: Optional[str] = None,
) -> bool:
    """직원 한 명의 embedding_content(없으면 생성)·embedding 갱신. 성공 시 True."""
    row = db.query(Employee).filter(Employee.id == eid).first()
    if not row:
        return False
    content = embedding_content_override or row.embedding_content or build_embedding_content(row)
    if not row.embedding_content and not embedding_content_override:
        row.embedding_content = content
    try:
        if hasattr(embeddings_model, "embed_query"):
            vec = embeddings_model.embed_query(content)
        else:
            vec = embeddings_model.embed_documents([content])[0]
    except Exception:
        return False
    if vec is not None:
        row.embedding = list(vec)
    db.commit()
    return True


def fill_embeddings_for_employees(
    db: Session,
    embeddings_model: Any,
    batch_size: int = 32,
) -> int:
    """embedding_content가 없으면 생성하고, embedding이 null인 행만 임베딩 후 업데이트."""
    processed = 0
    while True:
        rows = (
            db.query(Employee)
            .filter(Employee.embedding.is_(None))
            .limit(200)
            .all()
        )
        if not rows:
            break
        texts = []
        for r in rows:
            content = r.embedding_content or build_embedding_content(r)
            if not r.embedding_content:
                r.embedding_content = content
            texts.append(content or r.id)
        vectors: List[Optional[List[float]]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                if hasattr(embeddings_model, "embed_documents"):
                    vs = embeddings_model.embed_documents(batch)
                else:
                    vs = [embeddings_model.embed_query(t) for t in batch]
                for v in (vs if isinstance(vs, list) else []):
                    vectors.append(list(v) if v is not None else None)
            except Exception:
                if hasattr(embeddings_model, "embed_query"):
                    for t in batch:
                        vectors.append(embeddings_model.embed_query(t))
                else:
                    vectors.extend([None] * len(batch))
        if len(vectors) < len(rows):
            vectors.extend([None] * (len(rows) - len(vectors)))
        for r, vec in zip(rows, vectors):
            if vec is not None:
                r.embedding = vec
        db.commit()
        db.expunge_all()
        processed += len(rows)
    return processed


def search_employees_with_filter(
    db: Session,
    query_embedding: List[float],
    k: int = 5,
) -> List[Tuple[Document, float]]:
    """
    employees 테이블에서 벡터 유사도 검색. Neon pgvector(HNSW) 전용(FAISS 미사용).
    반환: (Document, distance) 리스트. 코사인 거리(작을수록 유사).
    """
    vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    sql = (
        "SELECT id, name, job_title, department, embedding_content, "
        "(embedding <-> CAST(:vec AS vector)) AS distance "
        "FROM employees WHERE embedding IS NOT NULL "
        "ORDER BY embedding <-> CAST(:vec AS vector) LIMIT :k"
    )
    r = db.execute(sql_text(sql), {"vec": vec_str, "k": k})
    result = []
    for row in r:
        eid, name, job_title, department, content, distance = row
        doc = Document(
            page_content=content or f"직원 {name} ({job_title}, {department})",
            metadata={
                "table": "employees",
                "id": eid,
                "name": name or "",
                "job_title": job_title or "",
                "department": department or "",
            },
        )
        result.append((doc, float(distance)))
    return result
