"""
GGUF 최종 복구 스크립트.

문제: exaone_competency_q4_k_m.gguf 의 어휘 KV 데이터가 누락됨.
해결: exaone_f16.gguf (올바른 어휘) + exaone_competency_q4_k_m.gguf (Q4_K_M 텐서) 조합.

출력: exaone_competency_q4_k_m_v3.gguf
  → 이 파일을 EC2에 업로드하면 됩니다.

실행:
  conda activate llamacpp_convert
  cd C:\\dev\\RAG\\backend\\ontology\\apps
  python scripts\\patch_gguf_from_f16.py
"""
from __future__ import annotations

from pathlib import Path

# ── 경로 ──────────────────────────────────────────────────────────────────────
BASE     = Path(__file__).parent.parent / "artifacts" / "fine_tuned" / "exaone"
F16_IN   = BASE / "gguf" / "exaone_f16.gguf"                         # 어휘 소스
Q4_IN    = BASE / "gguf" / "exaone_competency_q4_k_m.gguf"           # 텐서 소스
GGUF_OUT = BASE / "gguf" / "exaone_competency_q4_k_m_v3.gguf"        # 출력

assert F16_IN.exists(), f"f16 GGUF 없음: {F16_IN}"
assert Q4_IN.exists(),  f"Q4_K_M GGUF 없음: {Q4_IN}"

# ── LenientGGUFReader (중복 키 허용) ──────────────────────────────────────────
from gguf.gguf_reader import GGUFReader as _BaseReader, ReaderField  # type: ignore

class LenientGGUFReader(_BaseReader):
    def _push_field(self, field: ReaderField, **kwargs) -> int:
        try:
            return super()._push_field(field, **kwargs)
        except KeyError:
            print(f"  [WARN] 중복 키 무시: {field.name}")
            return sum(p.nbytes for p in field.parts)

from gguf import GGUFWriter, GGUFValueType  # type: ignore

# ── 필드 복사 헬퍼 ─────────────────────────────────────────────────────────────
def _read_scalar(field):
    """ReaderField 에서 실제 스칼라 값 추출.
    field.data 는 parts 에 대한 인덱스 리스트이므로 contents() 를 우선 시도.
    """
    if hasattr(field, "contents"):
        return field.contents()
    # fallback: 마지막 part 가 실제 값
    last = field.parts[field.data[-1]] if len(field.data) else field.parts[-1]
    vtype = field.types[0]
    if vtype == GGUFValueType.STRING:
        return bytes(last).decode("utf-8", errors="replace")
    return last[0] if hasattr(last, "__len__") else last


def _read_array(field):
    """ReaderField (ARRAY 타입) → Python list (numpy 스칼라 → Python 스칼라 변환)."""
    elem_type = field.types[1] if len(field.types) > 1 else None
    FLOAT_TYPES = {GGUFValueType.FLOAT32, GGUFValueType.FLOAT64}
    out = []
    for idx in field.data:
        part = field.parts[idx]
        if elem_type == GGUFValueType.STRING:
            out.append(bytes(part).decode("utf-8", errors="replace"))
        else:
            raw = part[0] if hasattr(part, "__len__") else part
            if elem_type in FLOAT_TYPES:
                out.append(float(raw))
            else:
                out.append(int(raw))
    return out


def _copy_field(w: GGUFWriter, key: str, field) -> None:
    vtype = field.types[0]
    if vtype == GGUFValueType.ARRAY:
        elem_type = field.types[1] if len(field.types) > 1 else None
        vals = _read_array(field)
        if elem_type == GGUFValueType.STRING:
            w.add_array(key, [str(v) for v in vals])
        else:
            w.add_array(key, vals)
        return
    val = _read_scalar(field)
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

# ── 1. f16 읽기 (KV 소스: 올바른 어휘 포함) ───────────────────────────────────
print(f"[INFO] f16 GGUF KV 읽는 중 (14 GB, 잠시 대기)…  {F16_IN.name}")
f16 = LenientGGUFReader(str(F16_IN), mode="r")
print(f"[INFO] f16 KV 수: {len(f16.fields)}")

# ── 2. Q4_K_M 읽기 (텐서 소스 + 양자화 KV) ────────────────────────────────────
print(f"[INFO] Q4_K_M GGUF 읽는 중…  {Q4_IN.name}")
q4 = LenientGGUFReader(str(Q4_IN), mode="r")
print(f"[INFO] Q4_K_M 텐서 수: {len(q4.tensors)}")

# ── 3. 새 GGUF 쓰기 ────────────────────────────────────────────────────────────
print(f"[INFO] 출력 GGUF: {GGUF_OUT.name}")
writer = GGUFWriter(str(GGUF_OUT), arch="exaone")

# f16 KV에서 제외할 키 (writer 생성자 추가 or 비표준)
SKIP_F16 = {
    "general.architecture",   # GGUFWriter 생성자에서 이미 추가
    "GGUF.version",           # 헤더 필드 - KV에 쓰면 안 됨
    "GGUF.tensor_count",      # 헤더 필드
    "GGUF.kv_count",          # 헤더 필드
    "general.file_type",      # Q4_K_M 값으로 덮어씀
    "general.quantization_version",  # Q4_K_M 값으로 덮어씀
}

# layer_norm_epsilon → layer_norm_rms_epsilon 키 이름 수정
OLD_KEY = "exaone.attention.layer_norm_epsilon"
NEW_KEY = "exaone.attention.layer_norm_rms_epsilon"

print("[INFO] f16 KV 복사 중 (어휘 포함)…")
for key, field in f16.fields.items():
    if key in SKIP_F16:
        continue
    out_key = NEW_KEY if key == OLD_KEY else key
    if out_key == NEW_KEY:
        print(f"  [RENAME] {key} → {out_key}")
    _copy_field(writer, out_key, field)

# Q4_K_M에서 양자화 전용 KV 가져오기
Q4_ONLY = {"general.file_type", "general.quantization_version"}
print("[INFO] Q4_K_M 양자화 KV 추가 중…")
for key in Q4_ONLY:
    if key in q4.fields:
        _copy_field(writer, key, q4.fields[key])

# ── 4. Q4_K_M 텐서 복사 ───────────────────────────────────────────────────────
print(f"[INFO] Q4_K_M 텐서 복사 중 ({len(q4.tensors)}개, ~4.5 GB)…")
for t in q4.tensors:
    writer.add_tensor(t.name, t.data, raw_dtype=t.tensor_type)

print("[INFO] 파일 쓰는 중 (수 분 소요)…")
writer.write_header_to_file()
writer.write_kv_data_to_file()
writer.write_tensors_to_file()
writer.close()

size_gb = GGUF_OUT.stat().st_size / 1024**3
print(f"[OK] 완료: {GGUF_OUT}  ({size_gb:.2f} GB)")
print()
print("다음 단계:")
print(f"  scp -i RSA.pem {GGUF_OUT} ubuntu@EC2:/home/ubuntu/app/artifacts/fine_tuned/exaone/gguf/exaone_competency_q4_k_m.gguf")
