/**
 * 비정형 행동 데이터 분석 (회의록·메신저 텍스트 → Success DNA 5대 역량 키워드 추출 및 점수화)
 */

import type { BehavioralSourceItem, SuccessDNA } from "@/modules/shared/types";

/** 기존 DNA(이력/평가)와 비정형 분석 결과를 합칠 때 기존 점수에 부여하는 가중치 (0~1) */
export const EXISTING_DNA_WEIGHT = 0.7;
/** 비정형 분석(회의록·이메일·슬랙 등) 결과에 부여하는 가중치 (0~1). EXISTING_DNA_WEIGHT + BEHAVIORAL_DNA_WEIGHT = 1 */
export const BEHAVIORAL_DNA_WEIGHT = 0.3;

/** 비정형 데이터 입력: 단순 텍스트 또는 출처별 구조(이메일·슬랙 연동 확장용) */
export type BehavioralDataInput =
  | string
  | { source: "meeting" | "email" | "slack"; content: string };

const SOURCE_LABELS: Record<"meeting" | "email" | "slack", string> = {
  meeting: "회의록",
  email: "이메일",
  slack: "슬랙",
};

/** 역량별 키워드 (한글·영어). 키워드 등장 빈도·강도에 따라 가중치 부여 */
const DIMENSION_KEYWORDS: Record<keyof SuccessDNA, { keyword: string[]; weight: number }[]> = [
  {
    leadership: [
      { keyword: ["리드", "주도", "방향", "결정", "팀장", "리더", "lead", "decision", "주도적"], weight: 12 },
      { keyword: ["제안", "의견", "제시", "제안하다", "suggest", "propose"], weight: 8 },
      { keyword: ["조율", "총괄", "coordinate", "oversee"], weight: 10 },
    ],
  },
  {
    technical: [
      { keyword: ["개발", "코드", "기술", "시스템", "개선", "develop", "technical", "system"], weight: 12 },
      { keyword: ["분석", "데이터", "검증", "analyze", "data", "verify"], weight: 8 },
      { keyword: ["설계", "구현", "design", "implement"], weight: 10 },
    ],
  },
  {
    creativity: [
      { keyword: ["아이디어", "창의", "혁신", "새로운", "idea", "creative", "innovative", "new"], weight: 12 },
      { keyword: ["개선안", "대안", "발상", "alternative", "improvement"], weight: 8 },
      { keyword: ["디자인", "설계", "design"], weight: 6 },
    ],
  },
  {
    collaboration: [
      { keyword: ["협업", "함께", "공유", "협력", "collaborate", "together", "share", "team"], weight: 12 },
      { keyword: ["논의", "의견", "합의", "discuss", "agree", "consensus"], weight: 8 },
      { keyword: ["지원", "도움", "support", "help"], weight: 6 },
    ],
  },
  {
    adaptability: [
      { keyword: ["적응", "변화", "유연", "대응", "adapt", "change", "flexible", "response"], weight: 12 },
      { keyword: ["학습", "습득", "배움", "learn", "acquire"], weight: 8 },
      { keyword: ["전환", "조정", "transition", "adjust"], weight: 8 },
    ],
  },
].reduce((acc, cur) => ({ ...acc, ...cur }), {} as Record<keyof SuccessDNA, { keyword: string[]; weight: number }[]>);

const BASE_SCORE = 50;
const MAX_BOOST = 50;

/**
 * 분석(점수 계산)용으로만 사용할 텍스트 정제.
 * 원문은 저장·표시 시 그대로 두고, 타임스탬프·화자 태그 등은 제거해 키워드 매칭 노이즈를 줄임.
 */
function getTextForAnalysis(raw: string): string {
  if (!raw?.trim()) return "";
  return (
    raw
      // [00:00:00], [00:01:23] 등 타임스탬프 제거
      .replace(/\[\d{1,2}:\d{2}(?::\d{2})?\]/g, " ")
      // 화자·발표자 라벨 제거 (앞부분만, 대화 내용은 유지)
      .replace(/^(Speaker|화자|발표자)\s*\d*:?\s*/gim, " ")
      .replace(/^\d+\.\s*/gm, " ")
      .trim()
  );
}

/** 텍스트에서 특정 역량 점수 계산 (키워드 등장 기반) */
function scoreDimension(text: string, dimension: keyof SuccessDNA): number {
  const lower = text.toLowerCase();
  const items = DIMENSION_KEYWORDS[dimension];
  if (!items) return BASE_SCORE;
  let score = 0;
  for (const { keyword, weight } of items) {
    for (const kw of keyword) {
      const count = (lower.match(new RegExp(kw.toLowerCase(), "g")) ?? []).length;
      score += Math.min(count * weight, 25);
    }
  }
  const capped = Math.min(MAX_BOOST, score);
  return Math.max(0, Math.min(100, BASE_SCORE + capped));
}

export interface BehavioralAnalysisResult {
  /** 5대 역량 점수 (0–100) */
  dna: SuccessDNA;
  /** 데이터 출처 설명 (UI 라벨용) */
  source: string;
  /** 분석에 사용된 원문 목록 — UI에서 내용 직접 확인용 */
  sourceItems?: BehavioralSourceItem[];
}

/**
 * 기존 DNA와 비정형 분석 결과를 가중 평균으로 합침.
 * chartDna = (기존 * EXISTING_DNA_WEIGHT) + (비정형 * BEHAVIORAL_DNA_WEIGHT)
 */
export function mergeDnaWithWeights(
  existing: SuccessDNA,
  behavioral: SuccessDNA
): SuccessDNA {
  const keys: (keyof SuccessDNA)[] = [
    "leadership",
    "technical",
    "creativity",
    "collaboration",
    "adaptability",
  ];
  const out = { ...existing };
  for (const k of keys) {
    out[k] = Math.round(
      existing[k] * EXISTING_DNA_WEIGHT + behavioral[k] * BEHAVIORAL_DNA_WEIGHT
    );
    out[k] = Math.max(0, Math.min(100, out[k]));
  }
  return out;
}

function normalizeInput(input: BehavioralDataInput): { content: string; sourceLabel: string } {
  if (typeof input === "string") {
    return { content: input, sourceLabel: "회의록" };
  }
  const content = input.content?.trim() ?? "";
  const sourceLabel = SOURCE_LABELS[input.source];
  return { content, sourceLabel };
}

/**
 * 회의록(Transcript)·이메일·슬랙 등 텍스트를 입력받아 Success DNA 5대 역량 키워드를 추출하고 점수화.
 * 인자: 문자열(기존 호환) 또는 { source: 'meeting' | 'email' | 'slack', content } 로 출처 확장 가능.
 * 실제 서비스에서는 NLP/LLM API로 대체 가능.
 */
export function analyzeBehavioralData(
  input: BehavioralDataInput
): BehavioralAnalysisResult {
  const { content: rawContent, sourceLabel } = normalizeInput(input);
  if (!rawContent) {
    return {
      dna: {
        leadership: BASE_SCORE,
        technical: BASE_SCORE,
        creativity: BASE_SCORE,
        collaboration: BASE_SCORE,
        adaptability: BASE_SCORE,
      },
      source: "분석할 텍스트가 없습니다.",
    };
  }

  const textForAnalysis = getTextForAnalysis(rawContent);
  const dna: SuccessDNA = {
    leadership: scoreDimension(textForAnalysis, "leadership"),
    technical: scoreDimension(textForAnalysis, "technical"),
    creativity: scoreDimension(textForAnalysis, "creativity"),
    collaboration: scoreDimension(textForAnalysis, "collaboration"),
    adaptability: scoreDimension(textForAnalysis, "adaptability"),
  };

  return {
    dna,
    source: `최근 ${sourceLabel} 기반 분석됨`,
  };
}

/**
 * 여러 텍스트(또는 출처별 입력)를 합쳐 한 번에 분석.
 * 각 항목은 string 또는 { source, content }.
 * 반환값의 sourceItems에 원문 목록이 담겨 UI에서 회의록/이메일/슬랙 내용을 직접 보여줄 수 있음.
 */
export function analyzeBehavioralDataFromMultiple(
  inputs: BehavioralDataInput[]
): BehavioralAnalysisResult {
  const parts: string[] = [];
  const sourceCounts: Record<string, number> = { meeting: 0, email: 0, slack: 0 };
  const sourceItems: BehavioralSourceItem[] = [];

  for (let i = 0; i < inputs.length; i++) {
    const raw = inputs[i];
    if (typeof raw === "string") {
      const originalContent = raw.trim();
      const contentForScoring = getTextForAnalysis(originalContent);
      if (contentForScoring) parts.push(contentForScoring);
      sourceCounts.meeting += 1;
      sourceItems.push({
        kind: "meeting",
        title: `회의록 ${i + 1}`,
        content: originalContent || "(내용 없음)",
      });
    } else {
      const originalContent = raw.content?.trim() ?? "";
      const contentForScoring = getTextForAnalysis(originalContent);
      if (contentForScoring) parts.push(contentForScoring);
      sourceCounts[raw.source] += 1;
      sourceItems.push({
        kind: raw.source,
        title: `${SOURCE_LABELS[raw.source]} ${i + 1}`,
        content: originalContent || "(내용 없음)",
      });
    }
  }

  const combined = parts.join("\n\n");
  const result = analyzeBehavioralData(combined);
  result.sourceItems = sourceItems;

  const labels: string[] = [];
  if (sourceCounts.meeting) labels.push(`${sourceCounts.meeting}개 ${SOURCE_LABELS.meeting}`);
  if (sourceCounts.email) labels.push(`${sourceCounts.email}개 ${SOURCE_LABELS.email}`);
  if (sourceCounts.slack) labels.push(`${sourceCounts.slack}개 ${SOURCE_LABELS.slack}`);
  if (labels.length > 0) {
    result.source = `최근 ${labels.join(", ")} 기반 분석됨`;
  }
  return result;
}
