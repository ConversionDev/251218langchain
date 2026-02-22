# 문서·역량 추출 및 데이터

## PDF 추출 전략 (전략 매트릭스)

| 전략 | 라이브러리 | 용도 | 비고 |
|------|------------|------|------|
| **FastExtract** | PyMuPDF | disclosures (IFRS, ISO, OECD) | 속도·메모리 효율 우선, 대량 공시 지침서 적재용 |
| **Structural** | pdfplumber | competency_anchors (NCS) | 표(Table) 구조 보존, 수행준거 행/열 추출 |
| **Intelligent** | LlamaParse | ESG·지속가능경영보고서 등 | 미구현 시 FastExtract fallback |

**라우팅**: 파일명/경로 **키워드**로 선택.  
- NCS·역량·수행준거 → Structural  
- IFRS·ISO·OECD·공시 → FastExtract  
- ESG·지속가능·sustainability → Intelligent  

패턴으로 결정 안 되면 ExaOne 샘플 분석으로 전략 번호(0/1/2) 할당·캐시 권장.

**구현 위치**: `domain/shared/strategies/pdf_strategy.py` (StrategyFactory, PAGE_SEP), `pdf_enums.py` (PdfStrategyType). 구현체: `strategy_imples/py_mu_pdf.py`, `pdf_plumber.py`. PyMuPDF 호출은 `PyMuPdfStrategy.extract()` 한 곳만.

## competency_anchors 통합 스키마

O*NET 4종 xlsx + NCS PDF 4종을 **동일 스키마**로 적재. RAG·채점·방사형 차트가 같은 테이블을 참조.

| 필드 | 설명 |
|------|------|
| content | 한 문장/한 항목 텍스트 (행동 지표 또는 능력·기술 설명) |
| category | 역량 유형 (과제/능력/기술/업무스타일 또는 지식·기술·태도) |
| level | 숙련도·중요도 (1~8 통일, 필요 시 프론트에서 5단계로 표시) |
| section_title | 소속 단위 (능력단위명, 직무명 등) |
| source | 출처 식별 (파일명·유형) |
| source_type | "ONET" / "NCS" |
| metadata | 원본 부가 정보 (JSON) |

- **O*NET**: `ExcelStrategyFactory.get_strategy(xlsx_path).extract(xlsx_path)` → `strategies/excel_strategy.py`, 구현체 `strategy_imples/onet_xlsx.py`. Abilities, Task Statements, Technology Skills, Work Styles 4종을 파일명으로 구분. 의존성: openpyxl, pandas.
- **NCS**: PDF는 Structural(pdfplumber) 추출 → ExaOne으로 수행준거 문장·category·level·section_title 구조화 후 동일 스키마로 적재. `source`=PDF stem, `source_type`="NCS".
- **폴더**: `data/competency_anchors/`에 xlsx 4종 + PDF 4종 유지해도 되고, `source`/`source_type`으로 구분. 필요 시 나중에 onet/ncs 서브폴더로 분리 가능.
