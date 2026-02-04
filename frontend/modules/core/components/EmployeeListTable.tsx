"use client";

import { useMemo, useState } from "react";
import { ChevronUp, ChevronDown, Pencil, Trash2, FileText } from "lucide-react";
import { useStore } from "@/store/useStore";
import type { Employee } from "@/modules/shared/types";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DNABadge, getDNAPersonaTooltip } from "@/modules/shared/components/DNABadge";

const EMPLOYMENT_LABELS: Record<string, string> = {
  regular: "정규직",
  contract: "계약직",
  part_time: "파트타임",
  intern: "인턴",
};

const GENDER_LABELS: Record<string, string> = {
  male: "남",
  female: "여",
  other: "기타",
  undisclosed: "미공개",
};

type SortKey = "name" | "department" | "jobTitle" | "trainingHours" | "employmentType";
type SortDir = "asc" | "desc";

interface EmployeeListTableProps {
  employees: Employee[];
  onEdit?: (emp: Employee) => void;
  onDelete?: (id: string) => void;
  onOpenProfile?: (emp: Employee) => void;
}

export function EmployeeListTable({ employees, onEdit, onDelete, onOpenProfile }: EmployeeListTableProps) {
  const setSelectedEmployee = useStore((s) => s.setSelectedEmployee);
  const [filterDept, setFilterDept] = useState("");
  const [filterName, setFilterName] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("name");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const filtered = useMemo(() => {
    let list = employees.filter((e) => {
      const matchDept = !filterDept || e.department.toLowerCase().includes(filterDept.toLowerCase());
      const matchName = !filterName || e.name.toLowerCase().includes(filterName.toLowerCase());
      return matchDept && matchName;
    });
    list = [...list].sort((a, b) => {
      let aVal: string | number = (a[sortKey] ?? "") as string | number;
      let bVal: string | number = (b[sortKey] ?? "") as string | number;
      if (sortKey === "trainingHours") {
        aVal = a.trainingHours ?? 0;
        bVal = b.trainingHours ?? 0;
      }
      const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDir === "asc" ? cmp : -cmp;
    });
    return list;
  }, [employees, filterDept, filterName, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const handleRowClick = (emp: Employee) => {
    setSelectedEmployee(emp);
    if (onOpenProfile) {
      onOpenProfile(emp);
    } else {
      const go = window.confirm(
        `${emp.name} 님을 선택했습니다. Talent Intelligence 페이지로 이동할까요?`
      );
      if (go) window.location.href = "/intelligence";
    }
  };

  const SortIcon = ({ column }: { column: SortKey }) =>
    sortKey === column ? (
      sortDir === "asc" ? (
        <ChevronUp className="ml-1 inline h-4 w-4" />
      ) : (
        <ChevronDown className="ml-1 inline h-4 w-4" />
      )
    ) : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <Label htmlFor="filterName" className="text-sm">이름</Label>
          <Input
            id="filterName"
            placeholder="검색..."
            value={filterName}
            onChange={(e) => setFilterName(e.target.value)}
            className="h-8 w-40"
          />
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="filterDept" className="text-sm">부서</Label>
          <Input
            id="filterDept"
            placeholder="검색..."
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className="h-8 w-40"
          />
        </div>
      </div>
      <div className="overflow-hidden rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>
                <button type="button" onClick={() => handleSort("name")} className="font-medium">
                  이름 <SortIcon column="name" />
                </button>
              </TableHead>
              <TableHead>
                <button type="button" onClick={() => handleSort("jobTitle")} className="font-medium">
                  직급 <SortIcon column="jobTitle" />
                </button>
              </TableHead>
              <TableHead>
                <button type="button" onClick={() => handleSort("department")} className="font-medium">
                  부서 <SortIcon column="department" />
                </button>
              </TableHead>
              <TableHead>성별</TableHead>
              <TableHead>
                <button type="button" onClick={() => handleSort("employmentType")} className="font-medium">
                  고용형태 <SortIcon column="employmentType" />
                </button>
              </TableHead>
              <TableHead>
                <button type="button" onClick={() => handleSort("trainingHours")} className="font-medium">
                  교육시간 <SortIcon column="trainingHours" />
                </button>
              </TableHead>
              {(onEdit || onDelete || onOpenProfile) && <TableHead className="w-32">작업</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((emp) => (
              <TableRow
                key={emp.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleRowClick(emp)}
              >
                <TableCell className="font-medium">
                  <span className="inline-flex items-center gap-2">
                    {emp.name}
                    <DNABadge
                      dna={emp.successDna}
                      tooltipText={getDNAPersonaTooltip(emp, employees)}
                      showTitle={false}
                      className="shrink-0"
                    />
                  </span>
                </TableCell>
                <TableCell>{emp.jobTitle}</TableCell>
                <TableCell>{emp.department}</TableCell>
                <TableCell>{GENDER_LABELS[emp.gender ?? "undisclosed"] ?? emp.gender}</TableCell>
                <TableCell>{EMPLOYMENT_LABELS[emp.employmentType ?? "regular"] ?? emp.employmentType}</TableCell>
                <TableCell>{emp.trainingHours ?? 0}h</TableCell>
                {(onEdit || onDelete || onOpenProfile) && (
                  <TableCell onClick={(e) => e.stopPropagation()} className="space-x-1">
                    {onOpenProfile && (
                      <Button
                        type="button"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => onOpenProfile(emp)}
                        aria-label="상세"
                        title="이력 상세"
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                    )}
                    {onEdit && (
                      <Button
                        type="button"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        onClick={() => onEdit(emp)}
                        aria-label="수정"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                    )}
                    {onDelete && (
                      <Button
                        type="button"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                        onClick={() => onDelete(emp.id)}
                        aria-label="삭제"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
