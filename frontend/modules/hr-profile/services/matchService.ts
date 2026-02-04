/**
 * 부서 적합도 매칭 서비스
 * Success DNA 점수 + 이력서 키워드를 조합해 추천 부서를 도출합니다.
 */

import type { Employee, SuccessDNA, Resume } from "@/modules/shared/types";

export interface DepartmentMatch {
  /** 추천 부서명 */
  department: string;
  /** 적합도 점수 (0–100) */
  score: number;
  /** 매칭 사유 (표시용) */
  reason: string;
}

/** 경력/직함/설명 텍스트를 한 문자열로 합침 */
function getExperienceText(resume: Resume | undefined): string {
  if (!resume?.experience?.length) return "";
  return resume.experience
    .map((e) => [e.role, e.company, e.description].filter(Boolean).join(" "))
    .join(" ");
}

/** 학력 전공/분야 텍스트 */
function getEducationFieldText(resume: Resume | undefined): string {
  if (!resume?.education?.length) return "";
  return resume.education.map((e) => e.field ?? "").filter(Boolean).join(" ");
}

/** 보유 기술명 텍스트 */
function getSkillsText(resume: Resume | undefined): string {
  if (!resume?.skills?.length) return "";
  return resume.skills.map((s) => s.name).join(" ");
}

/** 키워드가 텍스트에 포함되는지 (대소문자 무시) */
function containsKeyword(text: string, keyword: string): boolean {
  return text.toLowerCase().includes(keyword.toLowerCase());
}

/** 직원의 Success DNA + 이력서 기반 추천 부서 목록 반환 (점수 내림차순) */
export function getDepartmentMatches(employee: Employee): DepartmentMatch[] {
  const dna: SuccessDNA | undefined = employee.successDna;
  const resume = employee.resume;
  const expText = getExperienceText(resume);
  const eduFieldText = getEducationFieldText(resume);
  const skillsText = getSkillsText(resume);
  const matches: DepartmentMatch[] = [];

  const tech = dna?.technical ?? 0;
  const creative = dna?.creativity ?? 0;
  const leadership = dna?.leadership ?? 0;
  const collaboration = dna?.collaboration ?? 0;
  const adaptability = dna?.adaptability ?? 0;

  // 기술력 DNA > 80 && 경력에 '개발' 포함 → 기술연구소
  if (tech > 80 && containsKeyword(expText, "개발")) {
    matches.push({
      department: "기술연구소",
      score: Math.min(95, 75 + Math.floor(tech / 5)),
      reason: "기술력 DNA가 높고 경력에 개발 경험이 있어 기술연구소와 적합합니다.",
    });
  } else if (tech > 70 && (containsKeyword(expText, "개발") || containsKeyword(skillsText, "개발"))) {
    matches.push({
      department: "기술연구소",
      score: 60 + Math.floor(tech / 4),
      reason: "기술 역량과 개발 관련 경력/기술이 있어 기술연구소를 추천합니다.",
    });
  }

  // 창의성 DNA > 70 && 전공/분야에 '디자인' → 서비스디자인팀
  if (creative > 70 && containsKeyword(eduFieldText, "디자인")) {
    matches.push({
      department: "서비스디자인팀",
      score: Math.min(92, 70 + Math.floor(creative / 4)),
      reason: "창의성 DNA가 높고 디자인 관련 전공으로 서비스디자인팀과 적합합니다.",
    });
  } else if (creative > 65 && containsKeyword(expText, "디자인")) {
    matches.push({
      department: "서비스디자인팀",
      score: 65 + Math.floor(creative / 5),
      reason: "창의 역량과 디자인 경력이 있어 서비스디자인팀을 추천합니다.",
    });
  }

  // 리더십 DNA > 75 && 경력에 '관리' or '리드' → 경영기획실
  if (leadership > 75 && (containsKeyword(expText, "관리") || containsKeyword(expText, "리드"))) {
    matches.push({
      department: "경영기획실",
      score: Math.min(90, 70 + Math.floor(leadership / 4)),
      reason: "리더십 DNA가 높고 관리/리드 경력이 있어 경영기획실과 적합합니다.",
    });
  } else if (leadership > 70) {
    matches.push({
      department: "경영기획실",
      score: 55 + Math.floor(leadership / 3),
      reason: "리더십 역량이 뛰어나 경영기획 업무에 적합합니다.",
    });
  }

  // 협업 DNA > 80 → 인사조직팀
  if (collaboration > 80) {
    matches.push({
      department: "인사조직팀",
      score: Math.min(88, 65 + Math.floor(collaboration / 4)),
      reason: "협업 DNA가 높아 인사·조직 문화 업무에 적합합니다.",
    });
  } else if (collaboration > 70 && containsKeyword(expText, "인사")) {
    matches.push({
      department: "인사조직팀",
      score: 60 + Math.floor(collaboration / 3),
      reason: "협업 역량과 인사 경력으로 인사조직팀을 추천합니다.",
    });
  }

  // 적응력 DNA > 75 && 경력/기술 다양 → 전략기획팀
  if (adaptability > 75 && (expText.length > 20 || resume?.experience?.length >= 2)) {
    matches.push({
      department: "전략기획팀",
      score: Math.min(85, 60 + Math.floor(adaptability / 3)),
      reason: "적응력이 높고 다양한 경력으로 전략·기획 업무에 적합합니다.",
    });
  }

  // 마케팅 키워드 + 창의성
  if (creative > 65 && (containsKeyword(expText, "마케팅") || containsKeyword(eduFieldText, "마케팅"))) {
    matches.push({
      department: "마케팅",
      score: 62 + Math.floor(creative / 4),
      reason: "창의성과 마케팅 경력/전공으로 마케팅 부서를 추천합니다.",
    });
  }

  // R&D 키워드 + 기술력
  if (tech > 70 && (containsKeyword(expText, "연구") || containsKeyword(expText, "R&D"))) {
    matches.push({
      department: "R&D",
      score: 65 + Math.floor(tech / 4),
      reason: "기술 역량과 연구 개발 경력으로 R&D 부서와 적합합니다.",
    });
  }

  // 중복 부서 제거: 동일 부서면 최고 점수만 유지
  const byDept = new Map<string, DepartmentMatch>();
  for (const m of matches) {
    const existing = byDept.get(m.department);
    if (!existing || m.score > existing.score) byDept.set(m.department, m);
  }

  return Array.from(byDept.values()).sort((a, b) => b.score - a.score);
}

/** 최고 추천 부서 1건 (matchedDepartment 저장용) */
export function getTopDepartmentMatch(employee: Employee): DepartmentMatch | null {
  const list = getDepartmentMatches(employee);
  return list.length > 0 ? list[0] : null;
}
