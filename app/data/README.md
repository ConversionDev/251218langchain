# app/data 폴더 구조

도메인별로 **prepared**, **raw**, **sft** 3단계 구조를 통일해서 사용합니다.

## 공통 구조 (도메인 폴더)

| 폴더 | 용도 |
|------|------|
| **raw** | 원본/수집 데이터 |
| **prepared** | 전처리·정제된 중간 결과 |
| **sft** | SFT(Supervised Fine-Tuning) 형식 데이터, 학습용 분할(processed/filtered) 포함 |

## 도메인별 설명

- **disclosure/** — 공시 문서 (IFRS, ISO 30414 등). `prepared/`에 청킹·적재용 텍스트.
- **soccer/** — 수업/데모용. `raw/` 도메인 JSONL, `sft/` LLaMA 학습 데이터.
- **email/** — 이메일 SFT 파이프라인. `raw/` 원본, `sft/` 에 sft_train.jsonl·sft_train_cleaned.jsonl, `sft/processed/`(train·val), `sft/filtered/`(필터 결과).

## 이전 sft_dataset

`data/sft_dataset` 은 제거되었습니다. 이메일 SFT 관련 데이터는 **data/email/sft/** 아래로 통합했습니다.

- `sft_dataset/processed` → `email/sft/processed`
- `sft_dataset/filtered` → `email/sft/filtered`
- `sft_dataset/sft_train.jsonl` 등 → `email/sft/sft_train.jsonl`

## 학습 경로 체크리스트 (테스트 전 확인)

| 학습/파이프라인 | 입력 경로 | 출력 경로 |
|----------------|-----------|-----------|
| **이메일 SFT** | | |
| raw_to_sft_format | `data/email/raw/` 또는 `data/` 루트의 raw JSONL | `data/email/sft/sft_train.jsonl` |
| sft_to_train_val_split | `data/email/sft/sft_train.jsonl` (또는 sft_train_cleaned.jsonl) | `data/email/sft/processed/train.jsonl`, `val.jsonl` |
| ambiguous_case_filter | `data/email/sft/processed/train.jsonl`, `val.jsonl` | `data/email/sft/filtered/train_filtered.jsonl`, `val_filtered.jsonl` |
| EXAONE LoRA (lora_trainer, full_pipeline 등) | `data/email/sft/processed/` (또는 filtered) | `artifacts/fine_tuned/exaone/adapters/` |
| LLaMA 스팸 finetune | `data/email/sft/processed/` | `artifacts/fine_tuned/llama/adapters/` |
| **Soccer** | | |
| rule_policy_discriminator finetune | `data/soccer/sft/llama_training_dataset.jsonl` | `artifacts/fine_tuned/llama/semantic_classifier/` |

- 모든 데이터 경로는 `core.paths.get_data_dir()` (= `app/data/`) 기준.
- 모든 학습 출력은 `core.paths.get_output_dir()` (= `app/artifacts/fine_tuned/`) 기준.
