import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "V10 어드민 대시보드",
  description: "V10 어드민 관리 시스템",
};

export default function V10Layout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <>{children}</>;
}
