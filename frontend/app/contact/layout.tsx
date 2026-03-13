import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "연락처 | 강경구",
  description: "강경구에게 연락하는 방법입니다.",
};

export default function ContactLayout({
  children,
}: { children: React.ReactNode }) {
  return <>{children}</>;
}
