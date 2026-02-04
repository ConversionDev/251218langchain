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
import type { SuccessDNA } from "@/modules/shared/types";
import { DNA_DIMENSION_COLORS } from "@/modules/shared/constants/dnaColors";
import { HIGH_PERFORMER_AVERAGE } from "../services";

const DIMENSION_LABELS: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

const LABEL_TO_KEY: Record<string, keyof SuccessDNA> = {
  리더십: "leadership",
  기술력: "technical",
  창의성: "creativity",
  협업: "collaboration",
  적응력: "adaptability",
};

const dimensions: (keyof SuccessDNA)[] = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
];

/** AI 분석 상세 문구 (호버 시 툴팁) */
function getRadarAIInsight(
  dimensionKey: keyof SuccessDNA,
  selfValue: number,
  avgValue: number,
  trainingHours?: number
): string {
  const pct = avgValue > 0 ? Math.round(((selfValue - avgValue) / avgValue) * 100) : 0;
  if (dimensionKey === "adaptability") {
    if (pct < 0 && (trainingHours ?? 0) < 40) {
      return "해당 직원의 최근 교육 이수 시간이 부족하여 전사 평균 대비 " + Math.abs(pct) + "% 낮게 산출됨.";
    }
    if (pct >= 0) return "적응력이 전사 평균 이상으로, IFRS S2 기후/산업 전환 역량에 유리함.";
  }
  if (dimensionKey === "leadership" && pct < 0) {
    return "리더십 수치가 벤치마크 대비 낮아, 전환 공정의 팀 리드보다는 전문 기술 위원(SME) 배치가 유리할 수 있음.";
  }
  if (pct > 0) return `전사 고성과자 평균 대비 ${pct}% 높게 산출됨.`;
  if (pct < 0) return `전사 고성과자 평균 대비 ${Math.abs(pct)}% 낮게 산출됨.`;
  return "전사 고성과자 평균과 유사한 수준입니다.";
}

function toChartData(self: SuccessDNA, highPerformer: SuccessDNA) {
  return dimensions.map((key) => ({
    dimension: DIMENSION_LABELS[key],
    self: self[key],
    전사고성과자평균: highPerformer[key],
  }));
}

interface DNARadarChartProps {
  /** 본인 Success DNA */
  data: SuccessDNA;
  /** 전사 고성과자 평균 (미제공 시 서비스 기본값 사용) */
  highPerformerAverage?: SuccessDNA;
  /** 교육 이수 시간 (AI 인사이트 툴팁용) */
  trainingHours?: number;
  /** 역량 축(레이블) 클릭 시 호출 (우측 성장 궤적 차트와 연동) */
  onDimensionClick?: (dimension: keyof SuccessDNA) => void;
  /** 현재 강조된 역량 (레이더 축 강조 표시용) */
  highlightedDimension?: keyof SuccessDNA | null;
}

function RadarTooltipContent({
  active,
  payload,
  label,
  trainingHours,
}: {
  active?: boolean;
  payload?: readonly { name: string; value: number; dataKey: string }[];
  label?: string | number;
  trainingHours?: number;
}) {
  const labelStr = label == null ? "" : String(label);
  if (!active || !payload?.length || !labelStr) return null;
  const selfPayload = payload.find((p) => p.dataKey === "self");
  const avgPayload = payload.find((p) => p.dataKey === "전사고성과자평균");
  const selfValue = selfPayload?.value ?? 0;
  const avgValue = avgPayload?.value ?? 0;
  const dimensionKey = LABEL_TO_KEY[labelStr as keyof typeof LABEL_TO_KEY];
  const insight = dimensionKey
    ? getRadarAIInsight(dimensionKey, selfValue, avgValue, trainingHours)
    : "";

  return (
    <div
      className="rounded-lg border px-4 py-3 shadow-lg"
      style={{
        backgroundColor: "hsl(var(--chart-tooltip-bg))",
        borderColor: "hsl(var(--chart-tooltip-border))",
      }}
    >
      <p className="font-medium text-foreground">{labelStr}</p>
      <p className="mt-1 text-sm text-muted-foreground">
        본인 <strong className="text-foreground">{selfValue}</strong>점 · 전사 고성과자 평균{" "}
        <strong className="text-foreground">{avgValue}</strong>점
        {avgValue > 0 && (
          <span className="ml-1">
            (갭 {selfValue - avgValue >= 0 ? "+" : ""}{selfValue - avgValue}점)
          </span>
        )}
      </p>
      {insight && (
        <p className="mt-2 border-t pt-2 text-xs text-muted-foreground" style={{ borderColor: "hsl(var(--chart-tooltip-border))" }}>
          AI 분석: {insight}
        </p>
      )}
    </div>
  );
}

export function DNARadarChart({
  data,
  highPerformerAverage,
  trainingHours,
  onDimensionClick,
  highlightedDimension,
}: DNARadarChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const chartData = toChartData(data, highPerformerAverage ?? HIGH_PERFORMER_AVERAGE);

  if (!mounted) {
    return (
      <div className="h-[360px] w-full animate-pulse rounded-lg bg-muted/50" />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={360}>
      <RadarChart data={chartData} margin={{ top: 24, right: 24, bottom: 24, left: 24 }}>
        <PolarGrid
          stroke="hsl(var(--border))"
          strokeOpacity={0.5}
          strokeDasharray="3 3"
        />
        <PolarAngleAxis
          dataKey="dimension"
          tick={(props) => {
            const { payload, x, y } = props;
            const nx = typeof x === "number" ? x : Number(x) || 0;
            const ny = typeof y === "number" ? y : Number(y) || 0;
            const pl = payload as { value?: string; dimension?: string } | undefined;
            const label = pl?.value ?? pl?.dimension ?? "";
            const key = LABEL_TO_KEY[label];
            const isHighlighted = key && highlightedDimension === key;
            const fill = isHighlighted && key
              ? DNA_DIMENSION_COLORS[key]
              : "hsl(var(--muted-foreground))";
            const handleClick = () => {
              if (key && onDimensionClick) onDimensionClick(key);
            };
            return (
              <g
                transform={`translate(${nx},${ny})`}
                style={{ cursor: onDimensionClick ? "pointer" : "default" }}
                onClick={handleClick}
                onKeyDown={(e) => {
                  if ((e.key === "Enter" || e.key === " ") && key && onDimensionClick) {
                    e.preventDefault();
                    onDimensionClick(key);
                  }
                }}
                role={onDimensionClick ? "button" : undefined}
                tabIndex={onDimensionClick ? 0 : undefined}
              >
                <text
                  textAnchor="middle"
                  fill={fill}
                  fontSize={12}
                  fontWeight={isHighlighted ? 600 : 500}
                  style={{ textDecoration: isHighlighted ? "underline" : "none" }}
                >
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
          name="본인"
          dataKey="self"
          stroke="hsl(var(--primary))"
          fill="hsl(var(--primary))"
          fillOpacity={0.28}
          strokeWidth={2}
        />
        <Radar
          name="전사 고성과자 평균"
          dataKey="전사고성과자평균"
          stroke="hsl(var(--muted-foreground))"
          fill="hsl(var(--muted-foreground))"
          fillOpacity={0.12}
          strokeWidth={1.5}
          strokeDasharray="4 4"
        />
        <Tooltip
          content={({ active, payload, label }) => (
            <RadarTooltipContent
              active={active}
              payload={payload}
              label={label}
              trainingHours={trainingHours}
            />
          )}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
