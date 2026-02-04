"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { ShieldCheck, BarChart3, ArrowRight, Shield } from "lucide-react";
import { useStore } from "@/store/useStore";
import { useHydrated } from "@/hooks/use-hydrated";
import { VerificationFlow } from "@/modules/credential/components/VerificationFlow";
import { getVerificationResult } from "@/modules/credential/services";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function CredentialPageSkeleton() {
  return (
    <div className="space-y-8">
      <div className="h-10 w-48 animate-pulse rounded bg-muted" />
      <div className="h-24 animate-pulse rounded-xl bg-muted/50" />
      <div className="h-32 animate-pulse rounded-xl bg-muted/50" />
    </div>
  );
}

function CredentialContent() {
  const hydrated = useHydrated();
  const searchParams = useSearchParams();
  const selectedEmployee = useStore((s) => s.selectedEmployee);

  const employeeId = useMemo(
    () =>
      searchParams.get("id") ??
      selectedEmployee?.id ??
      "E001",
    [searchParams, selectedEmployee?.id]
  );

  const result = useMemo(
    () =>
      getVerificationResult(
        employeeId,
        selectedEmployee?.successDna,
        selectedEmployee?.ifrsMetrics
      ),
    [employeeId, selectedEmployee?.successDna, selectedEmployee?.ifrsMetrics]
  );

  /** 해시 생성에 사용된 원본 페이로드 (VerificationFlow 상세 보기용) */
  const hashPayloadDetail = useMemo(
    () => ({
      employeeId: result.employeeId,
      successDna: selectedEmployee?.successDna ?? undefined,
      ifrsMetrics: selectedEmployee?.ifrsMetrics ?? undefined,
      verifiedAt: result.verifiedAt,
    }),
    [result.employeeId, result.verifiedAt, selectedEmployee?.successDna, selectedEmployee?.ifrsMetrics]
  );

  const isVerified = result.status === "verified";

  if (!hydrated) {
    return (
      <div className="space-y-8">
        <div className="h-10 w-48 animate-pulse rounded bg-muted" />
        <div className="h-24 animate-pulse rounded-xl bg-muted/50" />
        <div className="h-32 animate-pulse rounded-xl bg-muted/50" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <div className="mb-1.5 flex items-center gap-2 text-muted-foreground">
          <Shield className="h-3.5 w-3.5 shrink-0" />
          <span className="text-xs">Verified Trust: DID/VC 블록체인 무결성 증명 레이어</span>
        </div>
        <h1 className="text-2xl font-bold text-foreground">Verified Credential (VC)</h1>
        <p className="mt-1 text-muted-foreground">
          분석 데이터 무결성 검증 결과
        </p>
      </div>

      {/* Status Badge + Performance 이동 CTA */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div
            className={`inline-flex items-center gap-3 rounded-lg px-5 py-4 ${
              isVerified
                ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                : "bg-muted text-muted-foreground"
            }`}
          >
            <ShieldCheck
              className={`h-8 w-8 shrink-0 ${
                isVerified ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
              }`}
            />
            <div>
              <p className="text-sm font-medium opacity-90">Status</p>
              <p className="text-lg font-bold">
                {isVerified ? "Integrity Verified" : result.status}
              </p>
            </div>
          </div>
          {isVerified && (
            <Link href="/performance">
              <Button className="inline-flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Performance 리포트 보기
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          )}
        </div>
      </section>

      {/* 3-Step Verification Flow */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">검증 과정</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          데이터 해시 추출 → 원장 대조 → 무결성 확인
        </p>
        <div className="mt-6">
          <VerificationFlow autoAdvanceMs={700} hashPayloadDetail={hashPayloadDetail} />
        </div>
      </section>

      {/* Data Hash */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">검증된 데이터 해시</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          분석 결과(Success DNA, IFRS 지표)로부터 생성된 SHA-256 해시
        </p>
        <div className="mt-4 overflow-x-auto rounded-lg border border-border bg-muted/30 p-4 font-mono text-sm text-foreground break-all">
          {result.dataHash}
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          직원 ID: {result.employeeId} · 검증 시각: {new Date(result.verifiedAt).toLocaleString("ko-KR")}
        </p>
      </section>

      {/* Blockchain Transaction Log */}
      <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">블록체인 트랜잭션 로그</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          원장에 기록된 트랜잭션 내역
        </p>
        <div className="mt-4 overflow-hidden rounded-lg border border-border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Tx Hash</TableHead>
                <TableHead>타임스탬프</TableHead>
                <TableHead>지갑 주소</TableHead>
                <TableHead>Block #</TableHead>
                <TableHead>상태</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.transactions.map((tx) => (
                <TableRow key={tx.id}>
                  <TableCell className="font-medium">{tx.id}</TableCell>
                  <TableCell className="font-mono text-xs">{tx.txHash.slice(0, 18)}…</TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(tx.timestamp).toLocaleString("ko-KR")}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{tx.walletAddress.slice(0, 10)}…</TableCell>
                  <TableCell>{tx.blockNumber.toLocaleString()}</TableCell>
                  <TableCell>
                    <span
                      className={
                        tx.status === "confirmed"
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-amber-600 dark:text-amber-400"
                      }
                    >
                      {tx.status}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  );
}

export default function CredentialPage() {
  return (
    <Suspense fallback={<CredentialPageSkeleton />}>
      <CredentialContent />
    </Suspense>
  );
}
