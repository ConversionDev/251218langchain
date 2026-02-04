"use client";

import type { Employee, SuccessDNA } from "@/modules/shared/types";
import { DNA_DIMENSION_COLORS } from "@/modules/shared/constants/dnaColors";

const DIMENSION_CONFIG: Record<
  keyof SuccessDNA,
  { label: string; icon: string; title: string; personaTop5: string }
> = {
  leadership: { label: "리더십", icon: "👑", title: "The Leader", personaTop5: "Visionary Leader" },
  technical: { label: "기술력", icon: "💻", title: "The Specialist", personaTop5: "The Specialist Elite" },
  creativity: { label: "창의성", icon: "🎨", title: "The Visionary", personaTop5: "The Visionary" },
  collaboration: { label: "협업", icon: "🤝", title: "The Collaborator", personaTop5: "Master Connector" },
  adaptability: { label: "적응력", icon: "🔄", title: "The Adaptor", personaTop5: "The Adaptor Pro" },
};

const DIMENSION_KEYS = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
] as const;

/** 역량 중 최고 점수인 주특기(Primary DNA) 반환 */
export function getPrimaryDNA(dna: SuccessDNA | undefined): {
  dimension: keyof SuccessDNA;
  label: string;
  icon: string;
  title: string;
  score: number;
} | null {
  if (!dna) return null;
  let maxKey: keyof SuccessDNA = "leadership";
  let maxVal = dna.leadership ?? 0;
  DIMENSION_KEYS.forEach((key) => {
    const v = dna[key] ?? 0;
    if (v > maxVal) {
      maxVal = v;
      maxKey = key;
    }
  });
  const config = DIMENSION_CONFIG[maxKey];
  return {
    dimension: maxKey,
    label: config.label,
    icon: config.icon,
    title: config.title,
    score: maxVal,
  };
}

/**
 * 직원의 주특기 DNA에 대한 페르소나 툴팁 문구.
 * 전사 목록 대비 상위 5%이면 'Master Connector' 등 페르소나를 붙입니다.
 */
export function getDNAPersonaTooltip(
  employee: Employee,
  allEmployees: Employee[]
): string | null {
  const primary = getPrimaryDNA(employee.successDna);
  if (!primary || !employee.successDna) return null;
  const dim = primary.dimension;
  const scores = allEmployees
    .map((e) => e.successDna?.[dim] ?? 0)
    .filter(() => true);
  if (scores.length === 0) return null;
  const sorted = [...scores].sort((a, b) => b - a);
  const rankPos = (() => {
    const idx = sorted.findIndex((s) => s < primary.score);
    return idx === -1 ? sorted.length : idx;
  })();
  const percentile =
    scores.length <= 1 ? 100 : Math.round(((scores.length - rankPos) / scores.length) * 100);

  const config = DIMENSION_CONFIG[dim];
  if (percentile >= 95) {
    return `이 직원은 ${config.label}(${primary.score}점) DNA가 상위 5%인 '${config.personaTop5}'입니다.`;
  }
  if (percentile >= 80) {
    return `이 직원은 ${config.label} DNA가 상위 ${100 - percentile}%로, ${config.title} 성향이 뚜렷합니다.`;
  }
  return `${config.label} (${primary.score}점) · ${config.title}`;
}

interface DNABadgeProps {
  dna: SuccessDNA | undefined;
  /** 툴팁에 표시할 문구 (미지정 시 기본 문구 또는 페르소나 문구 사용) */
  tooltipText?: string | null;
  className?: string;
  showTitle?: boolean;
}

/** 주특기 DNA 아이콘 + 라벨 뱃지. 역량별 색상은 Intelligence 차트와 동기화됩니다. */
export function DNABadge({ dna, tooltipText, className = "", showTitle = true }: DNABadgeProps) {
  const primary = getPrimaryDNA(dna);

  if (!primary) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full border border-dashed border-muted-foreground/40 bg-muted/30 px-2 py-0.5 text-[10px] text-muted-foreground ${className}`}
        title="역량 데이터가 없습니다. 직원 수정에서 DNA 점수를 입력하세요."
      >
        역량 미측정
      </span>
    );
  }

  const title = tooltipText ?? `${primary.label} (${primary.score}점) · ${primary.title}`;
  const color = DNA_DIMENSION_COLORS[primary.dimension];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}
      title={title}
      style={{
        backgroundColor: `${color}18`,
        color,
      }}
    >
      <span aria-hidden>{primary.icon}</span>
      <span>{primary.label}</span>
      {showTitle && (
        <span className="text-muted-foreground">· {primary.title}</span>
      )}
    </span>
  );
}
