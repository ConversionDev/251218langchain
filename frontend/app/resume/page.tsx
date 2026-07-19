"use client";

import { useEffect } from "react";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

const INTRO_SHOWN_KEY = "portfolio-intro-shown";

export default function ResumePage() {
  useEffect(() => {
    sessionStorage.setItem(INTRO_SHOWN_KEY, "1");
  }, []);

  return (
    <div className="fixed inset-0 flex flex-col bg-slate-100">
      <div className="shrink-0 flex items-center gap-2 px-4 py-2 bg-white border-b border-slate-200">
        <Link
          href="/"
          className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ChevronLeft size={18} />
          <span>돌아가기</span>
        </Link>
      </div>
      <div className="flex-1 min-h-0 w-full">
        <iframe
          src={encodeURI("/resume/강경구(이력서).pdf")}
          title="이력서"
          className="w-full h-full border-0"
        />
      </div>
    </div>
  );
}
