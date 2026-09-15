from __future__ import annotations

import numpy as np
import pandas as pd


LAGS = (1, 2, 3, 6, 12, 24, 48, 168)
ROLLING_WINDOWS = (6, 24, 168)
HOUR_HARMONICS = (1, 2, 3, 4)

LAG_FEATURES = [
    f"lag_{lag}h"
    for lag in LAGS
]

ROLLING_FEATURES = [
    feature
    for window in ROLLING_WINDOWS
    for feature in (
        f"rolling_mean_{window}h",
        f"rolling_std_{window}h",
    )
]

CALENDAR_FEATURES = [
    feature
    for harmonic in HOUR_HARMONICS
    for feature in (
        f"hour_sin_{harmonic}",
        f"hour_cos_{harmonic}",
    )
] + [
    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",
]

FEATURE_COLUMNS = (
    LAG_FEATURES
    + ROLLING_FEATURES
    + CALENDAR_FEATURES
    + ["recent_delta_1h"]
)


def build_feature_frame(
    series: pd.DataFrame,
) -> pd.DataFrame:
    """Transforma uma série em uma tabela supervisionada sem leakage."""

    required_columns = {
        "din_instante",
        "val_geracao",
    }

    missing = required_columns - set(series.columns)

    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(missing)}"
        )

    if not pd.api.types.is_datetime64_any_dtype(
        series["din_instante"]
    ):
        raise ValueError(
            "A coluna din_instante deve possuir tipo datetime."
        )

    if series["din_instante"].isna().any():
        raise ValueError("Existem timestamps ausentes.")

    data = (
        series
        .sort_values("din_instante")
        .reset_index(drop=True)
        .copy()
    )

    if data["din_instante"].duplicated().any():
        raise ValueError("Existem timestamps duplicados.")

    timestamp_deltas = data["din_instante"].diff().dropna()

    if not timestamp_deltas.eq(pd.Timedelta(hours=1)).all():
        raise ValueError(
            "A série deve possuir frequência horária sem lacunas."
        )

    data["val_geracao"] = pd.to_numeric(
        data["val_geracao"],
        errors="raise",
    )

    target = data["val_geracao"]

    for lag in LAGS:
        data[f"lag_{lag}h"] = target.shift(lag)

    # shift(1) garante que a janela termina em t-1.
    known_history = target.shift(1)

    for window in ROLLING_WINDOWS:
        data[f"rolling_mean_{window}h"] = (
            known_history
            .rolling(window, min_periods=window)
            .mean()
        )

        data[f"rolling_std_{window}h"] = (
            known_history
            .rolling(window, min_periods=window)
            .std()
        )

    data["hour"] = data["din_instante"].dt.hour
    data["day_of_week"] = data["din_instante"].dt.dayofweek
    data["month"] = data["din_instante"].dt.month

    for harmonic in HOUR_HARMONICS:
        angle = (
            2
            * np.pi
            * harmonic
            * data["hour"]
            / 24
        )

        data[f"hour_sin_{harmonic}"] = np.sin(angle)
        data[f"hour_cos_{harmonic}"] = np.cos(angle)

    dow_angle = (
        2 * np.pi * data["day_of_week"] / 7
    )

    data["dow_sin"] = np.sin(dow_angle)
    data["dow_cos"] = np.cos(dow_angle)

    month_angle = (
        2 * np.pi * (data["month"] - 1) / 12
    )

    data["month_sin"] = np.sin(month_angle)
    data["month_cos"] = np.cos(month_angle)

    data["recent_delta_1h"] = (
        target.shift(1) - target.shift(2)
    )

    feature_frame = (
        data
        .dropna(
            subset=FEATURE_COLUMNS + ["val_geracao"]
        )
        .reset_index(drop=True)
    )

    if feature_frame.empty:
        raise ValueError(
            "Dados insuficientes para construir as features."
        )

    return feature_frame
