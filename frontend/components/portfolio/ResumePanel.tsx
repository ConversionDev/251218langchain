"use client";

import { useEffect } from "react";
import { ResumeView } from "./ResumeView";

type ResumePanelProps = {
  open: boolean;
  onClose: () => void;
};

export function ResumePanel({ open, onClose }: ResumePanelProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col"
      role="dialog"
      aria-modal="true"
      aria-label="Resume"
    >
      {/* Dim background */}
      <button
        type="button"
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
        aria-label="Close resume"
      />
      {/* Panel */}
      <div className="relative flex flex-col m-4 md:m-8 flex-1 min-h-0 rounded-lg overflow-hidden shadow-2xl bg-white">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 flex-shrink-0 bg-[#1a1f36] text-white">
          <h2 className="text-lg font-bold">Resume</h2>
          <div className="flex items-center gap-2">
            <a
              href="/resume.pdf"
              download
              className="text-sm font-medium px-3 py-1.5 rounded border border-[#C8861A] text-[#C8861A] hover:bg-[#C8861A]/10 transition-colors"
            >
              PDF 다운로드
            </a>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        {/* Body */}
        <div className="flex-1 min-h-0 overflow-auto bg-[#f7fafc]">
          <ResumeView />
        </div>
      </div>
    </div>
  );
}
