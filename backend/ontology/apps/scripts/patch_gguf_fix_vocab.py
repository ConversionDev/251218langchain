"""
GGUF 어휘 복구 패치 스크립트.

증상: 이전 layer_norm_epsilon 패치 시 tokenizer.ggml.tokens / tokenizer.ggml.merges
       등 어휘 KV 데이터가 누락됨.

처리:
  1. 기존 Q4_K_M GGUF에서 모델 구조 KV + 텐서(raw) 읽기
  2. merged_hf_for_gguf/tokenizer.json 에서 어휘(tokens, merges) 추출
  3. 새 GGUF 파일에 모두 합쳐 쓰기 → exaone_competency_q4_k_m_fixed.gguf

실행 방법 (llamacpp_convert 또는 gguf 라이브러리가 있는 환경):
  conda activate llamacpp_convert
  python patch_gguf_fix_vocab.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE     = Path(__file__).parent.parent / "artifacts" / "fine_tuned" / "exaone"
GGUF_IN  = BASE / "gguf" / "exaone_competency_q4_k_m.gguf"
GGUF_OUT = BASE / "gguf" / "exaone_competency_q4_k_m_fixed.gguf"
TOK_DIR  = BASE / "merged_hf_for_gguf"

assert GGUF_IN.exists(),  f"입력 GGUF 없음: {GGUF_IN}"
assert (TOK_DIR / "tokenizer.json").exists(), f"tokenizer.json 없음: {TOK_DIR}"

# ── GGUFReader 중복 키 허용 패치 ────────────────────────────────────────────
# 일부 convert_hf_to_gguf.py 버전이 GGUF.version 등을 KV 섹션에 중복 기록함
from gguf.gguf_reader import GGUFReader as _BaseReader, ReaderField  # type: ignore

class LenientGGUFReader(_BaseReader):
    """중복 KV 키를 오류 대신 경고로 처리하는 GGUFReader."""
    def _push_field(self, field: ReaderField, **kwargs) -> int:
        try:
            return super()._push_field(field, **kwargs)
        except KeyError:
            print(f"  [WARN] 중복 키 무시: {field.name}")
            # field.parts 에 기록된 크기만큼 offset 전진
            return sum(p.nbytes for p in field.parts)

# ── 1. 어휘 읽기 (tokenizer.json) ─────────────────────────────────────────────
print("[INFO] tokenizer.json 읽는 중…")
tok = json.loads((TOK_DIR / "tokenizer.json").read_text(encoding="utf-8"))

vocab_dict: dict[str, int] = tok["model"]["vocab"]          # token_str → id
tokens: list[str]           = [t for t, _ in sorted(vocab_dict.items(), key=lambda x: x[1])]
merges: list[str]            = tok["model"]["merges"]        # ["X Y", …]

# 특수 토큰 ID (config.json 또는 위 메타데이터에서 확인)
SPECIAL_IDS = {0, 1, 3, 361}  # padding=0, bos=1, unknown=3, eos=361
token_types: list[int] = [3 if i in SPECIAL_IDS else 1 for i in range(len(tokens))]
scores: list[float]    = [0.0] * len(tokens)   # BPE 는 unigram score 사용 안 함

print(f"[INFO] 토큰 수: {len(tokens)}, 병합 수: {len(merges)}")

# ── 2. 기존 GGUF 읽기 ─────────────────────────────────────────────────────────
print(f"[INFO] GGUF 읽는 중: {GGUF_IN}")
from gguf import GGUFWriter, GGUFValueType  # type: ignore

reader = LenientGGUFReader(str(GGUF_IN), mode="r")

# ── 3. 새 GGUF 쓰기 ───────────────────────────────────────────────────────────
print(f"[INFO] 패치된 GGUF 쓰는 중: {GGUF_OUT}")
writer = GGUFWriter(str(GGUF_OUT), arch="exaone")

SKIP_KEYS = {
    "general.architecture",          # GGUFWriter 생성자에서 이미 추가
    "GGUF.version",                  # 헤더 필드를 KV에 중복 기록한 비표준 항목
    "tokenizer.ggml.tokens",         # 새로 주입
    "tokenizer.ggml.scores",
    "tokenizer.ggml.token_type",
    "tokenizer.ggml.merges",
}


def _copy_field(w: GGUFWriter, key: str, field) -> None:
    """GGUFReader 필드를 GGUFWriter 로 복사 (타입별 분기)."""
    vtype = field.types[0]

    if vtype == GGUFValueType.ARRAY:
        elem_type = field.types[1] if len(field.types) > 1 else None
        if elem_type == GGUFValueType.STRING:
            vals = [str(v) for v in field.data]
            w.add_array(key, vals)
        else:
            w.add_array(key, field.data.tolist())
        return

    val = field.data[0]
    if   vtype == GGUFValueType.STRING:  w.add_string(key,  str(val))
    elif vtype == GGUFValueType.BOOL:    w.add_bool(key,    bool(val))
    elif vtype == GGUFValueType.UINT8:   w.add_uint8(key,   int(val))
    elif vtype == GGUFValueType.UINT16:  w.add_uint16(key,  int(val))
    elif vtype == GGUFValueType.UINT32:  w.add_uint32(key,  int(val))
    elif vtype == GGUFValueType.UINT64:  w.add_uint64(key,  int(val))
    elif vtype == GGUFValueType.INT8:    w.add_int8(key,    int(val))
    elif vtype == GGUFValueType.INT16:   w.add_int16(key,   int(val))
    elif vtype == GGUFValueType.INT32:   w.add_int32(key,   int(val))
    elif vtype == GGUFValueType.INT64:   w.add_int64(key,   int(val))
    elif vtype == GGUFValueType.FLOAT32: w.add_float32(key, float(val))
    elif vtype == GGUFValueType.FLOAT64: w.add_float64(key, float(val))
    else:
        print(f"  [SKIP] 지원 안 되는 타입 {vtype} (키: {key})")


# 기존 KV 복사 (어휘 키 제외)
for key, field in reader.fields.items():
    if key in SKIP_KEYS:
        continue
    _copy_field(writer, key, field)

# 어휘 KV 추가
print("[INFO] 어휘 KV 추가 중…")
writer.add_array("tokenizer.ggml.tokens",     tokens)
writer.add_array("tokenizer.ggml.scores",     scores)
writer.add_array("tokenizer.ggml.token_type", token_types)
writer.add_array("tokenizer.ggml.merges",     merges)

# 텐서 복사 (Q4_K_M raw, mmap 기반 → RAM 절약)
print(f"[INFO] 텐서 복사 중 ({len(reader.tensors)}개)…")
for t in reader.tensors:
    writer.add_tensor(t.name, t.data, raw_dtype=t.tensor_type)

print("[INFO] 파일 쓰는 중 (4~5 GB, 수 분 소요)…")
writer.write_header_to_file()
writer.write_kv_data_to_file()
writer.write_tensors_to_file()
writer.close()

print(f"[OK] 완료: {GGUF_OUT}")
print("다음 단계: scp 로 EC2 에 업로드 후 테스트")
