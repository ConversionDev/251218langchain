"use client";

import { useMemo, useState } from "react";
import {
  Archive,
  Inbox,
  Pencil,
  Search,
  Send,
  Sparkles,
  Star,
  Tag,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

type MailItem = {
  id: string;
  from: string;
  subject: string;
  preview: string;
  receivedAt: string;
  unread?: boolean;
  aiTag?: "핵심" | "주의" | "요청";
  body: string;
};

const SAMPLE_MAILS: MailItem[] = [
  {
    id: "m1",
    from: "People Ops",
    subject: "[안내] 2026 Q1 역량 점검 자료 제출 요청",
    preview: "이번 분기 역량 점검을 위해 부서별 활동 요약과 회의록 링크를 제출해 주세요.",
    receivedAt: "오전 9:12",
    unread: true,
    aiTag: "요청",
    body:
      "안녕하세요. 2026 Q1 역량 점검을 위해 부서별 활동 요약과 회의록 링크 제출을 요청드립니다.\n" +
      "마감: 2/26(수) 18:00\n" +
      "제출 항목: 핵심성과, 실행 이슈, 다음 분기 계획",
  },
  {
    id: "m2",
    from: "경영지원팀",
    subject: "[공유] 신규 협업 툴 사용 가이드",
    preview: "문서 결재 흐름과 보안 정책이 업데이트되어 공유드립니다.",
    receivedAt: "어제",
    aiTag: "핵심",
    body:
      "신규 협업 툴 사용 가이드 문서를 공유드립니다.\n" +
      "주요 변경: 문서 결재 흐름 표준화, 권한 분리 정책 강화, 반출 절차 명시.",
  },
  {
    id: "m3",
    from: "보안운영팀",
    subject: "[주의] 외부 메일 링크 클릭 유의",
    preview: "유사 피싱 메일 유입 사례가 확인되어 보안 수칙을 재안내합니다.",
    receivedAt: "2월 20일",
    aiTag: "주의",
    body:
      "최근 외부 발신자로 위장한 피싱 메일 사례가 확인되었습니다.\n" +
      "출처가 불분명한 첨부파일/링크는 열람하지 마시고 보안운영팀으로 즉시 전달해 주세요.",
  },
];

const TAG_STYLES: Record<NonNullable<MailItem["aiTag"]>, string> = {
  핵심: "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300",
  주의: "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300",
  요청: "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900/50 dark:bg-sky-950/30 dark:text-sky-300",
};

type FolderId = "inbox" | "sent" | "starred" | "archive";

const FOLDERS: { id: FolderId; label: string; icon: typeof Inbox; count: number }[] = [
  { id: "inbox", label: "받은편지함", icon: Inbox, count: 24 },
  { id: "sent", label: "보낸편지함", icon: Send, count: 8 },
  { id: "starred", label: "중요 메일", icon: Star, count: 6 },
  { id: "archive", label: "보관함", icon: Archive, count: 11 },
];

export default function WorkspaceMailPage() {
  const [folder, setFolder] = useState<FolderId>("inbox");
  const [activeId, setActiveId] = useState(SAMPLE_MAILS[0]?.id ?? "");
  const [query, setQuery] = useState("");
  const [composing, setComposing] = useState(false);
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return SAMPLE_MAILS;
    return SAMPLE_MAILS.filter(
      (mail) =>
        mail.subject.toLowerCase().includes(q) ||
        mail.from.toLowerCase().includes(q) ||
        mail.preview.toLowerCase().includes(q)
    );
  }, [query]);

  const active = filtered.find((mail) => mail.id === activeId) ?? filtered[0] ?? null;

  return (
    <div className="grid h-[calc(100vh-5.5rem)] gap-0 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#141518] lg:grid-cols-[220px,minmax(0,380px),1fr]">
      <aside className="flex flex-col border-r border-slate-200 dark:border-white/10">
        <div className="shrink-0 p-3">
          <Button
            type="button"
            onClick={() => {
              setComposing(true);
              setTo("");
              setSubject("");
              setBody("");
            }}
            className="w-full justify-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-500"
          >
            <Pencil className="h-4 w-4" />
            메일 작성
          </Button>
        </div>
        <div className="p-3">
          {FOLDERS.map((item) => {
            const Icon = item.icon;
            const isActive = folder === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setFolder(item.id)}
                className={`mb-0.5 flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm transition ${
                  isActive
                    ? "bg-emerald-500 font-medium text-white"
                    : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-white/5"
                }`}
              >
                <span className="inline-flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {item.label}
                </span>
                <span className={`text-xs tabular-nums ${isActive ? "text-white/90" : "text-slate-500 dark:text-slate-400"}`}>{item.count}</span>
              </button>
            );
          })}
        </div>
        <div className="mt-auto border-t border-slate-200 p-3 dark:border-white/10">
          <p className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <Sparkles className="h-3.5 w-3.5" />
            AI 분석
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            요청/주의/핵심 태그로 우선순위를 표시합니다.
          </p>
        </div>
      </aside>

      <section className="flex flex-col border-r border-slate-200 dark:border-white/10">
        <div className="shrink-0 border-b border-slate-200 p-2 dark:border-white/10">
          <label className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-white/5">
            <Search className="h-4 w-4 shrink-0 text-slate-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="메일 검색"
              className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
            />
          </label>
        </div>
        <ul className="min-h-0 flex-1 divide-y divide-slate-100 overflow-auto dark:divide-white/5">
          {filtered.map((mail) => (
            <li key={mail.id}>
              <button
                type="button"
                onClick={() => setActiveId(mail.id)}
                className={`w-full px-4 py-3 text-left transition ${
                  active?.id === mail.id
                    ? "bg-emerald-50 dark:bg-emerald-950/20"
                    : "hover:bg-slate-50 dark:hover:bg-white/5"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className={`text-sm ${mail.unread ? "font-semibold text-slate-900 dark:text-slate-100" : "text-slate-700 dark:text-slate-300"}`}>
                    {mail.from}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{mail.receivedAt}</p>
                </div>
                <p className={`mt-1 text-sm ${mail.unread ? "font-semibold text-slate-900 dark:text-slate-100" : "text-slate-800 dark:text-slate-200"}`}>
                  {mail.subject}
                </p>
                <p className="mt-1 line-clamp-1 text-xs text-slate-600 dark:text-slate-400">{mail.preview}</p>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="flex min-h-0 flex-col overflow-auto p-4">
        {composing ? (
          <div className="flex flex-1 flex-col">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">새 메일</h2>
              <Button type="button" variant="ghost" size="sm" onClick={() => setComposing(false)}>
                취소
              </Button>
            </div>
            <form
              className="space-y-4"
              onSubmit={(e) => {
                e.preventDefault();
                if (!to.trim() || !subject.trim()) return;
                setComposing(false);
                setTo("");
                setSubject("");
                setBody("");
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="mail-to">받는 사람</Label>
                <Input
                  id="mail-to"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  placeholder="수신자 이메일 또는 이름"
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mail-subject">제목</Label>
                <Input
                  id="mail-subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="제목"
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="mail-body">본문</Label>
                <Textarea
                  id="mail-body"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="메일 내용을 입력하세요."
                  rows={12}
                  className="min-h-[200px] resize-y"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={!to.trim() || !subject.trim()} className="bg-emerald-600 hover:bg-emerald-500">
                  <Send className="mr-2 h-4 w-4" />
                  보내기
                </Button>
                <Button type="button" variant="outline" onClick={() => setComposing(false)}>
                  취소
                </Button>
              </div>
            </form>
          </div>
        ) : !active ? (
          <div className="flex flex-1 flex-col items-center justify-center text-center">
            <Inbox className="h-12 w-12 text-slate-300 dark:text-slate-500" />
            <p className="mt-3 text-sm font-medium text-slate-500 dark:text-slate-400">메일을 선택하세요</p>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-slate-500 dark:text-slate-400">{active.from}</p>
                <h2 className="mt-1 text-base font-semibold text-slate-900 dark:text-slate-100">{active.subject}</h2>
              </div>
              {active.aiTag ? (
                <span className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${TAG_STYLES[active.aiTag]}`}>
                  <Tag className="h-3.5 w-3.5" />
                  {active.aiTag}
                </span>
              ) : null}
            </div>

            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
              {active.body.split("\n").map((line, i) => (
                <p key={i}>{line || "\u00A0"}</p>
              ))}
            </div>

            <div className="mt-4 rounded-lg border border-emerald-200/70 bg-emerald-50/80 p-3 dark:border-emerald-900/40 dark:bg-emerald-950/20">
              <p className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                <Sparkles className="h-3.5 w-3.5" />
                AI 요약
              </p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                {active.aiTag ?? "일반"} 분류. 후속 업무는 직원 포털에서 업무 제출로 등록하세요.
              </p>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
