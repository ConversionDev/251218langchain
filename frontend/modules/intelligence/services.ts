import type { Employee, SuccessDNA } from "@/modules/shared/types";
import { getIfrsMetricsView } from "@/modules/shared/utils/disclosureMetrics";
import type { IntelligenceEmployee, DNAGrowthPoint, DNATrajectoryPoint } from "./types";

/** 엑사원 직무 전환 분석 요청용: 직원 데이터를 담은 메시지와 시스템 프롬프트 */
export function buildTransitionAnalysisPrompt(employee: Employee): {
  message: string;
  system_prompt: string;
} {
  const dna = employee.successDna;
  const ifrs = getIfrsMetricsView(employee.disclosureMetrics);
  const parts = [
    `직원: ${employee.name ?? "(이름 없음)"}`,
    `부서: ${employee.department ?? "-"}`,
    `직급: ${employee.jobTitle ?? "-"}`,
  ];
  if (dna) {
    parts.push(
      `Success DNA(0-100): 리더십 ${dna.leadership ?? 0}, 기술력 ${dna.technical ?? 0}, 창의성 ${dna.creativity ?? 0}, 협업 ${dna.collaboration ?? 0}, 적응력 ${dna.adaptability ?? 0}`
    );
  }
  if (ifrs) {
    parts.push(
      `전환 준비도(IFRS S2): ${ifrs.transitionReadyScore}점, 스킬 갭: ${ifrs.skillGap}점, 인적자본 ROI: ${ifrs.humanCapitalROI}`
    );
  }
  if (employee.trainingHours != null) {
    parts.push(`연간 교육훈련 시간: ${employee.trainingHours}시간`);
  }
  const dataBlock = parts.join("\n");
  const message = `다음 직원에 대한 직무 전환(산업·역할 전환) 분석을 요청합니다.\n\n${dataBlock}\n\n위 데이터를 바탕으로 직무 전환 분석을 한국어로 작성해 주세요.`;
  const system_prompt =
    "당신은 HR 인사이트 분석가입니다. 주어진 직원 데이터(Success DNA, 전환 준비도, 스킬 갭 등)만을 근거로 직무 전환 분석을 작성합니다. " +
    "다음 세 가지를 반드시 포함해 주세요: 1) 현재 상태 요약 2) 전환 제언 3) 배치 시 고려사항. " +
    "각 항목을 '1)', '2)', '3)'로 구분해 주세요. 추측이나 일반론이 아닌, 제공된 수치와 지표에 기반한 분석만 작성하세요.";
  return { message, system_prompt };
}

/** 엑사원 응답에서 1) 2) 3) 구간을 파싱. 없으면 전체를 currentState로 */
export function parseTransitionAnalysisResponse(text: string): {
  currentState: string;
  transitionRecommendation: string;
  riskNotice: string;
} {
  const t = text.trim();
  const one = /1\)\s*([\s\S]*?)(?=2\)|$)/i.exec(t);
  const two = /2\)\s*([\s\S]*?)(?=3\)|$)/i.exec(t);
  const three = /3\)\s*([\s\S]*?)$/i.exec(t);
  return {
    currentState: one?.[1]?.trim() ?? t,
    transitionRecommendation: two?.[1]?.trim() ?? "",
    riskNotice: three?.[1]?.trim() ?? "",
  };
}

const DIMENSION_LABELS: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

const DIMENSION_KEYS: (keyof SuccessDNA)[] = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
];

/** 5대 역량 요약: 종합 점수, 강점 Top2, 보완 1개. 역량 진단 UI용 */
export function getCapabilitySummary(dna: SuccessDNA | undefined): {
  overallScore: number;
  topDimensions: { key: keyof SuccessDNA; label: string; score: number }[];
  improveDimension: { key: keyof SuccessDNA; label: string; score: number } | null;
} | null {
  if (!dna) return null;
  const entries = DIMENSION_KEYS.map((key) => ({
    key,
    label: DIMENSION_LABELS[key],
    score: (dna[key] as number) ?? 0,
  }));
  const sorted = [...entries].sort((a, b) => b.score - a.score);
  const sum = entries.reduce((s, e) => s + e.score, 0);
  const overallScore = Math.round(sum / DIMENSION_KEYS.length);
  return {
    overallScore,
    topDimensions: sorted.slice(0, 2),
    improveDimension: sorted.length > 0 ? sorted[sorted.length - 1]! : null,
  };
}

/** 5대 역량 (라벨 — 기술력=technical) */
const DNA_DIMENSIONS: { dimension: keyof SuccessDNA; label: string }[] = [
  { dimension: "leadership", label: "리더십" },
  { dimension: "technical", label: "기술력" },
  { dimension: "creativity", label: "창의성" },
  { dimension: "collaboration", label: "협업" },
  { dimension: "adaptability", label: "적응력" },
];

/** DNA 성장 이력(초기 vs 현재): 초기=이력서만 산출(resume.baselineSuccessDna), 현재=이력서+성과. 둘 다 있을 때만. */
export function getDNAGrowthHistory(employee: Employee): DNAGrowthPoint[] {
  const current = employee.successDna;
  const baseline = employee.resume?.baselineSuccessDna;
  if (!current || !baseline) return [];
  return DNA_DIMENSIONS.map((d) => {
    const past = baseline[d.dimension] ?? 0;
    const cur = current[d.dimension] ?? 0;
    return {
      dimension: d.dimension,
      label: d.label,
      pastYear: past,
      current: cur,
      growthPct: past > 0 ? Math.round(((cur - past) / past) * 100) : 0,
    };
  });
}

/** DNA 성장 궤적(2지점): 초기 → 현재. 시계열 대신 초기 이력서 vs 현재(이력서+성과) 2점. */
export function getDNAGrowthTrajectory(employee: Employee): DNATrajectoryPoint[] {
  const current = employee.successDna;
  const baseline = employee.resume?.baselineSuccessDna;
  if (!current || !baseline) return [];
  const point = (label: string, dna: SuccessDNA): DNATrajectoryPoint => ({
    month: label,
    monthLabel: label,
    leadership: dna.leadership ?? 0,
    technical: dna.technical ?? 0,
    creativity: dna.creativity ?? 0,
    collaboration: dna.collaboration ?? 0,
    adaptability: dna.adaptability ?? 0,
  });
  return [point("초기", baseline), point("현재", current)];
}

/** 하위호환: 기존 호출부 유지용. 더 이상 합성 데이터를 만들지 않음. */
export function getDNAGrowthTrajectoryFromDNA(dna: SuccessDNA): DNATrajectoryPoint[] {
  void dna;
  return [];
}

/** 직원 데이터로 IntelligenceEmployee 구성 (실데이터만 사용, 합성 추이 미생성) */
export function toIntelligenceEmployee(employee: Employee): IntelligenceEmployee {
  return {
    ...employee,
    transitionTrend: [],
  };
}

/** AI 전환 가능성 리포트 요약. Success DNA + 공시 지표(transitionReadyScore, skillGap) 연동. 실무 관점의 데이터 기반 문구만 사용. */
export function getTransitionReadinessSummary(employee: Employee) {
  const dna = employee.successDna;
  const ifrs = getIfrsMetricsView(employee.disclosureMetrics);
  const adaptability = dna?.adaptability ?? 0;
  const technical = dna?.technical ?? 0;
  const leadership = dna?.leadership ?? 0;
  const collaboration = dna?.collaboration ?? 0;
  const creativity = dna?.creativity ?? 0;

  const transitionScore = ifrs?.transitionReadyScore ?? null;
  const skillGap = ifrs?.skillGap ?? null;
  const hasDisclosureMetrics = transitionScore != null || skillGap != null;

  const probabilityFromDna = adaptability >= 80 ? 85 : Math.min(79, 50 + Math.round(adaptability * 0.4));
  const transitionProbability = hasDisclosureMetrics && transitionScore != null
    ? Math.round((transitionScore * 0.6 + probabilityFromDna * 0.4))
    : probabilityFromDna;
  const strengthDimension: keyof SuccessDNA = "adaptability";

  // 현재 상태: 보유 데이터만으로 서술. 역할·점수·지표만 언급.
  const role = [employee.jobTitle, employee.department].filter(Boolean).join(" · ") || "역할 미지정";
  const dnaParts: string[] = [];
  if (adaptability > 0) dnaParts.push(`적응력 ${adaptability}점`);
  if (technical > 0) dnaParts.push(`기술력 ${technical}점`);
  if (leadership > 0) dnaParts.push(`리더십 ${leadership}점`);
  if (collaboration > 0) dnaParts.push(`협업 ${collaboration}점`);
  if (creativity > 0) dnaParts.push(`창의성 ${creativity}점`);
  const dnaSummary = dnaParts.length > 0 ? dnaParts.join(", ") : "역량 데이터 없음";

  let currentState: string;
  if (hasDisclosureMetrics && transitionScore != null) {
    currentState = `${role}. 전환 준비도 ${transitionScore}점, 스킬 갭 ${skillGap ?? 0}점. 역량: ${dnaSummary}. 전환 가능성 산출에 활용된 수치입니다.`;
  } else if (dnaParts.length > 0) {
    currentState = `${role}. 역량: ${dnaSummary}. 전환 준비도·스킬 갭 등 공시 지표가 있으면 전환 가능성이 더 정교하게 산출됩니다.`;
  } else {
    currentState = "역량·전환 준비도 데이터가 없어 전환 가능성만 단순 산출된 상태입니다. 역량 진단 또는 공시 지표 입력 후 「직무 전환 분석 요청」을 권장합니다.";
  }

  // 전환 제언: 스킬 갭·강점 역량 기반으로만 짧게. 특정 산업/직무 하드코딩 없음.
  let transitionRecommendation: string;
  if (skillGap != null && skillGap > 0) {
    transitionRecommendation = `스킬 갭 ${skillGap}점. 전환 시 보완 교육·OJT 계획 수립을 권장합니다.`;
  } else if (technical >= 70 && adaptability >= 70) {
    transitionRecommendation = "기술력·적응력이 양호해 신규 역할 전환 시 이수 기간 단축이 기대됩니다. 구체적 직무·산업 제언은 「직무 전환 분석 요청」으로 생성하세요.";
  } else {
    transitionRecommendation = "전환 방향·필요 역량은 직무·산업별로 상이합니다. 「직무 전환 분석 요청」을 실행하면 해당 직원 데이터 기반 맞춤 제언을 생성합니다.";
  }

  // 배치 시 고려사항: 리더십 수치만으로 팀 리드 vs SME 구분. 실무 용어로.
  const riskNotice =
    leadership >= 75
      ? `리더십 ${leadership}점. 전환 후 팀 리드 또는 전문가(SME) 역할 배치 모두 검토 가능합니다.`
      : leadership > 0
        ? `리더십 ${leadership}점. 전환 초기에는 팀 리드보다 전문가(SME) 역할로 배치한 뒤, 역량 확보 시 리드 역할을 검토하는 것을 권장합니다.`
        : "리더십 데이터가 없습니다. 배치 검토 시 역량 평가 또는 「직무 전환 분석 요청」 결과를 참고하세요.";

  const narrative = [currentState, transitionRecommendation, riskNotice].join(" ");

  return {
    transitionProbability: Math.min(100, Math.max(0, transitionProbability)),
    strengthDimension,
    narrative,
    currentState,
    transitionRecommendation,
    riskNotice,
    transitionReadyScore: transitionScore ?? undefined,
    skillGap: skillGap ?? undefined,
  };
}
