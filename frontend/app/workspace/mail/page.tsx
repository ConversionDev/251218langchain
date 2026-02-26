"use client";

import { useMemo, useState } from "react";
import {
  ChevronDown,
  Inbox,
  Mail,
  Pencil,
  Reply,
  Forward,
  Trash2,
  Send,
  Star,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

type MailItem = {
  id: string;
  from: string;
  to?: string;
  subject: string;
  preview: string;
  receivedAt: string;
  unread?: boolean;
  starred?: boolean;
  body: string;
};

const SAMPLE_INBOX: MailItem[] = [
  {
    id: "m1",
    from: "peopleops@company.com",
    subject: "[안내] 2026 Q1 역량 점검 자료 제출 요청",
    preview: "이번 분기 역량 점검을 위해 부서별 활동 요약과 회의록 링크를 제출해 주세요.",
    receivedAt: "오전 9:12",
    unread: true,
    starred: true,
    body:
      "안녕하세요. 2026 Q1 역량 점검을 위해 부서별 활동 요약과 회의록 링크 제출을 요청드립니다.\n\n마감: 2/26(수) 18:00\n제출 항목: 핵심성과, 실행 이슈, 다음 분기 계획\n\n감사합니다.",
  },
  {
    id: "m2",
    from: "support@company.com",
    subject: "[공유] 신규 협업 툴 사용 가이드",
    preview: "문서 결재 흐름과 보안 정책이 업데이트되어 공유드립니다.",
    receivedAt: "어제",
    unread: false,
    body:
      "신규 협업 툴 사용 가이드 문서를 공유드립니다.\n\n주요 변경: 문서 결재 흐름 표준화, 권한 분리 정책 강화, 반출 절차 명시.\n\n문의사항은 경영지원팀으로 연락 부탁드립니다.",
  },
  {
    id: "m3",
    from: "security@company.com",
    subject: "[주의] 외부 메일 링크 클릭 유의",
    preview: "유사 피싱 메일 유입 사례가 확인되어 보안 수칙을 재안내합니다.",
    receivedAt: "2월 20일",
    unread: true,
    body:
      "최근 외부 발신자로 위장한 피싱 메일 사례가 확인되었습니다.\n\n출처가 불분명한 첨부파일/링크는 열람하지 마시고 보안운영팀으로 즉시 전달해 주세요.",
  },
  {
    id: "m4",
    from: "hr@company.com",
    subject: "2월 급여 명세서 안내",
    preview: "2월 급여 명세서가 MyHR에서 확인 가능합니다.",
    receivedAt: "2월 19일",
    unread: false,
    body: "2월 급여 명세서가 MyHR 포털에서 확인 가능합니다. 문의: 인사팀 내선 1234.",
  },
  {
    id: "m5",
    from: "it@company.com",
    subject: "시스템 정기 점검 안내 (2/22 02:00~06:00)",
    preview: "2월 22일 새벽 전사 시스템 정기 점검이 진행됩니다.",
    receivedAt: "2월 18일",
    unread: false,
    starred: true,
    body: "2월 22일(토) 02:00~06:00 전사 시스템 정기 점검이 진행됩니다. 해당 시간대 서비스 이용이 제한될 수 있습니다.",
  },
];

const SAMPLE_SENT: MailItem[] = [
  {
    id: "s1",
    from: "me",
    to: "team@company.com",
    subject: "Re: 주간 회의록 공유",
    preview: "첨부와 같이 주간 회의록 공유드립니다.",
    receivedAt: "2월 25일",
    unread: false,
    body: "첨부와 같이 주간 회의록 공유드립니다. 검토 부탁드립니다.",
  },
];

type FolderId = "inbox" | "sent" | "drafts" | "starred" | "trash";

const FOLDERS: { id: FolderId; label: string; icon: typeof Inbox }[] = [
  { id: "inbox", label: "받은편지함", icon: Inbox },
  { id: "sent", label: "보낸편지함", icon: Send },
  { id: "drafts", label: "임시보관", icon: Mail },
  { id: "starred", label: "중요 메일", icon: Star },
  { id: "trash", label: "휴지통", icon: Trash2 },
];

export default function WorkspaceMailPage() {
  const [folder, setFolder] = useState<FolderId>("inbox");
  const [activeId, setActiveId] = useState<string | null>(SAMPLE_INBOX[0]?.id ?? null);
  const [query, setQuery] = useState("");
  const [composing, setComposing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [mails, setMails] = useState<MailItem[]>(SAMPLE_INBOX);
  const [sentMails, setSentMails] = useState<MailItem[]>(SAMPLE_SENT);

  const list = folder === "inbox" ? mails : folder === "sent" ? sentMails : folder === "starred" ? mails.filter((m) => m.starred) : [];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (mail) =>
        mail.subject.toLowerCase().includes(q) ||
        mail.from.toLowerCase().includes(q) ||
        mail.preview.toLowerCase().includes(q)
    );
  }, [query, list]);

  const active = useMemo(() => {
    if (!activeId) return null;
    return mails.find((m) => m.id === activeId) ?? sentMails.find((m) => m.id === activeId) ?? null;
  }, [activeId, mails, sentMails]);

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === filtered.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(filtered.map((m) => m.id)));
  };

  const toggleStar = (id: string) => {
    setMails((prev) => prev.map((m) => (m.id === id ? { ...m, starred: !m.starred } : m)));
  };

  const markAsRead = (id: string) => {
    setMails((prev) => prev.map((m) => (m.id === id ? { ...m, unread: false } : m)));
  };

  const deleteSelected = () => {
    if (folder === "inbox") setMails((prev) => prev.filter((m) => !selectedIds.has(m.id)));
    setSelectedIds(new Set());
    setActiveId(null);
  };

  const openCompose = () => {
    setComposing(true);
    setTo("");
    setSubject("");
    setBody("");
  };

  const sendMail = (e: React.FormEvent) => {
    e.preventDefault();
    if (!to.trim() || !subject.trim()) return;
    setSentMails((prev) => [
      ...prev,
      { id: "s" + Date.now(), from: "me", to, subject, preview: body.slice(0, 50), receivedAt: "방금 전", unread: false, body },
    ]);
    setComposing(false);
    setTo("");
    setSubject("");
    setBody("");
  };

  return (
    <div className="grid h-[calc(100vh-5.5rem)] gap-0 overflow-hidden rounded-xl border border-[#a8d5c4] bg-white shadow-sm dark:border-primary/30 dark:bg-card lg:grid-cols-[200px,minmax(0,360px),1fr]">
      {/* 왼쪽: 폴더 */}
      <aside className="flex flex-col border-r border-[#a8d5c4]/60 dark:border-primary/20">
        <div className="shrink-0 p-3">
          <Button
            type="button"
            onClick={openCompose}
            className="workspace-hero-btn w-full justify-center gap-2 rounded-lg border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
          >
            <Pencil className="h-4 w-4" />
            메일 쓰기
          </Button>
        </div>
        <nav className="flex-1 space-y-0.5 px-2 py-2">
          {FOLDERS.map((item) => {
            const Icon = item.icon;
            const isActive = folder === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setFolder(item.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                  isActive
                    ? "bg-[#e8f5ef] font-medium text-slate-900 dark:bg-primary/20 dark:text-foreground"
                    : "text-slate-600 hover:bg-[#e8f5ef]/60 dark:text-muted-foreground dark:hover:bg-primary/10"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* 가운데: 메일 목록 + 툴바 */}
      <section className="flex flex-col border-r border-[#a8d5c4]/60 dark:border-primary/20">
        <div className="shrink-0 border-b border-[#a8d5c4]/40 p-2 dark:border-primary/20">
          <label className="flex items-center gap-2 rounded-lg border border-[#a8d5c4]/80 bg-[#e8f5ef]/50 px-3 py-2 dark:border-primary/30 dark:bg-primary/10">
            <Search className="h-4 w-4 shrink-0 text-slate-500 dark:text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="메일 검색"
              className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-500 dark:placeholder:text-muted-foreground"
            />
          </label>
        </div>
        {filtered.length > 0 && (
          <div className="flex shrink-0 items-center gap-1 border-b border-[#a8d5c4]/30 px-2 py-1 dark:border-primary/10">
            <button
              type="button"
              onClick={toggleSelectAll}
              className="rounded p-1.5 text-slate-500 hover:bg-[#e8f5ef]/70 hover:text-slate-700 dark:hover:bg-primary/15"
              title="전체 선택"
              aria-label="전체 선택"
            >
              <ChevronDown className="h-4 w-4" />
            </button>
            {selectedIds.size > 0 ? (
              <>
                <span className="text-xs text-slate-500 dark:text-muted-foreground">{selectedIds.size}개 선택</span>
                <Button type="button" variant="ghost" size="sm" className="h-8 text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/50" onClick={deleteSelected}>
                  <Trash2 className="mr-1 h-3.5 w-3.5" />
                  삭제
                </Button>
              </>
            ) : null}
          </div>
        )}
        <ul className="min-h-0 flex-1 overflow-auto">
          {filtered.length === 0 ? (
            <li className="flex flex-col items-center justify-center py-12 text-center">
              <Inbox className="h-10 w-10 text-slate-400 dark:text-muted-foreground" />
              <p className="mt-2 text-sm text-slate-500 dark:text-muted-foreground">메일이 없습니다.</p>
            </li>
          ) : (
            filtered.map((mail) => (
              <li
                key={mail.id}
                className={`flex items-start gap-2 border-b border-[#a8d5c4]/20 px-3 py-2 dark:border-primary/10 ${
                  active?.id === mail.id ? "bg-[#e8f5ef]/70 dark:bg-primary/15" : "hover:bg-[#e8f5ef]/50 dark:hover:bg-primary/10"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(mail.id)}
                  onChange={() => toggleSelect(mail.id)}
                  className="mt-1.5 h-4 w-4 rounded border-[#a8d5c4] text-primary focus:ring-primary/30 dark:border-primary/50"
                  onClick={(e) => e.stopPropagation()}
                />
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); toggleStar(mail.id); }}
                  className="shrink-0 rounded p-0.5 text-slate-400 hover:text-amber-500 dark:hover:text-amber-400"
                  aria-label={mail.starred ? "중요 해제" : "중요 표시"}
                >
                  <Star className={`h-4 w-4 ${mail.starred ? "fill-amber-400 text-amber-500" : ""}`} />
                </button>
                <button
                  type="button"
                  className="min-w-0 flex-1 text-left"
                  onClick={() => { setActiveId(mail.id); markAsRead(mail.id); }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`truncate text-sm ${mail.unread ? "font-semibold text-slate-900 dark:text-foreground" : "text-slate-700 dark:text-muted-foreground"}`}>
                      {mail.from}
                    </span>
                    <span className="shrink-0 text-xs text-slate-500 dark:text-muted-foreground">{mail.receivedAt}</span>
                  </div>
                  <p className={`mt-0.5 truncate text-sm ${mail.unread ? "font-semibold text-slate-900 dark:text-foreground" : "text-slate-800 dark:text-foreground/90"}`}>
                    {mail.subject}
                  </p>
                  <p className="mt-0.5 line-clamp-1 text-xs text-slate-500 dark:text-muted-foreground">{mail.preview}</p>
                </button>
              </li>
            ))
          )}
        </ul>
      </section>

      {/* 오른쪽: 읽기 / 쓰기 */}
      <section className="flex min-h-0 flex-col overflow-auto bg-[#f0f5f0]/60 dark:bg-primary/5">
        {composing ? (
          <div className="flex flex-1 flex-col p-4">
            <h2 className="mb-4 text-base font-semibold text-slate-900 dark:text-foreground">새 메일</h2>
            <form className="flex flex-1 flex-col gap-4" onSubmit={sendMail}>
              <div className="grid gap-2">
                <Label htmlFor="mail-to" className="text-slate-600 dark:text-muted-foreground">받는 사람</Label>
                <Input
                  id="mail-to"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  placeholder="수신자 이메일"
                  className="border-[#a8d5c4]/60 bg-white dark:border-primary/30 dark:bg-card"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="mail-subject" className="text-slate-600 dark:text-muted-foreground">제목</Label>
                <Input
                  id="mail-subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="제목"
                  className="border-[#a8d5c4]/60 bg-white dark:border-primary/30 dark:bg-card"
                  required
                />
              </div>
              <div className="grid flex-1 gap-2">
                <Label htmlFor="mail-body" className="text-slate-600 dark:text-muted-foreground">본문</Label>
                <Textarea
                  id="mail-body"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="내용을 입력하세요."
                  rows={12}
                  className="min-h-[200px] flex-1 resize-y border-[#a8d5c4]/60 bg-white dark:border-primary/30 dark:bg-card"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={!to.trim() || !subject.trim()}
                  className="workspace-hero-btn border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
                >
                  <Send className="mr-2 h-4 w-4" />
                  보내기
                </Button>
                <Button type="button" variant="outline" onClick={() => setComposing(false)} className="border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10">
                  취소
                </Button>
              </div>
            </form>
          </div>
        ) : !active ? (
          <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
            <Mail className="h-14 w-14 text-slate-400 dark:text-muted-foreground" />
            <p className="mt-4 text-sm text-slate-500 dark:text-muted-foreground">메일을 선택하세요</p>
          </div>
        ) : (
          <div className="flex flex-1 flex-col p-4">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <Button type="button" variant="outline" size="sm" className="gap-1 border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10">
                <Reply className="h-3.5 w-3.5" />
                답장
              </Button>
              <Button type="button" variant="outline" size="sm" className="gap-1 border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10">
                <Forward className="h-3.5 w-3.5" />
                전달
              </Button>
              <Button type="button" variant="outline" size="sm" className="gap-1 text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/50">
                <Trash2 className="h-3.5 w-3.5" />
                삭제
              </Button>
            </div>
            <div className="rounded-lg border border-[#a8d5c4]/60 bg-white p-4 shadow-sm dark:border-primary/20 dark:bg-card">
              <h1 className="text-lg font-semibold text-slate-900 dark:text-foreground">{active.subject}</h1>
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-muted-foreground">
                <span><strong className="text-slate-700 dark:text-foreground">보낸 사람:</strong> {active.from}</span>
                {active.to && <span><strong className="text-slate-700 dark:text-foreground">받는 사람:</strong> {active.to}</span>}
                <span><strong className="text-slate-700 dark:text-foreground">날짜:</strong> {active.receivedAt}</span>
              </div>
              <div className="mt-4 border-t border-[#a8d5c4]/40 pt-4 text-sm leading-6 text-slate-700 dark:border-primary/20 dark:text-foreground/90">
                {active.body.split("\n").map((line, i) => (
                  <p key={i}>{line || "\u00A0"}</p>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
