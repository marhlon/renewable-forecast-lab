"""M05: custo de alarmes sobre previsões já produzidas; não treina modelos.

Salvar em notebooks/inspecao_decisoes.py.
Executar na raiz: python notebooks/inspecao_decisoes.py
Entrada opcional: caminho explícito do predictions.csv ou da pasta do experimento.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_DIR / (
    "reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/predictions.csv"
)
METHODS = (
    "historical_frequency", "logistic_weather", "hgb_weather_classifier",
)
THRESHOLDS = (0.2, 0.5)


def avaliar_limiar(y, p, threshold, cost_fp=1.0, cost_fn=4.0) -> dict:
    """Custos por emissão: FP custa cost_fp; FN custa cost_fn; acertos custam zero."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if y.ndim != 1 or p.ndim != 1 or y.shape != p.shape or y.size == 0:
        raise ValueError("y e p devem ser vetores não vazios, de mesmo tamanho.")
    if not np.isfinite(y).all() or not np.isin(y, [0, 1]).all():
        raise ValueError("y deve conter somente rótulos 0/1, sem ausentes.")
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("p deve conter probabilidades finitas entre 0 e 1.")
    params = np.asarray([threshold, cost_fp, cost_fn], dtype=float)
    if not np.isfinite(params).all():
        raise ValueError("Limiar e custos devem ser finitos.")
    threshold, cost_fp, cost_fn = params.tolist()
    if not 0 <= threshold <= 1 or cost_fp < 0 or cost_fn < 0:
        raise ValueError("Limiar deve estar em [0,1]; custos devem ser não negativos.")

    preds = p >= threshold
    tp = int(np.sum(preds & (y == 1)))
    fp = int(np.sum(preds & (y == 0)))
    fn = int(np.sum(~preds & (y == 1)))
    tn = int(np.sum(~preds & (y == 0)))
    cost_total = float(fp * cost_fp + fn * cost_fn)
    return {
        "threshold": threshold, "rows": len(y), "alarms": tp + fp,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": tp / (tp + fp) if tp + fp else np.nan,
        "recall": tp / (tp + fn) if tp + fn else np.nan,
        "cost_total": cost_total, "cost_per_emission": cost_total / len(y),
    }


def carregar_previsoes(path: Path) -> tuple[Path, pd.DataFrame]:
    """Usa exatamente o caminho informado; nunca procura outro experimento."""
    path = path / "predictions.csv" if path.is_dir() else path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    df = pd.read_csv(path)
    required = {"method", "fold", "forecast_origin", "event_drop", "p_event"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV de eventos incompatível; faltam: {sorted(missing)}. Arquivo: {path}")
    if df.empty or df[list(required)].isna().any().any():
        raise ValueError("CSV vazio ou com dados obrigatórios ausentes.")
    if set(df["method"]) != set(METHODS):
        raise ValueError(f"Esta inspeção espera os três métodos: {METHODS}.")
    # O relatório weather_events tem timestamps UTC explícitos.
    origins = df["forecast_origin"].map(pd.Timestamp)
    if any(ts.tzinfo is None for ts in origins):
        raise ValueError("forecast_origin deve informar o fuso horário.")
    df["forecast_origin"] = pd.to_datetime(origins, utc=True, errors="raise")
    if df["forecast_origin"].isna().any():
        raise ValueError("forecast_origin contém timestamps ausentes.")
    fold = pd.to_numeric(df["fold"], errors="raise")
    if not np.isfinite(fold).all() or not ((fold >= 1) & (fold % 1 == 0)).all():
        raise ValueError("fold deve conter inteiros positivos.")
    df["fold"] = fold.astype(int)
    for col in ["event_drop", "p_event"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
    avaliar_limiar(df["event_drop"], df["p_event"], 0.5)
    if df.duplicated(["method", "forecast_origin"]).any():
        raise ValueError("Uma emissão se repete para o mesmo método.")

    # A comparação deve usar as mesmas emissões, folds e rótulos.
    reference = None
    for method in METHODS:
        paired = (
            df.loc[df["method"].eq(method), ["forecast_origin", "fold", "event_drop"]]
            .sort_values("forecast_origin").reset_index(drop=True)
        )
        if reference is not None and not paired.equals(reference):
            raise ValueError("Métodos não compartilham as mesmas emissões, folds e rótulos.")
        reference = paired
    return path, df


def tabela_decisoes(df, cost_fp=1.0, cost_fn=4.0):
    rows = []
    for method in METHODS:
        part = df.loc[df["method"].eq(method)]
        groups = [(str(f), g) for f, g in part.groupby("fold", sort=True)]
        groups.append(("Geral", part))
        for fold, group in groups:
            for threshold in THRESHOLDS:
                result = avaliar_limiar(
                    group["event_drop"], group["p_event"], threshold, cost_fp, cost_fn,
                )
                rows.append({"method": method, "fold": fold, **result})
    return pd.DataFrame(rows)


def trocas_hgb(decisions):
    """Compara apenas as duas regras fixas: custo(0,2) - custo(0,5)."""
    rows = []
    hgb = decisions.loc[decisions["method"].eq("hgb_weather_classifier")]
    for fold, group in hgb.groupby("fold", sort=False):
        low = group.loc[group["threshold"].eq(0.2)].iloc[0]
        high = group.loc[group["threshold"].eq(0.5)].iloc[0]
        extra_fp = int(low["fp"] - high["fp"])
        avoided_fn = int(high["fn"] - low["fn"])
        rows.append({
            "fold": fold, "extra_fp": extra_fp, "avoided_fn": avoided_fn,
            "break_even_cost_fn_over_fp": extra_fp / avoided_fn if avoided_fn else np.nan,
            "delta_cost_at_ratio_4": extra_fp - 4 * avoided_fn,
        })
    return pd.DataFrame(rows)


def selecionar_politica(tabela: pd.DataFrame, max_alarms: int) -> dict:
    """Escolhe uma política candidata sob a capacidade observada no desenvolvimento."""
    if isinstance(max_alarms, bool) or not isinstance(max_alarms, int) or max_alarms < 0:
        raise ValueError("max_alarms deve ser um inteiro não negativo.")
    df_geral = tabela.loc[tabela["fold"].eq("Geral")].copy()
    df_viavel = df_geral.loc[df_geral["alarms"] <= max_alarms]
    if df_viavel.empty:
        raise ValueError(f"Nenhuma regra tem alarms <= {max_alarms} no desenvolvimento.")
    melhor = df_viavel.sort_values(
        by=["cost_total", "alarms", "method", "threshold"],
        ascending=True,
    ).iloc[0]
    return {
        "method": str(melhor["method"]),
        "threshold": float(melhor["threshold"]),
        "alarms": int(melhor["alarms"]),
        "cost_total": float(melhor["cost_total"]),
        "precision": None if pd.isna(melhor["precision"]) else float(melhor["precision"]),
        "recall": None if pd.isna(melhor["recall"]) else float(melhor["recall"]),
    }


def conferir_contrato_exportacao(path: Path, df: pd.DataFrame) -> None:
    """Vincula policy.json ao experimento de eventos h24/d2 deste conjunto."""
    protocol_path = path.parent / "protocol.json"
    metadata_path = path.parent / "metadata.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if metadata["output_sha256"]["predictions.csv"] != sha(path):
        raise ValueError("Hash de predictions.csv difere do experimento de eventos.")
    if metadata["protocol_sha256"] != sha(protocol_path):
        raise ValueError("Hash do protocolo difere do experimento de eventos.")
    source = protocol["source_dataset"]
    if (source["conjunto"], source["horizon_hours"], source["availability_delay_hours"], protocol["drop_mw"]) != ("CJU_BA5EIGT", 24, 2, 22.77):
        raise ValueError("A exportação exige CJU_BA5EIGT, h24, d2 e queda22,77.")
    target = pd.to_datetime(df["target_time"], utc=True, errors="raise")
    history = pd.to_datetime(df["history_end"], utc=True, errors="raise")
    if not (target - df["forecast_origin"]).eq(pd.Timedelta(hours=24)).all():
        raise ValueError("Alvos incompatíveis com h24.")
    if not (df["forecast_origin"] - history).eq(pd.Timedelta(hours=2)).all():
        raise ValueError("Histórico incompatível com atraso de2h.")
    if not df["drop_threshold_mwmed"].eq(22.77).all():
        raise ValueError("Limiar físico incompatível com a política.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    path, df = carregar_previsoes(args.input)
    conferir_contrato_exportacao(path, df)
    output = args.output_dir or path.parent / "decisions"
    output.mkdir(parents=True, exist_ok=True)

    # O exemplo autoral do aluno: quatro decisões, uma em cada célula.
    toy = avaliar_limiar([1, 0, 1, 0], [.8, .3, .1, .05], .2)
    assert tuple(toy[k] for k in ("tp", "fp", "fn", "tn")) == (1, 1, 1, 1)
    assert toy["cost_total"] == 5.0

    decisions = tabela_decisoes(df)
    policy = selecionar_politica(decisions, max_alarms=120)
    print("Política sob capacidade hipotética:", policy)
    trades = trocas_hgb(decisions)
    # Sensibilidade: regras e probabilidades ficam fixas; só o custo muda.
    sensitivity = pd.concat([
        tabela_decisoes(df, cost_fp=1.0, cost_fn=ratio).assign(cost_fn_over_fp=ratio)
        for ratio in (1.0, 2.0, 4.0, 6.0, 8.0)
    ], ignore_index=True)
    tables = {
        "threshold_metrics.csv": decisions,
        "cost_sensitivity.csv": sensitivity,
        "hgb_tradeoffs.csv": trades,
    }
    for name, table in tables.items():
        table.to_csv(output / name, index=False)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    policy_document = {
        "schema_version": "1.0",
        "policy_id": "CJU_BA5EIGT-h24-d2-drop22p77-cap120-v1",
        "status": "development",
        "conjunto": "CJU_BA5EIGT",
        "horizon_hours": 24,
        "availability_delay_hours": 2,
        "drop_mw": 22.77,
        "event_reference": "last_available_generation",
        "cost_fp": 1.0, "cost_fn": 4.0,
        "max_alarms_on_selection": 120,
        "selection_rows": int(df["forecast_origin"].nunique()),
        "capacity_enforced_at_runtime": False,
        "source_predictions_sha256": sha(path),
        "selected": policy,
    }
    (output / "policy.json").write_text(
        json.dumps(policy_document, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    metadata = {
        "source_predictions": str(path), "source_predictions_sha256": sha(path),
        "inspection_code_sha256": sha(Path(__file__)),
        "thresholds": list(THRESHOLDS), "cost_fp": 1.0, "cost_fn": 4.0,
        "cost_unit": "hypothetical relative unit per hourly decision; not currency",
        "evaluation_scope": "existing exploratory development predictions; no new holdout",
        "probabilities_unchanged": True, "models_retrained": False,
        "operational_policy_approved": False,
        "output_sha256": {name: sha(output / name) for name in [*tables, "policy.json"]},
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8",
    )
    print(f"Lendo dados de: {path}")
    print("\nDecisões: custo = FP + 4*FN; NaN indica razão indefinida.")
    print(decisions.round(6).to_string(index=False))
    print("\nHGB: troca de limiar 0,5 para 0,2; delta negativo reduz custo.")
    print(trades.round(6).to_string(index=False))
    print("\nSensibilidade salva para C_FN/C_FP = 1, 2, 4, 6 e 8.")
    print("Os resultados comparam custos por emissão, não por episódio meteorológico.")
    print(f"Arquivos: {output.resolve()}")


if __name__ == "__main__":
    main()
