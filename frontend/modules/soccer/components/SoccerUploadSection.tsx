"use client";

import { useRef, useState } from "react";
import { Upload, Users, Calendar, Building2, Trophy } from "lucide-react";
import { Button } from "@/components/ui/button";
import { uploadSoccerJsonl, type SoccerDataType } from "../services";
import type { SoccerUploadResult } from "../types";

const LABELS: Record<SoccerDataType, string> = {
  players: "선수",
  teams: "팀",
  schedules: "일정",
  stadiums: "경기장",
};

const ICONS: Record<SoccerDataType, React.ComponentType<{ className?: string }>> = {
  players: Users,
  teams: Trophy,
  schedules: Calendar,
  stadiums: Building2,
};

interface SoccerUploadSectionProps {
  dataType: SoccerDataType;
  onResult?: (result: SoccerUploadResult) => void;
}

export function SoccerUploadSection({ dataType, onResult }: SoccerUploadSectionProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [lastResult, setLastResult] = useState<SoccerUploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const processFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".jsonl")) {
      setError("JSONL 파일(.jsonl)만 업로드 가능합니다.");
      return;
    }
    setLoading(true);
    setError(null);
    setLastResult(null);
    try {
      const result = await uploadSoccerJsonl(dataType, file);
      setLastResult(result);
      onResult?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "업로드 실패");
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (loading) return;
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!loading) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const Icon = ICONS[dataType];
  const label = LABELS[dataType];

  return (
    <section className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <Icon className="h-4 w-4" />
        {label} JSONL 업로드
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".jsonl"
        className="hidden"
        aria-hidden
        disabled={loading}
        onChange={handleInputChange}
      />

      <div
        role="button"
        tabIndex={0}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onClick={() => inputRef.current?.click()}
        className={`
          mt-3 flex min-h-[100px] cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-4 transition-colors
          ${isDragging ? "border-primary bg-primary/10" : "border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/50"}
          ${loading ? "pointer-events-none opacity-70" : ""}
        `}
      >
        <Upload className="h-8 w-8 text-muted-foreground" />
        <span className="text-center text-sm text-muted-foreground">
          {isDragging ? "여기에 놓으세요" : "파일을 여기에 놓거나 클릭하여 선택"}
        </span>
        <span className="text-xs text-muted-foreground">.jsonl</span>
      </div>

      {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
      {lastResult && (
        <div className="mt-2 text-sm text-muted-foreground">
          {lastResult.success ? (
            <span className="text-green-600 dark:text-green-400">
              {lastResult.total_rows ?? 0}건 처리됨 · 전략: {lastResult.strategy ?? "-"}
            </span>
          ) : (
            <span className="text-amber-600 dark:text-amber-400">{lastResult.message}</span>
          )}
        </div>
      )}
    </section>
  );
}
