"""Emissão h+6 sem alvo conhecido, com o modelo avaliado no holdout.

Salvar em src/renewable_forecast/horizon_predict.py.
O registro de previsões permite incorporar seus resíduos quando os alvos chegam.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from renewable_forecast.features import (
    CALENDAR_FEATURES, FEATURE_COLUMNS, LAGS, ROLLING_WINDOWS,
    build_calendar_features, build_feature_frame,
)


def build_prediction_row(
    series, forecast_origin, *, horizon_hours, availability_delay_hours,
):
    """Uma linha de X; não constrói nem exige target_generation.

    Mantém a convenção do treino: geração disponível no instante da emissão
    pode entrar nas features; resíduos da correção exigem disponibilidade < t.
    """
    for name, value, minimum in (
        ("horizon_hours", horizon_hours, 1),
        ("availability_delay_hours", availability_delay_hours, 0),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name} deve ser inteiro >= {minimum}.")
    origin = pd.Timestamp(forecast_origin)
    if pd.isna(origin) or origin != origin.floor("h"):
        raise ValueError("A emissão deve ser um timestamp preenchido em hora exata.")
    data = series[["din_instante", "val_geracao"]].copy()
    data["din_instante"] = pd.to_datetime(data["din_instante"], errors="raise")
    if data["din_instante"].isna().any() or data["din_instante"].duplicated().any():
        raise ValueError("A série contém timestamps ausentes ou duplicados.")

    history_end = origin - pd.Timedelta(hours=availability_delay_hours)
    reference = history_end + pd.Timedelta(hours=1)
    target_time = origin + pd.Timedelta(hours=horizon_hours)
    lookback = max(*LAGS, *ROLLING_WINDOWS)
    expected = pd.date_range(end=history_end, periods=lookback, freq="h")
    known = data.loc[
        (data["din_instante"] >= expected[0])
        & (data["din_instante"] <= history_end)
    ].sort_values("din_instante").reset_index(drop=True)
    if len(known) != lookback or not known["din_instante"].eq(pd.Series(expected)).all():
        raise ValueError(
            f"São necessárias {lookback} observações horárias consecutivas "
            f"de {expected[0]} até {history_end}."
        )
    known["val_geracao"] = pd.to_numeric(known["val_geracao"], errors="raise").astype(float)
    if not np.isfinite(known["val_geracao"].to_numpy()).all():
        raise ValueError("O histórico necessário contém geração ausente ou não finita.")

    # Linha de referência para os shifts. NaN é ausência, não geração simulada.
    placeholder = pd.DataFrame({"din_instante": [reference], "val_geracao": [np.nan]})
    features = build_feature_frame(
        pd.concat([known, placeholder], ignore_index=True), require_target=False
    )
    row = features.loc[features["din_instante"].eq(reference), FEATURE_COLUMNS].copy()
    if len(row) != 1:
        raise ValueError("Não foi possível construir uma única linha de previsão.")
    row[CALENDAR_FEATURES] = build_calendar_features(
        pd.Series([target_time], index=row.index)
    )
    row = row.reset_index(drop=True)
    row["forecast_origin"] = origin
    row["target_time"] = target_time
    row["history_reference_time"] = reference
    row["history_end"] = history_end
    return row


def available_mean_correction(
    predictions, observations, forecast_origin, *, horizon_hours,
    availability_delay_hours, window_hours=168, min_history=48,
):
    """Consulta previsões emitidas e calcula apenas resíduos já conhecidos.

    A previsão histórica é a saída do HGB bruto. O valor observado vem da
    série atual, permitindo incorporar resultados de novas emissões registradas.
    """
    origin = pd.Timestamp(forecast_origin)
    history = predictions[["forecast_origin", "target_time", "prediction"]].copy()
    for column in ("forecast_origin", "target_time"):
        history[column] = pd.to_datetime(history[column], errors="raise")
        if history[column].isna().any():
            raise ValueError("Há datas ausentes no registro de previsões.")
    if history["forecast_origin"].duplicated().any():
        raise ValueError("Há emissões duplicadas no registro de previsões.")
    if not (history["target_time"] == history["forecast_origin"] + pd.Timedelta(hours=horizon_hours)).all():
        raise ValueError("O registro contém previsões de outro horizonte.")
    history["target_available_at"] = (
        history["target_time"] + pd.Timedelta(hours=availability_delay_hours)
    )
    eligible = history.loc[
        (history["target_available_at"] >= origin - pd.Timedelta(hours=window_hours))
        & (history["target_available_at"] < origin)
    ].copy()
    observed = observations[["din_instante", "val_geracao"]].copy()
    observed["din_instante"] = pd.to_datetime(observed["din_instante"], errors="raise")
    if observed["din_instante"].isna().any() or observed["din_instante"].duplicated().any():
        raise ValueError("Há timestamps ausentes ou duplicados nas observações.")
    observed = observed.rename(columns={
        "din_instante": "target_time", "val_geracao": "target_generation"
    })
    # Esta junção só procura alvos de previsões ANTERIORES já elegíveis.
    available = eligible.merge(observed, on="target_time", how="left", validate="one_to_one")
    for column in ("prediction", "target_generation"):
        available[column] = pd.to_numeric(available[column], errors="raise")
    available = available.dropna(subset=["target_generation"])
    if not np.isfinite(available[["prediction", "target_generation"]].to_numpy(dtype=float)).all():
        raise ValueError("Há valores não finitos nos resíduos disponíveis.")
    residuals = available["target_generation"] - available["prediction"]
    active = len(residuals) >= min_history
    latest = available["target_available_at"].max()
    return {
        "offset_mean": float(residuals.mean()) if active else 0.0,
        "calibration_n": len(residuals),
        "calibration_active": active,
        "calibration_latest_available_at": None if pd.isna(latest) else str(latest),
        "calibration_missing_observations": len(eligible) - len(available),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--forecast-origin", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/forecasts/h6_d2"))
    args = parser.parse_args(argv)
    metadata = json.loads((args.model_dir / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("selected_method") != "hgb_mean" or not metadata.get("holdout_evaluated"):
        raise ValueError("Informe a pasta do holdout concluído com hgb_mean.")
    if metadata["features"] != list(FEATURE_COLUMNS):
        raise ValueError("As features atuais diferem das usadas pelo modelo salvo.")
    origin = pd.Timestamp(args.forecast_origin)
    if origin <= pd.Timestamp(metadata["last_origin"]):
        raise ValueError("Esta CLI emite após a última origem avaliada no holdout.")
    protocol = metadata["source_protocol"]
    horizon, delay = protocol["horizon_hours"], protocol["availability_delay_hours"]
    series = pd.read_parquet(args.input)
    row = build_prediction_row(
        series, origin, horizon_hours=horizon, availability_delay_hours=delay
    )

    # Um registro separado por modelo evita misturar resíduos de artefatos distintos.
    output = args.output_dir / metadata["run_id"]
    ledger_path = output / "prediction_log.csv"
    columns = ["forecast_origin", "target_time", "prediction"]
    histories = [
        pd.read_parquet(args.model_dir / "initial_calibration_seed.parquet")[columns],
        pd.read_parquet(args.model_dir / "predictions.parquet")[columns],
    ]
    ledger = pd.read_csv(ledger_path) if ledger_path.exists() else None
    if ledger is not None:
        logged_origins = pd.to_datetime(ledger["forecast_origin"], errors="raise")
        if origin <= logged_origins.max():
            raise ValueError("A emissão já foi registrada ou é anterior à última emissão deste registro.")
        histories.append(ledger[columns])
    correction = available_mean_correction(
        pd.concat(histories, ignore_index=True), series, origin,
        horizon_hours=horizon, availability_delay_hours=delay,
        window_hours=metadata["window_hours"], min_history=metadata["min_history"],
    )

    import joblib
    import sklearn

    if sklearn.__version__ != metadata["versions"]["sklearn"]:
        raise ValueError("Use a mesma versão de scikit-learn do modelo avaliado.")
    model_path = args.model_dir / "model.joblib"
    model = joblib.load(model_path)
    raw = float(np.maximum(model.predict(row[FEATURE_COLUMNS])[0], 0.0))
    prediction = max(raw + correction["offset_mean"], 0.0)
    if not np.isfinite([raw, prediction]).all():
        raise ValueError("O modelo produziu uma previsão não finita.")
    result = {
        "model_run_id": metadata["run_id"],
        "forecast_origin": str(origin), "target_time": str(row.at[0, "target_time"]),
        "horizon_hours": horizon, "availability_delay_hours": delay,
        "availability_is_assumed": protocol["availability_is_assumed"],
        "history_end": str(row.at[0, "history_end"]),
        "history_reference_time": str(row.at[0, "history_reference_time"]),
        "prediction": raw, "prediction_mean": prediction,
        "persistence_prediction": float(row.at[0, "lag_1h"]),
        **correction,
        "target_available_at": str(row.at[0, "target_time"] + pd.Timedelta(hours=delay)),
        "target_observed_in_input": bool(
            pd.to_datetime(series["din_instante"]).eq(row.at[0, "target_time"]).any()
        ),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "model_retrained": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    stamp = origin.strftime("%Y%m%dT%H%M%S")
    json_path = output / f"forecast_{stamp}.json"
    with json_path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
    row.to_csv(output / f"features_{stamp}.csv", index=False)
    record = pd.DataFrame([{
        key: result[key] for key in (
            "forecast_origin", "target_time", "prediction", "prediction_mean",
            "target_available_at", "model_run_id"
        )
    }])
    ledger = record if ledger is None else pd.concat([ledger, record], ignore_index=True)
    temporary = ledger_path.with_suffix(".tmp")
    ledger.to_csv(temporary, index=False)
    temporary.replace(ledger_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    print("\nPrevisão salva:", json_path.resolve())
    print("Registro de emissões:", ledger_path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
