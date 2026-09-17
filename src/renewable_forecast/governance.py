from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def _improvement_pct(baseline: float, candidate: float) -> float:
    if baseline == 0:
        return 0.0 if candidate == 0 else float("-inf")
    return (baseline - candidate) / baseline * 100.0


def _bootstrap_mean_ci(
    values: np.ndarray,
    *,
    samples: int,
    seed: int,
) -> tuple[float, float]:
    if samples < 1:
        raise ValueError("samples deve ser maior que zero.")
    if values.size == 0:
        raise ValueError("Não há ganhos por fold para calcular estabilidade.")
    if values.size == 1:
        value = float(values[0])
        return value, value

    rng = np.random.default_rng(seed)
    indexes = rng.integers(0, values.size, size=(samples, values.size))
    means = values[indexes].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def evaluate_candidate(
    summary: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    *,
    candidate_model: str,
    baseline_model: str = "persistence_1h",
    mae_tolerance: float = 0.02,
    max_absolute_bias: float = 2.0,
    min_rmse_improvement_pct: float = 5.0,
    min_ramp_improvement_pct: float = 20.0,
    min_win_rate_pct: float = 60.0,
    bootstrap_samples: int = 5000,
    seed: int = 42,
) -> dict[str, object]:
    indexed = summary.set_index("model")
    missing = {candidate_model, baseline_model} - set(indexed.index)
    if missing:
        raise ValueError(f"Modelos ausentes no resumo: {sorted(missing)}")

    candidate = indexed.loc[candidate_model]
    baseline = indexed.loc[baseline_model]
    if isinstance(candidate, pd.DataFrame) or isinstance(baseline, pd.DataFrame):
        raise ValueError("O resumo possui modelos duplicados.")

    fold_mae = (
        fold_metrics[fold_metrics["model"].isin([candidate_model, baseline_model])]
        .pivot(index="fold", columns="model", values="mae")
        .dropna()
    )
    if fold_mae.empty:
        raise ValueError("Não há folds comparáveis entre candidato e baseline.")

    gains = (
        fold_mae[baseline_model] - fold_mae[candidate_model]
    ).to_numpy(dtype=float)
    ci_low, ci_high = _bootstrap_mean_ci(
        gains,
        samples=bootstrap_samples,
        seed=seed,
    )
    win_rate = float(np.mean(gains > 0) * 100.0)

    rmse_improvement = _improvement_pct(
        float(baseline["rmse"]),
        float(candidate["rmse"]),
    )
    ramp_improvement = _improvement_pct(
        float(baseline["ramp_mae"]),
        float(candidate["ramp_mae"]),
    )

    checks = {
        "mae_within_tolerance": bool(
            float(candidate["mae"])
            <= float(baseline["mae"]) * (1.0 + mae_tolerance)
        ),
        "absolute_bias_within_limit": bool(
            abs(float(candidate["bias"])) <= max_absolute_bias
        ),
        "rmse_improvement_sufficient": bool(
            rmse_improvement >= min_rmse_improvement_pct
        ),
        "ramp_mae_improvement_sufficient": bool(
            ramp_improvement >= min_ramp_improvement_pct
        ),
        "fold_win_rate_sufficient": bool(win_rate >= min_win_rate_pct),
        "mae_gain_ci_above_zero": bool(ci_low > 0.0),
    }
    shadow_gate_names = (
        "mae_within_tolerance",
        "absolute_bias_within_limit",
        "rmse_improvement_sufficient",
        "ramp_mae_improvement_sufficient",
        "fold_win_rate_sufficient",
    )

    shadow_ready = all(
        checks[name]
        for name in shadow_gate_names
    )

    statistically_superior = checks[
        "mae_gain_ci_above_zero"
    ]

    if not shadow_ready:
        decision = "rejected"
    elif statistically_superior:
        decision = (
            "eligible_for_promotion_pending_holdout"
        )
    else:
        decision = "approved_for_shadow"

    return {
        "evidence_scope": "development_backtest",
        "champion": baseline_model,
        "challenger": candidate_model,
        "decision": decision,
        "shadow_ready": shadow_ready,
        "statistically_superior": statistically_superior,
        "production_ready": False,
        "requires_locked_holdout": True,
        "checks": checks,
        "metrics": {
            "candidate_mae": float(candidate["mae"]),
            "baseline_mae": float(baseline["mae"]),
            "candidate_bias": float(candidate["bias"]),
            "rmse_improvement_pct": rmse_improvement,
            "ramp_mae_improvement_pct": ramp_improvement,
            "fold_win_rate_pct": win_rate,
            "mean_fold_mae_gain": float(gains.mean()),
            "mae_gain_ci_low": ci_low,
            "mae_gain_ci_high": ci_high,
        },
        "thresholds": {
            "mae_tolerance": mae_tolerance,
            "max_absolute_bias": max_absolute_bias,
            "min_rmse_improvement_pct": min_rmse_improvement_pct,
            "min_ramp_improvement_pct": min_ramp_improvement_pct,
            "min_win_rate_pct": min_win_rate_pct,
        },
    }


def _markdown_report(report: dict[str, object]) -> str:
    checks = report["checks"]
    metrics = report["metrics"]
    rows = [
        "# Model governance report",
        "",
        f"- Champion: `{report['champion']}`",
        f"- Challenger: `{report['challenger']}`",
        f"- Decision: **{report['decision']}**",
        f"- Evidence: `{report['evidence_scope']}`",
        f"- Shadow ready: `{report['shadow_ready']}`",
        f"- Statistically superior: `{report['statistically_superior']}`",
        f"- Production ready: `{report['production_ready']}`",
        "",
        "## Gates",
        "",
        "| Gate | Passed |",
        "|---|---:|",
    ]
    rows.extend(
        f"| {name} | {'yes' if passed else 'no'} |"
        for name, passed in checks.items()
    )
    rows.extend(
        [
            "",
            "## Metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
    )
    rows.extend(
        f"| {name} | {value:.6f} |"
        for name, value in metrics.items()
    )
    rows.extend(
        [
            "",
            "> Production promotion is not authorized. A locked chronological "
            "holdout is required before production promotion.",
            "",
        ]
    )
    return "\n".join(rows)


def run_governance(
    *,
    calibration_dir: Path,
    output_dir: Path,
    candidate_model: str = "hist_gradient_boosting_calibrated_mean",
    baseline_model: str = "persistence_1h",
    mae_tolerance: float = 0.02,
    max_absolute_bias: float = 2.0,
    min_rmse_improvement_pct: float = 5.0,
    min_ramp_improvement_pct: float = 20.0,
    min_win_rate_pct: float = 60.0,
    bootstrap_samples: int = 5000,
    seed: int = 42,
) -> dict[str, object]:
    summary = pd.read_csv(calibration_dir / "summary.csv")
    fold_metrics = pd.read_csv(calibration_dir / "fold_metrics.csv")
    report = evaluate_candidate(
        summary,
        fold_metrics,
        candidate_model=candidate_model,
        baseline_model=baseline_model,
        mae_tolerance=mae_tolerance,
        max_absolute_bias=max_absolute_bias,
        min_rmse_improvement_pct=min_rmse_improvement_pct,
        min_ramp_improvement_pct=min_ramp_improvement_pct,
        min_win_rate_pct=min_win_rate_pct,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "promotion_report.json").open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    (output_dir / "promotion_report.md").write_text(
        _markdown_report(report),
        encoding="utf-8",
    )
    return report
