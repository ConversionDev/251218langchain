/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async redirects() {
    return [];
  },

  experimental: {
    optimizePackageImports: ['react-markdown', 'zustand'],
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
