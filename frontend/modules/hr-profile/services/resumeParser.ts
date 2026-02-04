/**
 * 이력서 원문 텍스트 → 구조화된 Resume 파싱 (휴리스틱)
 * 학력/경력/기술/자격 섹션 키워드와 날짜 패턴으로 추출
 */

import type { Resume, EducationEntry, ExperienceEntry, SkillEntry, CertificationEntry } from "@/modules/shared/types";

const SECTION_HEADERS = [
  /학력|교육|education/i,
  /경력|경험|경력사항|experience|career/i,
  /기술|스킬|보유\s*기술|skills/i,
  /자격|자격증|인증|certification|license/i,
];

function extractSections(text: string): Record<string, string> {
  const normalized = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const sections: Record<string, string> = {};
  let currentKey = "preamble";
  let currentLines: string[] = [];

  const flush = (key: string) => {
    if (currentLines.length) sections[key] = currentLines.join("\n").trim();
    currentLines = [];
  };

  for (const line of normalized.split("\n")) {
    const trimmed = line.trim();
    const matched = SECTION_HEADERS.findIndex((re) => re.test(trimmed));
    if (matched >= 0) {
      flush(currentKey);
      currentKey = ["education", "experience", "skills", "certifications"][matched];
      const afterHeader = trimmed.replace(SECTION_HEADERS[matched], "").trim();
      if (afterHeader) currentLines.push(afterHeader);
      continue;
    }
    currentLines.push(trimmed);
  }
  flush(currentKey);
  return sections;
}

function parseEducation(section: string): EducationEntry[] {
  const entries: EducationEntry[] = [];
  const lines = section.split("\n").filter((l) => l.trim());
  for (const line of lines) {
    const dateMatch = line.match(/(\d{4})[.\-/]?(\d{1,2})?[.\-/]?\s*[-~]\s*(\d{4})?[.\-/]?(\d{1,2})?|재학|졸업/);
    const school = line.replace(/\d{4}[.\-\/\s~년월재학졸업]+/g, "").replace(/\s*[-|]\s*.*$/, "").trim();
    if (!school || school.length < 2) continue;
    const degreeMatch = line.match(/학사|석사|박사|전문학사|고졸|대졸|MBA|PhD|Bachelor|Master/i);
    const fieldMatch = line.match(/(?:전공|분야|학과)\s*[:]\s*([^\d\n]+)/i) || line.match(/\s+([가-힣a-zA-Z]+(?:학과|전공|학부))/);
    const startYear = dateMatch?.[1];
    const startMonth = dateMatch?.[2];
    const endYear = dateMatch?.[3];
    const endMonth = dateMatch?.[4];
    entries.push({
      school: school.slice(0, 80),
      degree: degreeMatch ? degreeMatch[0] : "학사",
      field: fieldMatch ? fieldMatch[1].trim().slice(0, 50) : undefined,
      startDate: startYear ? `${startYear}-${(startMonth || "01").padStart(2, "0")}` : "",
      endDate: endYear ? `${endYear}-${(endMonth || "01").padStart(2, "0")}` : undefined,
    });
  }
  return entries.slice(0, 10);
}

function parseExperience(section: string): ExperienceEntry[] {
  const entries: ExperienceEntry[] = [];
  const lines = section.split("\n").filter((l) => l.trim());
  for (const line of lines) {
    const dateMatch = line.match(/(\d{4})[.\-/]?(\d{1,2})?[.\-/]?\s*[-~]\s*(\d{4})?[.\-/]?(\d{1,2})?|재직|현재/);
    const rest = line.replace(/(\d{4}[.\-\/\s~년월재직현재]+)/g, " ").trim();
    const parts = rest.split(/\s*[-|·]\s*|\s{2,}/).filter(Boolean);
    const company = parts[0]?.trim().slice(0, 80) ?? "";
    const role = parts[1]?.trim().slice(0, 80) ?? "";
    if (!company) continue;
    const startYear = dateMatch?.[1];
    const startMonth = dateMatch?.[2];
    const endYear = dateMatch?.[3];
    const endMonth = dateMatch?.[4];
    entries.push({
      company,
      role: role || "—",
      startDate: startYear ? `${startYear}-${(startMonth || "01").padStart(2, "0")}` : "",
      endDate: endYear ? `${endYear}-${(endMonth || "01").padStart(2, "0")}` : undefined,
      description: parts[2]?.trim().slice(0, 200),
    });
  }
  return entries.slice(0, 15);
}

function parseSkills(section: string): SkillEntry[] {
  const entries: SkillEntry[] = [];
  const tokens = section.split(/[,，、\n·;]/).map((s) => s.trim()).filter(Boolean);
  for (const t of tokens) {
    const levelMatch = t.match(/(초급|중급|고급|Expert|Intermediate|Beginner)/i);
    const name = t.replace(/(초급|중급|고급|Expert|Intermediate|Beginner)/i, "").trim().slice(0, 60);
    if (name.length >= 1) entries.push({ name, level: levelMatch ? levelMatch[1] : undefined });
  }
  return entries.slice(0, 20);
}

function parseCertifications(section: string): CertificationEntry[] {
  const entries: CertificationEntry[] = [];
  const lines = section.split("\n").filter((l) => l.trim());
  for (const line of lines) {
    const dateMatch = line.match(/(\d{4})[.\-/](\d{1,2})/);
    const name = line.replace(/\d{4}[.\-/]\d{1,2}.*$/, "").trim().slice(0, 80);
    if (name.length >= 1) entries.push({ name, date: dateMatch ? `${dateMatch[1]}-${dateMatch[2].padStart(2, "0")}` : undefined });
  }
  return entries.slice(0, 10);
}

export function parseResumeFromText(text: string): Resume {
  const sections = extractSections(text);
  return {
    education: parseEducation(sections.education ?? ""),
    experience: parseExperience(sections.experience ?? ""),
    skills: parseSkills(sections.skills ?? ""),
    certifications: parseCertifications(sections.certifications ?? ""),
  };
}
