"use client";

import { useState, useEffect } from "react";
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { fetchEmployeesPaginated } from "@/modules/core/services";
import { getAverageSuccessDna } from "@/modules/shared/utils/employeeAggregates";
import type { Employee, SuccessDNA } from "@/modules/shared/types";
import { DNA_DIMENSION_COLORS } from "@/modules/shared/constants/dnaColors";

const DIMENSION_LABELS: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

const DIMENSIONS: (keyof SuccessDNA)[] = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
];

function toChartData(candidate: SuccessDNA, benchmark?: SuccessDNA) {
  return DIMENSIONS.map((key) => ({
    dimension: DIMENSION_LABELS[key],
    지원자: candidate[key] ?? 0,
    기존직원평균: benchmark?.[key] ?? 0,
  }));
}

interface NewHireCompareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** 비교할 신입 지원자 (successDna 필수) */
  candidate: Employee | null;
}

export function NewHireCompareDialog({
  open,
  onOpenChange,
  candidate,
}: NewHireCompareDialogProps) {
  const [benchmark, setBenchmark] = useState<SuccessDNA | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !candidate?.successDna) {
      setBenchmark(null);
      return;
    }
    setLoading(true);
    fetchEmployeesPaginated({ page: 1, pageSize: 100, employmentType: "regular" })
      .then(({ items }) => {
        const avg = getAverageSuccessDna(items ?? []);
        setBenchmark(avg);
      })
      .catch(() => setBenchmark(null))
      .finally(() => setLoading(false));
  }, [open, candidate?.id]);

  const candidateDna = candidate?.successDna as SuccessDNA | undefined;
  const compareDna = benchmark ?? undefined;
  const chartData = candidateDna ? toChartData(candidateDna, compareDna) : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {candidate?.name ?? "지원자"} · 기존 직원과 역량 비교
          </DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">
          지원자 Success DNA를 기존 직원 평균과 비교합니다. (실제 DB 데이터만 사용)
        </p>
        {loading ? (
          <div className="flex h-[320px] items-center justify-center rounded-lg border border-border bg-muted/20 text-sm text-muted-foreground">
            기존 직원 데이터 불러오는 중…
          </div>
        ) : candidateDna && compareDna && chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={chartData} margin={{ top: 24, right: 24, bottom: 24, left: 24 }}>
              <PolarGrid stroke="hsl(var(--border))" strokeOpacity={0.5} strokeDasharray="3 3" />
              <PolarAngleAxis
                dataKey="dimension"
                tick={({ payload, x, y }: { payload?: { value?: string }; x?: number | string; y?: number | string }) => {
                  const label = payload?.value ?? "";
                  const key = DIMENSIONS.find((k) => DIMENSION_LABELS[k] === label);
                  const fill = key ? DNA_DIMENSION_COLORS[key] : "hsl(var(--foreground))";
                  return (
                    <g transform={`translate(${Number(x ?? 0)},${Number(y ?? 0)})`}>
                      <text textAnchor="middle" fill={fill} fontSize={12} fontWeight={500}>
                        {label}
                      </text>
                    </g>
                  );
                }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
              />
              <Radar
                name="지원자"
                dataKey="지원자"
                stroke="hsl(var(--primary))"
                fill="hsl(var(--primary))"
                fillOpacity={0.35}
                strokeWidth={2}
              />
              <Radar
                name="기존 직원 평균"
                dataKey="기존직원평균"
                stroke="hsl(var(--muted-foreground))"
                fill="hsl(var(--muted-foreground))"
                fillOpacity={0.12}
                strokeWidth={1.5}
                strokeDasharray="4 4"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "var(--radius)",
                }}
                formatter={(value?: number, name?: string) => [`${value ?? 0}점`, name ?? ""]}
                labelFormatter={(label) => `역량: ${label}`}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-[200px] items-center justify-center rounded-lg border border-border bg-muted/20 text-sm text-muted-foreground">
            지원자 또는 기존 직원의 Success DNA 데이터가 부족합니다.
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
