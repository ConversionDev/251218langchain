# -*- coding: utf-8 -*-
"""
배터리 EC 번호: data/env_mapping 내 두 xlsx만 사용.
- 배터리 산업 공급망 리스트 보강.xlsx (1차)
- zvg-cas-list-d.xlsx (GESTIS, 2차)
API 호출 없음.
"""
from __future__ import annotations

import re
from pathlib import Path


def _normalize_cas(v) -> str:
    if v is None or (isinstance(v, float) and (v != v or v == 0)):
        return ""
    return re.sub(r"\s+", "", str(v).strip())


def load_ec_from_supply_chain_xlsx(path: Path) -> dict[str, str]:
    """공급망 리스트 보강.xlsx → CAS(정규화) -> EC."""
    if not path.exists():
        return {}
    try:
        import pandas as pd
        df = pd.read_excel(path, sheet_name=0)
    except Exception:
        return {}
    cas_col = ec_col = None
    for c in df.columns:
        s = str(c).strip()
        if "CAS" in s and "번호" in s:
            cas_col = c
        if "EC" in s and "번호" in s:
            ec_col = c
    if not cas_col or not ec_col:
        return {}
    out = {}
    for _, row in df.iterrows():
        cas = _normalize_cas(row.get(cas_col))
        if not cas:
            continue
        v = row.get(ec_col)
        if v is None or (isinstance(v, float) and (v != v)):
            continue
        ec = re.sub(r"\s+", "", str(v).strip())
        if ec:
            out[cas] = ec
    return out


def load_ec_from_zvg_xlsx(path: Path) -> dict[str, str]:
    """zvg-cas-list-d.xlsx (GESTIS) → CAS(정규화) -> EC."""
    if not path.exists():
        return {}
    try:
        import pandas as pd
        df = pd.read_excel(path, sheet_name=0, header=0)
    except Exception:
        return {}
    col_cas = col_ec = None
    for c in df.columns:
        cstr = str(c).strip().lower()
        if col_cas is None and ("cas" in cstr and ("nummer" in cstr or "number" in cstr)):
            col_cas = c
        if col_ec is None and ("eg" in cstr or "ec" in cstr) and ("nummer" in cstr or "number" in cstr or cstr == "ec"):
            col_ec = c
    if col_cas is None:
        for c in df.columns:
            if "cas" in str(c).lower():
                col_cas = c
                break
    if col_ec is None:
        for c in df.columns:
            if "ec" in str(c).lower() or "eg" in str(c).lower():
                col_ec = c
                break
    if not col_cas or not col_ec:
        return {}
    out = {}
    for _, row in df.iterrows():
        cas = _normalize_cas(row.get(col_cas))
        if not cas:
            continue
        v = row.get(col_ec)
        if v is None:
            continue
        ec = re.sub(r"\s+", "", str(v).strip())
        if ec:
            out[cas] = ec
    return out


def build_ec_by_cas(data_dir: Path) -> dict[str, str]:
    """
    data_dir 내 공급망 리스트 보강.xlsx(1차) + zvg-cas-list-d.xlsx(2차) 로
    CAS -> EC 딕셔너리 반환. 공급망에 있으면 그대로, 없으면 GESTIS.
    """
    ec_by_cas = {}
    # 1차: 공급망 리스트 보강 (파일명에 '공급망','보강' 포함 xlsx)
    for f in data_dir.glob("*.xlsx"):
        if "공급망" in f.name and "보강" in f.name:
            ec_by_cas.update(load_ec_from_supply_chain_xlsx(f))
            break
    # 2차: GESTIS
    zvg_path = data_dir / "zvg-cas-list-d.xlsx"
    zvg_ec = load_ec_from_zvg_xlsx(zvg_path)
    for cas, ec in zvg_ec.items():
        if cas not in ec_by_cas and ec:
            ec_by_cas[cas] = ec
    return ec_by_cas
