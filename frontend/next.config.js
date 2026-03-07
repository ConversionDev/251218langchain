/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,

  async redirects() {
    return [];
  },

  experimental: {
    optimizePackageImports: [
      'react-markdown',
      'zustand',
      'framer-motion',
      '@radix-ui/react-dialog',
      '@radix-ui/react-label',
      '@radix-ui/react-slot',
    ],
    turbopackFileSystemCacheForDev: true,
  },
  // 로컬에서만 Turbopack 루트 설정 (Windows 경로 해석 방지). Vercel 빌드에서는 미설정으로 경고 제거.
  ...(process.env.VERCEL ? {} : { turbopack: { root: path.resolve(__dirname) } }),
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
        pathname: '/**',
      },
    ],
  },
  compress: true,
  poweredByHeader: false,

  typescript: {
    ignoreBuildErrors: false,
  },
};

module.exports = nextConfig;
