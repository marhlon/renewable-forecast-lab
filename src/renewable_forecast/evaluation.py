from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def compare_with_baseline(
    fold_metrics: pd.DataFrame,
    baseline: str = "persistence_1h",
    bootstrap_iterations: int = 10_000,
    random_state: int = 42,
) -> pd.DataFrame:
    """Compara modelos por fold usando diferenças pareadas."""

    baseline_metrics = (
        fold_metrics.loc[
            fold_metrics["model"] == baseline
        ]
        .set_index("fold")
    )

    if baseline_metrics.empty:
        raise ValueError(
            f"Baseline ausente: {baseline}"
        )

    rng = np.random.default_rng(random_state)
    comparisons = []

    models = sorted(
        set(fold_metrics["model"]) - {baseline}
    )

    for model in models:
        model_metrics = (
            fold_metrics.loc[
                fold_metrics["model"] == model
            ]
            .set_index("fold")
        )

        paired = baseline_metrics.join(
            model_metrics,
            how="inner",
            lsuffix="_baseline",
            rsuffix="_model",
        )

        # Positivo significa que o modelo venceu.
        mae_gain = (
            paired["mae_baseline"]
            - paired["mae_model"]
        )

        rmse_gain = (
            paired["rmse_baseline"]
            - paired["rmse_model"]
        )

        ramp_gain = (
            paired["ramp_mae_baseline"]
            - paired["ramp_mae_model"]
        )

        bootstrap_samples = rng.choice(
            mae_gain.to_numpy(),
            size=(
                bootstrap_iterations,
                len(mae_gain),
            ),
            replace=True,
        )

        bootstrap_means = bootstrap_samples.mean(
            axis=1
        )

        ci_low, ci_high = np.quantile(
            bootstrap_means,
            [0.025, 0.975],
        )

        comparisons.append({
            "model": model,
            "folds": len(paired),
            "fold_wins": int((mae_gain > 0).sum()),
            "fold_losses": int((mae_gain < 0).sum()),
            "win_rate_pct": (
                (mae_gain > 0).mean() * 100
            ),
            "mean_mae_gain": mae_gain.mean(),
            "median_mae_gain": mae_gain.median(),
            "worst_fold_mae_gain": mae_gain.min(),
            "best_fold_mae_gain": mae_gain.max(),
            "mae_gain_ci_low": ci_low,
            "mae_gain_ci_high": ci_high,
            "mean_rmse_gain": rmse_gain.mean(),
            "mean_ramp_mae_gain": ramp_gain.mean(),
        })

    return (
        pd.DataFrame(comparisons)
        .sort_values(
            "mean_mae_gain",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def calculate_monthly_metrics(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula desempenho por mês e modelo."""

    data = predictions.copy()

    data["din_instante"] = pd.to_datetime(
        data["din_instante"]
    )

    data["month"] = (
        data["din_instante"]
        .dt.to_period("M")
        .astype(str)
    )

    records = []

    for (month, model), group in data.groupby(
        ["month", "model"]
    ):
        error = (
            group["actual"]
            - group["prediction"]
        )

        ramp_group = group.loc[group["is_ramp"]]

        records.append({
            "month": month,
            "model": model,
            "observations": len(group),
            "mae": error.abs().mean(),
            "rmse": np.sqrt(
                np.mean(np.square(error))
            ),
            "bias": error.mean(),
            "ramp_observations": len(ramp_group),
            "ramp_mae": (
                (
                    ramp_group["actual"]
                    - ramp_group["prediction"]
                )
                .abs()
                .mean()
                if not ramp_group.empty
                else np.nan
            ),
        })

    return pd.DataFrame(records)


def run_evaluation(
    backtest_dir: Path,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fold_metrics = pd.read_csv(
        backtest_dir / "fold_metrics.csv"
    )

    predictions = pd.read_parquet(
        backtest_dir / "predictions.parquet"
    )

    stability = compare_with_baseline(
        fold_metrics
    )

    monthly = calculate_monthly_metrics(
        predictions
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stability.to_csv(
        output_dir / "stability.csv",
        index=False,
    )

    monthly.to_csv(
        output_dir / "monthly_metrics.csv",
        index=False,
    )

    return stability, monthly