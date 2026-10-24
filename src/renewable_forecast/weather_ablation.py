"""M04: comparação temporal pareada de HGB com e sem meteorologia.

Destino: src/renewable_forecast/weather_ablation.py.
Recebe model_frame.csv + metadata.json de weather_training.
É uma ablação exploratória de desenvolvimento, sem calibração ou novo tuning.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from renewable_forecast.supervised import purged_time_series_splits


# Mesma configuração para os dois grupos de entradas.
# Estes valores vieram do desenvolvimento h+6 anterior, que já incluiu julho.
# Portanto, não interpretar a comparação como um teste final independente.
HGB_PARAMS = {
    "loss": "squared_error",
    "learning_rate": 0.03,
    "max_iter": 250,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 42,
}
METHODS = ["persistence", "hgb_history", "hgb_history_weather"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(y, prediction):
    residual = np.asarray(y, dtype=float) - np.asarray(prediction, dtype=float)
    return {
        "rows": len(residual),
        "mae": float(np.abs(residual).mean()),
        "rmse": float(np.sqrt(np.square(residual).mean())),
        "signed_bias": float(residual.mean()),
    }


def evaluate_ablation(frame, *, historical_features, weather_features, n_splits, test_size_hours):
    """Mesmas linhas/cortes/parâmetros; a única diferença são as cinco entradas.

    Cada estimador é ajustado do zero no início do fold. Seus pesos ficam
    fixos durante o bloco; cada linha usa as entradas da própria emissão.
    delta_absolute_error > 0 significa benefício da meteorologia nessa linha.
    """
    groups = {
        "hgb_history": list(historical_features),
        "hgb_history_weather": [*historical_features, *weather_features],
    }
    prediction_parts, fold_rows, fold_plan = [], [], []
    splits = list(purged_time_series_splits(frame, n_splits=n_splits, test_size=test_size_hours))
    for fold, (train_idx, valid_idx) in enumerate(splits, start=1):
        train, valid = frame.iloc[train_idx], frame.iloc[valid_idx]
        cutoff = valid["forecast_origin"].min()
        latest_label = train["target_available_at"].max()
        if latest_label >= cutoff:
            raise ValueError("Rótulo de treino indisponível no início da validação.")
        fold_plan.append({
            "fold": fold, "train_rows": len(train), "valid_rows": len(valid),
            "train_origin_start": train["forecast_origin"].min(),
            "train_origin_end": train["forecast_origin"].max(),
            "latest_train_label_available_at": latest_label,
            "valid_start": cutoff, "valid_end": valid["forecast_origin"].max(),
        })
        print(f"Fold {fold}: treino={len(train)}; validação={len(valid)}; início={cutoff}", flush=True)
        part = valid[["forecast_origin", "target_time", "target_available_at", "target_generation"]].copy()
        part["fold"] = fold
        part["persistence"] = valid["lag_1h"].to_numpy(dtype=float)
        for method, columns in groups.items():
            model = HistGradientBoostingRegressor(**HGB_PARAMS)
            model.fit(train[columns], train["target_generation"])
            part[method] = np.maximum(model.predict(valid[columns]), 0.0)
        for method in METHODS:
            fold_rows.append({"fold": fold, "method": method, **metrics(part["target_generation"], part[method])})
            part[f"absolute_error_{method}"] = (part["target_generation"] - part[method]).abs()
        part["delta_absolute_error"] = part["absolute_error_hgb_history"] - part["absolute_error_hgb_history_weather"]
        prediction_parts.append(part)

    predictions = pd.concat(prediction_parts, ignore_index=True)
    folds = pd.DataFrame(fold_rows)
    summary = pd.DataFrame([
        {"method": method, **metrics(predictions["target_generation"], predictions[method])}
        for method in METHODS
    ])
    history_mae = float(summary.loc[summary.method.eq("hgb_history"), "mae"].iloc[0])
    persistence_mae = float(summary.loc[summary.method.eq("persistence"), "mae"].iloc[0])
    summary["mae_gain_vs_history_pct"] = 100 * (1 - summary["mae"] / history_mae) if history_mae > 0 else np.nan
    summary["mae_gain_vs_persistence_pct"] = 100 * (1 - summary["mae"] / persistence_mae) if persistence_mae > 0 else np.nan
    summary["mean_absolute_fold_bias"] = summary.method.map(folds.assign(absolute_bias=folds.signed_bias.abs()).groupby("method").absolute_bias.mean())
    return predictions, folds, summary, pd.DataFrame(fold_plan)


def load_model_frame(input_dir):
    csv_path, meta_path = input_dir / "model_frame.csv", input_dir / "metadata.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    if sha256(csv_path) != metadata["output_sha256"]:
        raise ValueError("model_frame.csv difere do hash registrado na junção.")
    history = metadata["historical_feature_columns"]
    weather = metadata["weather_feature_columns"]
    columns = [*history, *weather]
    if len(history) != 27 or len(weather) != 5 or len(set(columns)) != 32:
        raise ValueError("Este experimento exige as 27 entradas existentes e as 5 de vento.")
    if columns != metadata["model_feature_columns"] or "target_generation" in columns:
        raise ValueError("Contrato de X/y inválido.")
    frame = pd.read_csv(csv_path)
    if len(frame) != metadata["rows"] or frame.empty:
        raise ValueError("Tabela vazia ou contagem diferente dos metadados.")
    for column in ["model_row_complete", "weather_complete"]:
        if not pd.api.types.is_bool_dtype(frame[column]) or not frame[column].fillna(False).all():
            raise ValueError("Use uma tabela completa; os dois modelos devem receber as mesmas emissões.")
    time_columns = ["forecast_origin", "target_time", "target_available_at", "history_end", "weather_latest_available_at"]
    for column in time_columns:
        if any(pd.isna(value) or pd.Timestamp(value).tzinfo is None for value in frame[column]):
            raise ValueError(f"{column} exige timestamps preenchidos e com fuso.")
        frame[column] = pd.to_datetime(frame[column], errors="raise", utc=True)
    if not frame.forecast_origin.is_unique or not frame.forecast_origin.is_monotonic_increasing:
        raise ValueError("Emissões devem ser únicas e ordenadas.")
    if not frame.forecast_origin.diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError("Este experimento exige emissões horárias contínuas.")
    horizon = pd.Timedelta(hours=metadata["horizon_hours"])
    delay = pd.Timedelta(hours=metadata["availability_delay_hours"])
    if not (frame.target_time - frame.forecast_origin).eq(horizon).all():
        raise ValueError("Horizonte inconsistente.")
    if not (frame.target_time + delay).eq(frame.target_available_at).all():
        raise ValueError("Disponibilidade dos rótulos inconsistente.")
    if not (frame.history_end + delay).eq(frame.forecast_origin).all():
        raise ValueError("Histórico de geração inconsistente.")
    if (frame.weather_latest_available_at > frame.forecast_origin).any():
        raise ValueError("Meteorologia indisponível na emissão.")
    if not np.isfinite(frame[[*columns, "target_generation"]].to_numpy(dtype=float)).all():
        raise ValueError("Entradas e alvos devem ser finitos.")
    return frame, metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--n-splits", type=int, default=3)
    parser.add_argument("--test-size-hours", type=int, required=True)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.threads < 1 or args.test_size_hours < 1 or args.n_splits < 2:
        raise ValueError("Use threads e test-size-hours positivos, n-splits >= 2.")
    if args.input_dir.resolve() == args.output_dir.resolve():
        raise ValueError("A saída do experimento deve ficar em pasta própria.")
    frame, source = load_model_frame(args.input_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "exploratory_development_ablation; not independent final evaluation",
        "source_frame_sha256": source["output_sha256"],
        "source_metadata_sha256": sha256(args.input_dir / "metadata.json"),
        "code_sha256": sha256(Path(__file__)),
        "historical_feature_columns": source["historical_feature_columns"],
        "weather_feature_columns": source["weather_feature_columns"],
        "estimator_params": HistGradientBoostingRegressor(**HGB_PARAMS).get_params(),
        "parameter_origin": "previous h6 development, which already included July; frozen for both arms",
        "n_splits": args.n_splits, "test_size_hours": args.test_size_hours,
        "training_rule": "expanding origin; target_available_at strictly before first validation origin",
        "forecast_schedule": "one forecast per validation origin; model weights fixed within each fold",
        "calibration": "none in either HGB arm",
        "prediction_floor": 0.0,
        "metric_aggregation": "pooled validation rows; mean_absolute_fold_bias is a separate fold statistic",
        "signed_bias_definition": "mean(observed - predicted)",
        "delta_absolute_error_definition": "abs(y - hgb_history) - abs(y - hgb_history_weather)",
        "threads": args.threads,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__},
        "source_dataset": source,
        "model_promotion": False,
    }
    # O protocolo é gravado antes do ajuste e da exibição das métricas.
    (args.output_dir / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False, indent=2), encoding="utf-8")
    with threadpool_limits(limits=args.threads):
        predictions, folds, summary, plan = evaluate_ablation(
            frame, historical_features=source["historical_feature_columns"],
            weather_features=source["weather_feature_columns"],
            n_splits=args.n_splits, test_size_hours=args.test_size_hours,
        )
    outputs = {"predictions.csv": predictions, "fold_metrics.csv": folds, "summary.csv": summary, "folds.csv": plan}
    for filename, table in outputs.items():
        table.to_csv(args.output_dir / filename, index=False)
    metadata = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_rows": len(frame), "validation_rows": len(predictions),
        "protocol_sha256": sha256(args.output_dir / "protocol.json"),
        "output_sha256": {filename: sha256(args.output_dir / filename) for filename in outputs},
        "scope": protocol["scope"], "model_promotion": False,
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nResumo: métricas calculadas sobre todas as previsões de validação.")
    print(summary.round(4).to_string(index=False))
    print("\nMAE por fold:")
    print(folds.pivot(index="fold", columns="method", values="mae").round(4).to_string())
    print(f"\nDelta médio do erro absoluto (positivo favorece vento): {predictions.delta_absolute_error.mean():.4f} MWmed")
    print("Escopo: exploração no desenvolvimento, condicionada às hipóteses temporais do dataset.")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
