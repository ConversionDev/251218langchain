/**
 * HR Profile 모듈 서비스
 * 정형화된 이력 정보(Resume) 처리·검증·매칭 로직
 */

import type { Resume, Employee } from "@/modules/shared/types";

/** 이력서가 비어 있지 않은지 여부 */
export function hasResumeData(resume: Resume | undefined): boolean {
  if (!resume) return false;
  const hasEd = resume.education?.length > 0;
  const hasExp = resume.experience?.length > 0;
  const hasSkills = resume.skills?.length > 0;
  const hasCerts = resume.certifications?.length > 0;
  return hasEd || hasExp || hasSkills || hasCerts;
}

/** 직원의 이력서 요약 라벨 (표시용) */
export function getResumeSummaryLabel(employee: Employee): string {
  const r = employee.resume;
  if (!r || !hasResumeData(r)) return "이력 없음";
  const parts: string[] = [];
  if (r.education?.length) parts.push(`학력 ${r.education.length}건`);
  if (r.experience?.length) parts.push(`경력 ${r.experience.length}건`);
  if (r.skills?.length) parts.push(`기술 ${r.skills.length}건`);
  if (r.certifications?.length) parts.push(`자격 ${r.certifications.length}건`);
  return parts.length ? parts.join(" · ") : "이력 없음";
}
