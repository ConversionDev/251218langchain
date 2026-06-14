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
  fromEmail?: string;
  to?: string;
  toEmail?: string;
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
  /** 역량 분류 결과(JSON 문자열): {kind,model,is_performance,competency_labels} */
  aiResultRaw?: string;
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
  aiResultRaw?: string;
};

/** 역량 분류 결과 (메일 행 ai_result_raw JSON) */
type Competency = { model?: string; is_performance?: boolean; competency_labels?: string[] };

function parseCompetency(raw?: string): Competency | null {
  if (!raw) return null;
  try {
    const o = JSON.parse(raw);
    if (o && o.kind === "competency") return o as Competency;
  } catch {
    /* ignore */
  }
  return null;
}

const MODEL_LABEL: Record<string, string> = {
  exaone: "EXAONE 파인튜닝",
  gemini: "Gemini",
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
    fromEmail: api.fromEmail,
    to: api.toDisplay,
    toEmail: api.toEmail,
    subject: api.subject || "(제목 없음)",
    preview: body.slice(0, 50) || "(내용 없음)",
    receivedAt,
    unread: api.isUnread,
    starred: api.isStarred,
    body,
    aiStatus: api.aiStatus,
    spamScore: api.spamScore,
    status: api.status,
    aiResultRaw: api.aiResultRaw,
  };
}

type FolderId = "inbox" | "sent" | "drafts" | "starred" | "trash" | "spam" | "spam-test";

// 개발용 메일 도구(스팸 테스트 주입 등) 노출 여부. 배포(Vercel prod)에선 미설정 → 숨김.
const MAIL_DEVTOOLS = process.env.NEXT_PUBLIC_ENABLE_MAIL_DEVTOOLS === "true";

const FOLDERS: { id: FolderId; label: string; icon: typeof Inbox }[] = [
  { id: "inbox", label: "받은편지함", icon: Inbox },
  { id: "sent", label: "보낸편지함", icon: Send },
  { id: "drafts", label: "임시보관", icon: Mail },
  { id: "starred", label: "중요 메일", icon: Star },
  { id: "spam", label: "스팸함", icon: ShieldAlert },
  { id: "trash", label: "휴지통", icon: Trash2 },
  // 스팸 테스트는 개발용 — MAIL_DEVTOOLS가 켜졌을 때만 표시
  { id: "spam-test", label: "스팸 테스트", icon: FlaskConical },
];

// 실제 사용자에게 보이는 폴더 (개발 도구는 플래그로 게이트)
const VISIBLE_FOLDERS = MAIL_DEVTOOLS ? FOLDERS : FOLDERS.filter((f) => f.id !== "spam-test");

export default function WorkspaceMailPage() {
  const [folder, setFolder] = useState<FolderId>("inbox");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [composing, setComposing] = useState(false);
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null);
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
  /** 사내 주소록 vs 외부 이메일 직접 입력 */
  const [recipientMode, setRecipientMode] = useState<"internal" | "external">("internal");
  const [toExternalEmail, setToExternalEmail] = useState("");
  const [toExternalDisplayName, setToExternalDisplayName] = useState("");
  const [mails, setMails] = useState<MailItem[]>([]);
  const [sentMails, setSentMails] = useState<MailItem[]>([]);
  const [draftMails, setDraftMails] = useState<MailItem[]>([]);
  const [trashMails, setTrashMails] = useState<MailItem[]>([]);
  const [spamMails, setSpamMails] = useState<MailItem[]>([]);
  const [starredMails, setStarredMails] = useState<MailItem[]>([]);
  const [mailLoading, setMailLoading] = useState(false);
  const [spamTestResult, setSpamTestResult] = useState<{ type: "ham" | "spam" | "rejected"; folder: string; mailId?: string; error?: string } | null>(null);
  const [spamTestLoading, setSpamTestLoading] = useState<"ham" | "spam" | "rejected" | null>(null);
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
                ? starredMails
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
  const fetchMailFolder = (folderId: "inbox" | "sent" | "draft" | "trash" | "spam" | "starred") => {
    const owner = employeeId.trim();
    if (!owner) {
      setMails([]);
      setSentMails([]);
      setDraftMails([]);
      setTrashMails([]);
      setSpamMails([]);
      setStarredMails([]);
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
        else if (folderId === "starred") setStarredMails(items);
      })
      .catch(() => {
        if (folderId === "inbox") setMails([]);
        else if (folderId === "sent") setSentMails([]);
        else if (folderId === "draft") setDraftMails([]);
        else if (folderId === "trash") setTrashMails([]);
        else if (folderId === "spam") setSpamMails([]);
        else if (folderId === "starred") setStarredMails([]);
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
    else if (folder === "starred") fetchMailFolder("starred");
  }, [folder, employeeId]);

  // 5.4 받은편지함/스팸함/보낸편지함 폴링 (4초). 탭 비활성 시 스킵, 포커스 시 즉시 재조회
  // (보낸편지함: 역량 분류가 백그라운드로 끝나면 배지가 자동 반영되도록 폴링)
  const POLL_INTERVAL_MS = 4000;
  useEffect(() => {
    if (!employeeId.trim() || (folder !== "inbox" && folder !== "spam" && folder !== "sent")) return;
    let timer: ReturnType<typeof setInterval> | null = null;
    const poll = () => {
      if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
      if (folder === "inbox") fetchMailFolder("inbox");
      else if (folder === "spam") fetchMailFolder("spam");
      else if (folder === "sent") fetchMailFolder("sent");
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
        else if (folder === "starred") fetchMailFolder("starred");
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
    const ts = new Date().toISOString().slice(0, 19).replace("T", " ");
    const messageId = `${type}-test-sample`;
    // 마커 없이 내용만으로 분류: 정상 = 업무 문의, 스팸 = 당첨/클릭 유도
    const body =
      type === "ham"
        ? {
            to_email: "hr@mg.kanggyeonggu.store",
            from_display: "김동료",
            from_email: "kim@company.com",
            subject: `회의 일정 확인 부탁드립니다 (${ts})`,
            body: `안녕하세요, 인사팀 김동료입니다.
3월 15일 오후 2시 회의 장소와 안건 공유 부탁드립니다.
회의실 예약 여부만 회신 주시면 됩니다.

감사합니다.`,
            message_id: messageId,
          }
        : type === "spam"
          ? {
              to_email: "hr@mg.kanggyeonggu.store",
              from_display: "광고",
              from_email: "noreply@promo.example.com",
              subject: `당첨 안내! 지금 클릭해 무료 혜택 받으세요 (${ts})`,
              body: `축하합니다! 당첨되셨습니다!
지금 바로 링크를 클릭해 비밀번호를 입력해 주세요.
한정 기간 무료 혜택! 선착 100명!
http://example.com/claim`,
              message_id: messageId,
            }
          : {
              to_email: "not-in-address-book@example.com",
              from_display: "외부 발신",
              from_email: "external@example.com",
              subject: `주소록에 없는 수신자 (${ts})`,
              body: "수신자(To)가 주소록에 없으면 Resolver 실패 → folder=rejected 로 저장됩니다.",
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
    else if (folder === "starred") fetchMailFolder("starred");
    setSelectedIds(new Set());
    setActiveId(null);
  };

  const openCompose = () => {
    setComposing(true);
    setClassifyResult(null);
    setToRecipient(null);
    setToSearch("");
    setToDropdownOpen(false);
    setRecipientMode("internal");
    setToExternalEmail("");
    setToExternalDisplayName("");
    setSubject("");
    setBody("");
    setEditingDraftId(null);
  };

  const openReply = (m: MailItem) => {
    openCompose();
    setRecipientMode("external");
    setToExternalEmail(m.fromEmail || "");
    setToExternalDisplayName(m.from || "");
    setSubject(m.subject.startsWith("Re:") ? m.subject : `Re: ${m.subject}`);
    setBody(`\n\n--- 원본 메일 ---\n${m.body || ""}`);
  };

  const openForward = (m: MailItem) => {
    openCompose();
    setRecipientMode("external");
    setSubject(m.subject.startsWith("Fwd:") ? m.subject : `Fwd: ${m.subject}`);
    setBody(`\n\n--- 전달된 메일 ---\n보낸 사람: ${m.from}\n\n${m.body || ""}`);
  };

  const openDraft = async (m: MailItem) => {
    openCompose();
    setEditingDraftId(m.id);
    setSubject(m.subject === "(제목 없음)" ? "" : m.subject);
    setBody(m.body || "");
    const email = (m.toEmail || "").trim();
    if (!email) {
      setRecipientMode("external");
      setToExternalEmail(m.to || "");
      return;
    }
    // 사내 주소록에 있으면 내부 수신자로 정확히 복원, 없으면 외부 입력으로
    try {
      const res = await fetch(`${API_BASE}/api/address-book`);
      const book: AddressBookEntry[] = res.ok ? await res.json() : [];
      const match = Array.isArray(book)
        ? book.find((e) => e.email && e.email.toLowerCase() === email.toLowerCase())
        : undefined;
      if (match) {
        setRecipientMode("internal");
        setToRecipient(match);
        return;
      }
    } catch {
      /* 주소록 조회 실패 → 외부 입력 폴백 */
    }
    setRecipientMode("external");
    setToExternalEmail(email);
    setToExternalDisplayName(m.to || "");
  };

  const deleteActive = async () => {
    if (!active) return;
    const permanent = folder === "trash";
    const url = permanent
      ? `${API_BASE}/api/mail/${encodeURIComponent(active.id)}?permanent=true`
      : `${API_BASE}/api/mail/${encodeURIComponent(active.id)}`;
    await fetch(url, { method: "DELETE" }).catch(() => {});
    setActiveId(null);
    if (folder === "inbox") fetchMailFolder("inbox");
    else if (folder === "sent") fetchMailFolder("sent");
    else if (folder === "drafts") fetchMailFolder("draft");
    else if (folder === "spam") fetchMailFolder("spam");
    else if (folder === "trash") fetchMailFolder("trash");
    else if (folder === "starred") fetchMailFolder("starred");
  };

  const saveDraft = async () => {
    const owner = employeeId.trim();
    if (!owner) return;
    const toPayload =
      recipientMode === "internal" && toRecipient
        ? { id: toRecipient.id, displayName: toRecipient.displayName, email: toRecipient.email || undefined }
        : recipientMode === "external" && toExternalEmail.trim()
          ? { id: toExternalEmail.trim(), displayName: (toExternalDisplayName || toExternalEmail).trim(), email: toExternalEmail.trim() }
          : undefined;
    await fetch(`${API_BASE}/api/mail/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ownerEmployeeId: owner,
        id: editingDraftId || undefined,
        to: toPayload,
        subject: subject.trim(),
        body: body.trim() || undefined,
      }),
    }).catch(() => {});
    setComposing(false);
    setEditingDraftId(null);
    fetchMailFolder("draft");
  };

  const sendMail = async (e: React.FormEvent) => {
    e.preventDefault();
    const owner = employeeId.trim();
    if (!owner) {
      setClassifyResult({ classification: { is_performance: false, competency_labels: [] }, performance_record_id: null, raw_response: "메일함 소유자(직원 ID)를 입력하세요." });
      return;
    }
    const subjectText = subject.trim();
    if (!subjectText) return;
    const isInternal = recipientMode === "internal";
    const toPayload =
      isInternal && toRecipient
        ? { id: toRecipient.id, displayName: toRecipient.displayName, email: toRecipient.email || undefined }
        : recipientMode === "external" && toExternalEmail.trim()
          ? { id: toExternalEmail.trim(), displayName: (toExternalDisplayName || toExternalEmail).trim(), email: toExternalEmail.trim() }
          : null;
    if (!toPayload) return;
    const bodyText = body.trim();
    setClassifyResult(null);
    setClassifyLoading(true);
    try {
      const sendRes = await fetch(`${API_BASE}/api/mail/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          senderEmployeeId: owner,
          to: toPayload,
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

      // 임시보관에서 작성해 보낸 경우 해당 draft 제거
      if (editingDraftId) {
        fetch(`${API_BASE}/api/mail/${encodeURIComponent(editingDraftId)}?permanent=true`, { method: "DELETE" }).catch(() => {});
        setEditingDraftId(null);
        fetchMailFolder("draft");
      }

      // 역량 분류는 백그라운드(학습 EXAONE)에서 수행 → 보낸편지함 메일에 배지로 채워짐
      setClassifyResult({
        classification: { is_performance: false, competency_labels: [] },
        performance_record_id: null,
        raw_response: "발송 완료 · 역량 분석을 백그라운드에서 진행합니다. 보낸편지함에서 결과 배지를 확인하세요.",
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
          {VISIBLE_FOLDERS.map((item) => {
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
                {(folder === "inbox" || folder === "spam" || folder === "sent") && mail.aiStatus && (
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
                  onClick={() => {
                    if (folder === "drafts") { openDraft(mail); return; }
                    setActiveId(mail.id);
                    markAsRead(mail.id);
                  }}
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
                  {(() => {
                    const c = parseCompetency(mail.aiResultRaw);
                    if (!c || !(c.competency_labels && c.competency_labels.length > 0)) return null;
                    return (
                      <div className="mt-1 flex flex-wrap items-center gap-1">
                        {c.competency_labels.map((lbl) => (
                          <span key={lbl} className="rounded bg-teal-100 px-1.5 py-0.5 text-[10px] font-medium text-teal-800 dark:bg-teal-900/50 dark:text-teal-200">
                            {lbl}
                          </span>
                        ))}
                        <span className="text-[10px] text-slate-400 dark:text-muted-foreground">
                          · {MODEL_LABEL[c.model ?? ""] ?? c.model}
                        </span>
                      </div>
                    );
                  })()}
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
            발송 중…
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
          <div className="flex flex-1 flex-col gap-6 overflow-auto p-4">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-foreground">메일 테스트</h2>

            {/* 사내용 메일 (직원간 테스트) */}
            <section className="rounded-xl border-2 border-[#a8d5c4]/70 bg-[#e8f5ef]/30 p-4 dark:border-primary/40 dark:bg-primary/10">
              <h3 className="mb-1 text-base font-semibold text-slate-900 dark:text-foreground">사내용 메일 (직원간 테스트)</h3>
              <p className="mb-3 text-sm text-slate-600 dark:text-muted-foreground">
                수신자: 주소록(@mg.kanggyeonggu.store). <strong>마커 없이 내용만으로</strong> LLaMA가 정상/스팸을 구분합니다. 직원간 발송은 메일 쓰기에서 사내용(주소록) 선택 시 DB만 반영됩니다.
              </p>
              <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm dark:border-slate-700 dark:bg-slate-900/30">
                <p className="font-medium text-slate-800 dark:text-foreground">판정 기준</p>
                <ul className="mt-1 list-inside list-disc text-slate-600 dark:text-muted-foreground">
                  <li>내용이 정상(업무 문의 등) → 받은편지함</li>
                  <li>내용이 스팸성(당첨/클릭 유도 등) → 스팸함</li>
                </ul>
              </div>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-[#a8d5c4]/60 bg-white p-4 shadow-sm dark:border-primary/20 dark:bg-card">
                  <h4 className="font-medium text-slate-900 dark:text-foreground">1) 정상 메일(햄) → 받은편지함</h4>
                  <p className="mt-1 text-xs text-slate-500 dark:text-muted-foreground">내용: 회의 일정·업무 문의 (정상 메일). 발신: 김동료</p>
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
                  <h4 className="font-medium text-slate-900 dark:text-foreground">2) 스팸성 메일 → 스팸함</h4>
                  <p className="mt-1 text-xs text-slate-500 dark:text-muted-foreground">내용: 당첨·클릭 유도 문구 (스팸성). 발신: 광고</p>
                  <Button
                    type="button"
                    className="mt-3 w-full border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
                    onClick={() => sendSpamTest("spam")}
                    disabled={!!spamTestLoading}
                  >
                    {spamTestLoading === "spam" ? <Loader2 className="mx-auto h-4 w-4 animate-spin" /> : "테스트 전송 (스팸)"}
                  </Button>
                </div>
                <div className="rounded-lg border border-amber-200 bg-amber-50/80 p-4 shadow-sm dark:border-amber-800/50 dark:bg-amber-950/20 sm:col-span-2">
                  <h4 className="font-medium text-slate-900 dark:text-foreground">3) 주소 없음 → REJECTED</h4>
                  <p className="mt-1 text-xs text-slate-500 dark:text-muted-foreground">to=not-in-address-book@example.com → Resolver 실패 → folder=rejected (분류 전에 거부)</p>
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
            </section>

            {/* 외부용 메일 테스트 */}
            <section className="rounded-xl border-2 border-amber-300/80 bg-amber-50/50 p-4 dark:border-amber-700/50 dark:bg-amber-950/20">
              <h3 className="mb-1 text-base font-semibold text-slate-900 dark:text-foreground">외부용 메일 테스트</h3>
              <p className="mb-3 text-sm text-slate-600 dark:text-muted-foreground">
                <strong>외부 주소로 발송</strong>하면 Mailgun API로 실제 전송됩니다. 메일 쓰기에서 받는 사람을 <strong>외부용 (이메일 직접 입력)</strong>으로 바꾼 뒤 이메일을 입력해 보내면 됩니다.
              </p>
              <p className="text-xs text-amber-800 dark:text-amber-200">수신 테스트(위 사내용)와 달리, 여기서는 “우리가 외부로 보내는” 발송만 해당합니다.</p>
            </section>

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
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600 dark:border-slate-700 dark:bg-slate-900/50 dark:text-muted-foreground">
              <p className="font-medium text-slate-700 dark:text-foreground">스팸 분류는 수신 즉시 자동 수행</p>
              <p className="mt-1">메일 수신 시 <strong>서버(rag-api)가 그 자리에서</strong> 스팸 분류 후 folder(spam/inbox)를 정합니다. 분류기는 환경별로 <strong>로컬=LLaMA / 배포=Gemini</strong>. 위 1)·2) 테스트 전송 후 받은편지함/스팸함에서 folder·spam_score를 확인하세요.</p>
              <p className="mt-2">받은편지함·스팸함에서 내 메일함(직원 ID)을 hr@mg.kanggyeonggu.store 소유자(예: E001)로 설정하면 저장된 메일을 볼 수 있습니다.</p>
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
                <div className="flex items-center gap-2">
                  <Label className="text-slate-600 dark:text-muted-foreground">받는 사람</Label>
                  <span className="flex gap-1 rounded-lg border border-[#a8d5c4]/60 bg-white p-0.5 dark:border-primary/30 dark:bg-card">
                    <button
                      type="button"
                      onClick={() => { setRecipientMode("internal"); setToExternalEmail(""); setToExternalDisplayName(""); }}
                      className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${recipientMode === "internal" ? "bg-[#e8f5ef] text-slate-800 dark:bg-primary/20 dark:text-foreground" : "text-slate-600 hover:bg-slate-100 dark:text-muted-foreground dark:hover:bg-primary/10"}`}
                    >
                      사내용 (주소록)
                    </button>
                    <button
                      type="button"
                      onClick={() => { setRecipientMode("external"); setToRecipient(null); setToSearch(""); setToDropdownOpen(false); }}
                      className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${recipientMode === "external" ? "bg-[#e8f5ef] text-slate-800 dark:bg-primary/20 dark:text-foreground" : "text-slate-600 hover:bg-slate-100 dark:text-muted-foreground dark:hover:bg-primary/10"}`}
                    >
                      외부용 (이메일 직접 입력)
                    </button>
                  </span>
                </div>
                {recipientMode === "internal" ? (
                  <>
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
                  </>
                ) : (
                  <div className="grid gap-2 rounded-lg border border-amber-200 bg-amber-50/50 p-3 dark:border-amber-800/50 dark:bg-amber-950/20">
                    <Input
                      id="mail-to-external-email"
                      type="email"
                      value={toExternalEmail}
                      onChange={(e) => setToExternalEmail(e.target.value)}
                      placeholder="외부 수신자 이메일 (예: partner@gmail.com)"
                      className="border-amber-300 bg-white dark:border-amber-700 dark:bg-card"
                    />
                    <Input
                      id="mail-to-external-name"
                      value={toExternalDisplayName}
                      onChange={(e) => setToExternalDisplayName(e.target.value)}
                      placeholder="표시명 (선택)"
                      className="border-amber-300 bg-white dark:border-amber-700 dark:bg-card"
                    />
                    <p className="text-xs text-amber-800 dark:text-amber-200">Mailgun으로 실제 발송됩니다. 주소록에 없는 주소로만 보내세요.</p>
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
                  disabled={
                    !employeeId.trim() ||
                    !subject.trim() ||
                    (recipientMode === "internal" ? !toRecipient : !toExternalEmail.trim())
                  }
                  className="workspace-hero-btn border border-[#a8d5c4] bg-[#e8f5ef] text-slate-800 hover:border-[#a8d5c4] dark:border-primary/40 dark:bg-primary/15 dark:text-foreground"
                >
                  <Send className="mr-2 h-4 w-4" />
                  보내기
                </Button>
                <Button type="button" variant="outline" onClick={saveDraft} disabled={!employeeId.trim()} className="border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10">
                  임시저장
                </Button>
                <Button type="button" variant="outline" onClick={() => { setComposing(false); setEditingDraftId(null); }} className="border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10">
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
              <Button type="button" variant="outline" size="sm" onClick={() => active && openReply(active)} className="gap-1 border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10">
                <Reply className="h-3.5 w-3.5" />
                답장
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={() => active && openForward(active)} className="gap-1 border-[#a8d5c4]/80 dark:border-primary/30 dark:hover:bg-primary/10">
                <Forward className="h-3.5 w-3.5" />
                전달
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={deleteActive} className="gap-1 text-red-600 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-950/50">
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
