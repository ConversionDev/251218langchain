"use client";

import Link from "next/link";

const NAV = [
  { href: "#about", label: "소개" },
  { href: "#experience", label: "경력" },
  { href: "#projects", label: "프로젝트" },
];

const SOCIAL = [
  { href: "https://github.com", label: "GitHub" },
  { href: "https://linkedin.com", label: "LinkedIn" },
];

const EXPERIENCE = [
  {
    period: "2024 — 현재",
    title: "포지션 · 회사명",
    desc: "담당 업무와 성과를 한두 문장으로 적어 주세요. 컴포넌트 라이브러리, 디자인 시스템, 웹 접근성 등.",
    tags: ["JavaScript", "TypeScript", "React"],
  },
  {
    period: "2022 — 2024",
    title: "포지션 · 회사명",
    desc: "이전 경력 요약. 웹/앱 개발, 크로스펙 협업 등.",
    tags: ["Next.js", "Node.js", "HTML & CSS"],
  },
];

const PROJECTS = [
  {
    title: "개인 프로젝트",
    desc: "지금 진행 중인 프로젝트와 사이드 프로젝트를 소개합니다.",
    href: "/portfolio/personal",
    tags: ["React", "TypeScript"],
  },
  {
    title: "팀 프로젝트",
    desc: "함께 진행한 팀 프로젝트와 협업 경험을 공유합니다.",
    href: "/portfolio/team",
    tags: ["협업", "기획", "개발"],
  },
];

export default function PortfolioPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-300 font-sans antialiased">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-slate-700 focus:text-white focus:rounded"
      >
        본문으로 건너뛰기
      </a>

      <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06] bg-[#0a0a0f]/90 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-5 sm:px-6">
          <Link href="/portfolio" className="text-sm font-semibold text-white tracking-tight">
            강경구
          </Link>
          <nav className="flex items-center gap-6 text-sm">
            {NAV.map(({ href, label }) => (
              <a
                key={href}
                href={href}
                className="text-slate-400 hover:text-white transition-colors"
              >
                {label}
              </a>
            ))}
          </nav>
        </div>
      </header>

      <main id="main" className="mx-auto max-w-4xl px-5 pt-24 pb-20 sm:px-6 sm:pt-28">
        <section className="mb-24 sm:mb-32">
          <p className="text-sm font-medium text-[#64ffda]">안녕하세요, 저는</p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            강경구
          </h1>
          <p className="mt-3 text-2xl font-semibold text-slate-400 sm:text-3xl">
            Frontend Developer
          </p>
          <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-400">
            접근성과 픽셀 퍼펙트한 웹 경험을 만듭니다.
          </p>
          <div className="mt-8 flex items-center gap-6 text-sm">
            {SOCIAL.map(({ href, label }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-[#64ffda] transition-colors"
              >
                {label}
              </a>
            ))}
          </div>
        </section>

        <section id="about" className="mb-24 sm:mb-32 scroll-mt-24">
          <h2 className="text-xl font-semibold text-white flex items-center gap-3 after:content-[''] after:flex-1 after:h-px after:bg-slate-700 after:max-w-[200px]">
            소개
          </h2>
          <div className="mt-6 space-y-4 text-slate-400 leading-relaxed">
            <p>
              프론트엔드 개발자로, 사용자 경험과 접근성을 고려한 웹 인터페이스를 만드는 일을 합니다.
              디자인과 엔지니어링이 만나는 지점에서, 견고하고 확장 가능한 코드로 픽셀 퍼펙트한 결과물을 만드는 것을 좋아합니다.
            </p>
            <p>
              현재는 [회사/팀명]에서 [담당 업무]를 맡고 있습니다. (본인 상황에 맞게 수정해 주세요.)
            </p>
            <p>
              업무 외에는 [취미/관심사]를 즐깁니다.
            </p>
          </div>
        </section>

        <section id="experience" className="mb-24 sm:mb-32 scroll-mt-24">
          <h2 className="text-xl font-semibold text-white flex items-center gap-3 after:content-[''] after:flex-1 after:h-px after:bg-slate-700 after:max-w-[200px]">
            경력
          </h2>
          <div className="mt-10 space-y-12">
            {EXPERIENCE.map((job, i) => (
              <div key={i} className="relative pl-6 border-l-2 border-slate-700">
                <span className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-[#64ffda]" />
                <span className="text-sm text-[#64ffda]">{job.period}</span>
                <h3 className="mt-1 text-lg font-semibold text-white">
                  {job.title}
                </h3>
                <p className="mt-2 text-slate-400 leading-relaxed">
                  {job.desc}
                </p>
                <ul className="mt-3 flex flex-wrap gap-2">
                  {job.tags.map((tag) => (
                    <li
                      key={tag}
                      className="text-xs text-slate-500 px-2 py-1 rounded bg-white/5"
                    >
                      {tag}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <p className="mt-8">
            <a
              href="#"
              className="text-sm text-[#64ffda] hover:underline"
            >
              이력서 전체 보기 →
            </a>
          </p>
        </section>

        <section id="projects" className="mb-24 sm:mb-32 scroll-mt-24">
          <h2 className="text-xl font-semibold text-white flex items-center gap-3 after:content-[''] after:flex-1 after:h-px after:bg-slate-700 after:max-w-[200px]">
            프로젝트
          </h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {PROJECTS.map((project) => (
              <Link
                key={project.title}
                href={project.href}
                className="group block rounded-lg border border-slate-700/80 bg-white/[0.02] p-5 transition-colors hover:border-[#64ffda]/40 hover:bg-white/[0.04]"
              >
                <h3 className="font-semibold text-white group-hover:text-[#64ffda] transition-colors">
                  {project.title}
                </h3>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                  {project.desc}
                </p>
                <ul className="mt-3 flex flex-wrap gap-2">
                  {project.tags.map((tag) => (
                    <li
                      key={tag}
                      className="text-xs text-slate-500"
                    >
                      {tag}
                    </li>
                  ))}
                </ul>
              </Link>
            ))}
          </div>
        </section>

        <footer className="pt-8 border-t border-slate-800 text-center text-sm text-slate-500">
          <p>
            Designed &amp; built by 강경구. Built with{" "}
            <a href="https://nextjs.org" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-[#64ffda]">
              Next.js
            </a>
            {" "}&amp;{" "}
            <a href="https://tailwindcss.com" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-[#64ffda]">
              Tailwind CSS
            </a>
            .
          </p>
        </footer>
      </main>
    </div>
  );
}
