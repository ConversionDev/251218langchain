import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "이력서 | Resume",
  description: "포트폴리오 이력서",
};

export default function ResumeLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return children;
}
