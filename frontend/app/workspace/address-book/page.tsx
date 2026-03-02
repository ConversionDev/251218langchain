"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, Search, Users, Mail, Plus, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const API_BASE = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") : "http://localhost:8000";

type AddressBookEntry = {
  id: string;
  type: "person" | "shared" | "group";
  displayName: string;
  email: string;
  department: string;
  source: string;
};

const TYPE_LABEL: Record<string, string> = {
  person: "직원",
  shared: "공용",
  group: "그룹",
};

export default function WorkspaceAddressBookPage() {
  const [entries, setEntries] = useState<AddressBookEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [createOpen, setCreateOpen] = useState(false);
  const [editEntry, setEditEntry] = useState<AddressBookEntry | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [formType, setFormType] = useState<"shared" | "group">("shared");
  const [formDisplayName, setFormDisplayName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formDepartment, setFormDepartment] = useState("");
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchList = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (typeFilter && ["person", "shared", "group"].includes(typeFilter)) params.set("type", typeFilter);
    fetch(`${API_BASE}/api/address-book?${params}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: AddressBookEntry[]) => setEntries(Array.isArray(data) ? data : []))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [q, typeFilter]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const openCreate = () => {
    setFormType("shared");
    setFormDisplayName("");
    setFormEmail("");
    setFormDepartment("");
    setError(null);
    setCreateOpen(true);
  };

  const openEdit = (entry: AddressBookEntry) => {
    setEditEntry(entry);
    setFormDisplayName(entry.displayName);
    setFormEmail(entry.email);
    setFormDepartment(entry.department || "");
    setError(null);
  };

  const closeEdit = () => {
    setEditEntry(null);
    setFormDisplayName("");
    setFormEmail("");
    setFormDepartment("");
    setError(null);
  };

  const handleCreate = async () => {
    if (!formDisplayName.trim() || !formEmail.trim()) {
      setError("표시명과 이메일을 입력하세요.");
      return;
    }
    setSubmitLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/address-book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: formType,
          displayName: formDisplayName.trim(),
          email: formEmail.trim(),
          department: formDepartment.trim() || null,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `요청 실패: ${res.status}`);
      }
      setCreateOpen(false);
      fetchList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "저장 실패");
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!editEntry || !formDisplayName.trim() || !formEmail.trim()) {
      setError("표시명과 이메일을 입력하세요.");
      return;
    }
    setSubmitLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/address-book/${encodeURIComponent(editEntry.id)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          displayName: formDisplayName.trim(),
          email: formEmail.trim(),
          department: formDepartment.trim() || null,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `요청 실패: ${res.status}`);
      }
      closeEdit();
      fetchList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "수정 실패");
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("이 주소를 삭제할까요?")) return;
    setDeleteId(id);
    try {
      const res = await fetch(`${API_BASE}/api/address-book/${encodeURIComponent(id)}`, { method: "DELETE" });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert(data.detail || "삭제 실패");
        return;
      }
      fetchList();
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-foreground">사내 주소록</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-muted-foreground">
            직원·공용 메일함·그룹을 한곳에서 검색합니다. 공용·그룹만 추가·수정·삭제할 수 있습니다.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            onClick={openCreate}
            className="gap-2 border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:bg-[#d4eddf] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground dark:hover:bg-primary/25"
          >
            <Plus className="h-4 w-4" />
            추가
          </Button>
          <Link
            href="/workspace"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-muted-foreground dark:hover:text-foreground"
          >
            <ExternalLink className="h-4 w-4" />
            워크스페이스
          </Link>
        </div>
      </header>

      <div className="mb-4 flex flex-wrap gap-4">
        <label className="flex flex-1 min-w-[200px] items-center gap-2 rounded-lg border border-[#a8d5c4]/60 bg-[#e8f5ef]/30 px-3 py-2 dark:border-primary/30 dark:bg-primary/10">
          <Search className="h-4 w-4 shrink-0 text-slate-500 dark:text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="이름·이메일·부서로 검색"
            className="min-w-0 flex-1 border-0 bg-transparent p-0 text-sm outline-none focus-visible:ring-0"
          />
        </label>
        <div className="flex items-center gap-2">
          <Label htmlFor="addr-type" className="text-sm text-slate-600 dark:text-muted-foreground">타입</Label>
          <select
            id="addr-type"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-[#a8d5c4]/60 bg-white px-3 py-2 text-sm dark:border-primary/30 dark:bg-card"
          >
            <option value="">전체</option>
            <option value="person">직원</option>
            <option value="shared">공용</option>
            <option value="group">그룹</option>
          </select>
        </div>
      </div>

      <div className="rounded-xl border border-[#a8d5c4]/60 bg-white shadow-sm dark:border-primary/30 dark:bg-card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-sm text-slate-500 dark:text-muted-foreground">
            불러오는 중…
          </div>
        ) : entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Users className="h-12 w-12 text-slate-400 dark:text-muted-foreground" />
            <p className="mt-3 text-sm text-slate-500 dark:text-muted-foreground">주소록이 비어 있거나 검색 결과가 없습니다.</p>
            <p className="mt-1 text-xs text-slate-400 dark:text-muted-foreground">
              샘플 데이터는 <code className="rounded bg-slate-100 px-1 dark:bg-slate-800">python -m training.pipelines.address_book.run_import_internal_addresses</code> 로 넣을 수 있습니다.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-[#a8d5c4]/30 dark:divide-primary/20">
            {entries.map((entry) => (
              <li
                key={`${entry.source}-${entry.id}`}
                className="flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-[#e8f5ef]/50 dark:hover:bg-primary/10"
              >
                <span
                  className={`inline-flex shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                    entry.type === "person"
                      ? "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                      : entry.type === "shared"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200"
                        : "bg-teal-100 text-teal-800 dark:bg-teal-900/50 dark:text-teal-200"
                  }`}
                >
                  {TYPE_LABEL[entry.type] ?? entry.type}
                </span>
                <span className="font-medium text-slate-900 dark:text-foreground">{entry.displayName}</span>
                <span className="flex items-center gap-1 text-sm text-slate-600 dark:text-muted-foreground">
                  <Mail className="h-3.5 w-3.5" />
                  {entry.email}
                </span>
                {entry.department && (
                  <span className="text-xs text-slate-500 dark:text-muted-foreground">{entry.department}</span>
                )}
                {entry.source === "internal_addresses" && (
                  <span className="ml-auto flex items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-8 gap-1 text-slate-600 hover:text-slate-900 dark:hover:text-foreground"
                      onClick={() => openEdit(entry)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                      수정
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-8 gap-1 text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/50"
                      onClick={() => handleDelete(entry.id)}
                      disabled={deleteId === entry.id}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      삭제
                    </Button>
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 추가 모달 */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>공용·그룹 추가</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="create-type">타입</Label>
              <select
                id="create-type"
                value={formType}
                onChange={(e) => setFormType(e.target.value as "shared" | "group")}
                className="rounded-lg border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="shared">공용</option>
                <option value="group">그룹</option>
              </select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-displayName">표시명</Label>
              <Input
                id="create-displayName"
                value={formDisplayName}
                onChange={(e) => setFormDisplayName(e.target.value)}
                placeholder="예: 경영지원팀"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-email">이메일</Label>
              <Input
                id="create-email"
                type="email"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
                placeholder="support@company.com"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-department">부서 (선택)</Label>
              <Input
                id="create-department"
                value={formDepartment}
                onChange={(e) => setFormDepartment(e.target.value)}
                placeholder="경영지원"
              />
            </div>
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
              취소
            </Button>
            <Button type="button" onClick={handleCreate} disabled={submitLoading}>
              {submitLoading ? "저장 중…" : "추가"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 수정 모달 */}
      <Dialog open={!!editEntry} onOpenChange={(open) => !open && closeEdit()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>수정</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="edit-displayName">표시명</Label>
              <Input
                id="edit-displayName"
                value={formDisplayName}
                onChange={(e) => setFormDisplayName(e.target.value)}
                placeholder="표시명"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-email">이메일</Label>
              <Input
                id="edit-email"
                type="email"
                value={formEmail}
                onChange={(e) => setFormEmail(e.target.value)}
                placeholder="email@company.com"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-department">부서 (선택)</Label>
              <Input
                id="edit-department"
                value={formDepartment}
                onChange={(e) => setFormDepartment(e.target.value)}
                placeholder="부서"
              />
            </div>
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={closeEdit}>
              취소
            </Button>
            <Button type="button" onClick={handleUpdate} disabled={submitLoading}>
              {submitLoading ? "저장 중…" : "저장"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
