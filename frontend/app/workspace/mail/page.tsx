"use client";

import { useEffect, useMemo, useState } from "react";
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
  Loader2,
  CheckCircle2,
  Info,
  X,
  ShieldAlert,
  FlaskConical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
const API_BASE = typeof window !== "undefined" ? (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") : "http://localhost:8000";

export type AddressBookEntry = {
  id: string;
  type: "person" | "shared" | "group";
  displayName: string;
  email: string;
  department: string;
  source: string;
};

const ADDRESS_TYPE_LABEL: Record<string, string> = {
  person: "직원",
  shared: "공용",
  group: "그룹",
};

function formatAddressLabel(entry: AddressBookEntry): string {
  if (entry.email?.trim()) return `${entry.displayName} (${entry.email})`;
  return `${entry.displayName} [${entry.id}]`;
}

function AddressTypeBadge({ type }: { type: string }) {
  const label = ADDRESS_TYPE_LABEL[type] ?? type;
  const style =
    type === "person"
      ? "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
      : type === "shared"
        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200"
        : "bg-teal-100 text-teal-800 dark:bg-teal-900/50 dark:text-teal-200";
  return (
    <span className={`inline-flex shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}

type ClassifyResult = {
  classification: { is_performance: boolean; competency_labels: string[] };
  performance_record_id: string | null;
  raw_response?: string;
} | null;

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
  /** 분석 상태: PENDING/PROCESSING → 분석 중, SUCCESS → 완료, FAILED → 실패 */
  aiStatus?: string;
  spamScore?: number;
  status?: string;
};

/** API mail_items 응답 1건 */
type MailApiItem = {
  id: string;
  folder: string;
  ownerEmployeeId: string;
  fromDisplay: string;
  fromEmail?: string;
  toDisplay?: string;
  toEmail?: string;
  subject: string;
  body?: string;
  sentAt?: string;
  receivedAt?: string;
  createdAt?: string;
  isStarred: boolean;
  isUnread: boolean;
  aiStatus?: string;
  spamScore?: number;
  status?: string;
};

function apiMailToMailItem(api: MailApiItem): MailItem {
  const body = api.body ?? "";
  const when = api.receivedAt ?? api.sentAt ?? api.createdAt ?? "";
  let receivedAt = "방금 전";
  if (when) {
    try {
      const d = new Date(when);
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      if (diffMs < 60_000) receivedAt = "방금 전";
      else if (diffMs < 24 * 60 * 60 * 1000) receivedAt = d.toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit" });
      else if (diffMs < 7 * 24 * 60 * 60 * 1000) receivedAt = `${Math.floor(diffMs / (24 * 60 * 60 * 1000))}일 전`;
      else receivedAt = d.toLocaleDateString("ko-KR", { month: "numeric", day: "numeric" });
    } catch {
      receivedAt = when.slice(0, 10);
    }
  }
  return {
    id: api.id,
    from: api.fromDisplay || "me",
    to: api.toDisplay,
    subject: api.subject || "(제목 없음)",
    preview: body.slice(0, 50) || "(내용 없음)",
    receivedAt,
    unread: api.isUnread,
    starred: api.isStarred,
    body,
    aiStatus: api.aiStatus,
    spamScore: api.spamScore,
    status: api.status,
  };
}

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

type FolderId = "inbox" | "sent" | "drafts" | "starred" | "trash" | "spam" | "spam-test";

const FOLDERS: { id: FolderId; label: string; icon: typeof Inbox }[] = [
  { id: "inbox", label: "받은편지함", icon: Inbox },
  { id: "sent", label: "보낸편지함", icon: Send },
  { id: "drafts", label: "임시보관", icon: Mail },
  { id: "starred", label: "중요 메일", icon: Star },
  { id: "spam", label: "스팸함", icon: ShieldAlert },
  { id: "trash", label: "휴지통", icon: Trash2 },
  { id: "spam-test", label: "스팸 테스트", icon: FlaskConical },
];

export default function WorkspaceMailPage() {
  const [folder, setFolder] = useState<FolderId>("inbox");
  const [activeId, setActiveId] = useState<string | null>(SAMPLE_INBOX[0]?.id ?? null);
  const [query, setQuery] = useState("");
  const [composing, setComposing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [addressBook, setAddressBook] = useState<AddressBookEntry[]>([]);

  // DB 메일 유지: 직원 ID를 localStorage에 저장해 새로고침·재방문 시 복원
  const MAIL_EMPLOYEE_ID_KEY = "workspace-mail-employeeId";
  useEffect(() => {
    if (typeof window === "undefined") return;
    const saved = localStorage.getItem(MAIL_EMPLOYEE_ID_KEY);
    if (saved != null && saved.trim() !== "") setEmployeeId(saved.trim());
  }, []);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (employeeId.trim()) localStorage.setItem(MAIL_EMPLOYEE_ID_KEY, employeeId.trim());
  }, [employeeId]);
  const [addressBookLoading, setAddressBookLoading] = useState(false);
  const [toRecipient, setToRecipient] = useState<AddressBookEntry | null>(null);
  const [toSearch, setToSearch] = useState("");
  const [toDropdownOpen, setToDropdownOpen] = useState(false);
  const [mails, setMails] = useState<MailItem[]>([]);
  const [sentMails, setSentMails] = useState<MailItem[]>([]);
  const [draftMails, setDraftMails] = useState<MailItem[]>([]);
  const [trashMails, setTrashMails] = useState<MailItem[]>([]);
  const [spamMails, setSpamMails] = useState<MailItem[]>([]);
  const [mailLoading, setMailLoading] = useState(false);
  const [spamTestResult, setSpamTestResult] = useState<{ type: "ham" | "spam" | "rejected"; folder: string; mailId?: string; error?: string } | null>(null);
  const [spamTestLoading, setSpamTestLoading] = useState<"ham" | "spam" | "rejected" | null>(null);
  const [llamaClassifyResult, setLlamaClassifyResult] = useState<{ spam_prob?: number; label?: string; confidence?: string } | { error: string } | null>(null);
  const [llamaClassifyLoading, setLlamaClassifyLoading] = useState(false);
  const [classifyLoading, setClassifyLoading] = useState(false);
  const [classifyResult, setClassifyResult] = useState<ClassifyResult>(null);

  const list =
    folder === "inbox"
      ? mails
      : folder === "sent"
        ? sentMails
        : folder === "drafts"
          ? draftMails
          : folder === "trash"
            ? trashMails
            : folder === "spam"
              ? spamMails
              : folder === "starred"
                ? [...mails, ...sentMails].filter((m) => m.starred)
                : [];

  const toFilteredEntries = useMemo(() => {
    const q = toSearch.trim().toLowerCase();
    if (!q) return addressBook.slice(0, 50);
    return addressBook
      .filter(
        (e) =>
          e.displayName?.toLowerCase().includes(q) ||
          e.email?.toLowerCase().includes(q) ||
          e.id?.toLowerCase().includes(q) ||
          e.department?.toLowerCase().includes(q)
      )
      .slice(0, 50);
  }, [addressBook, toSearch]);

  // 폴더별 메일 목록 API 조회 (받은/보낸/임시보관/휴지통/스팸) — 실제 DB 직원 ID 기준
  const fetchMailFolder = (folderId: "inbox" | "sent" | "draft" | "trash" | "spam") => {
    const owner = employeeId.trim();
    if (!owner) {
      setMails([]);
      setSentMails([]);
      setDraftMails([]);
      setTrashMails([]);
      setSpamMails([]);
      return;
    }
    setMailLoading(true);
    fetch(`${API_BASE}/api/mail?folder=${folderId}&ownerEmployeeId=${encodeURIComponent(owner)}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: MailApiItem[]) => {
        const items = Array.isArray(data) ? data.map(apiMailToMailItem) : [];
        if (folderId === "inbox") setMails(items);
        else if (folderId === "sent") setSentMails(items);
        else if (folderId === "draft") setDraftMails(items);
        else if (folderId === "trash") setTrashMails(items);
        else if (folderId === "spam") setSpamMails(items);
      })
      .catch(() => {
        if (folderId === "inbox") setMails([]);
        else if (folderId === "sent") setSentMails([]);
        else if (folderId === "draft") setDraftMails([]);
        else if (folderId === "trash") setTrashMails([]);
        else if (folderId === "spam") setSpamMails([]);
      })
      .finally(() => setMailLoading(false));
  };

  useEffect(() => {
    if (!employeeId.trim()) return;
    if (folder === "inbox") fetchMailFolder("inbox");
    else if (folder === "sent") fetchMailFolder("sent");
    else if (folder === "drafts") fetchMailFolder("draft");
    else if (folder === "trash") fetchMailFolder("trash");
    else if (folder === "spam") fetchMailFolder("spam");
  }, [folder, employeeId]);

  // 5.4 받은편지함/스팸함 폴링 (4초). 탭 비활성 시 스킵, 포커스 시 즉시 재조회
  const POLL_INTERVAL_MS = 4000;
  useEffect(() => {
    if (!employeeId.trim() || (folder !== "inbox" && folder !== "spam")) return;
    let timer: ReturnType<typeof setInterval> | null = null;
    const poll = () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
      if (folder === "inbox") fetchMailFolder("inbox");
      else if (folder === "spam") fetchMailFolder("spam");
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") poll();
    };
    document.addEventListener("visibilitychange", onVisibility);
    timer = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      if (timer) clearInterval(timer);
    };
  }, [folder, employeeId]);

  // 메일 쓰기 열릴 때마다 주소록 API에서 최신 조회 (직원+공용+그룹 모두 DB 기준)
  useEffect(() => {
    if (!composing) return;
    let cancelled = false;
    setAddressBookLoading(true);
    fetch(`${API_BASE}/api/address-book`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data: AddressBookEntry[]) => {
        if (!cancelled) setAddressBook(Array.isArray(data) ? data : []);
      })
      .catch(() => { if (!cancelled) setAddressBook([]); })
      .finally(() => { if (!cancelled) setAddressBookLoading(false); });
    return () => { cancelled = true; };
  }, [composing]);

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
    return list.find((m) => m.id === activeId) ?? null;
  }, [activeId, list]);

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
    const nextStarred = !list.find((m) => m.id === id)?.starred;
    fetch(`${API_BASE}/api/mail/${encodeURIComponent(id)}?isStarred=${nextStarred}`, { method: "PUT" })
      .then(() => {
        if (folder === "inbox") fetchMailFolder("inbox");
        else if (folder === "sent") fetchMailFolder("sent");
        else if (folder === "drafts") fetchMailFolder("draft");
        else if (folder === "trash") fetchMailFolder("trash");
        else if (folder === "spam") fetchMailFolder("spam");
        else if (folder === "starred") { fetchMailFolder("inbox"); fetchMailFolder("sent"); }
      })
      .catch(() => {});
    setMails((prev) => prev.map((m) => (m.id === id ? { ...m, starred: nextStarred } : m)));
    setSentMails((prev) => prev.map((m) => (m.id === id ? { ...m, starred: nextStarred } : m)));
    setDraftMails((prev) => prev.map((m) => (m.id === id ? { ...m, starred: nextStarred } : m)));
    setTrashMails((prev) => prev.map((m) => (m.id === id ? { ...m, starred: nextStarred } : m)));
    setSpamMails((prev) => prev.map((m) => (m.id === id ? { ...m, starred: nextStarred } : m)));
  };

  const sendSpamTest = async (type: "ham" | "spam" | "rejected") => {
    setSpamTestResult(null);
    setSpamTestLoading(type);
    // 고정 message_id로 같은 버튼 재클릭 시 멱등(200, 이미 저장) 동작
    const messageId = `${type}-test-sample`;
    const body =
      type === "ham"
        ? {
            to_email: "hr@company.com",
            from_display: "김동료",
            from_email: "kim@company.com",
            subject: "3월 15일 회의 일정 확인 부탁드립니다",
            body: "안녕하세요. 다음 주 회의 장소와 안건 공유 부탁드립니다.",
            message_id: messageId,
          }
        : type === "spam"
          ? {
              to_email: "hr@company.com",
              from_display: "광고",
              from_email: "noreply@spam.example.com",
              subject: "당첨 안내! 지금 클릭해 무료 혜택 받으세요",
              body: "축하합니다. 당첨되셨습니다. 링크를 클릭해 비밀번호를 입력해 주세요. 한정 기간 무료.",
              message_id: messageId,
            }
          : {
              to_email: "not-in-address-book@example.com",
              from_display: "외부 발신",
              from_email: "external@example.com",
              subject: "주소록에 없는 수신자 테스트",
              body: "Resolver 실패 → status=REJECTED, folder=rejected 저장 확인용.",
              message_id: messageId,
            };
    try {
      const res = await fetch(`${API_BASE}/api/mail/receive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setSpamTestResult({
          type,
          folder: "",
          error: typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || res.statusText),
        });
        return;
      }
      const folder = data.folder ?? data.mail?.folder ?? "";
      setSpamTestResult({
        type,
        folder,
        mailId: data.mail?.id,
      });
      if (employeeId.trim()) {
        fetchMailFolder("inbox");
        fetchMailFolder("spam");
      }
    } catch (e) {
      setSpamTestResult({
        type,
        folder: "",
        error: e instanceof Error ? e.message : "요청 실패",
      });
    } finally {
      setSpamTestLoading(null);
    }
  };

  const callLlamaClassifySpam = async () => {
    setLlamaClassifyResult(null);
    setLlamaClassifyLoading(true);
    const email_metadata = {
      subject: "당첨 안내! 지금 클릭해 무료 혜택 받으세요",
      sender: "noreply@spam.example.com",
      body: "축하합니다. 당첨되셨습니다. 링크를 클릭해 비밀번호를 입력해 주세요. 한정 기간 무료.",
      recipient: "hr@company.com",
    };
    try {
      const res = await fetch(`${API_BASE}/internal/llama/classify_spam`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email_metadata }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setLlamaClassifyResult({ error: typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || res.statusText) });
        return;
      }
      const result = data.result ?? data;
      setLlamaClassifyResult({
        spam_prob: result.spam_prob,
        label: result.label,
        confidence: result.confidence,
      });
    } catch (e) {
      setLlamaClassifyResult({ error: e instanceof Error ? e.message : "요청 실패" });
    } finally {
      setLlamaClassifyLoading(false);
    }
  };

  const markAsRead = (id: string) => {
    fetch(`${API_BASE}/api/mail/${encodeURIComponent(id)}?isUnread=false`, { method: "PUT" }).catch(() => {});
    setMails((prev) => prev.map((m) => (m.id === id ? { ...m, unread: false } : m)));
    setSentMails((prev) => prev.map((m) => (m.id === id ? { ...m, unread: false } : m)));
    setDraftMails((prev) => prev.map((m) => (m.id === id ? { ...m, unread: false } : m)));
    setTrashMails((prev) => prev.map((m) => (m.id === id ? { ...m, unread: false } : m)));
  };

  const deleteSelected = async () => {
    const ids = Array.from(selectedIds);
    const permanent = folder === "trash";
    for (const id of ids) {
      const url = permanent
        ? `${API_BASE}/api/mail/${encodeURIComponent(id)}?permanent=true`
        : `${API_BASE}/api/mail/${encodeURIComponent(id)}`;
      await fetch(url, { method: "DELETE" }).catch(() => {});
    }
    if (folder === "inbox") fetchMailFolder("inbox");
    else if (folder === "sent") fetchMailFolder("sent");
    else if (folder === "drafts") fetchMailFolder("draft");
    else if (folder === "trash") fetchMailFolder("trash");
    else if (folder === "starred") {
      fetchMailFolder("inbox");
      fetchMailFolder("sent");
    }
    setSelectedIds(new Set());
    setActiveId(null);
  };

  const openCompose = () => {
    setComposing(true);
    setClassifyResult(null);
    setToRecipient(null);
    setToSearch("");
    setToDropdownOpen(false);
    setSubject("");
    setBody("");
  };

  const sendMail = async (e: React.FormEvent) => {
    e.preventDefault();
    const owner = employeeId.trim();
    if (!owner) {
      setClassifyResult({ classification: { is_performance: false, competency_labels: [] }, performance_record_id: null, raw_response: "메일함 소유자(직원 ID)를 입력하세요." });
      return;
    }
    if (!toRecipient || !subject.trim()) return;
    const subjectText = subject.trim();
    const bodyText = body.trim();
    setClassifyResult(null);
    setClassifyLoading(true);
    try {
      const sendRes = await fetch(`${API_BASE}/api/mail/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          senderEmployeeId: owner,
          to: {
            id: toRecipient.id,
            displayName: toRecipient.displayName,
            email: toRecipient.email || undefined,
          },
          subject: subjectText,
          body: bodyText || undefined,
        }),
      });
      if (!sendRes.ok) {
        const errData = await sendRes.json().catch(() => ({}));
        throw new Error(errData.detail || `발송 실패: ${sendRes.status}`);
      }
      const sendData = await sendRes.json();
      const saved = sendData.mail as MailApiItem | undefined;
      if (saved) setSentMails((prev) => [apiMailToMailItem(saved), ...prev]);
      else fetchMailFolder("sent");

      setComposing(false);
      setToRecipient(null);
      setToSearch("");
      setSubject("");
      setBody("");

      const classifyRes = await fetch(`${API_BASE}/api/mail/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: subjectText,
          body: bodyText || undefined,
          employeeId: owner,
        }),
      });
      if (!classifyRes.ok) throw new Error(`분류 실패: ${classifyRes.status}`);
      const classifyData = await classifyRes.json();
      setClassifyResult({
        classification: classifyData.classification ?? { is_performance: false, competency_labels: [] },
        performance_record_id: classifyData.performance_record_id ?? null,
        raw_response: classifyData.raw_response,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "요청 실패";
      setClassifyResult({
        classification: { is_performance: false, competency_labels: [] },
        performance_record_id: null,
        raw_response: msg,
      });
    } finally {
      setClassifyLoading(false);
    }
  };

  return (
    <div className="grid h-[calc(100vh-5.5rem)] gap-0 overflow-hidden rounded-xl border border-[#a8d5c4] bg-white shadow-sm dark:border-primary/30 dark:bg-card lg:grid-cols-[200px,minmax(0,360px),1fr]">
      {/* 왼쪽: 폴더 */}
      <aside className="flex flex-col border-r border-[#a8d5c4]/60 dark:border-primary/20">
        <div className="shrink-0 space-y-2 p-3">
          <div className="grid gap-1">
            <Label htmlFor="mail-owner-id" className="text-xs text-slate-600 dark:text-muted-foreground">내 메일함 (직원 ID)</Label>
            <Input
              id="mail-owner-id"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              placeholder="예: E001"
              className="h-9 border-[#a8d5c4]/60 bg-white text-sm dark:border-primary/30 dark:bg-card"
            />
          </div>
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
          {mailLoading && filtered.length === 0 ? (
            <li className="flex flex-col items-center justify-center py-12 text-center">
              <Loader2 className="h-10 w-10 animate-spin text-slate-400 dark:text-muted-foreground" />
              <p className="mt-2 text-sm text-slate-500 dark:text-muted-foreground">메일 목록 불러오는 중…</p>
            </li>
          ) : folder === "spam-test" ? (
            <li className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <FlaskConical className="h-10 w-10 text-slate-400 dark:text-muted-foreground" />
              <p className="mt-2 text-sm text-slate-500 dark:text-muted-foreground">스팸 판정 테스트는 오른쪽 패널에서 진행하세요.</p>
            </li>
          ) : !employeeId.trim() ? (
            <li className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <Inbox className="h-10 w-10 text-slate-400 dark:text-muted-foreground" />
              <p className="mt-2 text-sm text-slate-500 dark:text-muted-foreground">왼쪽에 내 메일함(직원 ID)을 입력하세요.</p>
            </li>
          ) : filtered.length === 0 ? (
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
                {(folder === "inbox" || folder === "spam") && mail.aiStatus && (
                  <span className="shrink-0 flex items-center" title={mail.aiStatus === "PENDING" || mail.aiStatus === "PROCESSING" ? "분석 중" : mail.aiStatus === "SUCCESS" ? "분석 완료" : "분석 실패"}>
                    {mail.aiStatus === "PENDING" || mail.aiStatus === "PROCESSING" ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-400 dark:text-muted-foreground" />
                    ) : mail.aiStatus === "SUCCESS" ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                    ) : mail.aiStatus === "FAILED" ? (
                      <ShieldAlert className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                    ) : null}
                  </span>
                )}
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
        {classifyLoading && (
          <div className="shrink-0 flex items-center gap-2 border-b border-[#a8d5c4]/40 bg-[#e8f5ef]/80 px-4 py-3 text-sm text-slate-700 dark:border-primary/20 dark:bg-primary/10 dark:text-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            AI 분류 중 (성과·5대 역량 판단)…
          </div>
        )}
        {!classifyLoading && classifyResult && (
          <div className={`shrink-0 flex flex-wrap items-center justify-between gap-2 border-b px-4 py-3 ${
            classifyResult.performance_record_id == null && classifyResult.raw_response && classifyResult.raw_response.length < 100
              ? "border-amber-200 bg-amber-50 dark:border-amber-900/50 dark:bg-amber-950/30"
              : "border-[#a8d5c4]/40 bg-[#e8f5ef] dark:border-primary/20 dark:bg-primary/15"
          }`}>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              {classifyResult.performance_record_id != null || classifyResult.classification.competency_labels.length > 0 ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              ) : (
                <Info className="h-4 w-4 text-amber-600 dark:text-amber-400" />
              )}
              <span className="font-medium text-slate-800 dark:text-foreground">AI 분류 결과</span>
              <span className="text-slate-600 dark:text-muted-foreground">
                {classifyResult.classification.is_performance ? "성과 기록됨" : "성과 미기록"}
                {classifyResult.classification.competency_labels.length > 0 && (
                  <> · 역량: {classifyResult.classification.competency_labels.join(", ")}</>
                )}
              </span>
              {classifyResult.performance_record_id && (
                <span className="text-xs text-slate-500 dark:text-muted-foreground">(ID: {classifyResult.performance_record_id})</span>
              )}
              {classifyResult.raw_response && classifyResult.raw_response.length < 100 && !classifyResult.performance_record_id && (
                <span className="text-xs text-amber-700 dark:text-amber-400">({classifyResult.raw_response})</span>
              )}
            </div>
            <Button type="button" variant="ghost" size="sm" className="text-slate-600 hover:text-slate-900 dark:text-muted-foreground dark:hover:text-foreground" onClick={() => setClassifyResult(null)}>
              닫기
            </Button>
          </div>
        )}
        {folder === "spam-test" ? (
          <div className="flex flex-1 flex-col gap-4 overflow-auto p-4">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-foreground">스팸 판정 테스트 (5단계 검증)</h2>
            <p className="text-sm text-slate-600 dark:text-muted-foreground">
              수신 시 스팸 여부에 따라 <strong>folder=inbox</strong> vs <strong>folder=spam</strong>으로 저장됩니다. 전송 후 워커가 분석하므로, 받은편지함/스팸함은 잠시 후 자동 갱신되거나 새로고침으로 확인하세요.
            </p>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-700 dark:bg-slate-900/50">
              <p className="font-medium text-slate-800 dark:text-foreground">판정 기준 (현재)</p>
              <ul className="mt-1 list-inside list-disc text-slate-600 dark:text-muted-foreground">
                <li>스팸 감지 결과 <strong>action</strong>이 <strong>deliver</strong>이면 → 받은편지함</li>
                <li>그 외(reject, quarantine, deliver_with_warning 등) → 스팸함</li>
              </ul>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-[#a8d5c4]/60 bg-white p-4 shadow-sm dark:border-primary/20 dark:bg-card">
                <h3 className="font-medium text-slate-900 dark:text-foreground">1) 정상 메일(햄) → 받은편지함 기대</h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-muted-foreground">제목: 3월 15일 회의 일정 확인… / 본문: 회의 장소와 안건 공유…</p>
                <Button
                  type="button"
                  className="mt-3 w-full border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
                  onClick={() => sendSpamTest("ham")}
                  disabled={!!spamTestLoading}
                >
                  {spamTestLoading === "ham" ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : "테스트 전송 (햄)"}
                </Button>
              </div>
              <div className="rounded-lg border border-[#a8d5c4]/60 bg-white p-4 shadow-sm dark:border-primary/20 dark:bg-card">
                <h3 className="font-medium text-slate-900 dark:text-foreground">2) 스팸성 메일 → 스팸함 기대</h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-muted-foreground">제목: 당첨 안내! 무료 혜택… / 본문: 클릭해 비밀번호 입력…</p>
                <Button
                  type="button"
                  className="mt-3 w-full border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
                  onClick={() => sendSpamTest("spam")}
                  disabled={!!spamTestLoading}
                >
                  {spamTestLoading === "spam" ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : "테스트 전송 (스팸)"}
                </Button>
              </div>
              <div className="rounded-lg border border-amber-200 bg-amber-50/80 p-4 shadow-sm dark:border-amber-800/50 dark:bg-amber-950/20">
                <h3 className="font-medium text-slate-900 dark:text-foreground">3) 주소 없음(REJECTED) → rejected 저장 기대</h3>
                <p className="mt-1 text-xs text-slate-500 dark:text-muted-foreground">to_email=not-in-address-book@example.com → Resolver 실패 → status=REJECTED, folder=rejected</p>
                <Button
                  type="button"
                  className="mt-3 w-full border border-amber-300 bg-amber-100 text-slate-800 hover:border-amber-400 dark:border-amber-700 dark:bg-amber-900/30 dark:text-foreground"
                  onClick={() => sendSpamTest("rejected")}
                  disabled={!!spamTestLoading}
                >
                  {spamTestLoading === "rejected" ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : "테스트 전송 (주소 없음)"}
                </Button>
              </div>
            </div>
            {spamTestResult && (
              <div className={`rounded-lg border p-4 ${spamTestResult.error ? "border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/30" : "border-[#a8d5c4]/60 bg-[#e8f5ef]/50 dark:border-primary/20 dark:bg-primary/10"}`}>
                <p className="font-medium text-slate-800 dark:text-foreground">
                  {spamTestResult.type === "ham" ? "정상 메일" : spamTestResult.type === "spam" ? "스팸 메일" : "주소 없음"} 테스트 결과
                </p>
                {spamTestResult.error ? (
                  <p className="mt-1 text-sm text-red-700 dark:text-red-400">{spamTestResult.error}</p>
                ) : (
                  <>
                    <p className="mt-1 text-sm text-slate-600 dark:text-muted-foreground">
                      저장 폴더: <strong>{spamTestResult.folder}</strong>
                      {spamTestResult.mailId && ` · 메일 ID: ${spamTestResult.mailId}`}
                      {spamTestResult.type === "ham" && spamTestResult.folder === "inbox" && " ✓ 기대대로 받은편지함"}
                      {spamTestResult.type === "spam" && spamTestResult.folder === "spam" && " ✓ 기대대로 스팸함"}
                      {spamTestResult.type === "rejected" && spamTestResult.folder === "rejected" && " ✓ 기대대로 REJECTED (받은편지함에 안 보임)"}
                    </p>
                    <p className="mt-2 text-xs text-slate-500 dark:text-muted-foreground">
                      전송됨. 워커가 분석 중입니다. 받은편지함/스팸함은 4초마다 자동 갱신되거나 새로고침으로 확인하세요.
                    </p>
                  </>
                )}
              </div>
            )}
            <div className="rounded-lg border border-[#a8d5c4]/60 bg-white p-4 shadow-sm dark:border-primary/20 dark:bg-card">
              <h3 className="font-medium text-slate-900 dark:text-foreground">4) LLaMA 스팸 분류만 확인 (선택)</h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-muted-foreground">
                POST /internal/llama/classify_spam 호출. spam_prob, label(SPAM/HAM/SUSPICIOUS)로 스팸 판단 여부 확인.
              </p>
              <Button
                type="button"
                className="mt-3 w-full border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
                onClick={callLlamaClassifySpam}
                disabled={llamaClassifyLoading}
              >
                {llamaClassifyLoading ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : "분류만 확인 (스팸 예시)"}
              </Button>
              {llamaClassifyResult && (
                <div className={`mt-3 rounded border p-3 text-sm ${"error" in llamaClassifyResult ? "border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/30" : "border-[#a8d5c4]/40 bg-[#e8f5ef]/50 dark:border-primary/20 dark:bg-primary/10"}`}>
                  {"error" in llamaClassifyResult ? (
                    <p className="text-red-700 dark:text-red-400">{llamaClassifyResult.error}</p>
                  ) : (
                    <p className="text-slate-700 dark:text-foreground">
                      <strong>spam_prob</strong>: {llamaClassifyResult.spam_prob ?? "—"} · <strong>label</strong>: {llamaClassifyResult.label ?? "—"} · <strong>confidence</strong>: {llamaClassifyResult.confidence ?? "—"}
                    </p>
                  )}
                </div>
              )}
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-900/50 dark:text-muted-foreground">
              <p className="font-medium text-slate-700 dark:text-foreground">목록으로 확인</p>
              <p className="mt-1">받은편지함 / 스팸함에서 내 메일함(직원 ID)을 hr@company.com 소유자(예: E001)로 설정하면 저장된 메일을 볼 수 있습니다.</p>
              <p className="mt-2">참고: 스팸 감지 실패 시 수신을 막지 않고 inbox로 저장합니다. 라우팅이 rule이면 LLaMA, policy면 ExaOne 결과로 action이 결정됩니다.</p>
            </div>
          </div>
        ) : composing ? (
          <div className="flex flex-1 flex-col p-4">
            <h2 className="mb-4 text-base font-semibold text-slate-900 dark:text-foreground">새 메일</h2>
            <form className="flex flex-1 flex-col gap-4" onSubmit={sendMail}>
              <div className="grid gap-2">
                <p className="text-sm text-slate-600 dark:text-muted-foreground">
                  발신자: <strong>{employeeId || "— 내 메일함(직원 ID)을 왼쪽에 입력하세요"}</strong>
                </p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="mail-to" className="text-slate-600 dark:text-muted-foreground">받는 사람 (사내 주소록)</Label>
                {toRecipient ? (
                  <div className="flex items-center gap-2 rounded-lg border border-[#a8d5c4]/60 bg-[#e8f5ef]/50 px-3 py-2 dark:border-primary/30 dark:bg-primary/10">
                    <AddressTypeBadge type={toRecipient.type} />
                    <span className="flex-1 text-sm font-medium text-slate-800 dark:text-foreground">{formatAddressLabel(toRecipient)}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 shrink-0 p-0 text-slate-500 hover:text-slate-800 dark:hover:text-foreground"
                      onClick={() => { setToRecipient(null); setToSearch(""); setToDropdownOpen(true); }}
                      aria-label="받는 사람 변경"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <div className="relative">
                    <Input
                      id="mail-to"
                      value={toSearch}
                      onChange={(e) => { setToSearch(e.target.value); setToDropdownOpen(true); }}
                      onFocus={() => setToDropdownOpen(true)}
                      placeholder={addressBookLoading ? "주소록 불러오는 중…" : "이름·이메일·부서로 검색 (직원+공용+그룹)"}
                      className="border-[#a8d5c4]/60 bg-white dark:border-primary/30 dark:bg-card"
                      disabled={addressBookLoading}
                    />
                    {toDropdownOpen && (
                      <>
                        <div className="absolute left-0 right-0 top-full z-10 mt-1 max-h-48 overflow-auto rounded-lg border border-[#a8d5c4]/60 bg-white shadow-lg dark:border-primary/30 dark:bg-card" role="listbox">
                          {toFilteredEntries.length === 0 ? (
                            <p className="px-3 py-4 text-center text-sm text-slate-500 dark:text-muted-foreground">
                              {addressBook.length === 0 ? "주소록이 비어 있습니다." : "검색 결과가 없습니다."}
                            </p>
                          ) : (
                            toFilteredEntries.map((entry) => (
                              <button
                                key={`${entry.source}-${entry.id}`}
                                type="button"
                                role="option"
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-[#e8f5ef] dark:hover:bg-primary/15"
                                onClick={() => { setToRecipient(entry); setToSearch(""); setToDropdownOpen(false); }}
                              >
                                <AddressTypeBadge type={entry.type} />
                                <span className="min-w-0 flex-1 truncate">{formatAddressLabel(entry)}</span>
                                {entry.department && <span className="shrink-0 text-xs text-slate-500 dark:text-muted-foreground">{entry.department}</span>}
                              </button>
                            ))
                          )}
                        </div>
                        <div className="fixed inset-0 z-[9]" aria-hidden onClick={() => setToDropdownOpen(false)} />
                      </>
                    )}
                  </div>
                )}
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
                  disabled={!employeeId.trim() || !toRecipient || !subject.trim()}
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
