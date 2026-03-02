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
| `real_labeled.jsonl` | 실제 수신 메일 중 수동 레이블한 데이터 (추가 시 병합) |
| `sample_sft.jsonl` | 스키마 예시 2~3건 |

## 유형별 목표 (참고)

- 스팸: 피싱, 당첨/이벤트, 광고/마케팅, 가짜 경고/지원, 기타 — 유형당 50~200건
- 햄: 업무, 개인, 뉴스레터 등 — 500~1000건
- 학습 시 `train.jsonl` / `val.jsonl` 은 이 디렉터리 파일을 사용할 수 있음. 예:
  - `python -m training.models.llama.spam_classifier.finetune --train_path app/data/spam/sft/exaone_synthetic.jsonl`
  - 또는 `exaone_synthetic.jsonl` + `real_labeled.jsonl` 를 병합해 train/val로 나눈 뒤 `--train_path` / `--val_path` 지정
