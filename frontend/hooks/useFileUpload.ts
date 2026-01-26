"use client";

import { useState, useCallback } from "react";

type DataType = "players" | "teams" | "stadiums" | "schedules";

interface UploadResult {
  success: boolean;
  message?: string;
  data_type?: string;
  filename: string;
  results?: {
    db?: number;
    vector?: number;
  };
  // 미리보기 관련 (players 타입일 때)
  total_rows?: number;
  preview_rows?: number;
  preview?: Array<{
    row: number;
    data?: any;
    error?: string;
    raw?: string;
  }>;
}

export function useFileUpload(dataType: DataType) {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = useCallback(
    async (file: File) => {
      setUploading(true);
      setError(null);
      setUploadResult(null);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        // 모든 타입이 soccer/{type}/upload 사용 (복수형 -> 단수형 변환)
        const typeMap: Record<DataType, string> = {
          players: "player",
          teams: "team",
          stadiums: "stadium",
          schedules: "schedule",
        };
        const endpoint = `${backendUrl}/api/v10/soccer/${typeMap[dataType]}/upload`;

        const response = await fetch(endpoint, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setUploadResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "파일 업로드 실패");
      } finally {
        setUploading(false);
      }
    },
    [dataType]
  );

  const reset = useCallback(() => {
    setError(null);
    setUploadResult(null);
  }, []);

  const setErrorState = useCallback((errorMessage: string | null) => {
    setError(errorMessage);
  }, []);

  return {
    uploading,
    uploadResult,
    error,
    uploadFile,
    reset,
    setError: setErrorState,
  };
}
