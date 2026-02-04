import type { SuccessDNA, IfrsMetrics } from "@/modules/shared/types";
import type { AnalysisPayload, BlockchainTransaction, VerificationResult } from "./types";

/**
 * 분석 데이터를 정규화한 문자열로 직렬화 (해시 입력용)
 */
function canonicalize(payload: AnalysisPayload): string {
  return JSON.stringify({
    employeeId: payload.employeeId,
    successDna: payload.successDna ?? null,
    ifrsMetrics: payload.ifrsMetrics ?? null,
    verifiedAt: payload.verifiedAt,
  });
}

/**
 * 가상의 SHA-256 해시 생성 (64자 hex).
 * 동일 입력에 대해 항상 동일한 해시를 반환하는 결정적 함수.
 */
function virtualSha256Hex(input: string): string {
  let h = 5381;
  for (let i = 0; i < input.length; i++) {
    h = ((h << 5) + h) ^ input.charCodeAt(i);
  }
  const u = (h >>> 0).toString(16).padStart(8, "0");
  const seed = (h >>> 0) * 31 + input.length;
  const u2 = (seed >>> 0).toString(16).padStart(8, "0");
  const parts: string[] = [];
  for (let i = 0; i < 8; i++) {
    const n = (seed * (i + 1) + input.charCodeAt(i % input.length)) >>> 0;
    parts.push(n.toString(16).padStart(8, "0"));
  }
  return parts.join("").slice(0, 64);
}

/**
 * 분석 결과(Success DNA, IFRS 지표)로부터 가상 SHA-256 해시 생성
 */
export function generateAnalysisHash(payload: AnalysisPayload): string {
  const canonical = canonicalize(payload);
  return virtualSha256Hex(canonical);
}

/** Mock 블록체인 트랜잭션 생성 */
function createMockTransactions(
  dataHash: string,
  employeeId: string
): BlockchainTransaction[] {
  const now = new Date().toISOString();
  const baseTx = {
    dataHash,
    status: "confirmed" as const,
  };
  return [
    {
      id: "tx-1",
      txHash: `0x${virtualSha256Hex(dataHash + "anchor").slice(0, 64)}`,
      timestamp: now,
      walletAddress: "0x742d35Cc6634C0532925a3b844Bc9e7595f2A1B2",
      blockNumber: 19_238_471,
      ...baseTx,
    },
    {
      id: "tx-2",
      txHash: `0x${virtualSha256Hex(dataHash + "verify").slice(0, 64)}`,
      timestamp: new Date(Date.now() - 60_000).toISOString(),
      walletAddress: "0x892d35Cc6634C0532925a3b844Bc9e7595f2A1B3",
      blockNumber: 19_238_470,
      ...baseTx,
    },
    {
      id: "tx-3",
      txHash: `0x${virtualSha256Hex(employeeId + dataHash).slice(0, 64)}`,
      timestamp: new Date(Date.now() - 120_000).toISOString(),
      walletAddress: "0x9a2d35Cc6634C0532925a3b844Bc9e7595f2A1B4",
      blockNumber: 19_238_469,
      ...baseTx,
    },
  ];
}

/**
 * 직원 ID와 분석 데이터로 검증 결과(Mock) 생성
 */
export function getVerificationResult(
  employeeId: string,
  successDna?: SuccessDNA,
  ifrsMetrics?: IfrsMetrics
): VerificationResult {
  const verifiedAt = new Date().toISOString();
  const payload: AnalysisPayload = {
    employeeId,
    successDna,
    ifrsMetrics,
    verifiedAt,
  };
  const dataHash = generateAnalysisHash(payload);
  const transactions = createMockTransactions(dataHash, employeeId);

  return {
    dataHash,
    employeeId,
    verifiedAt,
    status: "verified",
    transactions,
  };
}
