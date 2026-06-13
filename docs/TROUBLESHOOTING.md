# 트러블슈팅 — 핵심 난제와 해결

이력서·면접에서 바로 설명할 수 있도록, **임팩트가 컸던 난제만** 큐레이션했습니다. 각 항목은 **문제 → 원인 → 해결 → 배운 점** 형식이며, **중요도(기술 깊이·프로덕션 영향·이력서 어필) 순**으로 정렬했습니다.

---

## 1. GPU 학습 모델을 CPU 전용 EC2에 서빙 (EXAONE 7.8B → GGUF)

**문제**
로컬 GPU에서만 동작하던 EXAONE 7.8B 파인튜닝 모델을 **GPU 없는 EC2 m7i-flex.large(2 vCPU, 8GB RAM, 월 ~$70)**에 배포하면서 변환·메모리 문제가 연쇄 발생.

**원인**

- `llama.cpp/convert_hf_to_gguf.py`가 bitsandbytes NF4 양자화 메타 텐서(`absmax`, `quant_map`)를 처리 못 함. `torch.dtype` 객체가 `config.json` 직렬화 시 JSON 비호환.
- `llama-quantize`로 Q4_K_M 변환 후 토크나이저 merges 손상 → `cannot find tokenizer merges in model file`.
- 8GB RAM에서 `n_ctx=8192` 로드 시 OOM.
- S3에 모델을 두어도 추론 시 RAM에 반드시 로드되므로 메모리 부담은 동일(OOM 해결 불가).

**해결**

- `export_exaone_merged_hf_for_gguf.py`: `Linear4bit` 레이어를 fp16으로 직접 역양자화, `torch.dtype`→문자열, `quantization_config`/`auto_map`/`rope_scaling` 제거.
- 2단계 변환: `convert_hf_to_gguf.py --outtype f16` → `llama-quantize ... Q4_K_M`.
- **자작 패치 스크립트** `patch_gguf_from_f16.py`: f16 GGUF의 KV 메타데이터(토크나이저 포함) + Q4_K_M GGUF의 텐서를 결합해 최종 배포본(4.5GB) 생성.
- EBS 6.8GB→30GB, swap 4GB 추가, `n_ctx` 8192→2048 단계 축소.

**배운 점**
양자화 포맷 간 변환은 텐서와 메타데이터를 분리해 다뤄야 하며, 표준 도구가 막히면 포맷 내부 구조(GGUF KV)를 직접 이해해 패치할 수 있어야 한다. 객체 스토리지는 "저장소"일 뿐이고, OOM을 피하려면 로드하지 않거나 외부 API로 분리해야 한다.

---

## 2. CPU 환경 프롬프트 토큰 폭주 (3839 → ~300, -92%)

**문제**
"강경구의 직급 알려줘" 같은 단일 직원 질의에도 `list_employees` 툴이 전 직원 리스트를 주입 → 3839 토큰 → 컨텍스트 윈도우 초과 + 영어 응답 혼입. CPU 추론이라 토큰 수가 곧 응답 지연.

**원인**
도구 강제 호출 가드 부재 + RAG 문서 무조건 주입 + 시스템 프롬프트의 언어 미지정.

**해결**

- `_build_forced_tool_calls`에 **단일 직원 속성 질의 가드** — `list_employees`·`get_hr_summary` 강제 호출 스킵.
- `rag_node`에서 단일 직원 질의 감지 시 **RAG 문서 주입 생략**(`get_employee_info`만).
- 시스템 프롬프트에 **한국어 강제 + 간결성 지시** 추가.

**결과/배운 점**
**3839 → ~300 토큰(-92%)**, 한국어 정답률 상승. CPU 서빙에서는 토큰 다이어트가 곧 UX(속도)다.

---

## 3. 채팅 1턴 GPU OOM — LLM 2회 호출을 1회로 최적화

**문제**
채팅 한 턴에서 `llm_with_tools.invoke()`(도구 수집) → 도구 실행 → `stream()`(답변)으로 **LLM을 2회 호출**, GPU 16GB에서 긴 컨텍스트 시 VRAM 부족(OOM).

**원인**
도구 호출 결정과 최종 답변 생성을 각각 LLM 호출로 처리하는 구조.

**해결**

- 첫 턴의 LLM invoke를 제거하고 `_build_forced_tool_calls(user_query)`로 **키워드 기반 도구 결정**만 수행.
- 도구 필요 시 `AIMessage(tool_calls=forced_calls)` 반환 → tool_node 실행 → **두 번째 model_node에서만 LLM stream 1회**.
- 도구 불필요(OOS) 질문은 첫 턴에서 바로 stream.

**결과/배운 점**
LLM 호출 1회로 **GPU 부하 절반 감소**, 답변 품질 유지. 모든 단계에 LLM을 쓰기보다, 결정 가능한 부분은 규칙으로 처리하는 하이브리드가 비용·안정성에 유리.

---

## 4. CPU tool-calling 한계 → 환경별 LLM 스팸 에스컬레이션

**문제**
스팸 분류에서 애매한 케이스를 LLM 에이전트로 재판정하려 했으나, CPU 배포 모델은 tool-calling을 안정적으로 지원하지 못함("tool-calling 미지원" 로그).

**원인**
tool-loop 방식이 CPU 추론·소형 런타임에서 비현실적.

**해결**

- 방식을 **tool-loop → "증거 수집 + LLM 판정"**으로 전환(tool-calling 미사용).
- 환경별 judge LLM 분리: **로컬은 EXAONE(GPU), 배포는 Gemini**(raw SDK, 신규 의존성 0).
- LLaMA 1차 분류 결과 + 규칙 + EXAONE 심층분석을 증거로 모아 judge가 최종 판정. 판정/실행 실패 시 기존 판정 유지(안전).

**배운 점**
런타임 제약(CPU)에 맞춰 에이전트 패턴 자체를 바꾸면, 미지원 기능 의존을 제거하면서 동일 목적을 달성할 수 있다.

---

## 5. 헥사고날 마이그레이션 완주 — domain의 인프라 의존 제거

**문제**
"절반 상태"의 계층 구조 — `domain/`이 DB(ORM)·레포지토리·오케스트레이터를 직접 참조해 도메인 순수성이 깨져 있었음.

**원인**
초기 구조가 `domain.hub.*`에 ORM·repository·LLM을 혼재시킴.

**해결**

- ORM 모델 7개 → `infrastructure/persistence/models/`(`*_orm.py`), 레포지토리 → `infrastructure/persistence/repositories/` 이동.
- 라우터 → `api/rest/`, 유스케이스 → `application/`(employee·chat·mail·address_book·disclosure·shared).
- **PR 머지 조건**: 각 라우터에서 `domain.hub.repositories/orchestrators.*` import 0개(순수 Pydantic·Enum만 예외).

**배운 점**
대규모 구조 마이그레이션은 "import 0개" 같은 **검증 가능한 완료 기준**을 PR 단위로 잡아야 절반 상태로 멈추지 않는다. (상세 이력: [archive/hexagonal-architecture-milestone.md](archive/hexagonal-architecture-milestone.md))

---

## 6. MCP 계층 순환 의존 해소

**문제**
MCP 허브·스포크 사이 `infrastructure ↔ domain` 양방향 import로 순환 의존 발생.

**원인**
스포크가 인프라를 직접 import하고, 인프라도 도메인 스포크를 참조.

**해결**

- 의존 방향을 **인바운드(`api/mcp` 허브)** / **아웃바운드(`infrastructure/mcp/http_client`)**로 분리.
- 스포크는 허브의 LLM·DB를 HTTP 클라이언트로만 호출. **스포크끼리 직접 통신 금지** 규칙 확립.

**배운 점**
순환 의존은 "호출 방향"을 단방향으로 강제하는 어댑터(인바운드/아웃바운드 분리)로 끊는다.

---

## 7. 첫 RAG/채팅 요청 시 OOM → Lazy 로딩 전략

**문제**
스타트업은 정상인데, **첫 번째 채팅·RAG·임베딩 요청**에서 프로세스가 죽음. t3.small(2GB) 등 소형 인스턴스에서 재현.

**원인**

- `ensure_rag_initialized()` → BGE-M3(수백 MB~1GB) lazy 로드가 첫 RAG 요청 시 발생.
- ExaONE·LLaMA도 각각 첫 채팅·스팸 요청 시 추가 메모리 사용.
- 스타트업에 모든 모델을 한꺼번에 올리면 OOM.

**해결**

- lifespan에서 **DB 연결만 확인**하고 Embedding·FAISS·EXAONE·LLaMA는 **첫 요청 시 lazy 로드**.
- RAG 검색은 FAISS 인덱스를 로드하지 않고 **pgvector(HNSW)만** 사용.
- (선택) 소형 인스턴스에서는 `DISABLE_RAG_EMBEDDING=true`로 BGE 로드를 건너뛰고 도구 기반 답변만 제공.

**배운 점**
소형 인스턴스 운영은 "기동 시 전부 로드"가 아니라 **요청 시점 분산 로드 + 기능 토글**로 메모리 예산을 관리해야 한다.

---

## 8. CI/CD `.env` 파싱 깨짐 + `nohup` 환경변수 유실

**문제**
GitHub Actions 배포 후 EC2에서 FastAPI가 `LLM_PROVIDER`, `DATABASE_URL`을 읽지 못해 DB·LLM 경로가 깨짐.

**원인**

- `nohup` 재시작 시 셸 환경이 유지되지 않아 `.env` 로드가 누락됨.
- Neon `DATABASE_URL` 값에 `&` 문자가 포함되어 Bash `source` 시 **백그라운드 실행으로 해석**되어 파싱 깨짐.

**해결**

- `.github/workflows/deploy.yml`에서 `ssh heredoc` 내 `printf`로 `.env`를 **직접 생성**해 배포마다 동일 내용 보장.
- `DATABASE_URL` 등 특수문자 포함 값은 **반드시 따옴표로 감싸서** 기록 (`printf 'DATABASE_URL="%s"\n' "$DATABASE_URL_VALUE"`).
- `LLM_PROVIDER`, `EXAONE_GGUF_PATH`, `EXAONE_GGUF_N_CTX=2048` 등 배포 필수값을 명시.

**배운 점**
URL·비밀값은 "값이 맞다"만으로 부족하고, **셸 파싱 규칙까지 포함한 배포 파이프라인 설계**가 필요하다.

---

## 9. 스팸 판정 라우팅 버그 — 스팸 메일이 받은편지함으로 저장

**문제**
`POST /api/mail/receive`에서 LLaMA가 스팸으로 판단해도 최종적으로 **받은편지함(inbox)**에 저장됨.

**원인**
라우팅이 `policy`(ExaOne) 경로로 가면 ExaOne이 `deliver`를 반환해, LLaMA 스팸 판정이 **최종 `action`에서 덮어써짐**.

**해결**

- `SpamGatewayService.read()`에서 LLaMA 결과가 있으면 **`routing_strategy`를 항상 `"rule"`**로 고정.
- 최종 결정을 LLaMA 기준으로만 내리도록 하여 스팸 시 `folder=spam` 저장.
- 분류 실패(미로드·타임아웃) 시에는 수신을 막지 않고 기본 `folder=inbox`로 저장(장애 시 수신 차단 방지).

**배운 점**
멀티 모델 파이프라인에서는 **최종 결정권 우선순위**를 코드로 명시하지 않으면, 느린/고급 모델이 1차 분류 결과를 조용히 뒤집는다.

---

## 10. Nginx SSE 스트리밍 타임아웃

**문제**
CPU 추론이 60초를 넘기자 채팅 SSE 응답이 `upstream timed out`으로 끊김.

**원인**
기본 `proxy_read_timeout`(60s) 초과 + 프록시 버퍼링.

**해결**
`/api/agent/chat/stream` 전용 location 블록: `proxy_buffering off`, `proxy_http_version 1.1`, `Connection ''`, `proxy_read_timeout 600s`. 일반 `/api/**`는 120s로 상향.

**배운 점**
스트리밍 엔드포인트는 일반 API와 프록시 정책을 분리해야 한다.

---

## 11. SSL 인증서 만료로 전 서비스 "연결 오류"

**문제**
`api.kanggyeonggu.store` Let's Encrypt 인증서가 만료되어 브라우저가 모든 연결을 거부(`curl -k`만 200).

**원인**
새 EC2로 이전하면서 **certbot 자동 갱신(`certbot.timer`) 설정이 누락**됨.

**해결**
`sudo certbot renew`(필요 시 `--nginx`/`--standalone`) 후 `nginx reload`. 재발 방지로 `certbot.timer` 활성화(자동 갱신).

**배운 점**
인스턴스 이전 시 인증서·크론/타이머 같은 **호스트 종속 자동화**가 함께 이전되지 않는다 — 이전 체크리스트에 포함해야 한다.

---

## 12. EC2 IP·DNS·CI Secret 동기화 혼선

**문제**
EC2 재기동/이전으로 퍼블릭 IP가 바뀌자 SSH·배포·DNS가 어긋나고, Spring Gateway가 옛 Upstash Redis 호스트로 붙어 `NXDOMAIN` 발생.

**원인**
가비아 DNS A 레코드, GitHub Secret(EC2 호스트·Redis), 로컬 `.env`가 각각 다른 값을 가리킴.

**해결**

- DNS·GitHub Secret·`.env`를 활성 리소스 기준으로 동기화. SSH는 올바른 사용자(`ubuntu`) + `-i RSA.pem`.
- Redis 환경변수를 **5개 → 단일 `UPSTASH_REDIS_URL`**로 통합(`rediss://default:TOKEN@HOST:6379`). Gateway·FastAPI 공통, REST URL·TOKEN은 코드에서 자동 추출.

**배운 점**
설정의 단일 출처(single source of truth)를 만들면 다중 환경 동기화 실수를 구조적으로 줄일 수 있다.

---

## 부록 — 데이터·정책 정리 이력 (요약)

핵심 난제는 아니지만 프로젝트 일관성을 위해 정리한 결정들:

- **채팅 모델 정책**: 채팅은 **EXAONE만**, 스팸은 **LLaMA만**. `classify_with_llama` 등 혼용 코드 제거.
- **EXAONE 학습 단일화**: 여러 진입점(`policy_solver` 등) 제거, 런타임은 역량 SFT(competency_adapters)만.
- **스팸 SFT 데이터 단일화**: 레거시 `email` 폴더 데이터 폐기, EXAONE 합성 데이터만 사용.
- **수신 메일 → 성과/역량 자동 반영**: inbox 저장 후 BackgroundTasks로 비동기 분류 → performance_records + 역량 태깅.
