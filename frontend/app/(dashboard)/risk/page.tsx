"use client";

import { useEffect, useMemo, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const API_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
    : "http://localhost:8000";

interface AuditLogItem {
  id: number;
  entityType: string;
  entityId: string;
  action: string;
  actor?: string | null;
  reason?: string | null;
  createdAt?: string | null;
}

export default function RiskPage() {
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");

  const loadLogs = async () => {
    setLoading(true);
    try {
      const url = new URL(`${API_BASE}/api/audit/logs`);
      url.searchParams.set("limit", "300");
      if (actionFilter.trim()) url.searchParams.set("action", actionFilter.trim());
      if (entityFilter.trim()) url.searchParams.set("entityId", entityFilter.trim());
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`Audit fetch failed: ${res.status}`);
      const data = (await res.json()) as { items?: AuditLogItem[] };
      setItems(Array.isArray(data.items) ? data.items : []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const rows = useMemo(() => items, [items]);

  return (
    <div className="space-y-6">
      <div>
        <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
          <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
          <span className="text-xs">컴플라이언스 · 감사 추적</span>
        </div>
        <h1 className="text-2xl font-bold text-foreground">리스크 관리</h1>
        <p className="mt-1 text-muted-foreground">
          핵심 변경 액션에 대한 감사 로그를 조회합니다. (append-only)
        </p>
      </div>

      <section className="rounded-xl border border-[#a8d5c4]/50 bg-card p-4 shadow-sm dark:border-primary/20">
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <label className="text-xs text-muted-foreground">액션</label>
            <Input
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              placeholder="create / update / delete / analyze"
              className="mt-1 h-9 w-64"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">엔터티 ID</label>
            <Input
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              placeholder="E001, HP001 ..."
              className="mt-1 h-9 w-48"
            />
          </div>
          <Button onClick={loadLogs} disabled={loading}>
            {loading ? "조회 중..." : "조회"}
          </Button>
        </div>

        <div className="mt-4 overflow-hidden rounded-lg border border-[#a8d5c4]/50 dark:border-primary/20">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>시각</TableHead>
                <TableHead>엔터티</TableHead>
                <TableHead>액션</TableHead>
                <TableHead>수행자</TableHead>
                <TableHead>사유</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">
                    {loading ? "조회 중..." : "감사 로그가 없습니다."}
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.createdAt ? new Date(r.createdAt).toLocaleString() : "-"}</TableCell>
                    <TableCell>{r.entityType}:{r.entityId}</TableCell>
                    <TableCell>{r.action}</TableCell>
                    <TableCell>{r.actor || "-"}</TableCell>
                    <TableCell className="max-w-[340px] truncate" title={r.reason ?? undefined}>
                      {r.reason || "-"}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}
