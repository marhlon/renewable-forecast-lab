"""M06.2/M01: consultar o registro do lote, sem alterar o banco.

python notebooks/inspecao_lote_sql.py
python notebooks/inspecao_lote_sql.py --autoria
"""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
DB = PROJECT / "reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite"

# Consulta entregue: LEFT JOIN conserva previsões com ou sem avaliação.
SQL_INSPECAO = """
SELECT p.forecast_origin, p.target_time, p.target_available_at,
       ROUND(p.p_event, 6) AS p_event, p.alarm,
       a.status, a.target_generation, a.event_drop, a.cost
FROM predictions AS p
LEFT JOIN assessments AS a
  ON a.forecast_origin = p.forecast_origin AND a.as_of = ?
ORDER BY p.forecast_origin
"""

# Tarefa: preencher somente esta consulta. Não mudar a infraestrutura.
# Deve retornar uma linha por as_of, com as colunas abaixo:
# as_of, observed, pending, fn, cost_total.
# observed: status='observed'; pending: status!='observed'.
# fn: status='observed' AND p.alarm=0 AND a.event_drop=1.
# cost_total: soma de a.cost (NULL significa que a avaliação não existe).
# Use JOIN, GROUP BY, SUM e CASE WHEN; não preencha ausentes como eventos zero.
SQL_AUTORAL = """
WITH assessment_scenario AS (
    SELECT
        as_of,
        forecast_origin,
        CASE
            WHEN forecast_origin = '2026-07-31T06:00:00Z'
                THEN 'missing_observation'
            ELSE status
        END AS status,
        CASE
            WHEN forecast_origin = '2026-07-31T06:00:00Z'
                THEN NULL
            ELSE event_drop
        END AS event_drop,
        CASE
            WHEN forecast_origin = '2026-07-31T06:00:00Z'
                THEN NULL
            ELSE brier
        END AS brier,
        CASE
            WHEN forecast_origin = '2026-07-31T06:00:00Z'
                THEN NULL
            ELSE cost
        END AS cost
    FROM assessments
)
SELECT a.as_of,
       SUM(CASE WHEN a.status='observed' THEN 1 ELSE 0 END) AS observed,
       SUM(CASE WHEN a.status!='observed' THEN 1 ELSE 0 END) AS pending,
       SUM(CASE WHEN a.status='observed' AND p.alarm=0 AND a.event_drop=1 THEN 1 ELSE 0 END) AS fn,
       SUM(a.cost) AS cost_total,
       SUM(CASE WHEN a.status='awaiting_label' THEN 1 ELSE 0 END) AS awaiting_label,
       SUM(CASE WHEN a.status='missing_observation' THEN 1 ELSE 0 END) AS missing_observation,
       ROUND(AVG(a.brier), 6) AS brier_observed,
       ROUND(SUM(a.cost) / NULLIF(1.0 * SUM(CASE WHEN a.status='observed' THEN 1 ELSE 0 END), 0), 6) AS cost_per_observed,
       (CASE WHEN SUM(CASE WHEN a.status='missing_observation' THEN 1 ELSE 0 END) >= 1 THEN 'investigate' ELSE 'OK' END) AS data_status
FROM assessment_scenario AS a
JOIN predictions AS p
  ON a.forecast_origin = p.forecast_origin
GROUP BY a.as_of
ORDER BY a.as_of
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--as-of", default="2026-08-01T12:00:00Z")
    parser.add_argument("--autoria", action="store_true")
    args = parser.parse_args()
    if not args.db.is_file():
        raise FileNotFoundError(f"Execute o lote primeiro: {args.db}")
    con = sqlite3.connect(args.db.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        if args.autoria:
            if not SQL_AUTORAL.strip():
                raise NotImplementedError("Preencha SQL_AUTORAL conforme as instruções acima.")
            result = pd.read_sql_query(SQL_AUTORAL, con)
            required = {"as_of", "observed", "pending", "fn", "cost_total"}
            if not required.issubset(result.columns):
                raise ValueError(f"Faltam colunas: {sorted(required - set(result.columns))}")
            print(result.to_string(index=False))
        else:
            print(pd.read_sql_query(SQL_INSPECAO, con, params=(args.as_of,)).to_string(index=False))
    finally:
        con.close()


if __name__ == "__main__":
    main()
