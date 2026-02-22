"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** /core 접근 시 신입 관리 페이지로 이동 */
export default function CorePage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/core/new-hires");
  }, [router]);
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <p className="text-muted-foreground">이동 중...</p>
    </div>
  );
}
