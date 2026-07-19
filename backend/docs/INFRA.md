# 인프라 운영 (INFRA)

> 최종 갱신: 2026-07-19 — AWS 계정 복구·t4g.large(ARM) 이전 + 채팅 LLM 운영 정리(§7)

## 1. 현재 인프라 요약

| 항목 | 값 |
|---|---|
| AWS 계정 | 2056-5027-7922 (kanggyeonggu) · 서울(ap-northeast-2) |
| EC2 인스턴스 | `i-01c24dba123582efe` (Name: `rag-api-arm`) |
| 인스턴스 타입 | **t4g.large** — ARM Graviton2, 2 vCPU, 8GB RAM, 버스터블(기준선 30%/vCPU, Unlimited) |
| AMI | Ubuntu 24.04 LTS ARM64 (`ami-04e3ca2324a305ad0`) |
| 디스크 | 30GB gp3 (DeleteOnTermination=true) |
| **Elastic IP** | **43.201.214.82** (고정 — 중지/시작해도 불변) |
| 보안그룹 | `rag-api-sg` (`sg-00251c1a2e8645dc9`) — 22/80/443 인바운드 |
| SSH 키 | 키 페어 `RSA` (기존 재사용, 로컬 `RSA.pem`) |
| DNS | 가비아 — `api.kanggyeonggu.store` A 레코드 → 43.201.214.82 |
| 프론트엔드 | Vercel (EC2와 무관, `www.kanggyeonggu.store`) |
| DB / 캐시 | Neon PostgreSQL / Upstash Redis (외부 서비스 — EC2 수명주기와 무관) |

## 2. 2026-07 이전(migration) 배경과 경위

1. **프리플랜 종료(6/18) → 계정 자동 폐쇄**: 신 프리티어 정책상 무료 플랜은 6개월 후 계정이 닫힌다. 구 인스턴스(m7i-flex.large, `chat`)가 중지되고 퍼블릭 IP가 반납됐다.
2. 반납된 IP(13.125.252.12)는 타인에게 재할당됐고, 가비아 DNS와 GitHub 시크릿 `EC2_HOST`가 그 낡은 IP를 가리켜 **배포 SSH 실패 + API 다운**이 발생했다.
3. **7/19 유료 플랜 전환으로 계정 재활성화** (기한 8/17 전). 크레딧 **$96.22**는 유지되며 **2026-12-18 만료**.
4. 새 프리티어 재수령은 불가(과거 계정 보유자는 부적격)하므로 동일 계정 유지가 확정.
5. 구 인스턴스는 종료(terminate)하고 구 볼륨(`vol-09a52c3632ff41fbe`, 27GB)은 함께 삭제. 코드(GitHub)·모델(GGUF, 로컬 보유)·DB(Neon)·Redis(Upstash)가 모두 외부에 있어 유실 데이터 없음.

## 3. 왜 t4g.large(ARM)인가

- 구 m7i-flex.large(x86): $0.1177/hr (월 $86) → **t4g.large: $0.0832/hr (월 $60.7) — 29% 절감** (서울 온디맨드 기준)
- 동일 8GB RAM — EXAONE 7.8B GGUF Q4_K_M(4.5GB) CPU 서빙 요구사항 충족 (기존 8GB 운영 검증됨)
- **코드 수정 0**: GGUF는 아키텍처 무관, 파이썬/자바 소스 동일. `deploy.yml`이 서버에서 pip를 새로 설치하므로 ARM 휠이 자동 적용됨. 단 `llama-cpp-python`은 ARM에서 소스 빌드되므로 `build-essential`·`cmake` 필요(셋업 시 설치 완료)
- 버스터블 특성: LLM 추론 시 CPU 100% 버스트는 적립 크레딧으로 흡수. 지속 고부하 시 vCPU-시간당 소액 추가 과금 — 데모성 사용 패턴에는 영향 미미. 상시 고부하 전환 시 m7g.large($0.1003/hr) 검토

## 4. 비용 모델 (평시 중지 · 필요 시 기동)

| 항목 | 비용 |
|---|---|
| 인스턴스 중지 중 | EBS 30GB ~$2.7/월 + Elastic IP ~$3.65/월 = **고정 ~$6.4/월** |
| 인스턴스 가동 시 | +$0.0832/시간 |
| 크레딧 | $96.22 (2026-12-18 만료) — 청구액에 자동 차감 |

> 크레딧 기준 약 770시간 가동 가능. 12월 만료 전까지 실비 0원 운영 목표.
> ⚠️ Elastic IP는 인스턴스가 꺼져 있어도 과금됨(2024.2 IPv4 유료화). IP 고정 가치로 수용.

## 5. 운영 절차

### 기동 (면접·시연 전)
1. AWS 콘솔 → EC2 → `rag-api-arm` → 인스턴스 시작 (또는 CloudShell: `aws ec2 start-instances --instance-ids i-01c24dba123582efe`)
2. systemd(`rag-api`, `rag-gateway`)와 nginx가 부팅 시 자동 기동 → 별도 조작 불필요
3. 확인: `https://api.kanggyeonggu.store/health`

### 중지 (사용 후)
- 콘솔에서 인스턴스 중지 (또는 `aws ec2 stop-instances --instance-ids i-01c24dba123582efe`)
- Elastic IP 덕분에 다음 기동 때도 IP·DNS·시크릿 변경 불필요

### 배포
- `main` 푸시 → GitHub Actions `Deploy to EC2` 자동 실행 (rsync → pip(변경 시) → systemd 재시작 → 헬스체크)
- **인스턴스가 꺼져 있으면 EC2 단계만 실패** (Vercel 프론트 배포는 정상 진행) → 켠 뒤 Actions에서 Re-run
- GitHub 시크릿: `EC2_HOST=43.201.214.82`, `EC2_USERNAME=ubuntu`, `EC2_SSH_KEY`=RSA 키(기존 재사용— 변경 불필요)

### SSL (Let's Encrypt)
- 새 인스턴스마다 필수: `sudo certbot --nginx -d api.kanggyeonggu.store` + `sudo systemctl enable --now certbot.timer`
- nginx 라우팅 원본: [`nginx_default.conf`](nginx_default.conf) — `/` → 8000(FastAPI), `/auth/` → 8080(Gateway), SSE 전용 location(버퍼링 off·600s)

### GGUF 모델
- 서버 경로: `/home/ubuntu/app/artifacts/fine_tuned/exaone/gguf/exaone_competency_q4_k_m.gguf` (4.5GB)
- CI rsync에서 제외되므로 서버 교체 시 로컬에서 `scp`로 1회 업로드
- ⚠️ **정본은 v3 패치본이다.** 로컬 gguf 폴더의 원본(패치 전) 파일은 tokenizer merges가 누락되어
  `cannot find tokenizer merges in model file` 로 로드에 실패한다(TROUBLESHOOTING 참고).
  2026-07-19부터 로컬·서버 모두 정식 파일명(`exaone_competency_q4_k_m.gguf`)에 **v3 내용**이 들어가 있으므로
  이 파일명을 그대로 업로드하면 된다. `_fixed`(중간 시도)·`_v3`(원본 보존용)는 참고용.

### FAISS 인덱스 (artifacts/faiss/)
- `disclosures.index`·`competency_anchors.index`(+id_map)를 서버에 업로드해 두었으나,
  **현행 코드는 런타임에 `load_faiss_indices()`를 호출하지 않는다**(메모리 절약 설계 — 로컬 동일).
  RAG는 pgvector로 동작하며, FAISS는 오프라인 파이프라인(클러스터링·시각화)용.

## 6. 문서 구조 변경 (2026-07-19)

- 루트 `docs/` 폴더를 **`backend/docs/`로 통합 이동** (ARCHITECTURE·FEATURES·FRONTEND·IMPLEMENTATION·MODEL_COMPARISON·PORTFOLIO·TROUBLESHOOTING·nginx_default.conf·archive/)
- `frontend.md` → `FRONTEND.md` 대소문자 정규화 (GitHub(리눅스)에서 링크 404 방지)
- 루트 README·`backend/ontology/apps/ARCHITECTURE.md`(포인터)의 링크 경로 갱신

## 7. 채팅 LLM 운영 (2026-07-19 정리)

### 7.1 provider 구조

| 용도 | 로컬 | 배포(EC2) |
|---|---|---|
| 채팅 최종 답변 | 학습 EXAONE (transformers, GPU) | **Gemini** (`CHAT_LLM=gemini`) |
| 역량/성과 분류(비동기) | 학습 EXAONE | 학습 EXAONE GGUF (llama.cpp CPU) |
| 스팸 1차 분류·이력서 폼 추출 | 학습 LLaMA / EXAONE | Gemini (`SPAM_CLASSIFIER=gemini` 등) |

### 7.2 이번에 고친 버그·개선 (커밋 기준)

1. **`364670e` — CHAT_LLM=gemini 강제 적용**: LangGraph 상태(state)에 `llama_cpp`가 새어 들어와
   Gemini 설정을 덮어쓰고 EXAONE CPU로 답변하던 버그(문항당 7분+). `model_node`에서
   `_chat_use_gemini()`가 참이면 provider를 무조건 gemini로 고정. provider 해석 로그 추가
   (`[MODEL] provider 해석: ... (default=..., state=...)`) — 재발 시 이 로그가 원인을 알려준다.
   부수 개선: 강제 도구(1턴 최적화) 분기에서 불필요하게 GGUF 4.5GB를 로드하던 비효율 제거(지연 생성).
2. **`f7e7887` — get_employee_info에 5대 지표 수치 노출**: 기존엔 "Success DNA 보유" 문구만 반환해
   "OOO의 5대 지표" 질문에 답변 불가. 리더십·기술력·창의성·협업·적응력 수치를 도구 출력에 포함.
3. **`518bce4` — Gemini 429 폴백 체인**: 무료 티어 일일 쿼터가 **모델별 ~20회**로 작다.
   첫 토큰 전 429 발생 시 `flash-lite → 2.5-flash → 2.0-flash` 순으로 자동 전환(`gemini_chat.py`).
   스트리밍 시작 후에는 폴백하지 않는다(중복 답변 방지).

### 7.3 Gemini 무료 쿼터 운영 수칙

- 모델당 일 ~20회, 폴백 체인으로 실질 일 ~60회. 리셋은 태평양 기준 자정.
- 대량 시연(면접 등) 예정 시: Google AI Studio에서 유료 결제 연결 권장(이 사용량이면 월 $1 미만).

### 7.4 학습 EXAONE으로 채팅 전환(시연용)

```bash
ssh -i RSA.pem ubuntu@43.201.214.82
sed -i 's/^CHAT_LLM=.*/CHAT_LLM=llama_cpp/' /home/ubuntu/app/.env && sudo systemctl restart rag-api
# 원복: llama_cpp → gemini 로 동일하게. 다음 CI 배포 시 .env가 gemini로 재작성되므로 자동 원복되기도 함.
```

### 7.5 18문항 전수 검증 결과 (2026-07-19)

| 경로 | 결과 | 문항당 소요 | 비고 |
|---|---|---|---|
| 로컬 EXAONE (GPU) | 18/18 | 8~29초 | 전체 ~5분 |
| 운영 EXAONE (t4g CPU) | 18/18 | 2.2~8.5분 | 전체 ~75분 — CPU 서빙 증빙용 |
| 운영 Gemini | 18/18 | 1~28초 | 기본 운영 경로, 폴백 체인 실동작 확인 |

### 7.6 로컬 개발 함정

- **루트 `.env`에 인라인 주석 금지** (`KEY=value  # 주석` 형태): Spring 게이트웨이가 `.env`를
  properties로 import(`application.yaml`의 `spring.config.import`)하므로 `#` 뒤까지 값에 포함된다.
  실제로 `NEON_DEV_DATABASE` 값 오염 → Neon `SASL authentication failed`로 게이트웨이 기동 실패했었다.
  주석은 반드시 별도 줄에 쓸 것.
- 로컬 소셜 로그인은 게이트웨이(8080) 기동이 전제: `python run_all.py` 또는 `backend/gateway`에서 `gradlew bootRun`.
