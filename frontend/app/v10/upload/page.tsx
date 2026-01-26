"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function UploadPage() {
  const router = useRouter();

  useEffect(() => {
    // 기본 경로로 player 페이지로 리다이렉트
    router.replace("/v10/upload/player");
  }, [router]);

  return null;
}
