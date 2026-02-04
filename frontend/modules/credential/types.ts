import type { SuccessDNA, IfrsMetrics } from "@/modules/shared/types";

/** 검증용 분석 데이터 페이로드 */
export interface AnalysisPayload {
  employeeId: string;
  successDna?: SuccessDNA;
  ifrsMetrics?: IfrsMetrics;
  verifiedAt: string; // ISO string
}

/** 블록체인 트랜잭션 Mock 항목 */
export interface BlockchainTransaction {
  id: string;
  txHash: string;
  timestamp: string;
  walletAddress: string;
  blockNumber: number;
  status: "confirmed" | "pending";
  dataHash: string;
}

/** VC 검증 결과 */
export interface VerificationResult {
  dataHash: string;
  employeeId: string;
  verifiedAt: string;
  status: "verified" | "pending" | "failed";
  transactions: BlockchainTransaction[];
}
