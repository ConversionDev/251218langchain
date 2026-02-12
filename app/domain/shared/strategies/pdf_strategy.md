# Success DNA: PDF Extraction Strategy Guide

이 문서는 Success DNA 솔루션이 글로벌 공시 표준(IFRS, ISO) 및 역량 데이터(NCS, O*NET)를 처리하기 위해 채택한 **다중 PDF 파싱 전략**을 정의합니다.

---

## 1. 설계 원칙 (Design Principles)

- **목적에 따른 최적화**: 지식 검색(RAG)용 문서와 평가/채점(Benchmark)용 문서의 특성에 맞춰 도구를 분리합니다.
- **추론 기반 라우팅**: 별도의 분류 모델 없이, **파일명/경로 패턴 매칭** 및 ExaOne/Llama의 추론을 통해 전략을 동적으로 선택합니다.
- **데이터 무결성**: 표(Table) 구조가 중요한 역량 데이터는 구조 보존형 라이브러리를 우선 사용합니다.

---

## 2. 전략 매트릭스 (Strategy Matrix)

| 전략명 (Strategy) | 추천 라이브러리 | 주 사용 용도 (Target) | 핵심 장점 |
|-------------------|-----------------|------------------------|-----------|
| **FastExtract**   | PyMuPDF         | disclosures (IFRS, ISO, OECD) | 압도적 속도. 대량의 공시 지침서를 빠르게 텍스트화하여 벡터 DB 적재에 최적화. |
| **Structural**    | pdfplumber      | competency_anchors (NCS)      | 표(Table) 구조 보존. 행/열 기반의 수행준거 데이터를 정밀 추출하여 채점 엔진 구축. |
| **Intelligent**   | LlamaParse      | ESG/지속가능경영보고서 등     | 마크다운(Markdown) 변환. 복잡한 레이아웃을 LLM이 가장 잘 이해하는 포맷으로 정제. |

---

## 3. 데이터 파이프라인 흐름 (Data Flow)

### Step 1: 문서 식별 (Identification)

- **Primary**: 파일명/경로 **키워드 검사**
  - 예: 경로 또는 파일명에 `NCS`, `역량`, `수행준거` 등 포함 → **Structural**
  - 예: `IFRS`, `ISO`, `OECD`, `공시` 등 포함 → **FastExtract**
  - 예: `ESG`, `지속가능`, `sustainability` 등 포함 → **Intelligent**
- **Secondary**: 패턴으로 결정되지 않을 경우, **ExaOne**을 활용한 샘플 텍스트 분석 후 **전략 번호(0=FastExtract, 1=Structural, 2=Intelligent)** 할당.  
  할당 결과는 메타데이터 또는 캐시(파일/DB)에 저장하여 동일 문서 재처리 시 재사용 권장.

### Step 2: 전략 실행 (Execution)

- **StrategyFactory**를 통해 선택된 구현체(`py_mu_pdf.py`, `pdf_plumber.py` 등) 호출.
- 추출된 텍스트는 **BGE-m3** 임베딩 모델을 거쳐 벡터화 진행.

### Step 3: 목적지 적재 (Sink)

| 전략        | 적재 대상 |
|-------------|-----------|
| FastExtract | **disclosures** 테이블 (RAG 챗봇용) |
| Structural  | **(예정) competency_anchors** 테이블 또는 동등 스키마 (인사 평가/시각화용) |
| Intelligent | 용도에 따라 disclosures 또는 별도 컬렉션 |

---

## 4. 라이브러리 선정 근거 (Rationale)

- **PyMuPDF**: 텍스트 추출 속도가 가장 빠르며 메모리 효율이 높음.
- **pdfplumber**: PDF 내 선(Line)과 사각형(Rect)을 인식하여 표 경계를 정확히 파악함.
- **LlamaParse**: 이미지, 다단 구성 등 비정형 데이터를 LLM 친화적인 텍스트로 재구성하는 성능 탁월.

---

## 5. PyMuPDF(pymupdf) 사용 위치 이전 전략

- **의존성**: `requirements.txt`에 `pymupdf==1.25.1` 유지. PDF 섹션 주석에 전략 패턴(FastExtract/Structural) 명시.
- **실제 사용처**: `fitz`(PyMuPDF) 호출은 **한 곳만** — `domain/shared/strategy_imples/py_mu_pdf.py`의 `PyMuPdfStrategy.extract()`.
- **기존 호출부 이전 완료**:
  - `data/disclosure/pdf_extract.py`: `extract_pdf_to_txt()`가 `StrategyFactory.get_strategy(pdf_path).extract(pdf_path)` 사용. 경로에 IFRS/ISO/OECD 등 포함 시 FastExtract → PyMuPDF 자동 선택.
  - `data/disclosure/pdf_verify.py`: `verify_one()`에서 PDF 텍스트를 동일하게 전략으로 추출해 TXT와 비교.
- **추가 전략 사용**: NCS/역량 PDF는 경로에 키워드 포함 시 Structural(pdfplumber) 자동 선택. LlamaParse(Intelligent)는 구현 전까지 FastExtract로 fallback.

---

## 6. 작업 정리 — `strategies` / `strategy_imples`

이 문서와 동일한 설계 기준으로, **domain/shared** 아래 두 디렉터리에서 한 작업 요약.

### `domain/shared/strategies/`

| 항목 | 내용 |
|------|------|
| **pdf_strategy.md** | PDF 추출 전략 가이드(설계 원칙, 전략 매트릭스, 데이터 흐름, 라이브러리 근거, PyMuPDF 이전 전략). |
| **pdf_enums.py** | `PdfStrategyType` IntEnum 정의. FastExtract=0, Structural=1, Intelligent=2. Secondary 라우팅·캐시 시 전략 번호로 사용. |
| **pdf_strategy.py** | **추상 전략**: `PDFExtractStrategy` (메서드 `extract(pdf_path) -> str`). **팩토리**: `StrategyFactory.get_strategy(path)`(경로 키워드로 전략 선택), `get_strategy_by_type(type)`. 상수 `PAGE_SEP` (disclosure 파이프라인 호환). GoF 전략 패턴 적용. |
| **excel_enums.py** | `ExcelSourceType` Enum. O*NET 4종(Abilities, Task Statements, Technology Skills, Work Styles) 식별용. |
| **excel_strategy.py** | **추상 전략**: `ExcelExtractStrategy` (메서드 `extract(xlsx_path) -> list[dict]`. 통합 스키마 `ANCHOR_KEYS`). **팩토리**: `ExcelStrategyFactory.get_strategy(path)`, `source_type_from_path(path)`. competency_anchors xlsx 추출용. |
| **__init__.py** | PDF·Excel 전략·팩토리·enum export. |

### `domain/shared/strategy_imples/`

| 항목 | 내용 |
|------|------|
| **py_mu_pdf.py** | **FastExtract** 구현체 `PyMuPdfStrategy`. PyMuPDF(fitz)로 페이지별 텍스트 추출 후 `PAGE_SEP`로 연결. disclosures 대량 추출용. |
| **pdf_plumber.py** | **Structural** 구현체 `PdfPlumberStrategy`. pdfplumber로 페이지·표 추출, 표는 행 단위로 보존 후 `PAGE_SEP`로 연결. competency_anchors(NCS)용. |
| **onet_xlsx.py** | **Excel** 구현체 `OnetXlsxStrategy`. O*NET xlsx 4종을 파일명으로 구분해 통합 스키마(content, category, level, section_title, source, source_type, metadata) 리스트로 반환. 의존성: pandas, openpyxl. |
| **__init__.py** | `PyMuPdfStrategy`, `PdfPlumberStrategy`, `OnetXlsxStrategy` export. |

**Intelligent(LlamaParse)** 는 미구현. PDF 팩토리에서는 FastExtract로 fallback.
