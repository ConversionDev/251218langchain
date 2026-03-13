export const RESUME_COLORS = {
  dark: "#1a1f36",
  dark2: "#252b47",
  accent: "#C8861A",
  accent2: "#e8a030",
  mid: "#4a5568",
  light: "#f7f8fc",
  border: "#e2e8f0",
  text: "#2d3748",
  sub: "#718096",
  barGradient: "linear-gradient(90deg, #b8740f 0%, #d4951e 50%, #c8861a 100%)",
} as const;

export const RESUME_BASIC = {
  name: "강경구",
  nameEn: "Kang Gyeong-gu",
  title: "Performance-Driven Full-Stack AI Developer",
  email: "kku1031@naver.com",
  github: "github.com/ConversionDev",
  blog: "kku1031.tistory.com",
  phone: "010-0000-0000",
  location: "서울시",
  tagline: '"한 줄의 코드가 세상을 바꾼다고 믿는 풀스택 AI 개발자"',
} as const;

/** 자기소개 (HTML 양식용) */
export const INTRO =
  "OCR·RAG 기반 HR 문서 분석과 ESG AI 플랫폼 개발 경험을 보유한 풀스택 AI 개발자입니다. 비전공 출신으로 의료 IT에서 기본기를 다진 뒤, LangChain·프롬프트 엔지니어링을 중심으로 AI 역량을 확장해 왔으며, 성능 최적화와 협업을 중시합니다.";

/** 수상·자격·어학 (HTML 양식용) */
export const AWARDS = [
  "정보처리기사 (2022)",
  "TOEIC 800점대",
  "한국어(모국어) / 영어(업무 가능)",
] as const;

/** 1페이지 메트릭 바용 (골드 그라데이션) */
export const METRICS = [
  { num: "95%", label: "OCR 정확도" },
  { num: "40%↑", label: "추론 속도" },
  { num: "60%↓", label: "비용 절감" },
] as const;

export const NON_DEVELOP_EXPERIENCE = [
  { period: "2013", role: "통기타 동아리 YEP 부회장" },
  { period: "2014", role: "필리핀(팡가시난) 해외 자원봉사 RaonAtti (6개월)" },
  { period: "2018 – 2019", role: "대구 YMCA 남자 중장기 청소년 쉼터 팀원" },
  { period: "2019 – 2020", role: "한국 YMCA전국 연맹 국제개발협력팀 팀원" },
] as const;

export const SKILL_GROUPS = [
  {
    title: "AI / ML",
    tags: ["LangChain", "RAG", "GPT-4", "Prompt Eng.", "Tesseract OCR", "ChromaDB", "Vector DB", "Multi-Agent"],
    hot: [0, 1, 2],
  },
  {
    title: "Backend",
    tags: ["FastAPI", "Python", "Django", "REST API", "ElasticSearch", "Redis"],
    hot: [0, 1],
  },
  {
    title: "Database",
    tags: ["PostgreSQL", "SQLite", "Redis", "ChromaDB"],
    hot: [0],
  },
  {
    title: "Frontend",
    tags: ["React", "TypeScript", "Next.js", "Tailwind CSS", "JavaScript"],
    hot: [],
  },
  {
    title: "Infra / DevOps",
    tags: ["Docker", "Linux", "AWS", "CI/CD", "Git"],
    hot: [],
  },
] as const;

export const EXPERIENCE = [
  {
    company: "AI Developer | 개인 프로젝트",
    role: "Full-Stack AI Developer",
    period: "2025.09 – Present",
    bullets: [
      "OCR & RAG 기반 HR 문서 분석 에이전트 — OCR 정확도 95%, 속도 +40%, 비용 -60%",
      "ESG AI 플랫폼 AIFIX — 리스크 탐지 92%, 자동화율 85%",
      "멀티 에이전트 아키텍처 설계 & 팀 리딩, 프롬프트 엔지니어링",
    ],
  },
  {
    company: "제로베이스 백엔드 스쿨 15기",
    role: "Backend Developer",
    period: "2023.04 – 2024.01",
    bullets: [
      "팀 프로젝트 KeyWord — OAuth 2.0 소셜 로그인, ElasticSearch 검색 기능 개발",
      "백엔드 기본·프레임워크 심화 과정 학습, 프론트엔드와 협업 경험",
    ],
  },
  {
    company: "(주)화산시스템",
    role: "인터페이스 팀 / 사원",
    period: "2022.09 – 2022.12",
    desc: "국내 대학병원 진단검사의학과 프로그램 개발·관리 전문 업체. 하드웨어 시리얼 통신 인터페이스 담당 — 병원 장비와 사내 LIS(환자정보·건강기록 등) 간 데이터 전송 확인 및 저장·관리.",
    bullets: [
      "출장: 전국 병원 LIS 사용 교육·원격 안내, 장비–LIS 데이터 호환 확인 (LOG 분석·네트워크 확인·백업)",
      "사내: 장비·LIS 코드 검토, 사용자 문의·요구사항 접수",
    ],
    stack: ["Visual Basic 6.0"],
  },
] as const;

export const EDUCATION = [
  { school: "영남대학교", info: "중어중문학과 학사 졸업", period: "2013.03 – 2020.02" },
  {
    school: "대구 중앙 직업전문학교",
    info: "응용 SW 엔지니어링 Java 과정 수료",
    period: "2022.02 – 2022.09",
    desc: "JAVA와 Spring 활용 통합 시스템 구축 개발자 양성 과정 — 자바 기초 학습 및 웹 쇼핑몰 개인 프로젝트 진행",
  },
  {
    school: "제로베이스 백엔드 스쿨 15기",
    info: "백엔드 기본·프레임워크 심화 과정 수료",
    period: "2023.04 – 2024.01",
    desc: "백엔드 기본 학습 및 프레임워크 심화 과정, 프론트엔드와 협업 경험",
  },
] as const;

export const PROJECTS = [
  {
    title: "Intelligent HR Agent",
    type: "개인 프로젝트 | 2025",
    desc: "OCR & RAG 기반 지능형 HR 문서 분석 에이전트. 멀티 포맷 PDF/이미지 OCR 파이프라인 구축, RAG Chunking 전략 최적화로 검색 정확도·속도 개선, FastAPI 기반 RESTful API 서버 설계.",
    metrics: ["OCR 정확도 95%", "추론 속도 +40%", "비용 -60%"],
    stack: ["Python", "LangChain", "GPT-4", "Tesseract OCR", "FastAPI", "ChromaDB"],
  },
  {
    title: "AIFIX ESG Supply Chain AI",
    type: "팀 프로젝트 (AI 파트 리드) | 2025",
    desc: "뉴스·보고서 크롤링 → NLP 분석 → 리스크 스코어링 파이프라인. 멀티 에이전트 아키텍처(분석-판단-보고 자동화) 설계, 실시간 ESG 대시보드 개발, AI 파트 팀 리딩.",
    metrics: ["리스크 탐지 92%", "자동화율 85%", "분석 시간 -70%"],
    stack: ["Python", "LangChain", "React", "FastAPI", "PostgreSQL", "Docker"],
  },
] as const;

export const GROWTH_JOURNEY = [
  { emoji: "📚", year: "2013–2020", label: "영남대학교", sub: "중어중문학과" },
  { emoji: "📱", year: "2022", label: "화산시스템", sub: "의료IT Backend" },
  { emoji: "⚙", year: "2023–24", label: "제로베이스", sub: "Backend School" },
  { emoji: "🤖", year: "2025–", label: "AI Developer", sub: "Full-Stack AI" },
] as const;

export const ABOUT_CARDS = [
  {
    title: "성능 최적화에 집중하는 개발자",
    text: "더 빠르고, 더 효율적인 방법을 찾는 과정이 즐겁습니다. 백엔드에서 AI까지 풀스택 시스템을 설계하며 성능 병목을 추적하고 해결하는 데 몰입해왔습니다. OCR 정확도 95%, 추론 속도 40% 개선, 인프라 비용 60% 절감이라는 측정 가능한 성과를 달성했습니다. 비전공 출신으로 의료 IT에서 기본기를 다진 뒤, LangChain·RAG·프롬프트 엔지니어링을 중심으로 AI/ML 역량을 확장하고 있습니다.",
  },
  {
    title: "협업으로 함께 성장하는 개발자",
    text: '필리핀 해외 자원봉사(6개월)와 YMCA 국제개발협력팀 활동을 통해 다양한 배경의 사람들과 협력하는 방법을 배웠습니다. 팀원이 이해할 수 있는 기술 문서 작성, 코드 리뷰를 통한 지식 공유를 중요하게 생각합니다. AIFIX에서 AI 파트를 리딩하며 리스크 탐지 92%, 자동화율 85%를 달성했습니다. "혼자 가면 빨리, 함께 가면 멀리."',
  },
] as const;

/** 편집용 초기 데이터 타입 */
export type EditableBasic = {
  name: string;
  nameEn: string;
  title: string;
  email: string;
  github: string;
  blog: string;
  phone: string;
  location: string;
  tagline: string;
};
export type EditableIntro = string;
export type EditableAwards = string[];
export type EditableNonDevelop = { period: string; role: string }[];
export type EditableSkillGroup = { title: string; tags: string[]; hot: number[] };
export type EditableExperience = { company: string; role: string; period: string; bullets: string[]; desc?: string; stack?: string[] };
export type EditableEducation = { school: string; info: string; period: string; desc?: string };
export type EditableProject = { title: string; type: string; desc: string; metrics: string[]; stack: string[] };
export type EditableGrowth = { emoji: string; year: string; label: string; sub: string };
export type EditableAboutCard = { title: string; text: string };

export type EditableResumeData = {
  basic: EditableBasic;
  intro: EditableIntro;
  awards: EditableAwards;
  nonDevelopExperience: EditableNonDevelop;
  skillGroups: EditableSkillGroup[];
  experience: EditableExperience[];
  education: EditableEducation[];
  projects: EditableProject[];
  growthJourney: EditableGrowth[];
  aboutCards: EditableAboutCard[];
};

/** 화면 인라인 편집용 초기 데이터 (복사본 반환) */
export function getEditableInitialData(): EditableResumeData {
  return {
    basic: { ...RESUME_BASIC },
    intro: INTRO,
    awards: [...AWARDS],
    nonDevelopExperience: NON_DEVELOP_EXPERIENCE.map((item) => ({ period: item.period, role: item.role })),
    skillGroups: SKILL_GROUPS.map((g) => ({ title: g.title, tags: [...g.tags], hot: [...g.hot] })),
    experience: EXPERIENCE.map((e) => ({
      company: e.company,
      role: e.role,
      period: e.period,
      bullets: [...e.bullets],
      ...("desc" in e && e.desc && { desc: e.desc }),
      ...("stack" in e && e.stack && { stack: [...e.stack] }),
    })),
    education: EDUCATION.map((e) => ({
      school: e.school,
      info: e.info,
      period: e.period,
      ...("desc" in e && e.desc && { desc: e.desc }),
    })),
    projects: PROJECTS.map((p) => ({ title: p.title, type: p.type, desc: p.desc, metrics: [...p.metrics], stack: [...p.stack] })),
    growthJourney: GROWTH_JOURNEY.map((item) => ({ ...item })),
    aboutCards: ABOUT_CARDS.map((c) => ({ title: c.title, text: c.text })),
  };
}
