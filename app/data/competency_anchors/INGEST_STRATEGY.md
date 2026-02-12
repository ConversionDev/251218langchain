# competency_anchors 적재·조회 전략

O*NET xlsx 4종 + NCS PDF 4종을 `competency_anchors` 테이블에 넣고 검색할 때의 전략 정리.

---

## 1. Repository — Upsert + Optional 필터

### ON CONFLICT (unique_id) DO UPDATE

- `unique_id`가 NOT NULL인 행만 UNIQUE 인덱스 대상이므로, `ON CONFLICT (unique_id) WHERE unique_id IS NOT NULL` 이나, PostgreSQL이 부분 유니크 인덱스를 쓰는 경우 **ON CONFLICT (unique_id) DO UPDATE** 로 충돌 행만 갱신하면 됨.
- 삭제 후 일괄 INSERT보다 **재적재·증분 적재가 단순**하고, 같은 소스를 여러 번 돌려도 안전함.

### category / level Optional

- **필터 없음** → `WHERE embedding IS NOT NULL` 만 두고 벡터 검색.
- **category만 / level만 / 둘 다** → btree 인덱스 조건 추가해서 조합.
- 쿼리에서 `category is None and level is None` 이면 필터 절을 붙이지 않도록 하면 **"전체 검색 vs 인덱스 활용"** 이 자연스럽게 나뉨.

---

## 2. O*NET — embedding_content + Batch

### 풍부한 embedding_content

- `[category] [section_title]: content` 처럼 **역할·맥락**을 앞에 두면 BGE-m3가 "무슨 종류의 문장인지"까지 보고 검색해서, 단순 `content`만 넣을 때보다 매칭 품질이 좋아짐.
- 예: `[기술] 데이터 분석: Using Python for...` — "기술" + 직무/문맥이 같이 임베딩되므로, 나중에 category 필터와도 잘 맞음.

### Batch INSERT 100~500

- 행 단위 INSERT보다 훨씬 유리함.
- **INSERT**는 100~500행씩, **fill_embeddings**는 32 등 작은 배치로 하면 메모리·속도 균형 좋음.

---

## 3. 5 & 6 — 점진적 고도화

### 1~4로 영문 O*NET만 먼저

- 테이블·인덱스·저장·검색·embedding_content 품질까지 한 번에 검증 가능.
- 문제 나오면 원인 추적이 쉬움.

### 그 다음 6(번역) → 5(NCS)

- **6**: O*NET 행에 Llama 3.2B 번역 적용해 `content`/`embedding_content`를 한글으로 보강 → 검색·채점을 한글 기준으로 확장.
- **5**: NCS PDF는 ExaOne 7.8B로 "수행준거 문장 + category/level/section_title" 뽑은 뒤, 같은 테이블·repository로 적재.

**순서**: 영문 O*NET 검증 → 번역(6) → NCS(5).

---

## 4. unique_id 설계 참고

- **O*NET**: `source + (Task ID / Element ID / 행 식별자)` 같은 고정 규칙으로 unique_id 생성 → 같은 xlsx 재실행 시 upsert로 갱신.
- **NCS**: ExaOne가 준 문장별로 `source + 페이지 + 순서` 또는 해시로 unique_id 부여 → 재적재 시 중복·깨짐 방지.
