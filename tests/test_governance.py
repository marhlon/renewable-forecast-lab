from __future__ import annotations

import pandas as pd

from renewable_forecast.governance import evaluate_candidate


def _summary(candidate_bias: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "model": "persistence_1h",
                "mae": 10.0,
                "rmse": 15.0,
                "bias": 0.0,
                "ramp_mae": 30.0,
            },
            {
                "model": "candidate",
                "mae": 8.0,
                "rmse": 12.0,
                "bias": candidate_bias,
                "ramp_mae": 20.0,
            },
        ]
    )


def _fold_metrics() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"fold": fold, "model": model, "mae": mae}
            for fold in range(1, 6)
            for model, mae in (
                ("persistence_1h", 10.0),
                ("candidate", 8.0),
            )
        ]
    )


def test_governance_marks_superior_candidate_for_holdout() -> None:
    report = evaluate_candidate(
        _summary(candidate_bias=1.0),
        _fold_metrics(),
        candidate_model="candidate",
        bootstrap_samples=1000,
    )

    assert report["decision"] == (
        "eligible_for_promotion_pending_holdout"
    )
    assert report["shadow_ready"] is True
    assert report["statistically_superior"] is True
    assert report["production_ready"] is False
    assert report["requires_locked_holdout"] is True


def test_governance_distinguishes_shadow_from_rejection() -> None:
    uncertain_folds = pd.DataFrame(
        [
            {"fold": fold, "model": model, "mae": mae}
            for fold, candidate_mae in enumerate(
                (9.0, 9.0, 9.0, 11.0, 11.0),
                start=1,
            )
            for model, mae in (
                ("persistence_1h", 10.0),
                ("candidate", candidate_mae),
            )
        ]
    )
    shadow_report = evaluate_candidate(
        _summary(candidate_bias=1.0),
        uncertain_folds,
        candidate_model="candidate",
        bootstrap_samples=1000,
    )

    assert shadow_report["decision"] == "approved_for_shadow"
    assert shadow_report["shadow_ready"] is True
    assert shadow_report["statistically_superior"] is False
    assert shadow_report["production_ready"] is False

    report = evaluate_candidate(
        _summary(candidate_bias=3.0),
        _fold_metrics(),
        candidate_model="candidate",
        bootstrap_samples=1000,
    )

    assert report["decision"] == "rejected"
    assert report["shadow_ready"] is False
    assert (
        report["checks"]["absolute_bias_within_limit"] is False
    )
