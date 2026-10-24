"""M07.1 — tentativa do aluno com revisão orientada em 19/10/2026.

Mantida a estratégia de agregar após o LEFT JOIN. As contagens distinguem
uma linha horária real com valor nulo da linha sem correspondência do JOIN.
Executar: python scripts/executar_m07_spark.py --autoria
"""
from pyspark.sql import functions as F


SQL_AUTORAL = """
    SELECT
        c.dia,
        24 AS horas_esperadas,
        COUNT(h.din_instante) AS horas_presentes,
        SUM(CASE WHEN h.val_geracao IS NOT NULL THEN 1 ELSE 0 END) AS horas_validas,
        COUNT(h.din_instante) - COUNT(h.val_geracao) AS horas_nulas,
        24 - COUNT(h.din_instante) AS horas_ausentes,
        (SUM(CASE WHEN h.val_geracao IS NOT NULL THEN 1 ELSE 0 END)
            / CAST(24 AS DOUBLE)) AS cobertura,
        AVG(h.val_geracao) AS geracao_media_mwmed,
        MIN(h.val_geracao) AS geracao_min_mwmed,
        MAX(h.val_geracao) AS geracao_max_mwmed
    FROM calendario_dias c
    LEFT JOIN geracao_horaria h ON c.dia = DATE(h.din_instante)
    GROUP BY c.dia
"""


def classificar_cobertura(diario):
    """Preserva a classificação enviada pelo aluno; remove apenas código inacessível."""
    return diario.withColumn(
        "qualidade",
        F.when(F.col("horas_validas") == 24, "completo")
        .when((F.col("horas_validas") >= 1) & (F.col("horas_validas") <= 23), "parcial")
        .when(F.col("horas_validas") == 0, "sem_dados")
        .otherwise(None)
    )
