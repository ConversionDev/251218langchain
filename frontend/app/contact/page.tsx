"use client";

import Link from "next/link";

const NAV_LINKS = [
  { href: "/", label: "홈" },
  { href: "/portfolio", label: "프로젝트" },
  { href: "/contact", label: "연락처" },
];

export default function ContactPage() {
  return (
    <div className="min-h-screen bg-white text-slate-900 font-sans antialiased">
      <header className="border-b border-slate-200/80">
        <div className="mx-auto max-w-2xl px-5 py-5 sm:px-6 flex items-center justify-between">
          <Link href="/" className="text-lg font-semibold text-slate-900 tracking-tight hover:text-slate-700">
            강경구
          </Link>
          <nav className="flex items-center gap-6 text-sm">
            {NAV_LINKS.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={
                  href === "/contact"
                    ? "font-medium text-slate-900"
                    : "text-slate-600 hover:text-slate-900"
                }
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-5 py-14 sm:px-6 sm:py-20">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          연락처
        </h1>

        <p className="mt-6 text-lg leading-relaxed text-slate-700">
          연락 주시면 감사하겠습니다.
        </p>

        <p className="mt-4 text-lg leading-relaxed text-slate-700">
          가장 빠른 방법은 이메일입니다.{" "}
          <a
            href="mailto:your@email.com"
            className="font-medium text-slate-900 underline decoration-slate-300 underline-offset-2 hover:decoration-slate-500"
          >
            your@email.com
          </a>
          으로 보내 주세요.
        </p>

        <blockquote className="mt-8 border-l-4 border-slate-200 pl-4 text-sm text-slate-600 italic">
          게스트 포스트·유료 링크 삽입 요청은 받지 않습니다. 그 외 문의는 언제든 환영합니다.
        </blockquote>

        <p className="mt-6 text-lg leading-relaxed text-slate-700">
          가볍게 이야기 나누고 싶으시면{" "}
          <a
            href="https://twitter.com"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-slate-900 underline decoration-slate-300 underline-offset-2 hover:decoration-slate-500"
          >
            Twitter
          </a>
          로 연락 주셔도 됩니다.
        </p>
      </main>

      <footer className="border-t border-slate-200/80 mt-20">
        <div className="mx-auto max-w-2xl px-5 py-8 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <span>© {new Date().getFullYear()} 강경구</span>
          <div className="flex items-center gap-6">
            <Link href="/" className="hover:text-slate-700">홈</Link>
            <Link href="/portfolio" className="hover:text-slate-700">프로젝트</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
