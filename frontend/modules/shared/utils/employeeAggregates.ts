/**
 * Employee[] → 차트/대시보드용 집계 데이터.
 * Core(ISOComplianceDashboard), Overview(PeopleCompositionCharts) 등에서 공통 사용.
 */
import type { Employee, SuccessDNA } from "@/modules/shared/types";
import { GENDER_LABELS, EMPLOYMENT_LABELS, AGE_GROUP_ORDER, toAgeGroup, toAgeGroupFromAge } from "@/modules/shared/constants/labels";

const ATS_STATUSES = ["pending", "screening", "rejected"] as const;

/** 신입(ATS)이 아닌 기존 직원인지. 총 인원·등록 직원 수에는 기존 직원만 포함. */
export function isRegularEmployee(e: Employee): boolean {
  if ((e.employmentType ?? "regular") === "new_hire") return false;
  const status = (e.status ?? "").trim();
  if (ATS_STATUSES.includes(status as (typeof ATS_STATUSES)[number])) return false;
  return true;
}

/** 기존 직원만 필터 (신입·ATS 후보 제외). */
export function getRegularEmployees(employees: Employee[]): Employee[] {
  return (employees ?? []).filter(isRegularEmployee);
}

export interface GenderDistributionItem {
  name: string;
  value: number;
}

export interface AgeGroupDistributionItem {
  name: string;
  인원: number;
}

export interface DepartmentHeadcountItem {
  department: string;
  총인원: number;
  정규직비율: number;
}

export interface EmploymentDistributionItem {
  name: string;
  value: number;
}

/** 성별 분포 (Pie/도넛용) */
export function getGenderDistribution(employees: Employee[]): GenderDistributionItem[] {
  const map: Record<string, number> = {};
  employees.forEach((e) => {
    const g = e.gender ?? "undisclosed";
    map[g] = (map[g] ?? 0) + 1;
  });
  return Object.entries(map).map(([key, value]) => ({
    name: GENDER_LABELS[key] ?? key,
    value,
  }));
}

/** 연령대 분포 (20대/30대/40대/50대 이상, BarChart용). age 우선, 없으면 ageBand 사용 */
export function getAgeGroupDistribution(employees: Employee[]): AgeGroupDistributionItem[] {
  const map: Record<string, number> = { "20대": 0, "30대": 0, "40대": 0, "50대 이상": 0 };
  employees.forEach((e) => {
    const group =
      e.age != null && e.age > 0
        ? toAgeGroupFromAge(e.age)
        : toAgeGroup(e.ageBand ?? "30-39");
    map[group] = (map[group] ?? 0) + 1;
  });
  return AGE_GROUP_ORDER.map((label) => ({
    name: label,
    인원: map[label] ?? 0,
  }));
}

/** 부서별 총인원 + 정규직 비율 (ComposedChart 또는 Bar 변환용) */
export function getDepartmentHeadcount(employees: Employee[]): DepartmentHeadcountItem[] {
  const deptMap: Record<string, Record<string, number>> = {};
  employees.forEach((e) => {
    const emp = e.employmentType ?? "regular";
    if (!deptMap[e.department]) deptMap[e.department] = {};
    deptMap[e.department][emp] = (deptMap[e.department][emp] ?? 0) + 1;
  });
  return Object.entries(deptMap).map(([department, counts]) => {
    const 총인원 = Object.values(counts).reduce((a, b) => a + b, 0);
    const 정규직비율 = 총인원 > 0 ? Math.round(((counts.regular ?? 0) / 총인원) * 100) : 0;
    return { department, 총인원, 정규직비율 };
  });
}

/** 고용형태 분포 (Pie/도넛용) */
export function getEmploymentDistribution(employees: Employee[]): EmploymentDistributionItem[] {
  const map: Record<string, number> = {};
  employees.forEach((e) => {
    const emp = e.employmentType ?? "regular";
    map[emp] = (map[emp] ?? 0) + 1;
  });
  return Object.entries(map).map(([key, value]) => ({
    name: EMPLOYMENT_LABELS[key] ?? key,
    value,
  }));
}

const DNA_KEYS: (keyof SuccessDNA)[] = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
];

/** Success DNA가 있는 직원들만 모아 평균 역량 계산. 없으면 null. */
export function getAverageSuccessDna(employees: Employee[]): SuccessDNA | null {
  const list = (employees ?? []).filter(
    (e): e is Employee & { successDna: SuccessDNA } =>
      !!e.successDna &&
      typeof e.successDna === "object" &&
      DNA_KEYS.every((k) => typeof (e.successDna as unknown as Record<string, unknown>)[k] === "number")
  );
  if (list.length === 0) return null;
  const sum: Record<keyof SuccessDNA, number> = {
    leadership: 0,
    technical: 0,
    creativity: 0,
    collaboration: 0,
    adaptability: 0,
  };
  list.forEach((e) => {
    DNA_KEYS.forEach((k) => {
      sum[k] += (e.successDna[k] as number) ?? 0;
    });
  });
  return {
    leadership: Math.round(sum.leadership / list.length),
    technical: Math.round(sum.technical / list.length),
    creativity: Math.round(sum.creativity / list.length),
    collaboration: Math.round(sum.collaboration / list.length),
    adaptability: Math.round(sum.adaptability / list.length),
  };
}
