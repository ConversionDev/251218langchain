"use client";

import BottomNavigation from "@/components/v10/BottomNavigation";
import UploadSidebar from "@/components/v10/upload/UploadSidebar";

export default function UploadLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="upload-container">
      <header className="upload-header">
        <h1 className="header-title">파일 업로드</h1>
      </header>

      <div className="upload-layout">
        <UploadSidebar />
        <main className="upload-main">{children}</main>
      </div>

      <BottomNavigation currentPage="upload" />

      <style jsx>{`
        .upload-container {
          min-height: 100vh;
          background: #f9fafb;
          display: flex;
          flex-direction: column;
        }

        .upload-header {
          background: #ffffff;
          border-bottom: 1px solid #e5e7eb;
          padding: 1rem 1.25rem;
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .header-title {
          font-size: 1.25rem;
          font-weight: 700;
          color: #1f2937;
        }

        .upload-layout {
          display: flex;
          flex: 1;
          padding-bottom: 5rem;
        }

        /* 메인 업로드 영역 */
        .upload-main {
          flex: 1;
          padding: 2rem;
          overflow-y: auto;
        }

        @media (max-width: 768px) {
          .upload-layout {
            flex-direction: column;
          }

          .upload-main {
            padding: 1.5rem 1rem;
          }
        }
      `}</style>
    </div>
  );
}
