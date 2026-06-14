"""직원 유스케이스 — 채용 흐름, AI 분석, 임베딩."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session  # type: ignore[import-untyped]

from api.services.resume_analyzer import _resume_dict_to_text, analyze_resume_text  # type: ignore
from infrastructure.persistence.repositories.employee_repository import (  # type: ignore
    backfill_missing_profile_fields,
    build_embedding_content,
    create as repo_create,
    delete as repo_delete,
    fill_embeddings_for_employees,
    find_by_resume_hash as repo_find_by_resume_hash,
    get_by_id as repo_get_by_id,
    get_next_id as repo_get_next_id,
    list_all as repo_list_all,
    list_paginated as repo_list_paginated,
    update as repo_update,
    update_one_employee_embedding,
)
from infrastructure.persistence.repositories.performance_record_repository import (  # type: ignore
    fill_embeddings_for_performance_records,
    list_by_employee as repo_list_performance_by_employee,
)

logger = logging.getLogger(__name__)

_DNA_KEYS = ("leadership", "technical", "creativity", "collaboration", "adaptability")


class EmployeeService:

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ CRUD

    def list_all(self) -> List[Dict[str, Any]]:
        return repo_list_all(self.db)

    def list_paginated(
        self, page: int, page_size: int, employment_type: Optional[str] = None, search: Optional[str] = None
    ):
        """Returns (items, total) tuple. search: 이름·부서·ID 부분일치(전체 대상)."""
        p = max(1, page)
        ps = max(1, min(100, page_size))
        return repo_list_paginated(
            self.db, page=p, page_size=ps, employment_type=employment_type, search=search
        )

    def get(self, employee_id: str) -> Optional[Dict[str, Any]]:
        return repo_get_by_id(self.db, employee_id)

    def get_next_id(self) -> Any:
        return repo_get_next_id(self.db)

    def find_by_resume_hash(self, resume_hash: str) -> Optional[Dict[str, Any]]:
        h = (resume_hash or "").strip()
        if not h:
            return None
        return repo_find_by_resume_hash(self.db, h)

    def update(self, employee_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return repo_update(self.db, employee_id, data)

    def delete(self, employee_id: str) -> bool:
        return repo_delete(self.db, employee_id)

    # ------------------------------------------------------------------ 생성

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """직원 생성. new_hire 타입이면 applicationDate·status 자동 설정."""
        if data.get("employmentType") == "new_hire":
            # 지원일: 관리자가 입력했으면 존중, 없을 때만 등록 시점(now)으로 기본 설정
            if not data.get("applicationDate"):
                data["applicationDate"] = datetime.now(timezone.utc)
            data["joinedAt"] = None
            data["status"] = "pending"
            data["successDna"] = None
            data["successDnaReason"] = None
        return repo_create(self.db, data)

    # ------------------------------------------------------------------ AI 분석

    def _has_success_dna(self, one: Dict[str, Any]) -> bool:
        d = one.get("successDna")
        if not isinstance(d, dict):
            return False
        for k in _DNA_KEYS:
            v = d.get(k)
            if v is None:
                return False
            try:
                float(v)
            except (TypeError, ValueError):
                return False
        return True

    async def analyze(self, employee_id: str, force: bool = False) -> Dict[str, Any]:
        """AI 분석 + 상태 전이.

        Returns dict with 'analysisSkipped' key.
        Raises ValueError if employee not found or no text available.
        """
        one = repo_get_by_id(self.db, employee_id)
        if not one:
            raise ValueError("Employee not found")

        is_new_hire = (one.get("employmentType") or "").strip().lower() == "new_hire"
        if is_new_hire and self._has_success_dna(one) and not force:
            st = str(one.get("status") or "").strip().lower()
            if st == "pending":
                updated = repo_update(self.db, employee_id, {"status": "screening"})
                out = dict(updated or one)
                out["analysisSkipped"] = True
                return out
            out = dict(one)
            out["analysisSkipped"] = True
            return out

        stored_resume_text = (one.get("resumeText") or "").strip()
        resume = one.get("resume")
        resume_text = stored_resume_text if stored_resume_text else (
            _resume_dict_to_text(resume) if isinstance(resume, dict) else ""
        )

        perf_rows = repo_list_performance_by_employee(self.db, employee_id, limit=50)
        perf_lines: List[str] = []
        for r in perf_rows:
            period = str(r.get("period") or "").strip()
            text_type = str(r.get("textType") or "").strip()
            content = str(r.get("content") or "").strip()
            if content:
                perf_lines.append(f"[{period}][{text_type}] {content}")
        perf_text = "\n".join(perf_lines)

        text_parts = []
        if resume_text and len(resume_text.strip()) >= 10:
            text_parts.append("## 이력/프로필\n" + resume_text.strip())
        if perf_text and len(perf_text.strip()) >= 10:
            text_parts.append("## 성과활동\n" + perf_text.strip())
        full_text = "\n\n".join(text_parts)
        if not full_text or len(full_text.strip()) < 10:
            raise ValueError("분석 가능한 텍스트가 없습니다. (resume 또는 성과활동 기록 필요)")

        result = await asyncio.to_thread(analyze_resume_text, full_text, True)

        update_payload: Dict[str, Any] = {
            "successDna": result.get("successDna"),
            "successDnaReason": result.get("successDnaReason"),
        }
        if is_new_hire:
            update_payload["status"] = "screening"

        updated = repo_update(self.db, employee_id, update_payload)
        out = dict(updated or one)
        out["analysisSkipped"] = False
        return out

    # ------------------------------------------------------------------ 임베딩

    def _build_persona_prompt(self, profile_text: str) -> str:
        return (
            "다음 직원 정보를 RAG 검색 최적화용 '직원 역량 페르소나'로 8~12문장 내외 한국어 평문으로 요약하세요. "
            "반드시 포함: 핵심역량, 업무도메인, 실무강점, 협업스타일, 교육/학습 포인트, 추천 질문 키워드. "
            "JSON/마크다운 없이 문장 텍스트만 출력하세요.\n\n"
            f"[직원 정보]\n{profile_text}"
        )

    def _generate_persona_text(self, profile_text: str) -> str:
        """EXAONE 페르소나 생성. 실패 시 원본 텍스트 반환."""
        try:
            from infrastructure.llm.exaone_adapter import generate_text  # type: ignore
            out = generate_text(self._build_persona_prompt(profile_text), max_tokens=512, temperature=0.3)
            txt = (out or "").strip()
            if not txt or txt.startswith("[ExaOne 오류]"):
                return profile_text
            return txt
        except Exception:
            return profile_text

    def refresh_embedding(
        self,
        emb: Any,
        employee_id: Optional[str] = None,
        include_existing: bool = False,
        force_rebuild_content: bool = False,
        use_exaone_persona: bool = False,
    ) -> Dict[str, Any]:
        """단건 또는 전체 직원 임베딩 갱신.

        Raises ValueError if employee not found (단건 모드).
        """
        if employee_id:
            content_override = None
            if use_exaone_persona:
                one = repo_get_by_id(self.db, employee_id)
                if not one:
                    raise ValueError("Employee not found")
                profile = (
                    f"직원 ID: {one.get('id', '')}. 이름: {one.get('name', '')}. 직급: {one.get('jobTitle') or ''}. "
                    f"부서: {one.get('department') or ''}. 고용형태: {one.get('employmentType') or ''}. "
                    f"교육훈련: {one.get('trainingHours') if one.get('trainingHours') is not None else '미기재'}시간. "
                    f"이력서: {one.get('resume') or {}}."
                )
                content_override = self._generate_persona_text(profile)
            ok = update_one_employee_embedding(self.db, employee_id, emb, embedding_content_override=content_override)
            if not ok:
                raise ValueError("Employee not found or embed failed")
            return {"updated": 1, "id": employee_id, "useExaonePersona": use_exaone_persona}

        content_builder = None
        if use_exaone_persona:
            def _content_builder(row: Any) -> str:
                return self._generate_persona_text(build_embedding_content(row))
            content_builder = _content_builder

        n = fill_embeddings_for_employees(
            self.db, emb,
            include_existing=include_existing,
            force_rebuild_content=force_rebuild_content,
            content_builder=content_builder,
        )
        perf_n = 0
        try:
            perf_n = fill_embeddings_for_performance_records(self.db, emb, include_existing=include_existing)
        except Exception as pe:
            logger.warning("performance_records 임베딩 생성 중 오류 (스키마 미설정 가능): %s", pe)
        return {
            "updated": n,
            "performanceUpdated": perf_n,
            "includeExisting": include_existing,
            "regenerateContent": force_rebuild_content,
            "useExaonePersona": use_exaone_persona,
        }

    def backfill_profiles(self, dry_run: bool = True, seed: int = 42) -> Dict[str, Any]:
        """결측 프로필(gender/age/training_hours) 일괄 보정."""
        return backfill_missing_profile_fields(self.db, dry_run=dry_run, seed=seed)
