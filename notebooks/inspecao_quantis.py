"""M05: recalcula a pinball por método e confere o relatório existente.

Destino: C:\\renewable-forecast-lab\\notebooks\\inspecao_quantis.py
"""
from pathlib import Path
import argparse

import numpy as np
import pandas as pd


QUANTILES = ((0.1, "p10"), (0.5, "p50"), (0.9, "p90"))


def pinball_manual(y, prediction, tau: float) -> float:
    """Preserva a fórmula implementada pelo aluno e valida seu domínio."""
    y = np.asarray(y, dtype=float)
    q_hat = np.asarray(prediction, dtype=float)
    if y.ndim != 1 or q_hat.shape != y.shape or y.size == 0:
        raise ValueError("y e prediction devem ser vetores não vazios do mesmo tamanho.")
    if not np.isfinite(y).all() or not np.isfinite(q_hat).all():
        raise ValueError("Valores observados e previstos devem ser finitos.")
    if not np.isfinite(tau) or not 0 < tau < 1:
        raise ValueError("tau deve estar estritamente entre 0 e 1.")
    r = y - q_hat
    loss = np.maximum(tau * r, (tau - 1.0) * r)
    return float(np.mean(loss))


def inspect_report(report_dir: Path) -> pd.DataFrame:
    predictions = pd.read_csv(report_dir / "predictions.csv")
    summary = pd.read_csv(report_dir / "summary.csv")
    metric_columns = [f"pinball_{name}" for _, name in QUANTILES] + ["mean_pinball"]
    contracts = (
        ("predictions.csv", predictions, {"method", "target_generation", "p10", "p50", "p90"}),
        ("summary.csv", summary, {"method", "rows", *metric_columns}),
    )
    for name, table, required in contracts:
        missing = required - set(table.columns)
        if missing:
            raise ValueError(f"{name}: colunas obrigatórias ausentes: {sorted(missing)}")
        if table.empty or table["method"].isna().any():
            raise ValueError(f"{name}: relatório vazio ou método ausente.")
    if summary["method"].duplicated().any():
        raise ValueError("summary.csv deve ter uma linha por método.")
    if set(predictions["method"]) != set(summary["method"]):
        raise ValueError("Os dois relatórios devem conter os mesmos métodos.")

    reference = summary.set_index("method")
    rows = []
    for method, part in predictions.groupby("method", sort=True):
        values = {
            f"pinball_{column}": pinball_manual(part["target_generation"], part[column], tau)
            for tau, column in QUANTILES
        }
        values["mean_pinball"] = float(np.mean(list(values.values())))
        if len(part) != reference.loc[method, "rows"]:
            raise ValueError(f"Contagem de previsões difere do resumo para {method}.")
        calculated = np.array([values[name] for name in metric_columns])
        official = reference.loc[method, metric_columns].to_numpy(dtype=float)
        np.testing.assert_allclose(
            calculated, official, rtol=1e-10, atol=1e-10, equal_nan=False,
            err_msg=f"Perda manual difere do relatório para {method}",
        )
        rows.append({
            "method": method, "rows": len(part), **values,
            "max_absolute_difference": float(np.max(np.abs(calculated - official))),
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-dir", type=Path,
        default=Path(__file__).resolve().parents[1]
        / "reports/probabilistic/CJU_BA5EIGT/h24_d2_july_quantiles_v1",
    )
    args = parser.parse_args()
    comparison = inspect_report(args.report_dir)
    print("Perdas recalculadas com NumPy, separadamente por método:")
    print(comparison.to_string(index=False, float_format=lambda v: f"{v:.10f}"))
    print("Conferência aprovada: as quatro métricas de cada método coincidem com summary.csv.")


if __name__ == "__main__":
    main()
