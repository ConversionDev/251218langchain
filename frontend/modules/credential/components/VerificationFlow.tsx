"use client";

import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { Hash, BookOpen, ShieldCheck, ChevronRight } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { AnalysisPayload } from "../types";

/** 해시 생성에 포함된 데이터 항목 (사용자 안내용) */
const HASH_INCLUDED_DATA_LIST = [
  "직원 ID",
  "5대 역량 점수(Success DNA)",
  "IFRS 지표(전환 준비도·스킬 갭·Human Capital ROI)",
  "검증 타임스탬프",
] as const;

const steps = [
  {
    key: "extract",
    label: "원본 데이터 해시 추출",
    sublabel: "Extracting Hash",
    icon: Hash,
  },
  {
    key: "compare",
    label: "블록체인 원장 대조",
    sublabel: "Comparing with Ledger",
    icon: BookOpen,
  },
  {
    key: "verified",
    label: "무결성 확인 완료",
    sublabel: "Integrity Verified",
    icon: ShieldCheck,
  },
] as const;

interface VerificationFlowProps {
  /** 자동으로 단계 진행 (ms). 0이면 즉시 모두 완료 */
  autoAdvanceMs?: number;
  /** 해시 생성에 사용된 원본 페이로드 (상세 보기 모달용) */
  hashPayloadDetail?: AnalysisPayload;
}

export function VerificationFlow({
  autoAdvanceMs = 800,
  hashPayloadDetail,
}: VerificationFlowProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const hasToasted = useRef(false);

  useEffect(() => {
    if (autoAdvanceMs <= 0) {
      setCurrentStep(steps.length - 1);
      return;
    }
    const timers: ReturnType<typeof setTimeout>[] = [];
    for (let i = 1; i <= steps.length; i++) {
      timers.push(
        setTimeout(() => setCurrentStep(Math.min(i, steps.length - 1)), i * autoAdvanceMs)
      );
    }
    return () => timers.forEach(clearTimeout);
  }, [autoAdvanceMs]);

  useEffect(() => {
    if (currentStep === steps.length - 1 && !hasToasted.current) {
      hasToasted.current = true;
      toast.success("무결성 검증 성공. Performance 리포트의 신뢰도 배지가 활성화되었습니다.");
    }
  }, [currentStep]);

  return (
    <div className="relative">
      <div className="flex items-start justify-between gap-4">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStep;
          const isCompleted = index < currentStep || currentStep === steps.length - 1;

          return (
            <motion.div
              key={step.key}
              className="relative flex flex-1 flex-col items-center"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
            >
              {/* Connector line to next */}
              {index < steps.length - 1 && (
                <div className="absolute left-1/2 top-5 h-0.5 w-full max-w-[80%] translate-x-[50%] bg-border">
                  <motion.div
                    className="h-full bg-primary"
                    initial={{ width: "0%" }}
                    animate={{
                      width: index < currentStep ? "100%" : "0%",
                    }}
                    transition={{ duration: 0.4, ease: "easeInOut" }}
                  />
                </div>
              )}

              <motion.div
                className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                  isCompleted
                    ? "border-primary bg-primary text-primary-foreground"
                    : isActive
                      ? "border-primary bg-primary/10 text-primary ring-4 ring-primary/20"
                      : "border-border bg-muted text-muted-foreground"
                }`}
                animate={{ scale: isActive ? 1.05 : 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
              >
                <Icon className="h-5 w-5" />
              </motion.div>

              <div className="mt-3 w-full max-w-[200px] text-center">
                <AnimatePresence mode="wait">
                  <motion.p
                    key={`${step.key}-label`}
                    className="text-sm font-medium text-foreground"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    {step.label}
                  </motion.p>
                </AnimatePresence>
                <p className="mt-0.5 text-xs text-muted-foreground">{step.sublabel}</p>

                {/* 1단계: 해시에 포함된 데이터 리스트 + 상세 보기 */}
                {step.key === "extract" && (
                  <div className="mt-3 text-left">
                    <p className="text-xs font-medium text-muted-foreground">
                      포함 데이터:
                    </p>
                    <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs text-muted-foreground">
                      {HASH_INCLUDED_DATA_LIST.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                    {hashPayloadDetail != null ? (
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button
                            variant="ghost"
                            className="mt-2 h-7 gap-1 px-2 text-xs text-primary hover:text-primary"
                          >
                            상세 보기
                            <ChevronRight className="h-3 w-3" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="flex max-h-[85vh] max-w-2xl flex-col overflow-hidden">
                          <DialogHeader>
                            <DialogTitle className="text-base">
                              해시 생성에 사용된 원본 데이터 (JSON)
                            </DialogTitle>
                          </DialogHeader>
                          <div className="flex-1 overflow-auto rounded-md border border-border bg-muted/30 p-4">
                            <pre className="whitespace-pre-wrap break-all font-mono text-xs text-foreground">
                              {JSON.stringify(hashPayloadDetail, null, 2)}
                            </pre>
                          </div>
                        </DialogContent>
                      </Dialog>
                    ) : null}
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
