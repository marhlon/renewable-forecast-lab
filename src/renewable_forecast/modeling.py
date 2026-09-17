from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import os
import mlflow

import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import (
    GridSearchCV,
    TimeSeriesSplit,
)

from renewable_forecast.features import (
    FEATURE_COLUMNS,
    build_feature_frame,
)


# Lista intencional de configurações, não produto cartesiano.
CANDIDATE_GRID = [
    {
        "learning_rate": [0.03],
        "max_iter": [250],
        "max_leaf_nodes": [15],
        "min_samples_leaf": [20],
        "l2_regularization": [1.0],
    },
    {
        "learning_rate": [0.03],
        "max_iter": [250],
        "max_leaf_nodes": [31],
        "min_samples_leaf": [20],
        "l2_regularization": [5.0],
    },
    {
        "learning_rate": [0.05],
        "max_iter": [200],
        "max_leaf_nodes": [15],
        "min_samples_leaf": [20],
        "l2_regularization": [0.0],
    },
    {
        "learning_rate": [0.05],
        "max_iter": [250],
        "max_leaf_nodes": [31],
        "min_samples_leaf": [20],
        "l2_regularization": [1.0],
    },
    {
        "learning_rate": [0.05],
        "max_iter": [250],
        "max_leaf_nodes": [31],
        "min_samples_leaf": [50],
        "l2_regularization": [5.0],
    },
    {
        "learning_rate": [0.10],
        "max_iter": [150],
        "max_leaf_nodes": [15],
        "min_samples_leaf": [20],
        "l2_regularization": [1.0],
    },
    {
        "learning_rate": [0.10],
        "max_iter": [150],
        "max_leaf_nodes": [31],
        "min_samples_leaf": [50],
        "l2_regularization": [5.0],
    },
    {
        "learning_rate": [0.03],
        "max_iter": [250],
        "max_leaf_nodes": [15],
        "min_samples_leaf": [50],
        "l2_regularization": [5.0],
    },
]


def _clipped_prediction(
    estimator: HistGradientBoostingRegressor,
    features: pd.DataFrame,
) -> np.ndarray:
    return np.maximum(
        estimator.predict(features),
        0.0,
    )


def _negative_mae(
    estimator: HistGradientBoostingRegressor,
    features: pd.DataFrame,
    target: pd.Series,
) -> float:
    prediction = _clipped_prediction(estimator, features)
    return -float(np.mean(np.abs(target - prediction)))


def _negative_rmse(
    estimator: HistGradientBoostingRegressor,
    features: pd.DataFrame,
    target: pd.Series,
) -> float:
    prediction = _clipped_prediction(estimator, features)
    return -float(
        np.sqrt(np.mean(np.square(target - prediction)))
    )


def _negative_absolute_bias(
    estimator: HistGradientBoostingRegressor,
    features: pd.DataFrame,
    target: pd.Series,
) -> float:
    prediction = _clipped_prediction(estimator, features)
    bias = np.mean(target - prediction)
    return -float(abs(bias))


def _negative_ramp_mae(
    estimator: HistGradientBoostingRegressor,
    features: pd.DataFrame,
    target: pd.Series,
) -> float:
    prediction = _clipped_prediction(estimator, features)

    ramp_size = np.abs(
        target.to_numpy()
        - features["lag_1h"].to_numpy()
    )

    threshold = np.quantile(ramp_size, 0.90)
    ramp_mask = ramp_size >= threshold

    return -float(
        np.mean(
            np.abs(
                target.to_numpy()[ramp_mask]
                - prediction[ramp_mask]
            )
        )
    )


def _negative_persistence_mae(
    estimator: HistGradientBoostingRegressor,
    features: pd.DataFrame,
    target: pd.Series,
) -> float:
    del estimator

    return -float(
        np.mean(
            np.abs(
                target.to_numpy()
                - features["lag_1h"].to_numpy()
            )
        )
    )


def constrained_refit(cv_results: dict[str, Any]) -> int:
    """Seleciona menor RampMAE sob restrições de MAE e viés."""

    mae = -np.asarray(
        cv_results["mean_test_neg_mae"]
    )

    rmse = -np.asarray(
        cv_results["mean_test_neg_rmse"]
    )

    ramp_mae = -np.asarray(
        cv_results["mean_test_neg_ramp_mae"]
    )

    absolute_bias = -np.asarray(
        cv_results["mean_test_neg_absolute_bias"]
    )

    persistence_mae = -np.asarray(
        cv_results["mean_test_neg_persistence_mae"]
    )

    eligible = (
        (mae <= 1.02 * persistence_mae)
        & (absolute_bias <= 2.0)
    )

    if eligible.any():
        eligible_indices = np.flatnonzero(eligible)

        # np.lexsort usa a última chave como principal.
        ordering = np.lexsort((
            mae[eligible_indices],
            rmse[eligible_indices],
            ramp_mae[eligible_indices],
        ))

        return int(eligible_indices[ordering[0]])

    relative_mae = mae / persistence_mae

    ordering = np.lexsort((
        ramp_mae,
        relative_mae,
    ))

    return int(ordering[0])


def build_temporal_search() -> GridSearchCV:
    """Cria busca temporal com cinco blocos mensais."""

    temporal_cv = TimeSeriesSplit(
        n_splits=5,
        test_size=24 * 28,
    )

    estimator = HistGradientBoostingRegressor(
        random_state=42,
    )

    return GridSearchCV(
        estimator=estimator,
        param_grid=CANDIDATE_GRID,
        scoring={
            "neg_mae": _negative_mae,
            "neg_rmse": _negative_rmse,
            "neg_ramp_mae": _negative_ramp_mae,
            "neg_absolute_bias": _negative_absolute_bias,
            "neg_persistence_mae": (
                _negative_persistence_mae
            ),
        },
        refit=constrained_refit,
        cv=temporal_cv,
        n_jobs=1,
        return_train_score=False,
        error_score="raise",
    )


def _configure_mlflow(experiment: str) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    database_path = repository_root / "mlflow_tracking.db"

    default_tracking_uri = (
        f"sqlite:///{database_path.resolve().as_posix()}"
    )

    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        default_tracking_uri,
    )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)


def _validation_metrics(
    search: GridSearchCV,
) -> dict[str, float]:
    index = search.best_index_
    results = search.cv_results_
    mae = float(
        -results["mean_test_neg_mae"][index]
    )

    absolute_bias = float(
        -results[
            "mean_test_neg_absolute_bias"
        ][index]
    )

    persistence_mae = float(
        -results[
            "mean_test_neg_persistence_mae"
        ][index]
    )

    mae_constraint_satisfied = (
        mae <= 1.02 * persistence_mae
    )

    bias_constraint_satisfied = (
        absolute_bias <= 2.0
    )

    return {
        "validation_mae": float(
            -results["mean_test_neg_mae"][index]
        ),
        "validation_rmse": float(
            -results["mean_test_neg_rmse"][index]
        ),
        "validation_ramp_mae": float(
            -results["mean_test_neg_ramp_mae"][index]
        ),
        "validation_absolute_bias": float(
            -results[
                "mean_test_neg_absolute_bias"
            ][index]
        ),
        "validation_persistence_mae": float(
            -results[
                "mean_test_neg_persistence_mae"
            ][index]
        ),
        "mae_constraint_satisfied": int(
            mae_constraint_satisfied
        ),
        "bias_constraint_satisfied": int(
            bias_constraint_satisfied
        ),
        "selection_approved": int(
            mae_constraint_satisfied
            and bias_constraint_satisfied
        ),
    }


def tune_model(
    input_path: Path,
    output_dir: Path,
    experiment: str,
) -> dict[str, Any]:
    """Seleciona hiperparâmetros no conjunto de desenvolvimento."""

    series = pd.read_parquet(input_path)
    frame = build_feature_frame(series)

    minimum_rows = 5 * 24 * 28 + 1

    if len(frame) < minimum_rows:
        raise ValueError(
            "Dados insuficientes para a validação temporal: "
            f"são necessárias pelo menos {minimum_rows} linhas "
            f"com features; foram encontradas {len(frame)}."
        )

    search = build_temporal_search()

    _configure_mlflow(experiment)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with mlflow.start_run(
        run_name="temporal-constrained-tuning"
    ) as run:
        search.fit(
            frame[FEATURE_COLUMNS],
            frame["val_geracao"],
        )

        best_params = {
            key: value
            for key, value in search.best_params_.items()
        }

        metrics = _validation_metrics(search)

        params_path = output_dir / "best_params.json"
        metrics_path = output_dir / "validation_metrics.json"
        results_path = output_dir / "cv_results.csv"

        params_path.write_text(
            json.dumps(
                best_params,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        metrics_path.write_text(
            json.dumps(
                metrics,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        pd.DataFrame(
            search.cv_results_
        ).to_csv(
            results_path,
            index=False,
        )

        mlflow.log_params({
            f"best_{key}": value
            for key, value in best_params.items()
        })

        mlflow.log_params({
            "cv_type": "TimeSeriesSplit",
            "cv_splits": 5,
            "cv_test_hours": 24 * 28,
            "mae_constraint_ratio": 1.02,
            "absolute_bias_constraint": 2.0,
        })

        mlflow.log_metrics(metrics)
        mlflow.log_artifacts(
            str(output_dir),
            artifact_path="tuning",
        )

        return {
            "run_id": run.info.run_id,
            "best_params": best_params,
            "metrics": metrics,
        }


def train_final_model(
    input_path: Path,
    params_path: Path,
    output_dir: Path,
    experiment: str,
) -> dict[str, Any]:
    """Treina o modelo final em todo o conjunto de desenvolvimento."""

    if not params_path.exists():
        raise FileNotFoundError(
            f"Parâmetros não encontrados: {params_path}. "
            "Execute renewcast tune primeiro."
        )

    model_path = output_dir / "model"

    if model_path.exists():
        raise FileExistsError(
            f"O modelo já existe em {model_path}. "
            "Use outro diretório de versão."
        )

    parameters = json.loads(
        params_path.read_text(encoding="utf-8")
    )

    series = pd.read_parquet(input_path)
    frame = build_feature_frame(series)

    model = HistGradientBoostingRegressor(
        **parameters,
        random_state=42,
    )

    model.fit(
        frame[FEATURE_COLUMNS],
        frame["val_geracao"],
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    input_example = (
        frame[FEATURE_COLUMNS]
        .tail(5)
        .copy()
    )

    mlflow.sklearn.save_model(
        sk_model=model,
        path=str(model_path),
        serialization_format="cloudpickle",
        input_example=input_example,
    )

    metadata = {
        "model_type": "HistGradientBoostingRegressor",
        "horizon_hours": 1,
        "features": FEATURE_COLUMNS,
        "training_rows": len(frame),
        "training_start": str(
            frame["din_instante"].min()
        ),
        "training_end": str(
            frame["din_instante"].max()
        ),
        "parameters": parameters,
        "target": "val_geracao",
    }

    metadata_path = output_dir / "metadata.json"

    _configure_mlflow(experiment)

    with mlflow.start_run(
        run_name="final-development-model"
    ) as run:
        metadata["run_id"] = run.info.run_id

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        mlflow.log_params(parameters)

        mlflow.log_params({
            "horizon_hours": 1,
            "training_rows": len(frame),
        })

        mlflow.sklearn.log_model(
            sk_model=model,
            name="model",
            serialization_format="cloudpickle",
            input_example=input_example,
        )

        mlflow.log_artifact(
            str(metadata_path)
        )

    return metadata


def predict_next(
    model_dir: Path,
    input_path: Path,
) -> dict[str, Any]:
    """Emite uma previsão para a hora seguinte."""

    metadata_path = model_dir / "metadata.json"
    mlflow_model_path = model_dir / "model"

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadados não encontrados: {metadata_path}"
        )

    if not mlflow_model_path.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado: {mlflow_model_path}"
        )

    model = mlflow.sklearn.load_model(
        str(mlflow_model_path)
    )

    series = (
        pd.read_parquet(input_path)
        .sort_values("din_instante")
        .reset_index(drop=True)
    )

    last_timestamp = series["din_instante"].max()
    next_timestamp = (
        last_timestamp + pd.Timedelta(hours=1)
    )

    last_generation = float(
        series.loc[
            series["din_instante"] == last_timestamp,
            "val_geracao",
        ].iloc[-1]
    )

    future_row = pd.DataFrame({
        "din_instante": [next_timestamp],
        "val_geracao": [np.nan],
    })

    extended = pd.concat(
        [
            series[["din_instante", "val_geracao"]],
            future_row,
        ],
        ignore_index=True,
    )

    feature_frame = build_feature_frame(
        extended,
        require_target=False,
    )

    next_features = feature_frame.loc[
        feature_frame["din_instante"] == next_timestamp,
        FEATURE_COLUMNS,
    ]

    if len(next_features) != 1:
        raise ValueError(
            "Não foi possível construir as features futuras."
        )

    model_prediction = float(
        np.maximum(
            model.predict(next_features)[0],
            0.0,
        )
    )

    return {
        "forecast_timestamp": str(next_timestamp),
        "forecast_horizon_hours": 1,
        "model_prediction_mwmed": model_prediction,
        "persistence_prediction_mwmed": last_generation,
        "difference_from_persistence_mwmed": (
            model_prediction - last_generation
        ),
    }
