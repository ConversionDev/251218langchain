"""
ESG 더미: 전력(usage) 시계열 예측 학습 (PyTorch, sklearn 미사용).

- 입력: app/data/esg_dummy/labeled_slots.csv (run_generate_measurements.py --output-labeled)
- 시계열: (process, line)별 usage lag 1~6 슬롯 + hour, month, production 등
- 시간 분할: 2024 train, 2025 상반기 val, 2025 하반기 test
- 저장: app/artifacts/esg_anomaly/ (usage_forecaster.pt, usage_scaler_*.json 등)
- 역량 SFT와 동일: 에폭 5, 속도·통계 출력
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from core.paths import get_artifacts_dir, get_esg_dummy_dir  # type: ignore  # app 하위 실행 시 core = app/core


class LabelEncoderPure:
    def __init__(self) -> None:
        self.classes_: list[str] = []
        self._idx: dict[str, int] = {}

    def fit_transform(self, y: np.ndarray) -> np.ndarray:
        self.classes_ = sorted(np.unique(y).astype(str).tolist())
        self._idx = {c: i for i, c in enumerate(self.classes_)}
        return np.array([self._idx[str(v)] for v in y], dtype=np.int64)

    def transform(self, y: np.ndarray) -> np.ndarray:
        return np.array([self._idx[str(v)] for v in y], dtype=np.int64)


class StandardScalerPure:
    def __init__(self) -> None:
        self.mean_: np.ndarray = np.array([])
        self.scale_: np.ndarray = np.array([])

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.mean_ = np.mean(X, axis=0).astype(np.float32)
        std = np.std(X, axis=0).astype(np.float32)
        self.scale_ = np.where(std > 1e-8, std, 1.0)
        return (X - self.mean_) / self.scale_

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean_) / self.scale_

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        return X * self.scale_ + self.mean_


LAG_STEPS = 6  # usage_lag1 ~ usage_lag6
FEATURE_NAMES = [
    "production", "equipment_ct", "hour", "month", "shift_day",
    "process_enc", "line_enc",
] + [f"usage_lag{i}" for i in range(1, LAG_STEPS + 1)]


class MLPRegressor(nn.Module):
    def __init__(self, in_dim: int, hidden: list[int] | None = None, dropout: float = 0.15):
        super().__init__()
        hidden = hidden or [256, 128]
        layers = []
        prev = in_dim
        for h in hidden:
            layers += [
                nn.Linear(prev, h),
                nn.BatchNorm1d(h),
                nn.ReLU(inplace=True),
                nn.Dropout(dropout),
            ]
            prev = h
        self.backbone = nn.Sequential(*layers)
        self.head = nn.Linear(prev, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(x)).squeeze(-1)


def load_and_build_lags(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "labeled_slots.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"labeled_slots.csv 없음: {path}\n"
            "먼저: python -m app.training.pipelines.esg_dummy.run_generate_measurements --output-labeled"
        )
    df = pd.read_csv(path)
    df["noticedate"] = pd.to_datetime(df["noticedate"])
    df = df.sort_values(["noticedate", "hour", "process", "line"]).reset_index(drop=True)
    for i in range(1, LAG_STEPS + 1):
        df[f"usage_lag{i}"] = df.groupby(["process", "line"])["usage"].shift(i)
    df = df.dropna(subset=[f"usage_lag{i}" for i in range(1, LAG_STEPS + 1)]).copy()
    return df


def time_split(
    df: pd.DataFrame,
    train_end: str = "2024-12-31",
    val_end: str = "2025-06-30",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["noticedate"] <= train_end].copy()
    val = df[(df["noticedate"] > train_end) & (df["noticedate"] <= val_end)].copy()
    test = df[df["noticedate"] > val_end].copy()
    return train, val, test


def main() -> None:
    parser = argparse.ArgumentParser(description="ESG 전력(usage) 시계열 예측")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=5, help="역량 SFT와 동일")
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=5e-4)
    parser.add_argument("--hidden", type=int, nargs="+", default=[256, 128])
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--device", type=str, default=None)
    args = parser.parse_args()

    data_dir = args.data_dir or get_esg_dummy_dir()
    out_dir = args.out_dir or (get_artifacts_dir() / "esg_anomaly")
    out_dir.mkdir(parents=True, exist_ok=True)
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    print("[1/5] labeled_slots.csv 로드 + 시계열 lag 생성")
    df = load_and_build_lags(data_dir)
    df["month"] = df["noticedate"].dt.month
    df["shift_day"] = (df["shift"] == "day").astype(int)
    print(f"  lag 적용 후 행: {len(df):,}")

    print("\n[2/5] 시간 기준 train/val/test 분할")
    train_df, val_df, test_df = time_split(df)
    print(f"  train: {len(train_df):,}, val: {len(val_df):,}, test: {len(test_df):,}")

    print("\n[3/5] 피처·타깃 준비 및 스케일링")
    process_enc = LabelEncoderPure()
    line_enc = LabelEncoderPure()
    train_df["process_enc"] = process_enc.fit_transform(train_df["process"].values)
    train_df["line_enc"] = line_enc.fit_transform(train_df["line"].values)
    val_df["process_enc"] = process_enc.transform(val_df["process"].values)
    val_df["line_enc"] = line_enc.transform(val_df["line"].values)
    test_df["process_enc"] = process_enc.transform(test_df["process"].values)
    test_df["line_enc"] = line_enc.transform(test_df["line"].values)

    X_train = train_df[FEATURE_NAMES].values.astype(np.float32)
    X_val = val_df[FEATURE_NAMES].values.astype(np.float32)
    X_test = test_df[FEATURE_NAMES].values.astype(np.float32)
    y_train = train_df["usage"].values.astype(np.float32)
    y_val = val_df["usage"].values.astype(np.float32)
    y_test = test_df["usage"].values.astype(np.float32)

    scaler_x = StandardScalerPure()
    scaler_y = StandardScalerPure()
    X_train_s = scaler_x.fit_transform(X_train)
    X_val_s = scaler_x.transform(X_val)
    X_test_s = scaler_x.transform(X_test)
    y_train_s = scaler_y.fit_transform(y_train.reshape(-1, 1)).ravel()
    y_val_s = scaler_y.transform(y_val.reshape(-1, 1)).ravel()
    y_test_s = scaler_y.transform(y_test.reshape(-1, 1)).ravel()

    train_ds = TensorDataset(torch.from_numpy(X_train_s), torch.from_numpy(y_train_s))
    val_ds = TensorDataset(torch.from_numpy(X_val_s), torch.from_numpy(y_val_s))
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=(device == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    in_dim = X_train_s.shape[1]
    model = MLPRegressor(in_dim=in_dim, hidden=args.hidden).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=8)
    criterion = nn.MSELoss()

    print("\n[4/5] PyTorch 시계열 예측 학습 (역량 SFT와 동일: 속도·통계)")
    t_train_start = time.perf_counter()
    best_val_loss = float("inf")
    best_epoch = 0
    no_improve = 0
    actual_epochs = 0
    for epoch in range(args.epochs):
        t_epoch_start = time.perf_counter()
        model.train()
        running_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            out = model(xb)
            loss = criterion(out, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            running_loss += loss.item() * xb.size(0)
        train_loss = running_loss / len(train_ds)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                val_loss += criterion(model(xb), yb).item() * xb.size(0)
        val_loss = val_loss / len(val_ds)
        scheduler.step(val_loss)

        elapsed_epoch = time.perf_counter() - t_epoch_start
        actual_epochs = epoch + 1
        samples_per_sec = len(train_ds) / elapsed_epoch if elapsed_epoch > 0 else 0.0
        remaining_epochs = (args.epochs - (epoch + 1)) if no_improve < args.patience else 0
        eta_sec = remaining_epochs * elapsed_epoch if remaining_epochs > 0 else 0

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch + 1
            no_improve = 0
            torch.save({k: v.cpu().clone() for k, v in model.state_dict().items()}, out_dir / "usage_forecaster.pt")
        else:
            no_improve += 1

        eta_str = f"  남은 시간 약 {eta_sec:.0f}초" if eta_sec > 0 else ""
        print(f"  epoch {actual_epochs}/{args.epochs}  train_loss={train_loss:.6f}  val_loss={val_loss:.6f}  best={best_val_loss:.6f} (epoch {best_epoch})  |  경과 {elapsed_epoch:.1f}초  초당 샘플 {samples_per_sec:,.0f}{eta_str}")
        if no_improve >= args.patience:
            print(f"  [조기 종료] val_loss {args.patience}에폭 개선 없음.")
            break

    train_runtime = time.perf_counter() - t_train_start
    total_samples = actual_epochs * len(train_ds)
    train_samples_per_second = total_samples / train_runtime if train_runtime > 0 else 0.0
    print()
    print("[INFO] 학습 통계 (역량 SFT와 동일 형식):")
    print(f"  - 총 학습 시간: {train_runtime:.2f}초 ({train_runtime/60:.1f}분)")
    print(f"  - 총 에폭: {actual_epochs}")
    print(f"  - 초당 샘플: {train_samples_per_second:.2f}")
    print()

    print("[5/5] test 평가 및 저장")
    model.load_state_dict(torch.load(out_dir / "usage_forecaster.pt", map_location=device))
    model.eval()
    with torch.no_grad():
        y_pred_s = model(torch.from_numpy(X_test_s).to(device)).cpu().numpy()
    y_pred = scaler_y.inverse_transform(y_pred_s.reshape(-1, 1)).ravel()
    mae = np.mean(np.abs(y_test - y_pred))
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    print(f"  test MAE: {mae:.2f}  RMSE: {rmse:.2f}")

    with open(out_dir / "usage_scaler_x.json", "w", encoding="utf-8") as f:
        json.dump({"mean": scaler_x.mean_.tolist(), "scale": scaler_x.scale_.tolist()}, f)
    with open(out_dir / "usage_scaler_y.json", "w", encoding="utf-8") as f:
        json.dump({"mean": scaler_y.mean_.tolist(), "scale": scaler_y.scale_.tolist()}, f)
    with open(out_dir / "usage_process_encoder.json", "w", encoding="utf-8") as f:
        json.dump({"classes": process_enc.classes_}, f, ensure_ascii=False)
    with open(out_dir / "usage_line_encoder.json", "w", encoding="utf-8") as f:
        json.dump({"classes": line_enc.classes_}, f, ensure_ascii=False)
    with open(out_dir / "usage_feature_names.json", "w", encoding="utf-8") as f:
        json.dump(FEATURE_NAMES, f, ensure_ascii=False, indent=2)
    with open(out_dir / "usage_forecaster_meta.json", "w", encoding="utf-8") as f:
        json.dump({"in_dim": in_dim, "hidden": args.hidden, "lag_steps": LAG_STEPS}, f, indent=2)

    print(f"\n저장: {out_dir}")
    print("  usage_forecaster.pt, usage_scaler_x/y.json, usage_*_encoder.json, usage_feature_names.json, usage_forecaster_meta.json")


if __name__ == "__main__":
    main()
