/**
 * Employee[] → 차트/대시보드용 집계 데이터.
 * Core(ISOComplianceDashboard), Overview(PeopleCompositionCharts) 등에서 공통 사용.
 */
import type { Employee } from "@/modules/shared/types";
import { GENDER_LABELS, EMPLOYMENT_LABELS, AGE_GROUP_ORDER, toAgeGroup } from "@/modules/shared/constants/labels";

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

/** 연령대 분포 (20대/30대/40대/50대 이상, BarChart용) */
export function getAgeGroupDistribution(employees: Employee[]): AgeGroupDistributionItem[] {
  const map: Record<string, number> = { "20대": 0, "30대": 0, "40대": 0, "50대 이상": 0 };
  employees.forEach((e) => {
    const group = toAgeGroup(e.ageBand ?? "30-39");
    map[group] = (map[group] ?? 0) + 1;
  });
  return AGE_GROUP_ORDER.map((label) => ({
    name: label,
    인원: map[label] ?? 0,
  }));
}

/** 부서별 총인원 + 정규직 비율 (ComposedChart 또는 Bar 변환용) */
export function getDepartmentHeadcount(employees: Employee[]): DepartmentHeadcountItem[] {
  const deptMap: Record<string, { regular: number; contract: number; part_time: number; intern: number }> = {};
  employees.forEach((e) => {
    const emp = e.employmentType ?? "regular";
    if (!deptMap[e.department]) {
      deptMap[e.department] = { regular: 0, contract: 0, part_time: 0, intern: 0 };
    }
    deptMap[e.department][emp] = (deptMap[e.department][emp] ?? 0) + 1;
  });
  return Object.entries(deptMap).map(([department, counts]) => {
    const 총인원 = counts.regular + counts.contract + counts.part_time + counts.intern;
    const 정규직비율 = 총인원 > 0 ? Math.round((counts.regular / 총인원) * 100) : 0;
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
