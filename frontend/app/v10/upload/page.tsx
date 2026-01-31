"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function UploadPage() {
  const router = useRouter();

  useEffect(() => {
    // 데이터 의존성 순서에 따라 stadium 페이지로 리다이렉트
    // 순서: Stadiums → Teams → Players → Schedules
    router.replace("/v10/upload/stadium");
  }, [router]);

  return null;
}
