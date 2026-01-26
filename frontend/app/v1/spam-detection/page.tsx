"use client";

import { useState } from "react";
import SpamDetectionForm from "@/components/v1/SpamDetectionForm";
import SpamResultCard from "@/components/v1/SpamResultCard";
import type {
  EmailMetadata,
  SpamDetectionResponse,
} from "@/lib/types/spam";
import { detectSpam } from "@/lib/api/spamDetection";

export default function SpamDetectionPage() {
  const [result, setResult] = useState<SpamDetectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (emailMetadata: EmailMetadata) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      console.log("[DEBUG] 스팸 감지 요청 시작:", emailMetadata);
      const response = await detectSpam(emailMetadata);
      console.log("[DEBUG] 스팸 감지 응답:", response);
      setResult(response);
    } catch (err) {
      console.error("[ERROR] 스팸 감지 오류:", err);
      const errorMessage =
        err instanceof Error
          ? err.message
          : "스팸 감지 중 오류가 발생했습니다.";
      setError(errorMessage);

      // 네트워크 오류인 경우 추가 안내
      if (err instanceof TypeError && err.message.includes("fetch")) {
        setError(
          `백엔드 서버에 연결할 수 없습니다.\n\n` +
          `확인 사항:\n` +
          `1. 백엔드 서버가 실행 중인지 확인 (http://localhost:8000)\n` +
          `2. CORS 설정이 올바른지 확인\n` +
          `3. 브라우저 콘솔에서 자세한 오류 확인`
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="spam-detection-page">
      <header className="page-header">
        <h1>🛡️ 스팸 감지 시스템</h1>
        <p className="subtitle">
          LLaMA와 EXAONE 모델을 활용한 이메일 스팸 감지
        </p>
      </header>

      <main className="page-main">
        <div className="input-section">
          <h2>이메일 입력</h2>
          <SpamDetectionForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {isLoading && (
          <div className="loading-section">
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>스팸 감지 분석 중...</p>
              <p className="loading-detail">
                ⏳ LLaMA 게이트웨이 실행 중...
              </p>
              <p className="loading-note">
                첫 실행 시 모델 로딩으로 인해 10-30초 정도 소요될 수 있습니다.
                <br />
                EXAONE 분석이 필요한 경우 추가로 30초-1분 정도 더 걸릴 수 있습니다.
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="error-section">
            <div className="error-card">
              <h3>오류 발생</h3>
              <p style={{ whiteSpace: "pre-line" }}>{error}</p>
            </div>
          </div>
        )}

        {result && !isLoading && (
          <div className="result-section">
            <h2>분석 결과</h2>
            <SpamResultCard result={result} />
          </div>
        )}
      </main>

      <style jsx>{`
        .spam-detection-page {
          min-height: 100vh;
          background: #0a0a1a;
          color: #e0e0e0;
          padding: 2rem 1rem;
        }

        .page-header {
          max-width: 1200px;
          margin: 0 auto 2rem;
          text-align: center;
          padding: 2rem 0;
        }

        .page-header h1 {
          font-size: 2rem;
          font-weight: 700;
          color: #fff;
          margin: 0 0 0.5rem 0;
        }

        .subtitle {
          font-size: 1rem;
          color: #a0a0a0;
          margin: 0;
        }

        .page-main {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .input-section,
        .result-section {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(102, 126, 234, 0.2);
          border-radius: 1rem;
          padding: 1.5rem;
        }

        .input-section h2,
        .result-section h2 {
          margin: 0 0 1.5rem 0;
          color: #fff;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .loading-section {
          display: flex;
          justify-content: center;
          align-items: center;
          padding: 3rem;
        }

        .loading-spinner {
          text-align: center;
        }

        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(102, 126, 234, 0.2);
          border-top-color: #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 1rem;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .loading-spinner p {
          color: #e0e0e0;
          margin: 0.5rem 0;
        }

        .loading-detail {
          font-size: 0.9rem;
          color: #e0e0e0;
          font-weight: 500;
          margin: 0.5rem 0;
        }

        .loading-note {
          font-size: 0.8rem;
          color: #a0a0a0;
          margin-top: 1rem;
          line-height: 1.5;
        }

        .error-section {
          padding: 1rem;
        }

        .error-card {
          background: rgba(248, 113, 113, 0.1);
          border: 1px solid rgba(248, 113, 113, 0.3);
          border-radius: 0.75rem;
          padding: 1.5rem;
        }

        .error-card h3 {
          margin: 0 0 0.5rem 0;
          color: #f87171;
          font-size: 1.1rem;
        }

        .error-card p {
          margin: 0;
          color: #e0e0e0;
        }

        @media (max-width: 768px) {
          .spam-detection-page {
            padding: 1rem 0.5rem;
          }

          .page-header h1 {
            font-size: 1.5rem;
          }

          .input-section,
          .result-section {
            padding: 1rem;
          }
        }
      `}</style>
    </div>
  );
}
