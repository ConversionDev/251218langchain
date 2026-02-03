"use client";

import { useState, useCallback } from "react";
import { useFileUpload } from "@/hooks/useFileUpload";

type DataType = "players" | "teams" | "stadiums" | "schedules";

interface UploadDropZoneProps {
  dataType: DataType;
  title: string;
}

export default function UploadDropZone({ dataType, title }: UploadDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const { uploading, uploadResult, error, uploadFile, cancelUpload, setError } = useFileUpload(dataType);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      const jsonlFile = files.find((file) => file.name.endsWith(".jsonl"));

      if (!jsonlFile) {
        setError("JSONL 파일만 업로드 가능합니다.");
        return;
      }

      await uploadFile(jsonlFile);
    },
    [uploadFile]
  );

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      if (!file.name.endsWith(".jsonl")) {
        setError("JSONL 파일만 업로드 가능합니다.");
        return;
      }

      await uploadFile(file);
    },
    [uploadFile]
  );

  return (
    <>
      <div className="upload-section">
        <div className="jsonl-badge">JSONL 업로드</div>
        <h2 className="section-title">{title} 데이터 업로드</h2>
        <p className="section-description">
          <strong>.jsonl</strong> 파일을 이 영역에 드래그앤드롭하거나, 영역을 클릭해 파일을 선택하세요.
        </p>

        <div
          className={`drop-zone ${isDragging ? "dragging" : ""} ${uploading ? "uploading" : ""}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id={`file-input-${dataType}`}
            accept=".jsonl"
            onChange={handleFileSelect}
            disabled={uploading}
            style={{ display: "none" }}
          />
          <label htmlFor={`file-input-${dataType}`} className="drop-zone-label">
            {uploading ? (
              <>
                <div className="upload-spinner"></div>
                <p>업로드 중...</p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    cancelUpload();
                  }}
                  className="cancel-button"
                >
                  취소
                </button>
              </>
            ) : (
              <>
                <svg
                  width="64"
                  height="64"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
                <p className="drop-zone-text">
                  {isDragging
                    ? "여기에 .jsonl 파일을 놓으세요"
                    : "파일을 드래그하거나 여기를 클릭하여 .jsonl 선택"}
                </p>
                <p className="drop-zone-hint">
                  <span className="drop-zone-hint-badge">.jsonl</span> 파일만 업로드 가능
                </p>
              </>
            )}
          </label>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {uploadResult && (
          <div className="success-message">
            <div className="success-header">
              <span className="success-icon">✅</span>
              <h3>업로드 완료!</h3>
            </div>
            <div className="result-details">
              <p>
                <strong>파일명:</strong> {uploadResult.filename}
              </p>
              {uploadResult.data_type && (
                <p>
                  <strong>데이터 타입:</strong> {uploadResult.data_type}
                </p>
              )}
              {uploadResult.message && (
                <p>
                  <strong>메시지:</strong> {uploadResult.message}
                </p>
              )}
              {uploadResult.results && (
                <div className="result-stats">
                  <p>
                    <strong>관계형 DB:</strong> {uploadResult.results.db || 0}개 저장
                  </p>
                  <p>
                    <strong>벡터 스토어:</strong> {uploadResult.results.vector || 0}개 저장
                  </p>
                </div>
              )}
              {/* 미리보기 데이터 (players 타입일 때) */}
              {uploadResult.preview && (
                <div className="preview-section">
                  <h4>미리보기 (첫 {uploadResult.preview_rows || 0}개 행)</h4>
                  <p className="preview-info">
                    총 {uploadResult.total_rows || 0}개 행 중 첫 {uploadResult.preview_rows || 0}개 행을 표시합니다.
                  </p>
                  <div className="preview-list">
                    {uploadResult.preview.map((item: any, index: number) => (
                      <div key={index} className="preview-item">
                        <div className="preview-row-number">행 {item.row}</div>
                        {item.error ? (
                          <div className="preview-error">
                            <strong>오류:</strong> {item.error}
                            {item.raw && <pre>{item.raw}</pre>}
                          </div>
                        ) : (
                          <pre className="preview-data">{JSON.stringify(item.data, null, 2)}</pre>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .upload-section {
          max-width: 800px;
          margin: 0 auto;
        }

        .jsonl-badge {
          display: inline-block;
          margin-bottom: 0.75rem;
          padding: 0.25rem 0.75rem;
          font-size: 0.75rem;
          font-weight: 700;
          color: #1d4ed8;
          background: #dbeafe;
          border: 1px solid #3b82f6;
          border-radius: 9999px;
          letter-spacing: 0.025em;
        }

        .section-title {
          font-size: 1.5rem;
          font-weight: 700;
          color: #1f2937;
          margin-bottom: 0.5rem;
        }

        .section-description {
          color: #6b7280;
          margin-bottom: 2rem;
        }

        .section-description strong {
          color: #1d4ed8;
        }

        /* 드롭 존 */
        .drop-zone {
          border: 2px dashed #93c5fd;
          border-radius: 0.75rem;
          padding: 3rem 2rem;
          min-height: 180px;
          text-align: center;
          background: #eff6ff;
          transition: all 0.3s;
          cursor: pointer;
        }

        .drop-zone:hover {
          border-color: #3b82f6;
          background: #dbeafe;
        }

        .drop-zone.dragging {
          border-color: #3b82f6;
          background: #bfdbfe;
          transform: scale(1.01);
        }

        .drop-zone.uploading {
          border-color: #10b981;
          background: #f0fdf4;
          cursor: not-allowed;
        }

        .drop-zone-label {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          cursor: pointer;
        }

        .drop-zone svg {
          color: #6b7280;
        }

        .drop-zone.dragging svg,
        .drop-zone:hover svg {
          color: #3b82f6;
        }

        .drop-zone-text {
          font-size: 1.125rem;
          font-weight: 600;
          color: #1f2937;
          margin: 0;
        }

        .drop-zone-hint {
          font-size: 0.875rem;
          color: #6b7280;
          margin: 0;
        }

        .drop-zone-hint-badge {
          display: inline-block;
          padding: 0.125rem 0.5rem;
          font-size: 0.8rem;
          font-weight: 600;
          color: #1d4ed8;
          background: #ffffff;
          border: 1px solid #93c5fd;
          border-radius: 0.375rem;
        }

        .upload-spinner {
          width: 48px;
          height: 48px;
          border: 4px solid #e5e7eb;
          border-top-color: #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .cancel-button {
          margin-top: 1rem;
          padding: 0.5rem 1.5rem;
          background: #ef4444;
          color: #ffffff;
          border: none;
          border-radius: 0.5rem;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .cancel-button:hover {
          background: #dc2626;
          transform: scale(1.05);
        }

        .cancel-button:active {
          transform: scale(0.95);
        }

        /* 에러 메시지 */
        .error-message {
          margin-top: 1.5rem;
          padding: 1rem;
          background: #fee2e2;
          border: 1px solid #ef4444;
          border-radius: 0.5rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          color: #dc2626;
          font-size: 0.875rem;
        }

        .error-icon {
          font-size: 1.25rem;
          color: #f59e0b;
          flex-shrink: 0;
        }

        /* 성공 메시지 */
        .success-message {
          margin-top: 1.5rem;
          padding: 1.5rem;
          background: #f0fdf4;
          border: 1px solid #86efac;
          border-radius: 0.75rem;
        }

        .success-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1rem;
        }

        .success-header h3 {
          font-size: 1.125rem;
          font-weight: 600;
          color: #166534;
          margin: 0;
        }

        .success-icon {
          font-size: 1.5rem;
        }

        .result-details {
          color: #166534;
        }

        .result-details p {
          margin: 0.5rem 0;
        }

        .result-stats {
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #86efac;
        }

        .result-stats p {
          font-weight: 600;
        }

        /* 미리보기 섹션 */
        .preview-section {
          margin-top: 1.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid #86efac;
        }

        .preview-section h4 {
          font-size: 1rem;
          font-weight: 600;
          color: #166534;
          margin-bottom: 0.5rem;
        }

        .preview-info {
          font-size: 0.875rem;
          color: #166534;
          margin-bottom: 1rem;
        }

        .preview-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .preview-item {
          background: #ffffff;
          border: 1px solid #d1d5db;
          border-radius: 0.5rem;
          padding: 1rem;
        }

        .preview-row-number {
          font-weight: 600;
          color: #3b82f6;
          margin-bottom: 0.5rem;
          font-size: 0.875rem;
        }

        .preview-data {
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 0.25rem;
          padding: 0.75rem;
          font-size: 0.75rem;
          overflow-x: auto;
          margin: 0;
          color: #1f2937;
          max-height: 200px;
          overflow-y: auto;
        }

        .preview-error {
          color: #dc2626;
          font-size: 0.875rem;
        }

        .preview-error pre {
          background: #fee2e2;
          border: 1px solid #fecaca;
          border-radius: 0.25rem;
          padding: 0.5rem;
          margin-top: 0.5rem;
          font-size: 0.75rem;
          overflow-x: auto;
        }

        /* 다크 모드 */
        :global(.dark) .jsonl-badge {
          color: #93c5fd;
          background: #1e3a8a;
          border-color: #3b82f6;
        }
        :global(.dark) .upload-section .section-title {
          color: #f1f5f9;
        }
        :global(.dark) .upload-section .section-description {
          color: #94a3b8;
        }
        :global(.dark) .upload-section .section-description strong {
          color: #93c5fd;
        }
        :global(.dark) .drop-zone {
          border-color: #3b82f6;
          background: #1e3a8a;
        }
        :global(.dark) .drop-zone:hover {
          border-color: #3b82f6;
          background: #334155;
        }
        :global(.dark) .drop-zone.dragging {
          border-color: #3b82f6;
          background: #1e3a5f;
        }
        :global(.dark) .drop-zone.uploading {
          border-color: #22c55e;
          background: #14532d;
        }
        :global(.dark) .drop-zone svg {
          color: #94a3b8;
        }
        :global(.dark) .drop-zone.dragging svg,
        :global(.dark) .drop-zone:hover svg {
          color: #60a5fa;
        }
        :global(.dark) .drop-zone-text {
          color: #f1f5f9;
        }
        :global(.dark) .drop-zone-hint {
          color: #94a3b8;
        }
        :global(.dark) .drop-zone-hint-badge {
          color: #93c5fd;
          background: #0f172a;
          border-color: #3b82f6;
        }
        :global(.dark) .upload-spinner {
          border-color: #334155;
          border-top-color: #3b82f6;
        }
        :global(.dark) .error-message {
          background: #7f1d1d;
          border-color: #b91c1c;
          color: #fecaca;
        }
        :global(.dark) .success-message {
          background: #14532d;
          border-color: #166534;
        }
        :global(.dark) .success-header h3,
        :global(.dark) .result-details {
          color: #bbf7d0;
        }
        :global(.dark) .result-stats {
          border-top-color: #166534;
        }
        :global(.dark) .preview-section h4,
        :global(.dark) .preview-info {
          color: #bbf7d0;
        }
        :global(.dark) .preview-item {
          background: #1e293b;
          border-color: #475569;
        }
        :global(.dark) .preview-row-number {
          color: #60a5fa;
        }
        :global(.dark) .preview-data {
          background: #0f172a;
          border-color: #475569;
          color: #e2e8f0;
        }
        :global(.dark) .preview-error pre {
          background: #7f1d1d;
          border-color: #b91c1c;
        }
      `}</style>
    </>
  );
}
