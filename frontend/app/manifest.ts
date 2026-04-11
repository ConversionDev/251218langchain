import type { MetadataRoute } from "next";

/**
 * Web App Manifest — PWA 설치 메타데이터 (이름, 아이콘, start_url, standalone).
 * DevTools → Application → Manifest 에서 검증 가능.
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Success DNA | Enterprise HR Solution",
    short_name: "Success DNA",
    description:
      "엔터프라이즈 HR 솔루션 — Core, Intelligence, Credential, Performance",
    start_url: "/hr",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#0f172a",
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
    ],
  };
}
