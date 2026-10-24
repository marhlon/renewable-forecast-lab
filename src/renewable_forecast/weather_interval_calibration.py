"""M05.1: calibração cronológica de intervalos h24, com expansão CQR.

Destino: src/renewable_forecast/weather_interval_calibration.py.
Treino, calibração e avaliação têm cortes de disponibilidade separados.
Experimento empírico em série temporal; não oferece garantia de cobertura.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

from renewable_forecast.supervised import purged_time_series_splits
from renewable_forecast.weather_ablation import HGB_PARAMS, load_model_frame, sha256


RELEASE = "2026.10.02-interval-calibration-1"
ALPHA = 0.2
QUANTILES = (0.1, 0.5, 0.9)
METHODS = ("hgb_uncalibrated", "hgb_cqr_expansion")


def expansion_threshold(scores, alpha=ALPHA):
    """Retorna o k-ésimo escore, k=ceil((n+1)*(1-alpha)), sem interpolar.

    Escores não negativos tornam esta uma variante que apenas expande.
    O uso deste rank não estabelece intercambialidade dos dados temporais.
    """
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("Escores devem formar um vetor finito e não vazio.")
    if (values < 0).any() or not 0 < alpha < 1:
        raise ValueError("Escores não negativos e alpha entre 0 e 1 são obrigatórios.")
    rank = math.ceil((values.size + 1) * (1 - alpha))
    if rank > values.size:
        raise ValueError("Calibração insuficiente para um limite finito neste nível.")
    return float(np.sort(values)[rank - 1]), rank


def three_way_splits(frame, *, n_splits=3, test_size_hours=168, calibration_size_hours=48):
    """Reserva a cauda elegível para calibrar e purga também treino/calibração."""
    if calibration_size_hours < 1:
        raise ValueError("A janela de calibração deve ser positiva.")
    outer = purged_time_series_splits(frame, n_splits=n_splits, test_size=test_size_hours)
    for fold, (eligible_idx, valid_idx) in enumerate(outer, start=1):
        if len(eligible_idx) <= calibration_size_hours:
            raise ValueError("Faltam dados anteriores para separar treino e calibração.")
        calibration_idx = eligible_idx[-calibration_size_hours:]
        calibration_start = frame.iloc[calibration_idx].forecast_origin.min()
        fitting_idx = eligible_idx[
            (frame.iloc[eligible_idx].target_available_at < calibration_start).to_numpy()
        ]
        if len(fitting_idx) < 40:
            raise ValueError("Menos de 40 linhas no treino após as duas separações temporais.")
        train, calibration, valid = (
            frame.iloc[index] for index in (fitting_idx, calibration_idx, valid_idx)
        )
        valid_start = valid.forecast_origin.min()
        if train.target_available_at.max() >= calibration_start:
            raise ValueError("Um alvo de treino não estava disponível antes da calibração.")
        if calibration.target_available_at.max() >= valid_start:
            raise ValueError("Um alvo de calibração não estava disponível antes da avaliação.")
        if set(fitting_idx) & set(calibration_idx) or set(calibration_idx) & set(valid_idx):
            raise ValueError("Partições sobrepostas.")
        plan = {
            "fold": fold,
            "outer_eligible_rows": len(eligible_idx),
            "fit_rows": len(train), "calibration_rows": len(calibration),
            "validation_rows": len(valid),
            "purged_between_fit_and_calibration": len(eligible_idx) - len(train) - len(calibration),
            "fit_origin_start": train.forecast_origin.min(),
            "fit_origin_end": train.forecast_origin.max(),
            "latest_fit_label_available_at": train.target_available_at.max(),
            "calibration_origin_start": calibration_start,
            "calibration_origin_end": calibration.forecast_origin.max(),
            "latest_calibration_label_available_at": calibration.target_available_at.max(),
            "validation_origin_start": valid_start,
            "validation_origin_end": valid.forecast_origin.max(),
        }
        yield fitting_idx, calibration_idx, valid_idx, plan


def fit_fold(train, calibration, valid, columns):
    """Os mesmos três estimadores preveem calibração e avaliação, sem refit."""
    calibration_raw, validation_raw = [], []
    for tau in QUANTILES:
        params = {**HGB_PARAMS, "loss": "quantile", "quantile": tau}
        estimator = HistGradientBoostingRegressor(**params)
        estimator.fit(train[columns], train.target_generation)
        calibration_raw.append(estimator.predict(calibration[columns]))
        validation_raw.append(estimator.predict(valid[columns]))
    return np.column_stack(calibration_raw), np.column_stack(validation_raw)


def ordered_quantiles(raw):
    values = np.asarray(raw, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3 or not np.isfinite(values).all():
        raise ValueError("O estimador deve produzir três quantis finitos por linha.")
    return np.sort(np.maximum(values, 0.0), axis=1)


def interval_metrics(part):
    y = part.target_generation.to_numpy(dtype=float)
    lower = part.lower_80.to_numpy(dtype=float)
    upper = part.upper_80.to_numpy(dtype=float)
    score = upper - lower + (2 / ALPHA) * (
        np.maximum(lower - y, 0) + np.maximum(y - upper, 0)
    )
    return {
        "rows": len(part),
        "coverage_80": float(((y >= lower) & (y <= upper)).mean()),
        "below_lower_rate": float((y < lower).mean()),
        "above_upper_rate": float((y > upper).mean()),
        "mean_width_mwmed": float((upper - lower).mean()),
        "interval_score_80": float(score.mean()),
        "mae_p50": float(np.abs(y - part.p50.to_numpy()).mean()),
    }


def evaluate_calibration(frame, columns, *, n_splits=3, test_size_hours=168, calibration_size_hours=48):
    predictions, score_tables, plans = [], [], []
    if (frame.target_generation < 0).any():
        raise ValueError("Esta prática pressupõe geração não negativa para aplicar piso zero.")
    splits = three_way_splits(
        frame, n_splits=n_splits, test_size_hours=test_size_hours,
        calibration_size_hours=calibration_size_hours,
    )
    for fit_idx, calibration_idx, valid_idx, plan in splits:
        fold = plan["fold"]
        train, calibration, valid = (frame.iloc[i] for i in (fit_idx, calibration_idx, valid_idx))
        print(
            f"Fold {fold}: ajuste={len(train)}; calibração={len(calibration)}; "
            f"avaliação={len(valid)}; início={plan['validation_origin_start']}", flush=True,
        )
        cal_raw, valid_raw = fit_fold(train, calibration, valid, columns)
        cal_q, valid_q = ordered_quantiles(cal_raw), ordered_quantiles(valid_raw)
        y_cal = calibration.target_generation.to_numpy(dtype=float)
        scores = np.maximum.reduce([cal_q[:, 0] - y_cal, y_cal - cal_q[:, 2], np.zeros(len(calibration))])
        threshold, rank = expansion_threshold(scores)
        plan.update({"alpha": ALPHA, "rank_k": rank, "expansion_mwmed": threshold})
        plans.append(plan)

        cal_table = calibration[["forecast_origin", "target_time", "target_available_at", "target_generation"]].copy()
        cal_table["fold"] = fold
        cal_table["base_p10"], cal_table["base_p50"], cal_table["base_p90"] = cal_q.T
        cal_table["score_mwmed"] = scores
        score_tables.append(cal_table)

        for method in METHODS:
            delta = threshold if method == "hgb_cqr_expansion" else 0.0
            part = valid[["forecast_origin", "target_time", "target_available_at", "target_generation"]].copy()
            part["fold"], part["method"] = fold, method
            for i, name in enumerate(("p10", "p50", "p90")):
                part[f"raw_{name}"] = valid_raw[:, i]
                part[f"base_{name}"] = valid_q[:, i]
            part["raw_quantile_crossing"] = (np.diff(valid_raw, axis=1) < 0).any(axis=1)
            part["expansion_mwmed"] = delta
            part["p50"] = valid_q[:, 1]
            part["lower_80"] = np.maximum(0.0, valid_q[:, 0] - delta)
            part["upper_80"] = valid_q[:, 2] + delta
            part["covered_80"] = part.target_generation.between(part.lower_80, part.upper_80)
            part["width_mwmed"] = part.upper_80 - part.lower_80
            predictions.append(part)
        print(f"  Escore de ordem {rank}/{len(scores)}: expansão={threshold:.4f} MWmed", flush=True)

    predictions = pd.concat(predictions, ignore_index=True)
    fold_metrics = pd.DataFrame([
        {"fold": int(fold), "method": method, **interval_metrics(part)}
        for (fold, method), part in predictions.groupby(["fold", "method"], sort=True)
    ])
    summary = pd.DataFrame([
        {"method": method, **interval_metrics(predictions.loc[predictions.method.eq(method)])}
        for method in METHODS
    ])
    return {
        "predictions.csv": predictions,
        "calibration_scores.csv": pd.concat(score_tables, ignore_index=True),
        "folds.csv": pd.DataFrame(plans), "fold_metrics.csv": fold_metrics,
        "summary.csv": summary,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--calibration-size-hours", type=int, default=48)
    parser.add_argument("--n-splits", type=int, default=3)
    parser.add_argument("--test-size-hours", type=int, default=168)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.n_splits < 2 or min(args.test_size_hours, args.threads, args.calibration_size_hours) < 1:
        parser.error("n-splits >= 2; demais parâmetros inteiros positivos.")
    frame, source = load_model_frame(args.input_dir)
    if source["horizon_hours"] != 24 or source["availability_delay_hours"] != 2:
        raise ValueError("Esta prática exige h24 e atraso assumido de 2 horas.")
    if args.output_dir.resolve() == args.input_dir.resolve():
        raise ValueError("A saída deve ser diferente da entrada.")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError("A saída já contém arquivos. Preserve-a e use outro diretório para nova execução.")
    # Verifica se todas as partições são viáveis antes de iniciar os nove ajustes.
    list(three_way_splits(frame, n_splits=args.n_splits, test_size_hours=args.test_size_hours,
                         calibration_size_hours=args.calibration_size_hours))
    expansion_threshold(np.zeros(args.calibration_size_hours))
    protocol = {
        "release": RELEASE, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "exploratory chronological development; not an independent holdout",
        "source_frame_sha256": sha256(args.input_dir / "model_frame.csv"),
        "source_metadata_sha256": sha256(args.input_dir / "metadata.json"),
        "source_dataset": source, "code_sha256": sha256(Path(__file__)),
        "feature_columns": source["model_feature_columns"],
        "quantiles": QUANTILES, "alpha": ALPHA,
        "n_splits": args.n_splits, "test_size_hours": args.test_size_hours,
        "calibration_size_hours": args.calibration_size_hours,
        "partition_rule": "last eligible 48 rows by default calibrate; fit labels < first calibration origin; calibration labels < first validation origin",
        "score": "max(base_p10-y, y-base_p90, 0); expansion-only CQR-inspired variant",
        "rank": "ceil((n_cal+1)*(1-alpha)); kth order statistic; no interpolation",
        "prediction_rule": "same fitted models in calibration and validation; no refit; expansion frozen within validation fold",
        "comparison": "paired raw/expanded bounds from identical models and origins; P50 unchanged; no additional baseline",
        "bounds_meaning": "central interval target 80%; does not impose 10% error in each tail",
        "coverage_guarantee": "none claimed: chronological dependent data do not establish CQR exchangeability assumptions",
        "postprocessing": "floor zero and sort raw quantiles; expanded lower bound floored at zero; nonnegative target domain",
        "estimator_params_by_quantile": {
            str(tau): HistGradientBoostingRegressor(**{**HGB_PARAMS, "loss": "quantile", "quantile": tau}).get_params()
            for tau in QUANTILES
        },
        "parameter_origin": "previous exploratory h6 configuration; no new search; July has been inspected",
        "threads": args.threads, "model_promotion": False,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol_path = args.output_dir / "protocol.json"
    protocol_path.write_text(json.dumps(protocol, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    with threadpool_limits(limits=args.threads):
        tables = evaluate_calibration(
            frame, source["model_feature_columns"], n_splits=args.n_splits,
            test_size_hours=args.test_size_hours, calibration_size_hours=args.calibration_size_hours,
        )
    for name, table in tables.items():
        table.to_csv(args.output_dir / name, index=False)
    metadata = {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_rows": len(frame),
        "validation_origins": int(tables["predictions.csv"].forecast_origin.nunique()),
        "prediction_rows": len(tables["predictions.csv"]), "methods": METHODS,
        "protocol_sha256": sha256(protocol_path),
        "output_sha256": {name: sha256(args.output_dir / name) for name in tables},
        "model_promotion": False,
    }
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print("\nComparação pareada: mesmos modelos, origens e medianas; somente os limites mudam.")
    print(tables["summary.csv"].round(4).to_string(index=False))
    print("\nResultados por fold:")
    print(tables["fold_metrics.csv"].round(4).to_string(index=False))
    print("\nCobertura nominal de 80% é objetivo; não é garantia para esta série temporal.")
    print(f"Arquivos: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
