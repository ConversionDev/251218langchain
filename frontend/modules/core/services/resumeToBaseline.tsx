/**
 * 이력서 파일 → 기본 정보 + Baseline DNA (목 데이터).
 * 실제 연동 시에는 파일 텍스트 추출 후 파싱/LLM으로 대체.
 */

import type { SuccessDNA, Resume } from "@/modules/shared/types";

export interface ResumeParseResult {
  /** AI가 채운 기본 정보 (사용자 확인·수정용) */
  name: string;
  jobTitle: string;
  department: string;
  email: string;
  joinedAt: string;
  /** 이력서 구조 데이터 (학력·경력·기술·자격) */
  resume: Resume;
  /** 이력서 텍스트 분석으로 추정한 최초 Baseline DNA */
  successDna: SuccessDNA;
}

/** 목 데이터: 업로드된 이력서(파일)를 분석한 것처럼 반환. 현재는 데이터 없음 → 고정 목 사용 */
export async function parseResumeToBaseline(_file: File): Promise<ResumeParseResult> {
  await new Promise((r) => setTimeout(r, 600));
  return {
    name: "홍길동",
    jobTitle: "주니어 개발자",
    department: "개발팀",
    email: "gildong.hong@company.com",
    joinedAt: new Date().toISOString().slice(0, 10),
    resume: {
      education: [
        { school: "○○대학교", degree: "학사", field: "컴퓨터공학", startDate: "2016-03", endDate: "2020-02" },
      ],
      experience: [
        { company: "△△소프트", role: "개발 인턴", startDate: "2019-07", endDate: "2019-12" },
        { company: "□□테크", role: "백엔드 개발자", startDate: "2020-03", endDate: "2023-01" },
      ],
      skills: [
        { name: "JavaScript", level: "중급" },
        { name: "TypeScript", level: "중급" },
        { name: "Node.js", level: "초급" },
      ],
      certifications: [{ name: "정보처리기사", issuer: "한국산업인력공단" }],
    },
    successDna: {
      leadership: 58,
      technical: 78,
      creativity: 72,
      collaboration: 75,
      adaptability: 70,
    },
  };
}
