import type { Employee, SuccessDNA, IfrsMetrics } from "@/modules/shared/types";
import type { IntelligenceEmployee, TransitionTrendPoint, HighPerformerAverage, DNAGrowthPoint, DNATrajectoryPoint } from "./types";

const DIMENSION_LABELS: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

/** 전환 준비도 추이: 최근 12개월 (과거 → 현재) */
function buildTransitionTrend(
  startScore: number,
  endScore: number,
  endYear: number,
  endMonth: number
): TransitionTrendPoint[] {
  const monthLabels = [
    "1월", "2월", "3월", "4월", "5월", "6월",
    "7월", "8월", "9월", "10월", "11월", "12월",
  ];
  const points: TransitionTrendPoint[] = [];
  for (let i = 0; i < 12; i++) {
    let m = endMonth - 11 + i;
    let y = endYear;
    while (m < 1) {
      m += 12;
      y -= 1;
    }
    const t = i / 11;
    const score = Math.round(startScore + (endScore - startScore) * t);
    points.push({
      month: `${y}-${String(m).padStart(2, "0")}`,
      year: y,
      monthLabel: `${y}년 ${monthLabels[m - 1]}`,
      transitionReadyScore: Math.max(0, Math.min(100, score)),
    });
  }
  return points;
}

/** 전사 고성과자 평균 Success DNA (비교용) */
export const HIGH_PERFORMER_AVERAGE: HighPerformerAverage = {
  leadership: 82,
  technical: 78,
  creativity: 80,
  collaboration: 85,
  adaptability: 84,
};

/** 현재 조회 대상 직원 1명 + 전환 추이 (Mock) */
const currentEmployeeSuccessDNA: SuccessDNA = {
  leadership: 72,
  technical: 75,
  creativity: 78,
  collaboration: 88,
  adaptability: 86,
};

const currentEmployeeIfrs: IfrsMetrics = {
  transitionReadyScore: 82,
  skillGap: 18,
  humanCapitalROI: 2.2,
};

const transitionTrendData = buildTransitionTrend(58, 82, 2024, 2);

const currentEmployeeBase: Employee = {
  id: "E001",
  name: "김민준",
  jobTitle: "선임 연구원",
  department: "R&D",
  email: "minjun.kim@company.com",
  joinedAt: "2020-03-01",
  successDna: currentEmployeeSuccessDNA,
  ifrsMetrics: currentEmployeeIfrs,
};

/** 1년 전 DNA (성장 서사용). 현재 대비 낮은 값으로 설정해 성장률 서사 시각화 */
function getPastYearDNA(current: SuccessDNA, employeeId: string): SuccessDNA {
  const seed = employeeId.split("").reduce((s, c) => s + c.charCodeAt(0), 0);
  return {
    leadership: Math.max(0, (current.leadership ?? 0) - 10 - (seed % 12)),
    technical: Math.max(0, (current.technical ?? 0) - 8 - (seed % 5)),
    creativity: Math.max(0, (current.creativity ?? 0) - 6 - (seed % 7)),
    collaboration: Math.max(0, (current.collaboration ?? 0) - 4 - (seed % 4)),
    adaptability: Math.max(0, (current.adaptability ?? 0) - 12 - (seed % 6)),
  };
}

/** DNA 성장 이력 (1년 전 vs 현재, 성장률 %) */
export function getDNAGrowthHistory(employee: Employee): DNAGrowthPoint[] {
  const dna = employee.successDna;
  if (!dna) return [];
  const past = getPastYearDNA(dna, employee.id);
  const dimensions = (["leadership", "technical", "creativity", "collaboration", "adaptability"] as const);
  return dimensions.map((dim) => {
    const cur = dna[dim] ?? 0;
    const p = past[dim] ?? 0;
    const growthPct = p > 0 ? Math.round(((cur - p) / p) * 100) : (cur > 0 ? 100 : 0);
    return {
      dimension: dim,
      label: DIMENSION_LABELS[dim],
      pastYear: p,
      current: cur,
      growthPct,
    };
  });
}

const MONTH_LABELS = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"];

/** 지난 12개월 역량 궤적 (월별 보간). Line Chart에서 '성장 궤적' 시각화용 */
export function getDNAGrowthTrajectory(employee: Employee): DNATrajectoryPoint[] {
  const dna = employee.successDna;
  if (!dna) return [];
  const past = getPastYearDNA(dna, employee.id);
  const dimensions = (["leadership", "technical", "creativity", "collaboration", "adaptability"] as const);
  const points: DNATrajectoryPoint[] = [];
  for (let i = 0; i < 12; i++) {
    const t = i / 11; // 0 → 1 (과거 → 현재)
    const monthIdx = i; // 0~11 → 1월~12월
    const year = 2023;
    const month = `${year}-${String(monthIdx + 1).padStart(2, "0")}`;
    const monthLabel = `${year}년 ${MONTH_LABELS[monthIdx]}`;
    const point: DNATrajectoryPoint = {
      month,
      monthLabel,
      leadership: 0,
      technical: 0,
      creativity: 0,
      collaboration: 0,
      adaptability: 0,
    };
    dimensions.forEach((dim) => {
      const pVal = past[dim] ?? 0;
      const cVal = dna[dim] ?? 0;
      point[dim] = Math.round(pVal + (cVal - pVal) * t);
    });
    points.push(point);
  }
  return points;
}

/** successDna만 있을 때 사용하는 12개월 궤적 (보간). 직원 id 없이도 차트 표시용 */
export function getDNAGrowthTrajectoryFromDNA(dna: SuccessDNA): DNATrajectoryPoint[] {
  const dimensions = (["leadership", "technical", "creativity", "collaboration", "adaptability"] as const);
  const past: SuccessDNA = {
    leadership: Math.max(0, (dna.leadership ?? 0) - 12),
    technical: Math.max(0, (dna.technical ?? 0) - 10),
    creativity: Math.max(0, (dna.creativity ?? 0) - 8),
    collaboration: Math.max(0, (dna.collaboration ?? 0) - 6),
    adaptability: Math.max(0, (dna.adaptability ?? 0) - 14),
  };
  const points: DNATrajectoryPoint[] = [];
  for (let i = 0; i < 12; i++) {
    const t = i / 11;
    const monthIdx = i;
    const year = 2023;
    const month = `${year}-${String(monthIdx + 1).padStart(2, "0")}`;
    const monthLabel = `${year}년 ${MONTH_LABELS[monthIdx]}`;
    const point: DNATrajectoryPoint = {
      month,
      monthLabel,
      leadership: 0,
      technical: 0,
      creativity: 0,
      collaboration: 0,
      adaptability: 0,
    };
    dimensions.forEach((dim) => {
      const pVal = past[dim] ?? 0;
      const cVal = dna[dim] ?? 0;
      point[dim] = Math.round(pVal + (cVal - pVal) * t);
    });
    points.push(point);
  }
  return points;
}

/** Intelligence 페이지용 직원 상세 Mock (전환 추이 포함) */
export function getIntelligenceEmployee(): IntelligenceEmployee {
  return {
    ...currentEmployeeBase,
    transitionTrend: transitionTrendData,
  };
}

/** 여러 직원 목록 (드롭다운 등용). 현재는 1명 반환 */
export function getIntelligenceEmployeeList(): IntelligenceEmployee[] {
  const trend2 = buildTransitionTrend(62, 78, 2024, 2);
  const list: IntelligenceEmployee[] = [
    {
      ...currentEmployeeBase,
      transitionTrend: transitionTrendData,
    },
    {
      id: "E002",
      name: "이서연",
      jobTitle: "마케팅 매니저",
      department: "마케팅",
      email: "seoyeon.lee@company.com",
      joinedAt: "2019-07-01",
      successDna: {
        leadership: 80,
        technical: 65,
        creativity: 88,
        collaboration: 82,
        adaptability: 72,
      },
      ifrsMetrics: {
        transitionReadyScore: 78,
        skillGap: 22,
        humanCapitalROI: 1.9,
      },
      transitionTrend: trend2,
    },
  ];
  return list;
}

/** AI 전환 가능성 리포트 요약 (Mock) */
export function getTransitionReadinessSummary(employee: Employee) {
  const dna = employee.successDna;
  const adaptability = dna?.adaptability ?? 0;
  const technical = dna?.technical ?? 0;
  const leadership = dna?.leadership ?? 0;
  const probability = adaptability >= 80 ? 85 : Math.min(79, 50 + Math.round(adaptability * 0.4));
  const strengthDimension: keyof SuccessDNA = "adaptability";

  const currentState =
    "대상자는 Adaptability(적응력) DNA가 상위 10% 고성과자 그룹과 유사한 패턴을 보임.";

  const transitionRecommendation =
    "IFRS S2 산업 전환 가이드라인에 비추어 볼 때, 현재의 Technical 역량을 Green Tech 분야로 전이(Transfer)할 경우 Skill Gap을 최단기간 내에 해소 가능할 것으로 예측됨.";

  const riskNotice =
    leadership >= 75
      ? "Leadership 수치가 벤치마크 수준으로, 전환 후 팀 리드 또는 SME 역할 모두 고려 가능함."
      : "단, Leadership 수치가 벤치마크 대비 낮아, 전환 공정의 팀 리드보다는 전문 기술 위원(Subject Matter Expert)으로서의 배치가 유리함.";

  const narrative = [currentState, transitionRecommendation, riskNotice].join(" ");

  return {
    transitionProbability: probability,
    strengthDimension,
    narrative,
    currentState,
    transitionRecommendation,
    riskNotice,
  };
}
