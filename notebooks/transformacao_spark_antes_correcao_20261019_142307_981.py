"""M07.1 — autoria do aluno; editável sem reconstruir a imagem Docker.

1. Preencha SQL_AUTORAL usando as views geracao_horaria e calendario_dias.
2. Implemente classificar_cobertura com expressões PySpark nativas.
3. Execute: python scripts/executar_m07_spark.py --autoria

Leia docs/Aula_M07_1_Spark_DuckDB.md. Não execute este arquivo diretamente.
"""
from pyspark.sql import functions as F


# A view geracao_horaria tem: din_instante TIMESTAMP_NTZ, val_geracao DOUBLE.
# A view calendario_dias tem: dia DATE (todas as datas, inclusive as sem linhas).
# Retorne exatamente, nesta ordem ou em outra:
# dia, horas_esperadas, horas_presentes, horas_validas, horas_nulas,
# horas_ausentes, cobertura, geracao_media_mwmed, geracao_min_mwmed,
# geracao_max_mwmed.
# Dica: primeiro agregue a geração; depois faça LEFT JOIN partindo do calendário.
# Só as contagens ausentes recebem zero; as três estatísticas permanecem NULL.
# Para cobertura, divida por CAST(24 AS DOUBLE) para evitar arredondamento DECIMAL.
SQL_AUTORAL = ""  # Substitua por uma consulta SELECT, podendo usar WITH/CTEs.


def classificar_cobertura(diario):
    """Devolva um DataFrame preservando todas as colunas e acrescentando qualidade.

    horas_validas == 24       -> "completo"
    1 <= horas_validas <= 23  -> "parcial"
    horas_validas == 0        -> "sem_dados"

    Use withColumn, F.when e otherwise. Não use collect, toPandas ou UDF.
    A função apenas constrói o plano; a infraestrutura executa a action.
    """
    raise NotImplementedError("Implemente classificar_cobertura conforme o contrato acima.")
