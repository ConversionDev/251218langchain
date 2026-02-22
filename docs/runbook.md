# 실행·데이터 요약

## 프론트엔드 (Next.js PWA)

- **설치·실행**: `cd frontend` → `pnpm install` → `pnpm dev`. 브라우저에서 [http://localhost:3000](http://localhost:3000) 확인.
- **환경 변수**: `.env.local`에 `NEXT_PUBLIC_API_URL=http://localhost:8000` (또는 배포 백엔드 URL). 프론트에서 API 호출 시 사용. 배포 시 반드시 실제 백엔드 주소로 설정.
- **빌드**: `pnpm build` / `pnpm start`. PWA는 모바일에서 "홈 화면에 추가"로 설치 가능.
- **기술 스택**: Next.js 14, TypeScript. 채팅·벡터 검색은 백엔드 `/api/chat` 등과 연동.

## 데이터 폴더 (app/data)

도메인별로 **raw** → **prepared** → **sft** 3단계 구조를 통일해서 사용. 모든 경로는 `core.paths.get_data_dir()` = `app/data` 기준.

| 폴더 | 용도 |
|------|------|
| **raw** | 원본/수집 데이터 |
| **prepared** | 전처리·정제된 중간 결과 (예: disclosure 청킹용 텍스트) |
| **sft** | SFT 형식, processed/filtered 등 학습용 분할 포함 |

**도메인**: **disclosure/** (공시 IFRS·ISO 등), **soccer/** (데모용), **email/** (이메일 SFT: raw, sft/sft_train.jsonl, sft/processed, sft/filtered).  
**학습 출력**: `core.paths.get_output_dir()` = `app/artifacts/fine_tuned/` (EXAONE LoRA, LLaMA 어댑터 등).  
이전 `data/sft_dataset`은 제거되었고, 이메일 SFT는 `data/email/sft/` 아래로 통합됨.

## 배포 시 확인

- **프론트**: `NEXT_PUBLIC_API_URL`을 배포 환경의 백엔드 URL로 설정 후 빌드. (`pnpm build`는 TypeScript 검사 포함.)
- **백엔드**: CORS 허용 도메인은 환경 변수 `CORS_ORIGINS`로 설정. 쉼표 구분 (예: `CORS_ORIGINS=https://app.example.com,https://www.example.com`). 비우면 `*`(전체 허용).
- **DB**: `DATABASE_URL` 또는 `POSTGRES_CONNECTION_STRING` 설정. `AUTO_MIGRATE=true`면 기동 시 Alembic `upgrade` 실행.
