"use client";

import { useRouter } from "next/navigation";
import { ArrowRight, UserCog, Users, User } from "lucide-react";
import { useDemoRoleStore, DEMO_ROLE_CONFIG, type DemoRole } from "@/store/useDemoRoleStore";

/** 로그인 페이지와 동일한 텍스트 로고 + 인재 멘트 */
function LogoWordmark() {
  return (
    <div className="text-center">
      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
        AI Powered HR Intelligence
      </p>
      <h1 className="mt-1 flex items-baseline justify-center gap-1.5">
        <span className="text-2xl font-bold tracking-tight text-[#14532d] dark:text-emerald-800">
          HR
        </span>
        <span
          className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-2xl font-bold tracking-tight text-transparent dark:from-teal-400 dark:to-emerald-400"
          style={{
            textShadow: "0 1px 2px rgba(0,0,0,0.06)",
            WebkitBackgroundClip: "text",
          }}
        >
          Insight
        </span>
      </h1>
      <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
        인재와 함께하는 인사 인사이트
      </p>
    </div>
  );
}

const DEMO_CARDS: {
  role: DemoRole;
  title: string;
  descriptionLines: string[];
  icon: React.ComponentType<{ className?: string }>;
  gradient: string;
  borderHover: string;
}[] = [
  {
    role: "admin",
    title: "관리자",
    descriptionLines: [
      "전체 인력·성과 분석",
      "RAG 챗봇",
      "신입/기존 직원 관리",
      "공시·감사 로그",
    ],
    icon: UserCog,
    gradient: "from-slate-700 to-emerald-800",
    borderHover: "hover:border-emerald-400",
  },
  {
    role: "employee",
    title: "일반직원",
    descriptionLines: [
      "나의 업무 로그",
      "사내 메일",
      "업무 제출 등 직원 전용 서비스",
    ],
    icon: Users,
    gradient: "from-teal-700 to-emerald-700",
    borderHover: "hover:border-teal-400",
  },
  {
    role: "applicant",
    title: "일반사용자",
    descriptionLines: [
      "채용 공고 확인",
      "이력서 제출",
      "지원자용 채용·공지",
    ],
    icon: User,
    gradient: "from-sky-600 to-teal-600",
    borderHover: "hover:border-sky-400",
  },
];

export default function DemoSelectPage() {
  const router = useRouter();
  const setDemoRole = useDemoRoleStore((s) => s.setDemoRole);

  const handleEnter = (role: DemoRole) => {
    setDemoRole(role);
    router.push(DEMO_ROLE_CONFIG[role].path);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-16">
      <LogoWordmark />
      <h1 className="mt-10 text-center text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl dark:text-slate-100">
        역할을 선택하세요
      </h1>
      <div className="mx-auto mt-3 max-w-xl space-y-1 text-center text-sm text-slate-600 dark:text-slate-400">
        <p>클릭하면 해당 역할에 맞는 화면으로 이동합니다.</p>
        <p>우측 하단 버튼으로 언제든 다른 역할로 전환할 수 있습니다.</p>
      </div>
      <div className="mt-12 grid w-full max-w-4xl gap-6 sm:grid-cols-3">
        {DEMO_CARDS.map((card) => {
          const Icon = card.icon;
          return (
            <button
              key={card.role}
              type="button"
              onClick={() => handleEnter(card.role)}
              className={`group flex flex-col rounded-2xl border-2 border-white/20 bg-white/95 p-6 text-left shadow-xl backdrop-blur-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-2xl hover:border-white/40 dark:border-white/10 dark:bg-[#171717]/95 ${card.borderHover}`}
            >
              <span className={`inline-flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${card.gradient} text-white shadow-md`} aria-hidden>
                <Icon className="h-7 w-7" />
              </span>
              <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-100">
                {card.title}
              </h2>
              <div className="mt-2 flex-1 space-y-1 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                {card.descriptionLines.map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
              <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-emerald-600 dark:text-emerald-400 group-hover:gap-3 transition-all">
                이 화면으로 이동
                <ArrowRight className="h-4 w-4" />
              </span>
            </button>
          );
        })}
      </div>
    </main>
  );
}
