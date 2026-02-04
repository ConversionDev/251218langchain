import type { Metadata } from "next";
import { Toaster } from "sonner";
import { RegisterSw } from "@/components/RegisterSw";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "Success DNA | Enterprise HR Solution",
  description: "엔터프라이즈 HR 솔루션 - Core, Intelligence, Credential, Performance",
};

const themeScript = `
  (function() {
    const key = 'theme';
    const stored = localStorage.getItem(key);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const dark = stored === 'dark' || (stored !== 'light' && prefersDark);
    document.documentElement.classList.toggle('dark', dark);
  })();
`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-background font-sans text-foreground">
        {children}
        <Toaster richColors position="top-right" closeButton duration={1500} />
        <RegisterSw />
      </body>
    </html>
  );
}
