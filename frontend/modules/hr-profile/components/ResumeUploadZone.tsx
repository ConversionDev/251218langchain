"use client";

import { useCallback, useState } from "react";
import { Upload, FileText } from "lucide-react";
import { fileToText } from "../services/fileToResumeText";
import { parseResumeFromText } from "../services/resumeParser";
import type { Resume } from "@/modules/shared/types";

const ACCEPT = ".pdf,.txt,application/pdf,text/plain";

interface ResumeUploadZoneProps {
  onParsed: (resume: Resume) => void;
  onError?: (message: string) => void;
}

export function ResumeUploadZone({ onParsed, onError }: ResumeUploadZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);

  const processFile = useCallback(
    async (file: File) => {
      if (!file) return;
      setLoading(true);
      onError?.("");
      try {
        const text = await fileToText(file);
        const resume = parseResumeFromText(text);
        onParsed(resume);
      } catch (e) {
        const msg = e instanceof Error ? e.message : "파일을 처리할 수 없습니다.";
        onError?.(msg);
      } finally {
        setLoading(false);
      }
    },
    [onParsed, onError]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer?.files?.[0];
      if (file && (file.type === "application/pdf" || file.type === "text/plain" || /\.(pdf|txt)$/i.test(file.name))) {
        processFile(file);
      } else {
        onError?.("PDF 또는 TXT 파일만 넣어 주세요.");
      }
    },
    [processFile, onError]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) processFile(file);
      e.target.value = "";
    },
    [processFile]
  );

  return (
    <div className="flex flex-1 flex-col gap-3">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`flex min-h-[160px] flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
          dragging ? "border-primary bg-primary/5" : "border-border bg-muted/30"
        } ${loading ? "pointer-events-none opacity-70" : ""}`}
      >
        <input
          type="file"
          accept={ACCEPT}
          onChange={handleFileInput}
          className="hidden"
          id="resume-upload-input"
          disabled={loading}
        />
        <label htmlFor="resume-upload-input" className="cursor-pointer">
          {loading ? (
            <span className="text-sm text-muted-foreground">처리 중…</span>
          ) : (
            <>
              <Upload className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium text-foreground">
                이력서 파일을 여기에 놓거나 클릭하세요
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">PDF, TXT (드래그 앤 드롭)</p>
            </>
          )}
        </label>
      </div>
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <FileText className="h-3.5 w-3.5" />
        학력·경력·기술·자격 섹션이 있으면 자동으로 채워집니다. 업로드 후 수정할 수 있습니다.
      </p>
    </div>
  );
}
