# 샘플 PDF 만드는 방법

프로젝트에서 **샘플 PDF**가 필요할 때(이력서·문서 테스트, 데모 등) 사용할 수 있는 방법입니다.

---

## 현재 구조

- **이력서/신입 샘플**: `resume_sample_generator`가 **JSONL**만 생성합니다. (`app/data/resume/samples/new_hire_samples_*.jsonl`)
- **PDF 자동 생성 스크립트**: 아래 §2의 `scripts/generate_sample_resume_pdf.py`를 사용하면 샘플 이력서 PDF를 생성할 수 있습니다.
- **성과 리포트 PDF**: 프론트엔드 성과 리포트 페이지에서 **인쇄 → PDF로 저장** (`window.print()`)으로 저장합니다.

---

## 1. HTML 이력서 → PDF (수동)

이력서를 HTML로 두고, 브라우저에서 PDF로 저장하는 방법입니다.

1. `이력서-깔끔양식.html`(프로젝트 루트 또는 데스크톱)을 브라우저에서 엽니다.
2. **Ctrl+P** (또는 Cmd+P) → 대상에서 **PDF로 저장** 선택 후 저장.

테스트용으로 한두 개만 필요할 때 적합합니다.

---

## 2. 스크립트로 샘플 이력서 PDF 생성 (PyMuPDF)

프로젝트에 이미 포함된 **PyMuPDF**로, 텍스트 기반 샘플 이력서 PDF를 생성할 수 있습니다.

### 실행

```bash
# app 가상환경 활성화 후
cd app
python scripts/generate_sample_resume_pdf.py

# 또는 프로젝트 루트에서
python app/scripts/generate_sample_resume_pdf.py --output app/data/resume/samples/sample_resume.pdf
```

- **출력 경로**: `app/data/resume/samples/sample_resume.pdf` (기본).  
- **옵션**: `--output`으로 경로 지정 가능.

### 동작

- 한 페이지 분량의 샘플 이력서 텍스트(이름, 학력, 경력 등)를 PDF로 출력합니다.
- 이력서 업로드·파싱 테스트용으로 사용할 수 있습니다.

스크립트 위치: `app/scripts/generate_sample_resume_pdf.py`.

---

## 3. 외부에서 준비한 PDF 사용

- 테스트·데모용 PDF를 외부에서 만들어 `app/data/resume/` 등 적절한 폴더에 넣고 사용할 수 있습니다.
- 백엔드 이력서 분석은 **PDF/TXT/Word/HWP** 업로드를 지원하므로, 해당 형식의 샘플 파일을 그대로 업로드해 동작을 확인하면 됩니다.

---

## 요약

| 목적 | 방법 |
|------|------|
| 이력서 1~2장 테스트 | HTML 열기 → 인쇄 → PDF로 저장 (§1) |
| 반복 생성·자동화 | `python app/scripts/generate_sample_resume_pdf.py` (§2) |
| 성과 리포트 PDF | 성과 리포트 페이지 → PDF 저장 버튼(인쇄) |
| 기타 형식 | 외부에서 PDF 준비 후 `app/data/` 등에 저장 (§3) |
