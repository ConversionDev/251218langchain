'use client';

import { useEffect } from 'react';

/**
 * Service Worker 등록 컴포넌트
 *
 * 프로덕션 빌드에서만 Service Worker를 등록합니다.
 */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    // 프로덕션 환경에서만 Service Worker 등록
    if (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      process.env.NODE_ENV === 'production'
    ) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log(
            '[ServiceWorker] 등록 성공:',
            registration.scope
          );
        })
        .catch((error) => {
          console.error('[ServiceWorker] 등록 실패:', error);
        });
    }
  }, []);

  return null;
}
