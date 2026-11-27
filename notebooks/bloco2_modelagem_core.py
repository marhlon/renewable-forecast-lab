"""Contratos novos do bloco 2; não modifica os experimentos históricos aceitos.

Os relógios ingênuos da fonte são interpretados como UTC por hipótese de estudo,
sem certificar fuso físico nem disponibilidade histórica do ONS. A latência fixa
assumida é de duas horas: na origem t, o último valor permitido é y(t-2h).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

RECENT = [f"lag_{i}h" for i in range(1, 7)]
OLDER = [f"lag_{i}h" for i in range(7, 25)]
STATS = ["mean6", "std6", "mean24", "std24", "delta1"]
CALENDAR = ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
GROUPS = {"recent6": RECENT, "older18": OLDER, "stats": STATS, "calendar": CALENDAR}
FEATURES = RECENT + OLDER + STATS + CALENDAR
FIELDS = ["forecast_origin", "history_end", "target_time", "label_available_at", "y24",
          "last_observed", "previous_observed", "ramp_down_1h", "ramp_label_available_at"] + FEATURES


class PersistenceRegressor:
    """Serializable baseline with the same predict(X[features]) interface."""
    def fit(self, X, y=None):
        return self

    def predict(self, X):
        return np.asarray(X.iloc[:, 0] if hasattr(X, "iloc") else np.asarray(X)[:, 0], dtype=float)


def timestamp(value) -> pd.Timestamp:
    t = pd.Timestamp(value)
    return t.tz_convert("UTC").tz_localize(None) if t.tzinfo is not None else t


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_series(path) -> pd.DataFrame:
    """Read only the declared source, reject duplicates, retain missing values."""
    raw = pd.read_parquet(path, columns=["din_instante", "val_geracao"])
    raw = raw.copy(deep=True)
    raw["din_instante"] = pd.to_datetime(raw["din_instante"], utc=True).dt.tz_localize(None)
    raw["val_geracao"] = pd.to_numeric(raw["val_geracao"], errors="raise")
    if raw["din_instante"].isna().any() or raw["din_instante"].duplicated().any():
        raise ValueError("Fonte requer instantes únicos e não nulos; não agregar silenciosamente.")
    if not raw["din_instante"].eq(raw["din_instante"].dt.floor("h")).all():
        raise ValueError("Fonte não é horária alinhada; não arredondar silenciosamente.")
    if not np.isfinite(raw["val_geracao"].dropna()).all():
        raise ValueError("Fonte contém geração infinita.")
    return raw.sort_values("din_instante", kind="stable").reset_index(drop=True)


def build_frame(series: pd.DataFrame) -> pd.DataFrame:
    """Create one row per hourly origin within source bounds, without imputation."""
    raw = series[["din_instante", "val_geracao"]].copy(deep=True)
    raw["din_instante"] = pd.to_datetime(raw["din_instante"], utc=True).dt.tz_localize(None)
    if raw.empty or raw["din_instante"].duplicated().any():
        raise ValueError("Série vazia ou instantes duplicados.")
    raw = raw.sort_values("din_instante")
    grid = pd.date_range(raw["din_instante"].min(), raw["din_instante"].max(), freq="h")
    y = raw.set_index("din_instante")["val_geracao"].reindex(grid)
    frame = pd.DataFrame({"forecast_origin": grid})
    frame["history_end"] = frame["forecast_origin"] - pd.Timedelta(hours=2)
    frame["target_time"] = frame["forecast_origin"] + pd.Timedelta(hours=24)
    frame["label_available_at"] = frame["target_time"] + pd.Timedelta(hours=2)
    frame["y24"] = y.shift(-24).to_numpy()
    frame["last_observed"] = y.shift(2).to_numpy()
    frame["previous_observed"] = y.shift(3).to_numpy()
    frame["ramp_down_1h"] = (y - y.shift(-1)).to_numpy()
    frame["ramp_label_available_at"] = frame["forecast_origin"] + pd.Timedelta(hours=3)
    for i in range(1, 25):
        frame[f"lag_{i}h"] = y.shift(i + 1).to_numpy()
    observed = y.shift(2)
    for window in (6, 24):
        frame[f"mean{window}"] = observed.rolling(window, min_periods=window).mean().to_numpy()
        frame[f"std{window}"] = observed.rolling(window, min_periods=window).std(ddof=0).to_numpy()
    frame["delta1"] = frame["last_observed"] - frame["previous_observed"]
    hour = frame["forecast_origin"].dt.hour
    dow = frame["forecast_origin"].dt.dayofweek
    frame["hour_sin"], frame["hour_cos"] = np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24)
    frame["dow_sin"], frame["dow_cos"] = np.sin(2*np.pi*dow/7), np.cos(2*np.pi*dow/7)
    return frame[FIELDS].copy()


def fit_mask(frame: pd.DataFrame, cutoff, target: str = "y24") -> pd.Series:
    """Expanding training cohort: complete features and label available strictly before cut."""
    label_clock = "ramp_label_available_at" if target == "ramp_down_1h" else "label_available_at"
    return (frame[label_clock].lt(timestamp(cutoff)) & np.isfinite(frame[target]) &
            np.isfinite(frame[FEATURES]).all(axis=1))


def period_mask(frame, start, end, target="y24"):
    return (frame["forecast_origin"].ge(timestamp(start)) &
            frame["forecast_origin"].lt(timestamp(end)) & np.isfinite(frame[target]) &
            np.isfinite(frame[FEATURES]).all(axis=1))
