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
  const map: Record<string, number> = { male: 0, female: 0, other: 0, undisclosed: 0 };
  employees.forEach((e) => {
    const raw = String(e.gender ?? "").trim().toLowerCase();
    const g =
      raw === "male" || raw === "남" ? "male"
      : raw === "female" || raw === "여" ? "female"
      : raw === "other" || raw === "기타" ? "other"
      : "undisclosed";
    map[g] = (map[g] ?? 0) + 1;
  });
  return ["male", "female", "other", "undisclosed"].map((key) => ({
    name: GENDER_LABELS[key] ?? key,
    value: map[key] ?? 0,
  }));
}

/** 연령대 분포 (20대/30대/40대/50대 이상, BarChart용). age 우선, 없으면 ageBand 사용 */
export function getAgeGroupDistribution(employees: Employee[]): AgeGroupDistributionItem[] {
  const map: Record<string, number> = { "20대": 0, "30대": 0, "40대": 0, "50대 이상": 0, "미기입": 0 };
  employees.forEach((e) => {
    const group = e.age != null && e.age > 0 ? toAgeGroupFromAge(e.age) : toAgeGroup(e.ageBand ?? "");
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
    const dept = (e.department || "").trim() || "미기입";
    if (!deptMap[dept]) deptMap[dept] = {};
    deptMap[dept][emp] = (deptMap[dept][emp] ?? 0) + 1;
  });
  const rows = Object.entries(deptMap).map(([department, counts]) => {
    const 총인원 = Object.values(counts).reduce((a, b) => a + b, 0);
    const regular = counts.regular ?? 0;
    return { department, 총인원, regular };
  });

  // 시각화 규칙: 상위 7개 부서 + 기타(나머지/단건 부서 포함)
  const topN = 7;
  const sorted = rows.sort((a, b) => b.총인원 - a.총인원 || a.department.localeCompare(b.department));
  const singles = sorted.filter((r) => r.총인원 <= 1);
  const major = sorted.filter((r) => r.총인원 > 1);
  const top = major.slice(0, topN);
  const rest = [...major.slice(topN), ...singles];

  const result: DepartmentHeadcountItem[] = top.map((r) => ({
    department: r.department,
    총인원: r.총인원,
    정규직비율: r.총인원 > 0 ? Math.round((r.regular / r.총인원) * 100) : 0,
  }));

  const restTotal = rest.reduce((s, r) => s + r.총인원, 0);
  if (restTotal > 0) {
    const restRegular = rest.reduce((s, r) => s + r.regular, 0);
    result.push({
      department: "기타",
      총인원: restTotal,
      정규직비율: Math.round((restRegular / restTotal) * 100),
    });
  }
  return result;
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
