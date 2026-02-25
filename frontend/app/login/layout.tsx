import Image from "next/image";

/**
 * 로그인 전용 레이아웃 — 깔끔한 사무실 배경(밝은 톤), 상단 헤더 없음.
 */
export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 min-h-screen overflow-hidden bg-slate-100 dark:bg-slate-900">
      <div className="absolute inset-0">
        <Image
          src="https://images.unsplash.com/photo-1497366216548-37526070297c?w=1920&q=80"
          alt=""
          fill
          className="object-cover"
          sizes="100vw"
          priority
        />
      </div>
      <div className="absolute inset-0 bg-white/75 dark:bg-slate-900/80" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-white/50 dark:to-slate-900/50" />
      <div className="relative z-10 min-h-screen">
        {children}
      </div>
    </div>
  );
}
