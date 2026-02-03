const withSerwistInit = require('@serwist/next').default;
const crypto = require('crypto');

const revision = crypto.randomUUID();
const withSerwist = withSerwistInit({
  additionalPrecacheEntries: [{ url: '/~offline', revision }],
  swSrc: 'app/sw.ts',
  swDest: 'public/sw.js',
  disable: process.env.NODE_ENV === 'development',
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // v1, v10, v20 → (dashboard) 루트로 통합. 구 경로 접속 시 새 경로로 리다이렉트
  async redirects() {
    return [
      { source: '/v20', destination: '/', permanent: true },
      { source: '/v20/:path*', destination: '/:path*', permanent: true },
      { source: '/v1', destination: '/', permanent: true },
      { source: '/v1/spam-detection', destination: '/spam-detection', permanent: true },
      { source: '/v10', destination: '/', permanent: true },
      { source: '/v10/upload', destination: '/upload', permanent: true },
      { source: '/v10/upload/:path*', destination: '/upload/:path*', permanent: true },
    ];
  },

  // === 성능 최적화 ===
  experimental: {
    optimizePackageImports: ['react-markdown', 'zustand'],
  },
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  compress: true,
  poweredByHeader: false,

  // Next.js 16 호환성
  typescript: {
    ignoreBuildErrors: false,
  },
};

module.exports = withSerwist(nextConfig);
