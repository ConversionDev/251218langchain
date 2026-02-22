# 입사 지원 페이지 (Apply)

## 양식 참조

- **지원서 양식**: `app/data/KPMG_입사지원서_Template.docx`
- 프론트 지원 폼(`frontend/app/apply/page.tsx`)은 위 템플릿 구조를 반영합니다.
- 템플릿 내용을 확인하려면 프로젝트 루트에서 다음을 실행하세요 (python-docx 필요):
  ```bash
  python -m app.scripts.extract_apply_template
  ```

## 디자인

- 메인 페이지(`/`)와 **맥락 유지**: 동일한 배경 그라데이션(`from-sky-200/60 via-teal-100/80 to-emerald-200/60`), 화이트 카드·둥근 모서리·그림자.
- 상단 **「메인으로」** 뒤로가기 링크.
- 기본 정보는 2열 그리드, 모바일에서는 1열로 반응형 처리.

## 데이터

- 제출 시 `createEmployeeApi`로 전송하며, `Employee`·`Resume` 타입(`@/modules/shared/types`)을 따릅니다.
