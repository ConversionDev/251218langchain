# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path

d = Path(__file__).resolve().parent
for f in d.glob("*.xlsx"):
    if "보강" in f.name:
        df = pd.read_excel(f, sheet_name=0)
        print("파일:", f.name)
        print("행 수:", len(df))
        print("열:", list(df.columns))
        print("\n비고 값 분포:")
        print(df["비고"].value_counts().head(20).to_string())
        print("\n상위 3행 (일부 열):")
        cols = [c for c in ["내부 표기명", "CAS 번호", "비고"] if c in df.columns]
        print(df[cols].head(5).to_string())
        break
else:
    print("보강 xlsx not found")
