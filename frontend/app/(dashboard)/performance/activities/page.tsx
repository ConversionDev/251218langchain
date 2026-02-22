"use client";

import { useEffect, useState, useMemo } from "react";
import { Search, FileText, Filter, ChevronLeft, ChevronRight } from "lucide-react";
import { useHydrated } from "@/hooks/use-hydrated";
import {
  fetchActivityRecords,
  getTextTypeLabel,
  type ActivityRecord,
  type ActivityTextType,
} from "@/modules/performance/services/activityServices";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const TEXT_TYPES: { value: ActivityTextType | "all"; label: string }[] = [
  { value: "all", label: "전체" },
  { value: "meeting", label: "회의록" },
  { value: "report", label: "보고서" },
  { value: "email", label: "이메일" },
];

const PERIODS = ["all", "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"];

export default function ActivitiesPage() {
  const hydrated = useHydrated();

  const [activities, setActivities] = useState<ActivityRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [textTypeFilter, setTextTypeFilter] = useState<ActivityTextType | "all">("all");
  const [periodFilter, setPeriodFilter] = useState("all");
  const [gradeFilter, setGradeFilter] = useState<"high" | "normal" | "all">("all");

  const [page, setPage] = useState(0);
  const pageSize = 50;

  const [selectedActivity, setSelectedActivity] = useState<ActivityRecord | null>(null);

  const loadActivities = async () => {
    setLoading(true);
    try {
      const res = await fetchActivityRecords({
        period: periodFilter === "all" ? undefined : periodFilter,
        textType: textTypeFilter === "all" ? undefined : textTypeFilter,
        grade: gradeFilter === "all" ? undefined : gradeFilter,
        limit: 1000,
      });
      setActivities(res.items);
      setTotal(res.total);
    } catch {
      setActivities([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (hydrated) loadActivities();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, textTypeFilter, periodFilter, gradeFilter]);

  const filteredActivities = useMemo(() => {
    if (!searchQuery.trim()) return activities;
    const q = searchQuery.toLowerCase();
    return activities.filter(
      (a) =>
        a.content.toLowerCase().includes(q) ||
        a.employeeId.toLowerCase().includes(q) ||
        a.tags.some((t) => t.toLowerCase().includes(q))
    );
  }, [activities, searchQuery]);

  const pagedActivities = useMemo(() => {
    const start = page * pageSize;
    return filteredActivities.slice(start, start + pageSize);
  }, [filteredActivities, page]);

  const totalPages = Math.max(1, Math.ceil(filteredActivities.length / pageSize));

  if (!hydrated) return null;

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-xl font-semibold">성과 활동 기록</h1>
      </header>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="검색..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(0);
            }}
            className="pl-9"
          />
        </div>
        <Select value={textTypeFilter} onValueChange={(v) => { setTextTypeFilter(v as typeof textTypeFilter); setPage(0); }}>
          <SelectTrigger className="w-32">
            <Filter className="mr-1.5 h-4 w-4" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TEXT_TYPES.map((t) => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={periodFilter} onValueChange={(v) => { setPeriodFilter(v); setPage(0); }}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="분기" />
          </SelectTrigger>
          <SelectContent>
            {PERIODS.map((p) => (
              <SelectItem key={p} value={p}>{p === "all" ? "전체 분기" : p}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={gradeFilter} onValueChange={(v) => { setGradeFilter(v as typeof gradeFilter); setPage(0); }}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="등급" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체 등급</SelectItem>
            <SelectItem value="high">고성과</SelectItem>
            <SelectItem value="normal">일반</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-24">유형</TableHead>
              <TableHead className="w-24">분기</TableHead>
              <TableHead className="w-24">사원ID</TableHead>
              <TableHead className="min-w-[4.5rem]">등급</TableHead>
              <TableHead>내용 미리보기</TableHead>
              <TableHead className="w-40">태그</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  로딩 중...
                </TableCell>
              </TableRow>
            ) : pagedActivities.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  데이터가 없습니다.
                </TableCell>
              </TableRow>
            ) : (
              pagedActivities.map((a) => (
                <TableRow
                  key={a.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => setSelectedActivity(a)}
                >
                  <TableCell>
                    <Badge variant="outline">{getTextTypeLabel(a.textType)}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">{a.period}</TableCell>
                  <TableCell className="text-sm font-mono">{a.employeeId}</TableCell>
                  <TableCell className="whitespace-nowrap">
                    <Badge variant={a.grade === "high" ? "default" : "secondary"} className="whitespace-nowrap">
                      {a.grade === "high" ? "고성과" : a.grade === "normal" ? "일반" : "—"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm max-w-md truncate">{a.content.slice(0, 80)}...</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {a.tags.slice(0, 2).map((tag, i) => (
                        <Badge key={i} variant="outline" className="text-[10px]">{tag}</Badge>
                      ))}
                      {a.tags.length > 2 && (
                        <Badge variant="outline" className="text-[10px]">+{a.tags.length - 2}</Badge>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          총 {total.toLocaleString()}건 중 {filteredActivities.length.toLocaleString()}건 표시
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span>
            {page + 1} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Detail Dialog */}
      <Dialog open={!!selectedActivity} onOpenChange={(open) => !open && setSelectedActivity(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {selectedActivity && getTextTypeLabel(selectedActivity.textType)} 상세
            </DialogTitle>
          </DialogHeader>
          {selectedActivity && (
            <div className="space-y-4 text-sm">
              <div className="flex flex-wrap gap-4">
                <div>
                  <span className="text-muted-foreground">사원ID:</span>{" "}
                  <span className="font-mono">{selectedActivity.employeeId}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">분기:</span> {selectedActivity.period}
                </div>
                <div>
                  <span className="text-muted-foreground">등급:</span>{" "}
                  <Badge variant={selectedActivity.grade === "high" ? "default" : "secondary"}>
                    {selectedActivity.grade === "high" ? "고성과" : selectedActivity.grade === "normal" ? "일반" : "—"}
                  </Badge>
                </div>
              </div>
              <div>
                <p className="text-muted-foreground mb-1">내용</p>
                <div className="rounded-md border p-3 bg-muted/30 whitespace-pre-wrap text-sm leading-relaxed">
                  {selectedActivity.content}
                </div>
              </div>
              {selectedActivity.tags.length > 0 && (
                <div>
                  <p className="text-muted-foreground mb-1">태그</p>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedActivity.tags.map((tag, i) => (
                      <Badge key={i} variant="outline">{tag}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
