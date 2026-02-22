/**
 * 문서 확장자 — 백엔드 domain/shared/document_extract.py와 동기화.
 * 실제 값은 GET /api/document/supported-extensions 로 확인 가능.
 */

export const SUPPORTED_TEXT_EXTENSIONS = [".pdf", ".txt", ".docx", ".hwp"] as const;
export const SUPPORTED_EXCEL_EXTENSIONS = [".xlsx"] as const;
export const SUPPORTED_EXTENSIONS = [
  ...SUPPORTED_TEXT_EXTENSIONS,
  ...SUPPORTED_EXCEL_EXTENSIONS,
] as const;

/** 이력서 업로드용 accept 속성 값 (텍스트 문서만) */
export const RESUME_ACCEPT =
  ".pdf,.txt,.docx,.hwp,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/x-hwp";

/** 전체 문서 업로드용 accept (텍스트 + Excel) */
export const DOCUMENT_ACCEPT =
  RESUME_ACCEPT +
  ",.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
