"""M05: confere a correção manual e a disponibilidade dos alvos.

Destino: C:\\renewable-forecast-lab\\notebooks\\inspecao_calibracao.py
Lê os relatórios existentes; não treina modelos nem altera os relatórios.
"""
from __future__ import annotations

import argparse
import math
from numbers import Real
from pathlib import Path

import numpy as np
import pandas as pd


TIME_COLUMNS = (
    "latest_fit_label_available_at",
    "calibration_origin_start",
    "latest_calibration_label_available_at",
    "validation_origin_start",
)


def correcao_manual(scores, alpha: float = 0.2) -> tuple[float, int]:
    """Seleciona o escore de ordem k; recusa casos sem correção finita."""
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("scores deve ser um vetor não vazio.")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("scores deve conter apenas valores finitos e não negativos.")
    if isinstance(alpha, (bool, np.bool_)) or not isinstance(alpha, Real):
        raise ValueError("alpha deve ser um número real entre 0 e 1.")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha deve ser um número finito entre 0 e 1.")

    scores_sorted = sorted(values)
    n = len(scores_sorted)
    pos_1based = math.ceil((n + 1) * (1.0 - alpha))
    if pos_1based > n:
        raise ValueError(
            f"Sem correção finita neste protocolo: k={pos_1based} excede n={n}. "
            "Não substitua o escore inexistente pelo máximo observado."
        )
    return float(scores_sorted[pos_1based - 1]), pos_1based


def require_columns(table, columns, filename):
    missing = set(columns) - set(table.columns)
    if missing:
        raise ValueError(f"{filename}: colunas obrigatórias ausentes: {sorted(missing)}")
    if table.empty or table[list(columns)].isna().any().any():
        raise ValueError(f"{filename}: tabela vazia ou campos obrigatórios ausentes.")


def inspect_report(report_dir: Path):
    # Os nomes são o contrato do produtor weather_interval_calibration.py.
    scores = pd.read_csv(report_dir / "calibration_scores.csv")
    folds = pd.read_csv(report_dir / "folds.csv")
    require_columns(scores, ("fold", "score_mwmed", "forecast_origin", "target_available_at"), "calibration_scores.csv")
    require_columns(folds, ("fold", "calibration_rows", "rank_k", "alpha", "expansion_mwmed", *TIME_COLUMNS), "folds.csv")
    if folds.fold.duplicated().any() or scores.duplicated(["fold", "forecast_origin"]).any():
        raise ValueError("Fold repetido no plano ou emissão duplicada na calibração.")
    if set(scores.fold) != set(folds.fold):
        raise ValueError("Os arquivos devem conter os mesmos folds.")

    for table, columns in ((folds, TIME_COLUMNS), (scores, ("forecast_origin", "target_available_at"))):
        for column in columns:
            if any(pd.Timestamp(value).tzinfo is None for value in table[column]):
                raise ValueError(f"{column}: timestamp sem fuso explícito.")
            table[column] = pd.to_datetime(table[column], errors="raise", utc=True)

    rows = []
    for fold in folds.itertuples(index=False):
        part = scores.loc[scores.fold.eq(fold.fold)]
        if len(part) != fold.calibration_rows:
            raise ValueError(f"Fold {fold.fold}: contagem de calibração diverge do plano.")
        manual, rank = correcao_manual(part.score_mwmed, alpha=fold.alpha)
        if rank != fold.rank_k:
            raise ValueError(f"Fold {fold.fold}: posição k diverge do plano.")
        np.testing.assert_allclose(
            manual, fold.expansion_mwmed, rtol=1e-10, atol=1e-10, equal_nan=False,
            err_msg=f"Fold {fold.fold}: correção manual diverge do relatório",
        )
        if part.forecast_origin.min() != fold.calibration_origin_start:
            raise ValueError(f"Fold {fold.fold}: início real da calibração diverge do plano.")
        if part.target_available_at.max() != fold.latest_calibration_label_available_at:
            raise ValueError(f"Fold {fold.fold}: disponibilidade real da calibração diverge do plano.")

        fit_before_calibration = fold.latest_fit_label_available_at < fold.calibration_origin_start
        calibration_before_validation = fold.latest_calibration_label_available_at < fold.validation_origin_start
        if not fit_before_calibration:
            raise ValueError(f"Fold {fold.fold}: alvo de treino indisponível no início da calibração.")
        if not calibration_before_validation:
            raise ValueError(f"Fold {fold.fold}: alvo de calibração indisponível no início da avaliação.")

        rows.append({
            "fold": fold.fold, "n_calibration": len(part),
            "zero_scores": int(part.score_mwmed.eq(0).sum()),
            "rank_k": rank, "manual_expansion": manual,
            "reported_expansion": float(fold.expansion_mwmed),
            "fit_before_calibration": bool(fit_before_calibration),
            "calibration_before_validation": bool(calibration_before_validation),
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-dir", type=Path,
        default=Path(__file__).resolve().parents[1]
        / "reports/probabilistic/CJU_BA5EIGT/h24_d2_july_calibration_v1",
    )
    args = parser.parse_args()
    result = inspect_report(args.report_dir)
    print(result.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\nConferência aprovada: escores, posições e duas fronteiras de disponibilidade.")
    print("A conferência usa o plano exportado; não reexecuta os estimadores.")
    summary = pd.read_csv(args.report_dir / "summary.csv")
    columns = ["method", "coverage_80", "below_lower_rate", "above_upper_rate", "mean_width_mwmed", "interval_score_80"]
    require_columns(summary, columns, "summary.csv")
    print("\nResumo da execução:")
    print(summary[columns].to_string(index=False))


if __name__ == "__main__":
    main()
