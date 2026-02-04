"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  RadialBarChart,
  RadialBar,
} from "recharts";
import { FileEdit, User, Sparkles } from "lucide-react";
import type { Employee, SuccessDNA, Resume } from "@/modules/shared/types";
import { DNA_DIMENSION_COLORS } from "@/modules/shared/constants/dnaColors";
import { hasResumeData } from "../services";
import { getDepartmentMatches } from "../services/matchService";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ResumeUploadZone } from "./ResumeUploadZone";
import { ResumeEditForm } from "./ResumeEditForm";

const DIMENSION_LABELS: Record<keyof SuccessDNA, string> = {
  leadership: "리더십",
  technical: "기술력",
  creativity: "창의성",
  collaboration: "협업",
  adaptability: "적응력",
};

const DNA_KEYS: (keyof SuccessDNA)[] = [
  "leadership",
  "technical",
  "creativity",
  "collaboration",
  "adaptability",
];

function dnaToChartData(dna: SuccessDNA) {
  return DNA_KEYS.map((key) => ({
    name: DIMENSION_LABELS[key],
    key,
    value: dna[key] ?? 0,
    fill: DNA_DIMENSION_COLORS[key],
  }));
}

const EMPTY_RESUME: Resume = {
  education: [],
  experience: [],
  skills: [],
  certifications: [],
};

interface ProfileSheetProps {
  employee: Employee | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onOpenResumeForm?: (employee: Employee) => void;
  /** 이력서 저장 시 즉시 스토어 반영 (수정 반응) */
  onResumeUpdate?: (employeeId: string, resume: Resume) => void;
}

export function ProfileSheet({
  employee,
  open,
  onOpenChange,
  onOpenResumeForm,
  onResumeUpdate,
}: ProfileSheetProps) {
  const [activeTab, setActiveTab] = useState("education");
  const [showInputForm, setShowInputForm] = useState(false);
  /** 업로드 파싱 결과 또는 직접 입력/수정 시 편집 중인 이력서. null이면 업로드 영역 표시 */
  const [editingResume, setEditingResume] = useState<Resume | null>(null);
  const [uploadError, setUploadError] = useState("");

  // 직원이 바뀌거나 시트를 열 때 입력 폼 플래그·편집 상태 초기화
  useEffect(() => {
    if (open || employee) {
      setShowInputForm(false);
      setEditingResume(null);
      setUploadError("");
    }
  }, [employee?.id, open]);

  const resume = employee?.resume;
  const hasData = resume && hasResumeData(resume);
  const dna = employee?.successDna;
  const chartData = dna ? dnaToChartData(dna) : [];
  const departmentMatches = useMemo(
    () => (employee ? getDepartmentMatches(employee) : []),
    [employee]
  );

  const handleOpenForm = () => {
    if (employee && onOpenResumeForm) {
      onOpenResumeForm(employee);
    } else {
      setShowInputForm(true);
      setEditingResume(hasData && resume ? resume : null);
    }
  };

  const handleResumeChange = useCallback(
    (resume: Resume) => {
      if (employee && onResumeUpdate) onResumeUpdate(employee.id, resume);
    },
    [employee, onResumeUpdate]
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full max-w-lg flex-col overflow-hidden p-0 sm:max-w-lg">
        {!employee ? (
          <div className="flex flex-1 items-center justify-center p-6 text-muted-foreground">
            직원을 선택해주세요
          </div>
        ) : (
          <>
            <SheetHeader className="sticky top-0 z-10 shrink-0 border-b border-border bg-background px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <User className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <SheetTitle className="truncate text-lg">{employee.name}</SheetTitle>
                  <SheetDescription className="truncate text-xs">
                    {employee.jobTitle} · {employee.department}
                  </SheetDescription>
                </div>
              </div>
            </SheetHeader>

            {/* Success DNA 미니 차트 */}
            {chartData.length > 0 && (
              <div className="shrink-0 border-b border-border px-6 py-4">
                <p className="mb-2 text-xs font-medium text-muted-foreground">Success DNA 요약</p>
                <div className="h-32 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      layout="vertical"
                      margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
                    >
                      <XAxis type="number" domain={[0, 100]} hide />
                      <YAxis type="category" dataKey="name" width={52} tick={{ fontSize: 10 }} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={12}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* 이력서 + 추천: 스크롤 가능하게 해서 수정 버튼·AI 추천이 모두 보이도록 */}
            <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-6 pb-6">
              {showInputForm ? (
                /* 업로드 영역 또는 편집 폼 (즉시 반영) */
                <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto py-4">
                  {editingResume === null ? (
                    <>
                      <p className="shrink-0 text-sm font-medium text-foreground">
                        {hasData ? "이력서 수정" : "이력서 등록"}
                      </p>
                      <ResumeUploadZone
                        onParsed={(parsed) => setEditingResume(parsed)}
                        onError={setUploadError}
                      />
                      {uploadError && (
                        <p className="shrink-0 text-xs text-destructive">{uploadError}</p>
                      )}
                      <div className="flex shrink-0 items-center gap-2">
                        <span className="text-xs text-muted-foreground">또는</span>
                        <Button
                          type="button"
                          variant="outline"
                          className="h-8 text-xs"
                          onClick={() => setEditingResume(EMPTY_RESUME)}
                        >
                          직접 입력
                        </Button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex shrink-0 items-center justify-between">
                        <p className="text-sm font-medium text-foreground">이력서 편집</p>
                        <Button
                          type="button"
                          variant="ghost"
                          className="text-sm"
                          onClick={() => {
                            setEditingResume(null);
                            setShowInputForm(false);
                          }}
                        >
                          목록으로 돌아가기
                        </Button>
                      </div>
                      <div className="min-h-0 flex-1 overflow-y-auto">
                        <ResumeEditForm
                          initialResume={editingResume}
                          onResumeChange={(next) => {
                            handleResumeChange(next);
                            setEditingResume(next);
                          }}
                        />
                      </div>
                    </>
                  )}
                </div>
              ) : !hasData ? (
                /* 이력서 없음 → 등록 유도 */
                <div className="flex flex-1 flex-col items-center justify-center gap-4 py-12 text-center">
                  <p className="text-sm text-muted-foreground">
                    이력서 정보를 입력해주세요
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    className="inline-flex items-center gap-2"
                    onClick={handleOpenForm}
                  >
                    <FileEdit className="h-4 w-4" />
                    이력서 등록하기
                  </Button>
                </div>
              ) : (
                /* 이력서 있음 → 학력/경력 탭 + 수정 버튼 */
                <Tabs value={activeTab} onValueChange={setActiveTab} className="flex min-h-0 flex-1 flex-col overflow-hidden">
                  <div className="mt-4 flex shrink-0 items-center justify-between gap-2">
                    <TabsList className="w-full">
                      <TabsTrigger value="education">학력</TabsTrigger>
                      <TabsTrigger value="experience">경력</TabsTrigger>
                    </TabsList>
                    <Button
                      type="button"
                      variant="outline"
                      className="h-8 shrink-0 px-2 text-xs"
                      onClick={handleOpenForm}
                      aria-label="이력서 수정"
                    >
                      <FileEdit className="mr-1 h-3.5 w-3.5" />
                      수정
                    </Button>
                  </div>
                  <div className="min-h-[180px] flex-1 overflow-y-auto pt-4">
                    {activeTab === "education" && (
                      <>
                        {resume?.education?.length ? (
                          <ul className="space-y-4">
                            {resume.education.map((ed, i) => (
                              <li key={i} className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
                                <p className="font-medium text-foreground">{ed.school}</p>
                                <p className="mt-0.5 text-muted-foreground">
                                  {ed.degree}
                                  {ed.field ? ` · ${ed.field}` : ""}
                                </p>
                                <p className="mt-1 text-xs text-muted-foreground">
                                  {ed.startDate} ~ {ed.endDate ?? "재학"}
                                </p>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-muted-foreground">등록된 학력이 없습니다.</p>
                        )}
                      </>
                    )}
                    {activeTab === "experience" && (
                      <>
                        {resume?.experience?.length ? (
                          <ul className="space-y-4">
                            {resume.experience.map((ex, i) => (
                              <li key={i} className="rounded-lg border border-border bg-muted/30 p-3 text-sm">
                                <p className="font-medium text-foreground">{ex.company}</p>
                                <p className="mt-0.5 text-muted-foreground">{ex.role}</p>
                                <p className="mt-1 text-xs text-muted-foreground">
                                  {ex.startDate} ~ {ex.endDate ?? "재직"}
                                </p>
                                {ex.description && (
                                  <p className="mt-2 text-xs text-muted-foreground">{ex.description}</p>
                                )}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-muted-foreground">등록된 경력이 없습니다.</p>
                        )}
                      </>
                    )}
                  </div>
                </Tabs>
              )}

            {/* AI 부서 적합도 분석 (컴팩트하게 해서 경력과 한 화면에) */}
            {employee && (
              <section className="mt-4 shrink-0 border-t border-border pt-3">
                <div className="flex items-center gap-2 text-primary">
                  <Sparkles className="h-3.5 w-3.5 shrink-0" />
                  <h3 className="text-xs font-semibold">AI 부서 적합도 분석</h3>
                </div>
                {departmentMatches.length > 0 ? (
                  <>
                    {/* 1순위: 작은 게이지 + 한 줄 요약 */}
                    {departmentMatches[0] && (
                      <div className="mt-2 flex items-center gap-3 rounded-lg border border-border bg-muted/10 px-3 py-2">
                        <div className="relative h-14 w-14 shrink-0">
                          <ResponsiveContainer width="100%" height="100%">
                            <RadialBarChart
                              cx="50%"
                              cy="50%"
                              innerRadius="55%"
                              outerRadius="90%"
                              barSize={6}
                              data={[
                                {
                                  name: departmentMatches[0].department,
                                  value: Math.min(100, departmentMatches[0].score),
                                  fill: "hsl(var(--primary))",
                                },
                              ]}
                              startAngle={180}
                              endAngle={0}
                            >
                              <RadialBar
                                background
                                dataKey="value"
                                cornerRadius={4}
                              />
                            </RadialBarChart>
                          </ResponsiveContainer>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-sm font-bold text-foreground">
                              {departmentMatches[0].score}%
                            </span>
                          </div>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-foreground">
                            {departmentMatches[0].department}
                          </p>
                          <p className="mt-0.5 line-clamp-1 text-[11px] text-muted-foreground">
                            {departmentMatches[0].reason}
                          </p>
                        </div>
                      </div>
                    )}
                    {/* 나머지 추천: 한 줄씩 진행 바만 */}
                    <ul className="mt-2 space-y-1.5">
                      {departmentMatches.slice(1, 4).map((match, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <span className="w-20 shrink-0 truncate text-[11px] font-medium text-foreground">
                            {match.department}
                          </span>
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                            <div
                              className="h-full rounded-full bg-primary transition-all"
                              style={{ width: `${Math.min(100, match.score)}%` }}
                            />
                          </div>
                          <span className="w-7 shrink-0 text-right text-[11px] font-medium text-primary">
                            {match.score}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : (
                  <p className="mt-2 text-[11px] text-muted-foreground">
                    Success DNA 또는 이력서 데이터를 보강하면 추천 부서가 표시됩니다.
                  </p>
                )}
              </section>
            )}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
