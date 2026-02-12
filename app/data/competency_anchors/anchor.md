# competency_anchors 데이터 정리 가이드

이 폴더의 원본 파일을 기준으로 **어떻게 정리하면 좋을지** 역할·스키마·파이프라인 관점에서 정리한 문서입니다.

---

## 1. 데이터 소스 역할 정리

| 소스 | 유형 | 주는 것 | 정리 시 포인트 |
|------|------|---------|----------------|
| **Abilities.xlsx** | O*NET | 직무별 능력(Element Name) + Importance/Level 점수 | 한 행 = 한 능력 항목. `content`=Element Name 또는 설명, `level`=Level 스케일(구간 매핑), `category`="능력". |
| **Task Statements.xlsx** | O*NET | 직무별 과제 문장(Task) | 한 행 = **한 문장(행동 지표)**. `content`=Task, `category`="과제", level은 직무·Task Type으로 유도 또는 기본값. |
| **Technology Skills.xlsx** | O*NET | 직무별 기술/소프트웨어 예시 | 한 행 = 기술 한 항목. `content`=Example 또는 Commodity Title, `category`="기술". |
| **Work Styles.xlsx** | O*NET | 직무별 업무 스타일(Element Name) + 순위/영향도 | 한 행 = 스타일 항목. `content`=Element Name, `category`="태도" 또는 "업무스타일", level=DR/WI 구간 매핑. |
| **대인관계능력_01_교수자용.pdf** 등 4종 | NCS | 수행준거 문장 + 능력단위 구조 | Structural 추출 → ExaOne 구조화 → **수행준거 문장 단위**로 분리. `content`=문장, `category`=지식/기술/태도, `level`=1~8, `section_title`=능력단위명. |

**정리 원칙**:  
- **O*NET 4종** → 행 단위로 읽어 `content`, `category`, `level`(필요 시 스케일 매핑) 채우고, 출처 구분용 `source`(파일명/유형) 추가.  
- **NCS PDF 4종** → 추출 텍스트를 ExaOne으로 수행준거 문장·category·level·section_title 구조화 후 동일 스키마로 적재.

---

## 2. 통합 스키마 제안 (DB·JSONL 공통)

역량 anchor 한 건을 아래 필드로 통일하면, RAG·채점·방사형 차트 모두 같은 테이블을 볼 수 있습니다.

| 필드 | 설명 | O*NET | NCS PDF |
|------|------|--------|---------|
| **content** | 한 문장/한 항목 텍스트 (행동 지표 또는 능력/기술 설명) | Task, Element Name, Example 등 | 수행준거 문장 |
| **category** | 역량 유형 | "과제" / "능력" / "기술" / "업무스타일" 또는 지식·기술·태도 | 지식 / 기술 / 태도 |
| **level** | 숙련도·중요도 수준 (1~8 또는 1~5로 통일) | Level/Importance/DR 구간 매핑 | 1~8 |
| **section_title** | 소속 단위(능력단위, 직무명 등) | Title(직무명) 또는 Element Name | 능력단위명 |
| **source** | 출처 식별자 | "Abilities", "Task Statements", "대인관계능력_01" 등 | PDF 파일명 stem |
| **source_type** | O*NET vs NCS 구분 | "ONET" | "NCS" |
| **metadata** | 원본 부가 정보 (JSON) | O*NET-SOC Code, Task ID, Scale 값 등 | 페이지, 발췌 위치 등 |

레벨은 **1~8**로 통일해 두고, 방사형 차트에서 5단계로 묶어서 보여줄지 여부만 프론트/리포트 단에서 결정하면 됩니다.

---

## 3. 폴더/파일 구조 (현재 유지 + 선택 사항)

**현재 구조를 유지해도 됩니다.**  
`data/competency_anchors/` 아래에 xlsx 4종 + PDF 4종이 같이 있는 형태로 두고, 코드에서 `source`로 구분하면 됩니다.

선택적으로만:

- **원본만 두고 싶다면**: `data/competency_anchors/` 에는 원본만 두고, **적재 결과(JSONL/DB)** 는 `data/competency_anchors/processed/` 또는 DB 전용이므로 폴더를 두지 않아도 됨.  
- **출처별로 나누고 싶다면**: `data/competency_anchors/onet/` (xlsx 4종), `data/competency_anchors/ncs/` (PDF 4종) 처럼 서브폴더를 둘 수 있음.  
  → 파이프라인에서 `onet/` 는 xlsx 읽기, `ncs/` 는 PDF Structural 추출로 일괄 처리하면 됨.

**권장**: 당장은 **현재처럼 한 폴더에 모두 두고**, `source` / `source_type` 으로 구분하는 쪽이 단순합니다. 필요해지면 나중에 onet/ncs 서브폴더로 옮겨도 됩니다.

---

## 4. 정리 순서 (파이프라인 관점)

1. **스키마 확정**  
   - 위 통합 스키마로 `competency_anchors` 테이블(또는 동일 목적 스키마) 설계.  
   - pgvector 컬럼(embedding) 추가 시 BGE-M3 차원과 호환.

2. **O*NET 4종**  
   - **엑셀 추출**: `domain.shared.strategies.ExcelStrategyFactory` 와 `domain.shared.strategy_imples.OnetXlsxStrategy` 사용.  
     `ExcelStrategyFactory.get_strategy(xlsx_path).extract(xlsx_path)` 로 통합 스키마 `list[dict]` 획득.  
   - Abilities / Task Statements / Technology Skills / Work Styles 를 **행 단위**로 읽어  
     `content`, `category`, `level`, `section_title`, `source`, `source_type`, `metadata` 채움.  
   - 필요 시 Llama 3.2B로 영문→한글 번역/포맷 후 `content` 에 반영.

3. **NCS PDF 4종**  
   - Structural(pdfplumber)로 추출 → ExaOne 7.8B 프롬프트로 수행준거 문장 분리 + category/level/section_title 매핑 →  
     동일 스키마로 행 생성. `source`=PDF stem, `source_type`="NCS".

4. **적재**  
   - 위에서 만든 행들을 BGE-M3로 임베딩 후 `competency_anchors` 테이블에 INSERT.  
   - 검색 시 `category`, `level` 필터 사용.

5. **조회·채점·리포트**  
   - 사용자 문장 → (선택) Llama 쿼리 확장 → BGE-M3 검색 → ExaOne 채점/리포트 → 방사형 차트.

---

## 5. 요약

- **정리 기준**: “한 문장(행동 지표) 단위 + category + level + 출처” 로 통일.  
- **O*NET**: 4개 xlsx를 행 단위로 위 스키마에 매핑.  
- **NCS**: 4개 PDF는 Structural 추출 후 ExaOne으로 구조화해 같은 스키마로 적재.  
- **폴더**: 지금처럼 한 디렉터리에 둬도 되고, 나중에 onet/ncs 로 나눠도 됨.  
- **레벨**: 1~8로 저장하고, 필요 시 프론트/리포트에서 5단계로만 표시.

이렇게 정리하면 disclosures와 독립적으로 competency_anchors 파이프라인을 설계·구현할 수 있습니다.

---

## 6. 엑셀 추출 구현 위치 (domain/shared)

O*NET xlsx 추출은 **PDF 추출과 같은 계층**에서 전략 패턴으로 제공됩니다.

- **인터페이스·팩토리**: `app/domain/shared/strategies/excel_strategy.py`  
  - `ExcelExtractStrategy` (추상): `extract(xlsx_path) -> list[dict]`  
  - `ExcelStrategyFactory.get_strategy(path)` → 구현체 반환  
- **구현체**: `app/domain/shared/strategy_imples/onet_xlsx.py`  
  - `OnetXlsxStrategy`: Abilities / Task Statements / Technology Skills / Work Styles 4종을 파일명으로 구분해 통합 스키마로 변환.  
- **의존성**: `openpyxl>=3.1.0` (requirements.txt). pandas `read_excel(engine="openpyxl")` 사용.

---

## 7. 최종 competency_anchors 테이블 정의 (전략 통합 후)

O*NET(Excel 전략) + NCS(PDF Structural + ExaOne 구조화)를 한 테이블에 적재할 때의 **최종 스키마**입니다.  
서버 기동 시 `auto_migrate=True` 이고 revision 006이 적용되면 이 구조로 생성됩니다.

### 7.1 컬럼

| 컬럼 | 타입 | nullable | 설명 |
|------|------|----------|------|
| **id** | BIGSERIAL (PK) | N | 자동 증가 PK. |
| **content** | TEXT | N | 한 문장/한 항목 텍스트 (행동 지표 또는 능력·기술 설명). |
| **embedding_content** | TEXT | Y | 임베딩용 문자열. `[category] [section_title]: content` 형태 권장. |
| **embedding** | vector(1024) | Y | BGE-m3 벡터. HNSW 인덱스 사용. |
| **category** | TEXT | Y | 역량 유형: 과제/능력/기술/업무스타일 또는 지식/기술/태도. btree 필터용. |
| **level** | INTEGER | Y | 숙련도·중요도 1~8. btree 필터용. |
| **section_title** | TEXT | Y | 능력단위명 또는 직무명. |
| **source** | TEXT | Y | 출처 식별자 (파일명·stem). |
| **source_type** | TEXT | Y | "ONET" 또는 "NCS". |
| **metadata** | JSONB | Y | O*NET-SOC Code, Task ID, 페이지 등 부가 정보. |
| **unique_id** | TEXT | Y | 재적재/업서트용 고유 키 (선택). |
| **created_at** | TIMESTAMP | Y | 생성 시각 (default now()). |

### 7.2 인덱스

| 종류 | 대상 | 이름 | 용도 |
|------|------|------|------|
| **HNSW** | embedding | idx_competency_anchors_embedding_hnsw | BGE-m3 코사인 유사도 검색 (vector_cosine_ops, m=24, ef_construction=128). |
| **btree** | category | idx_competency_anchors_category | WHERE category = … 필터. |
| **btree** | level | idx_competency_anchors_level | WHERE level = … 필터. |
| **btree** | (category, level) | idx_competency_anchors_category_level | category + level 복합 필터. |
| **unique** | unique_id | idx_competency_anchors_unique_id | unique_id IS NOT NULL 구간만 UNIQUE, 중복 적재 방지. |

### 7.3 요약

- **통합 소스**: O*NET 4종 xlsx(OnetXlsxStrategy) + NCS 4종 PDF(Structural → ExaOne 구조화) → 동일 테이블.
- **검색**: BGE-m3로 쿼리 임베딩 후 HNSW로 유사 anchor 검색, 필요 시 category/level로 btree 필터.
- **적재**: Excel 전략·NCS 파이프라인에서 만든 통합 스키마 행을 embedding 채운 뒤 INSERT. unique_id로 재적재 시 기존 행 교체 가능.
