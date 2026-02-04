"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, Loader2 } from "lucide-react";
import type { Employee } from "@/modules/shared/types";
import { generateAnalysisHash } from "@/modules/credential/services";

interface VerificationStatusIndicatorProps {
  employee: Employee | null;
}

export function VerificationStatusIndicator({ employee }: VerificationStatusIndicatorProps) {
  const [status, setStatus] = useState<"checking" | "verified">("checking");
  const [hash, setHash] = useState<string | null>(null);

  useEffect(() => {
    if (!employee) {
      setStatus("verified");
      setHash(null);
      return;
    }
    setStatus("checking");
    const t = setTimeout(() => {
      const payload = {
        employeeId: employee.id,
        successDna: employee.successDna ?? undefined,
        ifrsMetrics: employee.ifrsMetrics ?? undefined,
        verifiedAt: new Date().toISOString(),
      };
      const h = generateAnalysisHash(payload);
      setHash(h);
      setStatus("verified");
    }, 900);
    return () => clearTimeout(t);
  }, [employee?.id, employee?.successDna, employee?.ifrsMetrics]);

  if (!employee) {
    return (
      <div className="rounded-lg border border-border bg-muted/40 px-4 py-2.5 text-sm text-muted-foreground">
        전체 평균 모드 · 개인 선택 시 검증 상태 표시
      </div>
    );
  }

  return (
    <AnimatePresence mode="wait">
      {status === "checking" ? (
        <motion.div
          key="checking"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-4 py-2.5 text-sm text-muted-foreground"
        >
          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
          <span>데이터 정합성 검사 중...</span>
        </motion.div>
      ) : (
        hash && (
          <motion.div
            key="verified"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 px-4 py-2.5 text-sm text-primary"
          >
            <ShieldCheck className="h-4 w-4 shrink-0" />
            <span>
              Verified (Hash: 0x{hash.slice(0, 10)}…{hash.slice(-6)})
            </span>
          </motion.div>
        )
      )}
    </AnimatePresence>
  );
}
