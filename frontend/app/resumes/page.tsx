"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { fetchEmployees } from "@/modules/core/services";
import type { Employee } from "@/modules/shared/types";

/** 지원내역 — 이름·이메일로 조회 */

const EMAIL_DOMAINS = ["naver.com", "gmail.com", "daum.net", "hanmail.net", "kakao.com", "직접입력"];

/** 지원일 또는 ISO 제출일시를 읽기 쉬운 형식으로 (날짜. 시간 시:분) */
function formatDate(s: string | undefined): string {
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s.replace(/-/g, ".");
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  if (s.includes("T") || s.length > 10) return `${y}.${m}.${day} ${h}:${min}`;
  return `${y}.${m}.${day}`;
}

export default function MyCareersPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [emailId, setEmailId] = useState("");
  const [emailDomain, setEmailDomain] = useState("gmail.com");
  const [domainDirect, setDomainDirect] = useState("");
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    fetchEmployees()
      .then(setEmployees)
      .catch(() => setEmployees([]))
      .finally(() => setLoading(false));
  }, []);

  const fullEmail = useMemo(() => {
    const domain = emailDomain === "직접입력" ? domainDirect.trim() : emailDomain;
    if (!emailId.trim() || !domain) return "";
    return `${emailId.trim()}@${domain}`;
  }, [emailId, emailDomain, domainDirect]);

  const results = useMemo(() => {
    if (!searched) return [];
    const list = employees.filter((e) => (e.employmentType ?? "regular") === "new_hire");
    const byName = name.trim() ? list.filter((e) => e.name?.toLowerCase().includes(name.trim().toLowerCase())) : list;
    const byEmail = fullEmail ? byName.filter((e) => e.email?.toLowerCase() === fullEmail.toLowerCase()) : byName;
    return byEmail.sort((a, b) => (b.applicationDate ?? b.joinedAt ?? "").localeCompare(a.applicationDate ?? a.joinedAt ?? ""));
  }, [employees, searched, name, fullEmail]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearched(true);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-[#0f0f0f]">
      <header className="sticky top-0 z-50 flex min-h-[4.5rem] items-center justify-between border-b border-[#a8d5c4]/50 bg-white/85 px-6 py-3 backdrop-blur-md dark:border-primary/20 dark:bg-[#0f0f0f]/90 md:px-8 md:py-4">
        <div className="mx-auto flex w-full max-w-4xl items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/careers" className="flex items-center gap-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100">
              <span className="text-lg">⌂</span>
              <span>채용</span>
            </Link>
            <span className="text-slate-400 dark:text-slate-500">|</span>
            <span className="font-medium text-slate-900 dark:text-slate-100">지원내역</span>
          </div>
          <Link href="/hr" className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-700 transition-colors hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100">
            <ExternalLink className="h-4 w-4" />
            메인
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-10">
        {/* 지원내역 조회 */}
        <section>
          <h2 className="border-b border-slate-200 pb-3 text-xl font-semibold text-slate-900 dark:border-white/10 dark:text-slate-100">
            지원내역 조회
          </h2>
          <form onSubmit={handleSearch} className="mt-6 space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <label htmlFor="inq-name" className="w-16 text-sm font-medium text-slate-700 dark:text-slate-300">
                이름
              </label>
              <input
                id="inq-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-9 w-56 rounded border border-slate-300 bg-white px-3 text-sm dark:border-white/20 dark:bg-[#171717] dark:text-slate-100"
                placeholder="이름 입력"
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <label className="w-16 text-sm font-medium text-slate-700 dark:text-slate-300">이메일</label>
              <input
                type="text"
                value={emailId}
                onChange={(e) => setEmailId(e.target.value)}
                className="h-9 w-32 rounded border border-slate-300 bg-white px-3 text-sm dark:border-white/20 dark:bg-[#171717] dark:text-slate-100"
                placeholder="아이디"
              />
              <span className="text-slate-500">@</span>
              {emailDomain === "직접입력" ? (
                <input
                  type="text"
                  value={domainDirect}
                  onChange={(e) => setDomainDirect(e.target.value)}
                  className="h-9 w-36 rounded border border-slate-300 bg-white px-3 text-sm dark:border-white/20 dark:bg-[#171717] dark:text-slate-100"
                  placeholder="도메인"
                />
              ) : (
                <input
                  type="text"
                  value={emailDomain}
                  readOnly
                  className="h-9 w-36 rounded border border-slate-300 bg-slate-50 px-3 text-sm dark:border-white/20 dark:bg-[#171717] dark:text-slate-300"
                />
              )}
              <select
                value={emailDomain}
                onChange={(e) => setEmailDomain(e.target.value)}
                className="h-9 rounded border border-slate-300 bg-white px-2 text-sm dark:border-white/20 dark:bg-[#171717] dark:text-slate-100"
              >
                {EMAIL_DOMAINS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div className="border-t border-slate-200 pt-4 dark:border-white/10">
              <button
                type="submit"
                className="rounded bg-emerald-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600"
              >
                조회
              </button>
            </div>
          </form>
        </section>

        {/* 조회결과 */}
        <section className="mt-10">
          <h2 className="border-b border-slate-200 pb-3 text-xl font-semibold text-slate-900 dark:border-white/10 dark:text-slate-100">
            조회결과
          </h2>
          {loading ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">불러오는 중…</p>
          ) : !searched ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">이름과 이메일을 입력한 뒤 조회 버튼을 눌러 주세요.</p>
          ) : (
            <div className="mt-4 overflow-x-auto rounded border border-slate-200 dark:border-white/10">
              <table className="w-full min-w-[400px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-[#171717]">
                    <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">공고명</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">지원일</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-300">지원서</th>
                  </tr>
                </thead>
                <tbody>
                  {results.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="px-4 py-8 text-center text-slate-500 dark:text-slate-400">
                        조회 결과가 없습니다.
                      </td>
                    </tr>
                  ) : (
                    results.map((e) => (
                      <tr key={e.id} className="border-b border-slate-100 dark:border-white/5">
                        <td className="px-4 py-3 text-slate-900 dark:text-slate-100">
                          {[e.department, e.jobTitle].filter(Boolean).join(" · ") || "—"}
                        </td>
                        <td className="px-4 py-3 text-slate-600 dark:text-slate-400">
                          {formatDate(e.applicationDate ?? e.joinedAt)}
                        </td>
                        <td className="px-4 py-3">
                          <Link
                            href="/careers/recruit"
                            className="text-emerald-600 hover:underline dark:text-emerald-400"
                          >
                            보기
                          </Link>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
