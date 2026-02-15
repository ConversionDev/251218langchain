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
  // Turbopack 루트를 명시해 경로 해석 오류 방지 (Windows)
  turbopack: {
    root: path.resolve(__dirname),
  },
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  compress: true,
  poweredByHeader: false,

  typescript: {
    ignoreBuildErrors: false,
  },
};

module.exports = nextConfig;
