# 스팸 SFT 데이터 (LLaMA 학습용)

ExaOne 합성 데이터와 실제 레이블 데이터를 LLaMA 스팸 분류 학습에 사용합니다.

## 스키마 (JSONL 한 줄)

```json
{
  "input": {
    "subject": "제목",
    "sender": "발신자 표시명 또는 이메일",
    "body": "본문 (선택, 있으면 학습·추론 모두 사용)",
    "attachments": [],
    "received_at": ""
  },
  "output": {
    "action": "BLOCK"
  },
  "category": "phishing"
}
```

- **action**: `BLOCK` = 스팸, `ALLOW` = 정상(햄)
- **category** (선택): 다양성 추적용. 스팸 유형 예: `phishing`, `lottery`, `marketing`, `fake_alert`, `adult_gambling`, `other`. 햄: `work`, `personal`, `newsletter` 등

## 파일 규칙

| 파일 | 설명 |
|------|------|
| `exaone_synthetic.jsonl` | ExaOne으로 생성한 합성 스팸/햄 (파이프라인으로 생성) |
| `train.jsonl` | 학습용 (기존 분할) |
| `val.jsonl` | 검증용 (기존 분할) |
| `train_full.jsonl` | **전체 활용 시**: `train` + `exaone_synthetic` 병합·셔플 결과 (스크립트로 생성) |
| `real_labeled.jsonl` | 실제 수신 메일 중 수동 레이블한 데이터 (추가 시 병합) |
| `sample_sft.jsonl` | 스키마 예시 2~3건 |

## 데이터 전부 활용해서 학습하기 (권장)

1. **병합** — `train.jsonl` + `exaone_synthetic.jsonl` → `train_full.jsonl` (한 번만 실행)
   ```bash
   python -m app.training.pipelines.spam_sft.merge_train_data
   ```
2. **학습** — `train_full.jsonl` 로 학습, `val.jsonl` 로 검증  
   **PowerShell** (한 줄 또는 백틱 `` ` `` 줄 연결):
   ```powershell
   python -m app.training.models.llama.spam_classifier.finetune --train_path app/data/spam/sft/train_full.jsonl --val_path app/data/spam/sft/val.jsonl
   ```
   **Cmd / Bash** (백슬래시 `\` 줄 연결 가능):
   ```bash
   python -m app.training.models.llama.spam_classifier.finetune \
     --train_path app/data/spam/sft/train_full.jsonl \
     --val_path app/data/spam/sft/val.jsonl
   ```
   (프로젝트 루트에서 실행. `app` 이 패키지로 잡혀야 함.)

## 유형별 목표 (참고)

- 스팸: 피싱, 당첨/이벤트, 광고/마케팅, 가짜 경고/지원, 기타 — 유형당 50~200건
- 햄: 업무, 개인, 뉴스레터 등 — 500~1000건
- 단일 파일만 쓸 때: `--train_path app/data/spam/sft/exaone_synthetic.jsonl` 등으로 지정
