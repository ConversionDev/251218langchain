import type { Employee, SuccessDNA } from "@/modules/shared/types";
import type { PerformanceMetrics, ImpactDataPoint, DisclosureSummary } from "./types";

/** 전체 임직원 평균 지표 (selectedEmployee === null 시 사용) */
export function getAggregatePerformanceMetrics(employees: Employee[]): PerformanceMetrics | null {
  if (employees.length === 0) return null;
  let dnaSum = 0, trainingHours = 0, roiSum = 0, sustainSum = 0, perfSum = 0;
  employees.forEach((e) => {
    const m = getPerformanceMetrics(e);
    if (m) {
      dnaSum += m.dnaSum;
      trainingHours += m.trainingHours;
      roiSum += m.humanCapitalROI;
      sustainSum += m.sustainabilityImpact;
      perfSum += m.performanceIndex;
    }
  });
  const n = employees.length;
  return {
    dnaSum: Math.round(dnaSum / n),
    trainingHours: Math.round((trainingHours / n) * 10) / 10,
    virtualSalaryBase: VIRTUAL_SALARY_BASE,
    humanCapitalROI: Math.round((roiSum / n) * 100) / 100,
    sustainabilityImpact: Math.round(sustainSum / n),
    performanceIndex: Math.round(perfSum / n),
  };
}

/** 전체 임직원 평균 시계열: Q1~Q4 실제(막대), Q5~Q6 예측(라인) */
export function getAggregateImpactChartData(employees: Employee[]): ImpactDataPoint[] {
  if (employees.length === 0) {
    const periods = ["Q1", "Q2", "Q3", "Q4", "Q5(예측)", "Q6(예측)"];
    const past = [58, 62, 68, 72];
    const future = [72, 76, 78];
    return periods.map((p, i) => ({
      period: p,
      pastPerformance: i < 4 ? past[i] : 0,
      futureValue: i < 4 ? past[i] : future[i - 4],
    }));
  }
  const allPoints = employees.map((e) => getImpactChartData(e)).filter((arr) => arr.length > 0);
  if (allPoints.length === 0) return getAggregateImpactChartData([]);
  const periods = allPoints[0].map((_, i) => allPoints[0][i].period);
  const pastPerformance = periods.map((_, i) => {
    const vals = allPoints.map((arr) => arr[i]?.pastPerformance ?? 0).filter((v) => v > 0);
    return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
  });
  const futureValue = periods.map((_, i) => {
    const vals = allPoints.map((arr) => arr[i]?.futureValue ?? 0);
    return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
  });
  return periods.map((p, i) => ({
    period: p,
    pastPerformance: pastPerformance[i],
    futureValue: futureValue[i],
  }));
}

/** 전체 임직원 평균 공시 요약 */
export function getAggregateDisclosureSummary(employees: Employee[]): DisclosureSummary | null {
  if (employees.length === 0) return null;
  const m = getAggregatePerformanceMetrics(employees);
  if (!m) return null;
  return {
    narrative: `전체 ${employees.length}명 임직원 평균: Performance Index ${m.performanceIndex}점, Sustainability Impact ${m.sustainabilityImpact}점으로 산출되었으며, IFRS S1/S2 공시 요건에 부합하는 지표를 확보하였습니다.`,
    ifrsS1Summary:
      "본 인적 자본 공시는 IFRS S1 '지속가능성 관련 재무정보 공시'에 따른 일반 목적 재무제표 보완 정보로, 인력 구성·교육·성과 지표를 포함합니다.",
    ifrsS2Summary:
      "IFRS S2 '기후 관련 공시'에 부합하여, 산업 전환·Green 역량·적응력 기반 전환 기여도를 정량화하였습니다.",
  };
}

/** Success DNA 5개 역량 합산 (0~500) */
function sumDna(dna: SuccessDNA | undefined): number {
  if (!dna) return 0;
  return (
    (dna.leadership ?? 0) +
    (dna.technical ?? 0) +
    (dna.creativity ?? 0) +
    (dna.collaboration ?? 0) +
    (dna.adaptability ?? 0)
  );
}

/** 가상 연봉 상계치 (만 원 단위, ROI 분모용) */
const VIRTUAL_SALARY_BASE = 5000;

/**
 * 1. Human Capital ROI
 * (Success DNA 합산 * 교육 이수 시간) / 가상 연봉 상계치
 */
function calcHumanCapitalROI(
  dnaSum: number,
  trainingHours: number,
  salaryBase: number
): number {
  if (salaryBase <= 0) return 0;
  const raw = (dnaSum * Math.max(0, trainingHours)) / salaryBase;
  return Math.round(raw * 100) / 100;
}

/**
 * 2. Sustainability Impact (IFRS S2 기반)
 * 적응력(Adaptability) DNA를 활용한 산업 전환 기여도 (0~100)
 */
function calcSustainabilityImpact(employee: Employee): number {
  const adaptability = employee.successDna?.adaptability ?? 0;
  const transitionScore = employee.ifrsMetrics?.transitionReadyScore ?? 0;
  const contribution = (adaptability * 0.6 + transitionScore * 0.4);
  return Math.min(100, Math.round(contribution));
}

/**
 * 3. Performance Index
 * KPI 성과 60% + 미래 역량 40% 가중 합산 (0~100)
 */
function calcPerformanceIndex(employee: Employee): number {
  const ifrs = employee.ifrsMetrics;
  const kpi = (ifrs?.humanCapitalROI ?? 0) * 20 + (100 - (ifrs?.skillGap ?? 50)) * 0.5;
  const kpiNorm = Math.max(0, Math.min(100, kpi));
  const future = ifrs?.transitionReadyScore ?? 0;
  return Math.round(kpiNorm * 0.6 + future * 0.4);
}

/**
 * selectedEmployee 기반 통합 지표 계산
 */
export function getPerformanceMetrics(employee: Employee | null): PerformanceMetrics | null {
  if (!employee) return null;
  const dnaSum = sumDna(employee.successDna);
  const trainingHours = employee.trainingHours ?? 0;

  return {
    dnaSum,
    trainingHours,
    virtualSalaryBase: VIRTUAL_SALARY_BASE,
    humanCapitalROI: calcHumanCapitalROI(dnaSum, trainingHours, VIRTUAL_SALARY_BASE),
    sustainabilityImpact: calcSustainabilityImpact(employee),
    performanceIndex: calcPerformanceIndex(employee),
  };
}

/**
 * 과거 성과 + AI 예측 미래 가치 시계열 (ComposedChart용)
 */
export function getImpactChartData(employee: Employee | null): ImpactDataPoint[] {
  if (!employee) return [];
  const transitionScore = employee.ifrsMetrics?.transitionReadyScore ?? 50;
  const performanceIndex = calcPerformanceIndex(employee);

  const periods = ["Q1", "Q2", "Q3", "Q4", "Q5(예측)", "Q6(예측)"];
  const seed = employee.id.split("").reduce((s, c) => s + c.charCodeAt(0), 0);
  const r = (i: number) => ((seed * (i + 1)) % 11) - 5;
  const pastPerformance = [
    Math.max(0, performanceIndex - 15 + r(0)),
    Math.max(0, performanceIndex - 10 + r(1)),
    Math.max(0, performanceIndex - 5 + r(2)),
    performanceIndex,
  ];
  const futureValue = [
    performanceIndex,
    performanceIndex + (transitionScore - performanceIndex) * 0.25,
    performanceIndex + (transitionScore - performanceIndex) * 0.5,
    performanceIndex + (transitionScore - performanceIndex) * 0.75,
    transitionScore,
    Math.min(100, transitionScore + 5),
  ];

  return periods.map((period, i) => ({
    period,
    pastPerformance: i < 4 ? Math.round(pastPerformance[i]) : 0,
    futureValue: Math.round(futureValue[i]),
  }));
}

/**
 * IFRS S1/S2 가이드라인 인적 자본 공시 전문 + AI 요약
 */
export function getDisclosureSummary(employee: Employee | null): DisclosureSummary | null {
  if (!employee) return null;
  const name = employee.name;
  const metrics = getPerformanceMetrics(employee);
  const idx = metrics?.performanceIndex ?? 0;
  const impact = metrics?.sustainabilityImpact ?? 0;

  return {
    narrative: `${name} 직원의 인적 자본 가치는 Performance Index ${idx}점, Sustainability Impact ${impact}점으로 산출되었으며, IFRS S1/S2 공시 요건에 부합하는 지표를 확보하였습니다.`,
    ifrsS1Summary:
      "본 인적 자본 공시는 IFRS S1 '지속가능성 관련 재무정보 공시'에 따른 일반 목적 재무제표 보완 정보로, 인력 구성·교육·성과 지표를 포함합니다.",
    ifrsS2Summary:
      "IFRS S2 '기후 관련 공시'에 부합하여, 산업 전환·Green 역량·적응력 기반 전환 기여도를 정량화하였습니다.",
  };
}
