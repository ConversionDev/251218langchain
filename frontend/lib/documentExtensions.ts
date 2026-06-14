/**
 * 문서 확장자 — 백엔드 domain/shared/document_extract.py와 동기화.
 * 실제 값은 GET /api/document/supported-extensions 로 확인 가능.
 */

export const SUPPORTED_TEXT_EXTENSIONS = [".pdf", ".txt", ".docx"] as const;
export const SUPPORTED_EXCEL_EXTENSIONS = [".xlsx"] as const;
/** 이미지(스캔본) — 업로드 시 백엔드가 Gemini 비전 OCR로 텍스트 추출 */
export const SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"] as const;
export const SUPPORTED_EXTENSIONS = [
  ...SUPPORTED_TEXT_EXTENSIONS,
  ...SUPPORTED_EXCEL_EXTENSIONS,
] as const;

/** 이력서 업로드용 accept 속성 값 (텍스트 문서 + 이미지 스캔본은 OCR) */
export const RESUME_ACCEPT =
  ".pdf,.txt,.docx,.png,.jpg,.jpeg,.webp,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/png,image/jpeg,image/webp";

/** 전체 문서 업로드용 accept (텍스트 + Excel) */
export const DOCUMENT_ACCEPT =
  RESUME_ACCEPT +
  ",.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
