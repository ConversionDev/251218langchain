"use client";

import { useEffect, useCallback, useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import { ReportContent } from "./ReportContent";
import type { PerformanceMetrics, DisclosureSummary, ImpactDataPoint } from "../types";

interface ReportPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reportTitle: string;
  summaryName: string;
  metrics: PerformanceMetrics | null;
  chartData: ImpactDataPoint[];
  disclosureSummary: DisclosureSummary | null;
  /** true면 전체화면 이사회 보고 모드로 표시 */
  fullscreen?: boolean;
}

export function ReportPreviewModal({
  open,
  onOpenChange,
  reportTitle,
  summaryName,
  metrics,
  chartData,
  disclosureSummary,
  fullscreen = false,
}: ReportPreviewModalProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const handleClose = useCallback(() => onOpenChange(false), [onOpenChange]);

  useEffect(() => {
    if (!fullscreen || !open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [fullscreen, open, handleClose]);

  if (fullscreen && open) {
    const fullscreenOverlay = (
      <div
        className="fixed inset-0 bg-white"
        style={{ zIndex: 99999 }}
        role="presentation"
      >
        <div
          className="fixed inset-0 overflow-y-auto overflow-x-hidden"
          onClick={handleClose}
          aria-hidden
        >
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="report-preview-modal report-mode-fullscreen report-paper min-h-full w-full bg-white"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="이사회 보고 모드"
          >
            <Button
              variant="ghost"
              className="absolute right-4 top-4 z-10 h-10 w-10 rounded-full border border-slate-200 bg-white p-0 shadow-sm hover:bg-slate-50"
              onClick={handleClose}
              aria-label="닫기 (Esc)"
            >
              <X className="h-5 w-5 text-slate-600" />
            </Button>
            <div className="report-mode-layout flex min-h-full flex-col gap-8 px-8 py-12 pr-16 sm:px-12 sm:py-16 sm:pr-20 max-w-5xl mx-auto">
              <ReportContent
                reportTitle={reportTitle}
                summaryName={summaryName}
                metrics={metrics}
                chartData={chartData}
                disclosureSummary={disclosureSummary}
                reportMode
              />
            </div>
          </motion.div>
        </div>
      </div>
    );

    if (mounted && typeof document !== "undefined") {
      return createPortal(fullscreenOverlay, document.body);
    }
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="report-preview-modal flex max-h-[90vh] w-[92vw] max-w-3xl flex-col items-center overflow-y-auto overflow-x-hidden border-0 py-6 px-4 sm:px-6">
        <DialogHeader className="sr-only">
          <DialogTitle>{reportTitle} 미리보기</DialogTitle>
        </DialogHeader>
        <div className="relative flex w-full min-w-0 flex-col items-center">
          <Button
            variant="ghost"
            className="absolute right-1 top-1 z-10 h-8 w-8 rounded-full bg-white p-0 text-slate-600 shadow hover:bg-slate-50 sm:right-2 sm:top-2"
            onClick={() => onOpenChange(false)}
            aria-label="닫기"
          >
            <X className="h-4 w-4" />
          </Button>

          <AnimatePresence>
            {open && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="report-paper w-full max-w-full min-w-0 overflow-hidden rounded-lg bg-white px-5 py-5 shadow-xl sm:px-6 sm:py-6"
              >
                <ReportContent
                  reportTitle={reportTitle}
                  summaryName={summaryName}
                  metrics={metrics}
                  chartData={chartData}
                  disclosureSummary={disclosureSummary}
                  reportMode={false}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </DialogContent>
    </Dialog>
  );
}
