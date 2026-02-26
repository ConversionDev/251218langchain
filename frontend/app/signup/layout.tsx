/**
 * 회원가입 전용 레이아웃 — 사이트 컬러 배경, 헤더 없음.
 */
export default function SignupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 min-h-screen overflow-auto bg-gradient-to-br from-[#e8f5ef] via-[#f0f5f0] to-[#e8f5ef]/90 dark:from-[#0a0a0a] dark:via-[#0f0f0f] dark:to-[#0a0a0a]">
      <div className="relative z-10 min-h-screen">
        {children}
      </div>
    </div>
  );
}
