"""M06: diagnóstico independente da execução HTTP já gravada.

Salvar em notebooks/diagnostico_servico.py. Use --run-dir para uma execução
específica; sem esse argumento, usa exclusivamente latest_run.json.
Não inicia a API, não treina e não modifica os arquivos de entrada.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
RUN_ROOT = PROJECT / "reports/service/CJU_BA5EIGT/h24_event_telemetry_v1"
P95_LIMIT_MS = 250.0
ERROR_LIMIT = 0.01
SOURCE_FILES = ("requests.csv", "summary.csv", "client_requests.csv", "server_requests.jsonl")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encontrar_arquivos_execucao(run_dir: Path | None = None) -> tuple[Path, Path]:
    """Um caminho explícito tem precedência; caminho inválido encerra a execução."""
    pointer = None
    if run_dir is None:
        pointer_path = RUN_ROOT / "latest_run.json"
        if not pointer_path.is_file():
            raise FileNotFoundError(f"Informe --run-dir; ponteiro ausente: {pointer_path}")
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        run_dir = Path(pointer["directory"])
        if not run_dir.is_absolute():
            raise ValueError("latest_run.json deve conter directory absoluto.")
    run_dir = run_dir.resolve()
    for name in ("verification.json", *SOURCE_FILES):
        if not (run_dir / name).is_file():
            raise FileNotFoundError(f"Arquivo necessário ausente: {run_dir / name}")
    verification = run_dir / "verification.json"
    metadata = json.loads(verification.read_text(encoding="utf-8"))
    if run_dir.name != metadata["run_id"]:
        raise ValueError("O nome da pasta difere do run_id do manifesto.")
    if pointer is not None:
        if pointer["run_id"] != metadata["run_id"]:
            raise ValueError("O ponteiro identifica outra execução.")
        if pointer["verification_sha256"] != sha256(verification):
            raise ValueError("verification.json difere do hash registrado no ponteiro.")
    return run_dir / "requests.csv", verification


def verificar_hash(arquivo_csv: Path, arquivo_json: Path) -> str:
    """Compara SHA-256 somente com output_sha256[nome exato do arquivo]."""
    metadata = json.loads(arquivo_json.read_text(encoding="utf-8"))
    expected = metadata["output_sha256"][arquivo_csv.name]
    actual = sha256(arquivo_csv)
    if not isinstance(expected, str) or expected.lower() != actual:
        raise ValueError(f"SHA-256 divergente: {arquivo_csv.name}")
    return actual


def validar_requisicoes(df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
    required = {
        "request_id", "run_id", "phase", "status_code", "duration_ms",
        "client_duration_ms", "fault_injection", "error_type", "p_event",
        "model_sha256", "policy_sha256",
    }
    if required - set(df.columns):
        raise ValueError(f"Colunas ausentes: {sorted(required - set(df.columns))}")
    nonnull = required - {"fault_injection", "error_type", "p_event"}
    if df.empty or df[list(nonnull)].isna().any().any():
        raise ValueError("Requisições vazias ou com campos obrigatórios ausentes.")
    if df["request_id"].duplicated().any():
        raise ValueError("request_id duplicado: a unidade de contagem foi violada.")
    if len(df) != metadata["requests_excluding_warmup"]:
        raise ValueError("Contagem difere do manifesto.")
    for column in ("run_id", "model_sha256", "policy_sha256"):
        if not df[column].eq(metadata[column]).all():
            raise ValueError(f"Identidade divergente: {column}")
    if set(df["phase"]) != {"normal", "invalid_payload", "incident"}:
        raise ValueError("As fases diferem do protocolo deste exercício.")
    df = df.copy()
    for column in ("status_code", "duration_ms", "client_duration_ms"):
        df[column] = pd.to_numeric(df[column], errors="raise")
        if not np.isfinite(df[column]).all():
            raise ValueError(f"Valores não finitos: {column}")
    status = df["status_code"]
    if not ((status % 1 == 0) & (status.between(200, 299) | status.between(400, 599))).all():
        raise ValueError("Status fora das classes 2xx/4xx/5xx deste protocolo.")
    if (df[["duration_ms", "client_duration_ms"]] < 0).any().any():
        raise ValueError("Duração negativa.")
    df["p_event"] = pd.to_numeric(df["p_event"], errors="raise")
    successful = df.loc[status.between(200, 299), "p_event"]
    if not np.isfinite(successful).all() or not successful.between(0, 1).all():
        raise ValueError("Probabilidade inválida em resposta bem-sucedida.")
    return df


def calcular_metricas_por_fase(df: pd.DataFrame) -> pd.DataFrame:
    """Preserva o denominador 2xx + 5xx e a latência restrita aos sucessos."""
    rows = []
    for phase, group in df.groupby("phase", sort=False):
        status = group["status_code"]
        success = status.between(200, 299)
        n2, n4, n5 = int(success.sum()), int(status.between(400, 499).sum()), int(status.between(500, 599).sum())
        eligible = n2 + n5
        durations = group.loc[success, "duration_ms"]
        rate = n5 / eligible if eligible else np.nan
        median = float(np.median(durations)) if n2 else np.nan
        p95 = float(np.percentile(durations, 95)) if n2 else np.nan
        action = (
            "review_service" if rate > ERROR_LIMIT or p95 > P95_LIMIT_MS
            else "inspect_rejections" if not eligible
            else "within_exercise_rule"
        )
        rows.append({
            "phase": phase, "requests": len(group), "success_2xx": n2,
            "rejected_4xx": n4, "failed_5xx": n5, "eligible_requests": eligible,
            "server_error_rate": rate, "rejection_rate": n4 / len(group),
            "median_success_ms": median, "p95_success_ms": p95,
            "slow_successes": int((durations > P95_LIMIT_MS).sum()),
            "p95_client_success_ms": float(np.percentile(group.loc[success, "client_duration_ms"], 95)) if n2 else np.nan,
            "action": action,
        })
    return pd.DataFrame(rows)


def conferir_resumo(calculated: pd.DataFrame, reported: pd.DataFrame) -> list[dict]:
    """Confronta todas as métricas oficiais, tratando NaN como ausência definida."""
    required = set(calculated.columns) - {"rejection_rate"}
    if required - set(reported.columns):
        raise ValueError(f"summary.csv incompleto: {sorted(required - set(reported.columns))}")
    if reported["phase"].duplicated().any() or set(reported["phase"]) != set(calculated["phase"]):
        raise ValueError("Fases incompatíveis em summary.csv.")
    checks = []
    official = reported.set_index("phase")
    for row in calculated.to_dict("records"):
        for metric in sorted(required - {"phase"}):
            actual, expected = row[metric], official.loc[row["phase"], metric]
            passed = actual == expected if metric == "action" else bool(np.isclose(actual, expected, atol=1e-9, rtol=0, equal_nan=True))
            if not passed:
                raise ValueError(f"Divergência: fase={row['phase']}, métrica={metric}, recalculado={actual}, oficial={expected}")
            checks.append({"phase": row["phase"], "metric": metric, "passed": True})
    return checks


def gerar_incidentes(df: pd.DataFrame) -> pd.DataFrame:
    """Mantém os IDs originais; rejeição não é reclassificada como falha do servidor."""
    status = df["status_code"]
    rejection, error = status.between(400, 499), status.between(500, 599)
    slow = status.between(200, 299) & df["duration_ms"].gt(P95_LIMIT_MS)
    incidents = df.loc[rejection | error | slow].copy()
    incidents["tipo_incidente"] = np.select(
        [incidents["status_code"].between(400, 499), incidents["status_code"].between(500, 599)],
        ["rejected_4xx", "failed_5xx"], default="slow_2xx",
    )
    return incidents


def tomar_decisao_fundamentada(metrics: pd.DataFrame, incidents: pd.DataFrame, requests: pd.DataFrame) -> str:
    high_error = metrics.loc[metrics["server_error_rate"] > ERROR_LIMIT]
    high_latency = metrics.loc[metrics["p95_success_ms"] > P95_LIMIT_MS]
    lines = ["# Diagnóstico do exercício HTTP", "", f"Execução: `{requests['run_id'].iloc[0]}`.", ""]
    if not high_error.empty:
        chosen = high_error.sort_values("server_error_rate", ascending=False).iloc[0]
        support = incidents.loc[incidents["phase"].eq(chosen["phase"]) & incidents["tipo_incidente"].eq("failed_5xx")]
        lines += [f"Prioridade: falhas 5xx na fase `{chosen['phase']}`. Taxa {chosen['server_error_rate']:.2%}, acima do limite didático de {ERROR_LIMIT:.2%}.", ""]
        for row in support.to_dict("records"):
            tag = row["fault_injection"] if pd.notna(row["fault_injection"]) else "ausente"
            error_type = row["error_type"] if pd.notna(row["error_type"]) else "não registrado"
            lines.append(f"- `{row['request_id']}`: HTTP {int(row['status_code'])}; {row['duration_ms']:.4f} ms; fault_injection={tag}; error_type={error_type}.")
        injected = not support.empty and support["fault_injection"].eq("error").all()
        lines += ["", (
            "Causa registrada: injeção intencional de resposta HTTP 500 pelo laboratório. O código do exercício produz essa resposta antes de executar o estimador. Não há evidência aqui de exceção não tratada. A ação é registrar a detecção da falha controlada; em uma restauração real, confirmar o comportamento após retirar a injeção. A fase normal é a referência anterior, não uma medição posterior de recuperação."
            if injected else
            "A origem de todas as falhas não está identificada como injeção. Correlacionar os IDs com os logs e localizar a falha antes de propor alteração. HTTP 500 isoladamente não identifica a causa."
        ), ""]
    if not high_latency.empty:
        lines += ["Latência também ultrapassou a regra didática:", ""]
        for row in high_latency.to_dict("records"):
            support = incidents.loc[incidents["phase"].eq(row["phase"]) & incidents["tipo_incidente"].eq("slow_2xx")]
            lines.append(f"- `{row['phase']}`: P95 dos sucessos={row['p95_success_ms']:.6f} ms; {len(support)} sucessos acima de {P95_LIMIT_MS:g} ms.")
            lines.append("  IDs: " + ", ".join(f"`{rid}`" for rid in support["request_id"]) + ".")
            if not support.empty and support["fault_injection"].eq("slow").all():
                lines.append("  Os atrasos têm marcação de injeção `slow`. Esses registros não justificam atribuir o atraso a E/S ou ao modelo.")
        lines.append("")
    if high_error.empty and high_latency.empty:
        lines += ["Nenhuma fase ultrapassou os limites calculáveis. Fases sem chamadas elegíveis permanecem sem avaliação de taxa 5xx e latência de sucesso.", ""]
    good = requests.loc[requests["status_code"].between(200, 299)]
    lines += [
        "## Denominadores e alcance", "",
        "Quando uma fase contém somente rejeições, sem 2xx nem 5xx, a taxa 5xx é 0/0 e fica indefinida. Sem sucessos, mediana e P95 de sucesso também ficam indefinidos. Zero significaria uma medição que não ocorreu.", "",
        f"Foram avaliadas {len(requests)} chamadas, com {len(good)} sucessos e {good['p_event'].nunique()} valor(es) distinto(s) de probabilidade nesses sucessos. As chamadas medidas compartilham as identidades de modelo e política verificadas no manifesto.", "",
        "O exercício repete um pedido histórico. Probabilidades iguais demonstram repetibilidade neste pedido; não demonstram acurácia ou calibração. Falhas HTTP e atrasos não constituem evidência para retreinar o modelo. Não há novos rótulos nem medição de drift nesta inspeção.", "",
        "Esta medição é sequencial, local e com falhas controladas. Não estima uptime, capacidade sob concorrência ou um SLO operacional. Os hashes verificam consistência com o manifesto recebido; não são uma assinatura de autenticidade.", "",
    ]
    return "\n".join(lines)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args(argv)
    request_path, verification_path = encontrar_arquivos_execucao(args.run_dir)
    run_dir = request_path.parent
    metadata = json.loads(verification_path.read_text(encoding="utf-8"))
    if metadata.get("verified") is not True:
        raise ValueError("A execução de origem não foi marcada como verificada.")
    rules = metadata["rules"]
    if rules["status"] != "didactic" or rules["p95_success_limit_ms"] != P95_LIMIT_MS or rules["max_server_error_rate"] != ERROR_LIMIT:
        raise ValueError("Regras diferentes das declaradas nesta inspeção.")
    input_hashes = {name: verificar_hash(run_dir / name, verification_path) for name in SOURCE_FILES}
    input_hashes["verification.json"] = sha256(verification_path)
    requests = validar_requisicoes(pd.read_csv(request_path), metadata)
    metrics = calcular_metricas_por_fase(requests)
    checks = conferir_resumo(metrics, pd.read_csv(run_dir / "summary.csv"))
    incidents = gerar_incidentes(requests)
    decision = tomar_decisao_fundamentada(metrics, incidents, requests)
    if any(sha256(run_dir / name) != value for name, value in input_hashes.items()):
        raise ValueError("Uma entrada mudou durante a leitura; nenhuma saída foi gravada.")

    output = run_dir / "autoria"
    output.mkdir(exist_ok=True)
    metrics.to_csv(output / "diagnostico.csv", index=False, na_rep="NaN")
    incidents.to_csv(output / "incidentes.csv", index=False)
    (output / "decisao.md").write_text(decision, encoding="utf-8")
    audit = {
        "run_id": metadata["run_id"], "passed": True, "source_directory": str(run_dir),
        "source_sha256": input_hashes, "inspection_code_sha256": sha256(Path(__file__)),
        "summary_checks": checks, "absolute_tolerance": 1e-9, "relative_tolerance": 0,
        "request_rows": len(requests), "incident_rows": len(incidents),
        "inputs_preserved": True, "models_retrained": False, "new_http_requests": 0,
        "scope": "Independent recalculation of an existing labelled HTTP exercise",
        "output_sha256": {name: sha256(output / name) for name in ("diagnostico.csv", "incidentes.csv", "decisao.md")},
    }
    (output / "conferencia.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Execução: {metadata['run_id']}; quatro hashes de entrada conferidos.")
    columns = ["phase", "success_2xx", "rejected_4xx", "failed_5xx", "eligible_requests", "server_error_rate", "median_success_ms", "p95_success_ms", "action"]
    print(metrics[columns].round(6).to_string(index=False, na_rep="NaN"))
    print(f"Conferência aprovada: {len(checks)} comparações com summary.csv; {len(incidents)} incidentes.")
    print("NaN = métrica indefinida. A decisão distingue falhas injetadas de causa desconhecida.")
    print(f"Arquivos: {output}")


if __name__ == "__main__":
    main()
