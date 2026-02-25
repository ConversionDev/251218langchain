import Image from "next/image";

/**
 * 데모 역할 선택 전용 레이아웃 — 일반 회사원 협업 배경, 상단 헤더 없음.
 */
export default function DemoLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 min-h-screen overflow-hidden bg-slate-100 dark:bg-slate-900">
      <div className="absolute inset-0">
        <Image
          src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1920&q=80"
          alt=""
          fill
          className="object-cover"
          sizes="100vw"
          priority
        />
      </div>
      <div className="absolute inset-0 bg-white/70 dark:bg-slate-900/75" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-white/50 dark:to-slate-900/50" />
      <div className="relative z-10 min-h-screen">
        {children}
      </div>
    </div>
  );
}
