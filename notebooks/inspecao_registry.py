"""M06/M01: leitura do registro e base para auditoria autoral com SQL.

Execute na raiz: python notebooks/inspecao_registry.py
Consulta autoral revisada em 09/10/2026; execute com --autoria para auditá-la.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
RUN_ROOT = PROJECT / "reports/registry/CJU_BA5EIGT/h24_event_registry_v1"

# Revisão orientada: uma linha por transição; requisições agregadas por ativação.
# LAG encontra a linha anterior. A diferença de gerações verifica continuidade.
SQL_AUTORAL = """
WITH transitions AS (
    SELECT
        d.*,
        LAG(d.to_version) OVER (
            PARTITION BY d.alias ORDER BY d.generation
        ) AS previous_to_version,
        LAG(d.generation) OVER (
            PARTITION BY d.alias ORDER BY d.generation
        ) AS previous_generation
    FROM deployments AS d
),
successes AS (
    SELECT
        activation_id,
        SUM(CASE WHEN status_code BETWEEN 200 AND 299
                 THEN 1 ELSE 0 END) AS successes_2xx
    FROM requests
    GROUP BY activation_id
)
SELECT
    t.generation,
    t.from_version,
    t.to_version,
    t.previous_to_version,
    CASE
        WHEN t.generation = 1
             AND t.from_version IS NULL
             AND t.previous_generation IS NULL
            THEN 1
        WHEN t.generation = t.previous_generation + 1
             AND t.from_version = t.previous_to_version
            THEN 1
        ELSE 0
    END AS chain_ok,
    COALESCE(s.successes_2xx, 0) AS successes_2xx,
    v.model_sha256
FROM transitions AS t
JOIN versions AS v
    ON v.version_id = t.to_version
LEFT JOIN successes AS s
    ON s.activation_id = t.activation_id
ORDER BY t.alias, t.generation
"""


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def carregar_execucao(run_dir=None):
    pointer = None
    if run_dir is None:
        pointer = json.loads((RUN_ROOT / "latest_run.json").read_text(encoding="utf-8"))
        run_dir = Path(pointer["directory"])
        if not run_dir.is_absolute():
            raise ValueError("O ponteiro deve conter directory absoluto.")
    run_dir = Path(run_dir).resolve()
    manifest_path = run_dir / "verification.json"
    metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not metadata.get("verified") or metadata["run_id"] != run_dir.name:
        raise ValueError("Execução não aprovada ou com run_id incompatível.")
    if pointer and (pointer["run_id"] != metadata["run_id"] or pointer["verification_sha256"] != sha256(manifest_path)):
        raise ValueError("O ponteiro não identifica este manifesto.")
    for name in ("registry/registry.sqlite", "requests.csv", "deployments.csv", "versions.csv"):
        if sha256(run_dir / name) != metadata["output_sha256"][name]:
            raise ValueError(f"Arquivo alterado após o fechamento do exercício: {name}")
    database = run_dir / "registry/registry.sqlite"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as con:
        deployments = pd.read_sql_query("SELECT * FROM deployments ORDER BY generation", con)
        versions = pd.read_sql_query("SELECT * FROM versions ORDER BY version_id", con)
    requests = pd.read_csv(run_dir / "requests.csv")
    # As tabelas lidas do registro passam a uma base temporária em memória.
    memory = sqlite3.connect(":memory:")
    for name, table in (("deployments", deployments), ("versions", versions), ("requests", requests)):
        table.to_sql(name, memory, index=False, if_exists="fail")
    return run_dir, metadata, memory


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--autoria", action="store_true")
    args = parser.parse_args(argv)
    run_dir, metadata, con = carregar_execucao(args.run_dir)
    try:
        if args.autoria:
            if not isinstance(SQL_AUTORAL, str) or not SQL_AUTORAL.strip():
                parser.error("Escreva SQL_AUTORAL neste notebook conforme Aula_M06_Registro_Rollback.md; o modo de inspeção já funciona sem --autoria.")
            result = pd.read_sql_query(SQL_AUTORAL, con)
            required = {"generation", "from_version", "to_version", "previous_to_version", "chain_ok", "successes_2xx", "model_sha256"}
            if set(result.columns) != required or len(result) != 3 or result["generation"].duplicated().any():
                raise ValueError("A consulta deve devolver três gerações únicas e as sete colunas da aula.")
            output = run_dir / "autoria"
            output.mkdir(exist_ok=True)
            result.to_csv(output / "auditoria_transicoes.csv", index=False)
            print(result.to_string(index=False))
            print(f"Consulta executada e saída salva: {output / 'auditoria_transicoes.csv'}")
            print("Formato conferido; correção da consulta e interpretação serão avaliadas pela evidência.")
        else:
            transitions = pd.read_sql_query("SELECT generation,action,from_version,to_version,committed_at FROM deployments ORDER BY generation", con)
            calls = pd.read_sql_query("SELECT step,version_id,generation,status_code,COUNT(*) AS calls FROM requests GROUP BY step,version_id,generation,status_code ORDER BY MIN(sequence)", con)
            print(f"Execução: {metadata['run_id']}")
            print("\nTransições confirmadas no SQLite:")
            print(transitions.to_string(index=False))
            print("\nChamadas HTTP por etapa:")
            print(calls.to_string(index=False))
            for table in ("deployments", "versions", "requests"):
                columns = [row[1] for row in con.execute(f"PRAGMA table_info({table})")]
                print(f"\n{table}: {', '.join(columns)}")
            print("\nConsulta SQL_AUTORAL carregada; use --autoria para gerar a auditoria das transições.")
        print(f"Pasta da execução: {run_dir}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
