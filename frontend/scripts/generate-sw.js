/**
 * 빌드 후 실행: Next.js 빌드 결과(.next)를 기반으로 Workbox 서비스 워커 생성.
 * Turbopack/Webpack 무관하게 동작.
 *
 * 사용: pnpm build (next build 후 자동 실행) 또는 node scripts/generate-sw.js
 *
 * 오프라인 동작: static/chunks, css, media를 precache하므로 한 번 로드 후에는
 * Performance 시뮬레이션(Zustand + 순수 getPerformanceMetrics) 등 클라이언트 로직이
 * 네트워크 없이 동작합니다.
 */
const path = require('path');
const { generateSW } = require('workbox-build');

const ROOT = path.resolve(__dirname, '..');
const GLOB_DIR = path.join(ROOT, '.next');
const SW_DEST = path.join(ROOT, 'public', 'sw.js');

generateSW({
  globDirectory: GLOB_DIR,
  globPatterns: [
    'static/chunks/**/*.js',
    'static/css/**/*.css',
    'static/media/**/*',
  ],
  globIgnores: ['**/node_modules/**'],
  swDest: SW_DEST,
  mode: 'production',
  sourcemap: false,
  clientsClaim: true,
  skipWaiting: true,
  runtimeCaching: [
    {
      urlPattern: /^https?:\/\/.*\/_next\/.*/i,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'next-static',
        expiration: { maxEntries: 64, maxAgeSeconds: 60 * 60 * 24 * 30 },
      },
    },
  ],
})
  .then(({ count, size }) => {
    console.log(`[workbox] Generated public/sw.js: ${count} files, ${(size / 1024).toFixed(1)} KB`);
  })
  .catch((err) => {
    console.error('[workbox] generate-sw failed:', err);
    process.exit(1);
  });
