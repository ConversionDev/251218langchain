import type { Metadata, Viewport } from "next";
import { Toaster } from "sonner";
import { RegisterSw } from "@/components/RegisterSw";
import { RoleSwitcher } from "@/components/layout/RoleSwitcher";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "Success DNA | Enterprise HR Solution",
  description: "엔터프라이즈 HR 솔루션 - Core, Intelligence, Credential, Performance",
  icons: {
    icon: [{ url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" }],
    apple: "/icons/icon-192.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#0f172a",
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
        <link
          rel="stylesheet"
          as="style"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css"
        />
      </head>
      <body className="min-h-screen bg-background font-sans text-foreground">
        {children}
        <Toaster richColors position="top-right" closeButton duration={1500} />
        <RegisterSw />
        <RoleSwitcher />
      </body>
    </html>
  );
}
