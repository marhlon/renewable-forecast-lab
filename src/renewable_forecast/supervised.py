import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from renewable_forecast.features import (
    CALENDAR_FEATURES,
    FEATURE_COLUMNS,
    build_calendar_features,
    build_feature_frame,
)


def build_horizon_pairs(series: pd.DataFrame, horizon_hours: int = 6) -> pd.DataFrame:
    if isinstance(horizon_hours, bool) or not isinstance(horizon_hours, int) or horizon_hours <= 0:
        raise ValueError("O horizonte deve ser um número inteiro estritamente positivo (não booleano).")

    observed = series[["din_instante", "val_geracao"]].copy()
    observed["din_instante"] = pd.to_datetime(observed["din_instante"], errors="raise")

    if observed["din_instante"].isna().any():
        raise ValueError("A coluna 'din_instante' contém valores ausentes ou nulos.")

    if observed["din_instante"].duplicated().any():
        raise ValueError("A coluna 'din_instante' contém timestamps duplicados.")

    origins = observed[["din_instante"]].rename(columns={"din_instante": "forecast_origin"})
    origins["target_time"] = origins["forecast_origin"] + pd.Timedelta(hours=horizon_hours)

    targets = observed.rename(columns={
        "din_instante": "target_time",
        "val_geracao": "target_generation",
    })

    return (
        origins.merge(
            targets,
            on="target_time",
            how="left",
            validate="one_to_one",
        )
        .sort_values("forecast_origin")
        .reset_index(drop=True)
    )


def purged_time_series_splits(frame, *, n_splits=5, test_size=24 * 28):
    origins = pd.to_datetime(frame["forecast_origin"], errors="raise")
    available = pd.to_datetime(frame["target_available_at"], errors="raise")

    if origins.isna().any() or available.isna().any():
        raise ValueError("Origem e disponibilidade do alvo devem estar preenchidas.")

    if not origins.is_monotonic_increasing or not origins.is_unique:
        raise ValueError("As origens devem estar ordenadas e ser únicas.")

    cv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)

    for train_idx, valid_idx in cv.split(frame):
        cutoff = origins.iloc[valid_idx[0]]
        eligible = available.iloc[train_idx] < cutoff
        train_idx = train_idx[eligible.to_numpy()]

        if train_idx.size == 0:
            raise ValueError("Nenhum exemplo de treino disponível antes deste corte.")

        yield train_idx, valid_idx


def build_horizon_training_frame(series, horizon_hours, *, availability_delay_hours):
    if (
        isinstance(availability_delay_hours, bool)
        or not isinstance(availability_delay_hours, int)
        or availability_delay_hours < 0
    ):
        raise ValueError("O atraso deve ser um inteiro não negativo.")

    data = series.copy()
    data["din_instante"] = pd.to_datetime(data["din_instante"], errors="raise")
    data["val_geracao"] = pd.to_numeric(data["val_geracao"], errors="raise")

    pairs = build_horizon_pairs(data, horizon_hours)

    historical_columns = [c for c in FEATURE_COLUMNS if c not in CALENDAR_FEATURES]
    history = build_feature_frame(data, require_target=False)
    history = history[["din_instante", *historical_columns]].rename(
        columns={"din_instante": "history_reference_time"}
    )

    delay = pd.Timedelta(hours=availability_delay_hours)
    history["history_end"] = history["history_reference_time"] - pd.Timedelta(hours=1)
    history["forecast_origin"] = history["history_end"] + delay

    frame = pairs.merge(
        history,
        on="forecast_origin",
        how="inner",
        validate="one_to_one",
    )
    frame[CALENDAR_FEATURES] = build_calendar_features(frame["target_time"])
    frame["target_available_at"] = frame["target_time"] + delay

    frame = (
        frame.dropna(subset=[*FEATURE_COLUMNS, "target_generation"])
        .sort_values("forecast_origin")
        .reset_index(drop=True)
    )
    if frame.empty:
        raise ValueError("Dados insuficientes para montar o treino deste horizonte.")

    return frame