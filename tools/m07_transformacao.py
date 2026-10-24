"""M07.1: cobertura diária da série ONS em DuckDB e PySpark.

O contrato preserva os rótulos locais sem fuso; não integra energia nem infere UTC.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import duckdb
import pyspark
from pyspark.sql import SparkSession, functions as F

COLUNAS = ["dia", "horas_esperadas", "horas_presentes", "horas_validas",
           "horas_nulas", "horas_ausentes", "cobertura", "geracao_media_mwmed",
           "geracao_min_mwmed", "geracao_max_mwmed"]
DECIMAIS = {"cobertura", "geracao_media_mwmed", "geracao_min_mwmed", "geracao_max_mwmed"}
SQL_DUCKDB = """
WITH agregado AS (
  SELECT CAST(din_instante AS DATE) AS dia,
         COUNT(*) AS horas_presentes, COUNT(val_geracao) AS horas_validas,
         AVG(val_geracao) AS geracao_media_mwmed,
         MIN(val_geracao) AS geracao_min_mwmed, MAX(val_geracao) AS geracao_max_mwmed
  FROM geracao_horaria GROUP BY CAST(din_instante AS DATE)
)
SELECT c.dia, 24 AS horas_esperadas,
       COALESCE(a.horas_presentes, 0) AS horas_presentes,
       COALESCE(a.horas_validas, 0) AS horas_validas,
       COALESCE(a.horas_presentes, 0) - COALESCE(a.horas_validas, 0) AS horas_nulas,
       24 - COALESCE(a.horas_presentes, 0) AS horas_ausentes,
       COALESCE(a.horas_validas, 0) / CAST(24 AS DOUBLE) AS cobertura,
       a.geracao_media_mwmed, a.geracao_min_mwmed, a.geracao_max_mwmed
FROM calendario_dias c LEFT JOIN agregado a ON c.dia = a.dia
ORDER BY c.dia
"""


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def gravar_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    allow_nan=False) + "\n", encoding="utf-8")


def gravar_csv(path, rows, columns):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def conexao():
    con = duckdb.connect(":memory:")
    con.execute("SET threads=2")
    con.execute("SET memory_limit='512MB'")
    return con


def preparar_entrada(source, destination, conjunto):
    """Valida e grava apenas as duas colunas, em microssegundos, sem mudar o relógio."""
    source, destination = Path(source), Path(destination)
    before = sha(source)
    with conexao() as con:
        con.execute(f"CREATE VIEW original AS SELECT * FROM read_parquet({sql_literal(source)})")
        schema = dict((r[0], r[1]) for r in con.execute("DESCRIBE original").fetchall())
        required = {"din_instante", "val_geracao"}
        if required - schema.keys():
            raise ValueError(f"Colunas ausentes: {sorted(required - schema.keys())}")
        if schema["din_instante"] not in {"TIMESTAMP", "TIMESTAMP_NS", "TIMESTAMP_MS", "TIMESTAMP_S"}:
            raise ValueError("Esta unidade espera timestamp sem fuso, já normalizado. "
                             f"Recebido: {schema['din_instante']}. Não será feita conversão implícita.")
        numeric = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "FLOAT", "DOUBLE",
                   "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT", "UHUGEINT", "DECIMAL")
        if not schema["val_geracao"].startswith(numeric):
            raise ValueError("val_geracao deve possuir tipo numérico; textos não são convertidos silenciosamente.")
        identity_checked = "id_ons_conjunto" in schema
        if identity_checked:
            invalid = con.execute("SELECT COUNT(*) FROM original WHERE id_ons_conjunto IS NULL "
                                  "OR CAST(id_ons_conjunto AS VARCHAR) <> ?", [conjunto]).fetchone()[0]
            if invalid:
                raise ValueError("A série contém conjunto ausente ou diferente do solicitado.")
        n, unique, null_ts, off_hour, nonfinite, null_values, first, last = con.execute("""
          SELECT COUNT(*), COUNT(DISTINCT din_instante),
            COUNT(*) FILTER (WHERE din_instante IS NULL),
            COUNT(*) FILTER (WHERE din_instante <> date_trunc('hour', din_instante)),
            COUNT(*) FILTER (WHERE val_geracao IS NOT NULL AND NOT isfinite(CAST(val_geracao AS DOUBLE))),
            COUNT(*) FILTER (WHERE val_geracao IS NULL), MIN(din_instante), MAX(din_instante)
          FROM original
        """).fetchone()
        if not n or null_ts or n != unique or off_hour or nonfinite:
            raise ValueError(f"Entrada inválida: linhas={n}, timestamps nulos={null_ts}, "
                             f"chaves repetidas={n-unique-null_ts}, fora da hora={off_hour}, "
                             f"geração não finita={nonfinite}.")
        days = (last.date() - first.date()).days + 1
        if days > 3660:
            raise ValueError("Unidade limitada a 3.660 dias para manter a coleta agregada pequena.")
        con.execute(f"COPY (SELECT CAST(din_instante AS TIMESTAMP) AS din_instante, "
                    f"CAST(val_geracao AS DOUBLE) AS val_geracao FROM original) "
                    f"TO {sql_literal(destination)} (FORMAT PARQUET, COMPRESSION ZSTD)")
    if sha(source) != before:
        raise ValueError("O arquivo de entrada mudou durante a leitura.")
    return {"source_file": str(source.resolve()), "source_sha256": before,
            "source_schema": schema, "rows": n, "null_generation": null_values,
            "first_reference": first.isoformat(), "last_reference": last.isoformat(),
            "first_day": first.date().isoformat(), "last_day": last.date().isoformat(),
            "days": days, "conjunto": conjunto, "identity_checked_in_column": identity_checked,
            "timestamp_semantics": "naive_reference_labels_preserved; no_timezone_conversion",
            "daily_grid": "24 hourly labels per calendar date, including boundary dates",
            "normalized_sha256": sha(destination)}


def calendario(meta):
    start = date.fromisoformat(meta["first_day"])
    return [(start + timedelta(days=i),) for i in range(meta["days"])]


def sessao(partitions):
    if type(partitions) is not int or not 1 <= partitions <= 32:
        raise ValueError("shuffle_partitions deve ser inteiro de 1 a 32.")
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    # A biblioteca nativa Zstd é extraída para o temporário e carregada pelo Java.
    # Recusar noexec aqui evita uma pilha Java longa durante a primeira action.
    temporary_root = Path(tempfile.gettempdir()).resolve()
    if hasattr(os, "statvfs") and hasattr(os, "ST_NOEXEC"):
        noexec = bool(os.statvfs(temporary_root).f_flag & os.ST_NOEXEC)
        print(f"Temporário: {temporary_root}; montagem noexec={noexec}.", flush=True)
        if noexec:
            raise RuntimeError(
                f"O temporário {temporary_root} está montado com noexec. "
                "O codec Zstd precisa carregar sua biblioteca nativa nesse local. "
                "Atualize scripts/executar_m07_spark.py para usar "
                "--tmpfs /tmp:rw,exec,nosuid,nodev,size=512m."
            )
    # A raiz do contêiner é somente leitura. Os caches precisam de um destino
    # absoluto e gravável, independente da descoberta de user.home pelo Java.
    runtime_dir = Path(tempfile.mkdtemp(prefix="renewcast-spark-")).resolve()
    (runtime_dir / "ivy").mkdir()
    (runtime_dir / "warehouse").mkdir()
    spark = (SparkSession.builder.master("local[2]").appName("Renewcast-M07.1")
             .config("spark.driver.memory", "1g")
             .config("spark.driver.host", "127.0.0.1")
             .config("spark.driver.bindAddress", "127.0.0.1")
             .config("spark.jars.ivy", str(runtime_dir / "ivy"))
             .config("spark.sql.warehouse.dir", (runtime_dir / "warehouse").as_uri())
             .config("spark.sql.session.timeZone", "UTC")
             .config("spark.sql.timestampType", "TIMESTAMP_NTZ")
             .config("spark.sql.parquet.inferTimestampNTZ.enabled", "true")
             .config("spark.sql.shuffle.partitions", str(partitions))
             .config("spark.sql.adaptive.enabled", "false")
             .config("spark.ui.enabled", "false")
             .config("spark.ui.showConsoleProgress", "false")
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    print(f"Spark iniciado: {spark.version}; cache Ivy={runtime_dir / 'ivy'}.", flush=True)
    return spark


def diario_dataframe(horaria, dias):
    """Demonstração: expressões nativas, agregação antes do LEFT JOIN."""
    aggregated = (horaria.withColumn("dia", F.to_date("din_instante"))
                  .groupBy("dia").agg(
                      F.count("*").alias("horas_presentes"),
                      F.count("val_geracao").alias("horas_validas"),
                      F.avg("val_geracao").alias("geracao_media_mwmed"),
                      F.min("val_geracao").alias("geracao_min_mwmed"),
                      F.max("val_geracao").alias("geracao_max_mwmed")))
    joined = dias.join(aggregated, "dia", "left").fillna(
        0, subset=["horas_presentes", "horas_validas"])
    return joined.select(
        "dia", F.lit(24).alias("horas_esperadas"), "horas_presentes", "horas_validas",
        (F.col("horas_presentes") - F.col("horas_validas")).alias("horas_nulas"),
        (F.lit(24) - F.col("horas_presentes")).alias("horas_ausentes"),
        (F.col("horas_validas") / F.lit(24.0)).alias("cobertura"),
        "geracao_media_mwmed", "geracao_min_mwmed", "geracao_max_mwmed")


def consultar_duckdb(path, meta, output):
    start = time.perf_counter()
    with conexao() as con:
        con.execute(f"CREATE VIEW geracao_horaria AS SELECT * FROM read_parquet({sql_literal(path)})")
        con.execute("CREATE TABLE calendario_dias(dia DATE)")
        con.executemany("INSERT INTO calendario_dias VALUES (?)", calendario(meta))
        output.joinpath("plano_duckdb.txt").write_text(
            "\n".join(str(r[1]) for r in con.execute("EXPLAIN " + SQL_DUCKDB).fetchall()), encoding="utf-8")
        # Apenas a consulta/fetch das linhas diárias é cronometrada abaixo.
        setup_seconds = time.perf_counter() - start
        start = time.perf_counter()
        rows = [dict(zip(COLUNAS, r)) for r in con.execute(SQL_DUCKDB).fetchall()]
        seconds = time.perf_counter() - start
    return rows, {"engine": "duckdb", "setup_seconds": setup_seconds,
                  "action_seconds": seconds, "daily_rows": len(rows)}


def coletar_spark(frame, meta, output, name):
    if set(frame.columns) != set(COLUNAS) or len(frame.columns) != len(COLUNAS):
        raise ValueError(f"{name}: esperadas exatamente estas colunas: {COLUNAS}")
    # Limita a coleta: só se aceitam linhas diárias, com no máximo 3.660 datas.
    result = frame.select(*COLUNAS).orderBy("dia").limit(meta["days"] + 1)
    plan = io.StringIO()
    with redirect_stdout(plan):
        result.explain(mode="formatted")
    output.joinpath(f"plano_{name}.txt").write_text(plan.getvalue(), encoding="utf-8")
    start = time.perf_counter()
    rows = [r.asDict() for r in result.collect()]
    seconds = time.perf_counter() - start
    if len(rows) != meta["days"]:
        raise ValueError(f"{name}: {len(rows)} linhas; esperadas {meta['days']} datas únicas.")
    return rows, {"engine": name, "action_seconds": seconds, "daily_rows": len(rows)}


def comparar(expected, actual, name):
    if len(expected) != len(actual):
        raise ValueError(f"{name}: número de dias divergente.")
    biggest = 0.0
    for left, right in zip(expected, actual):
        for col in COLUNAS:
            x, y = left[col], right[col]
            if x is None or y is None:
                ok = x is None and y is None
            elif col in DECIMAIS:
                ok = isinstance(y, (int, float, Decimal)) and not isinstance(y, bool) and math.isfinite(y) and math.isclose(x, y, rel_tol=1e-10, abs_tol=1e-8)
                if isinstance(y, (int, float, Decimal)):
                    biggest = max(biggest, abs(float(x) - float(y)))
            else:
                ok = type(x) is type(y) and x == y
            if not ok:
                raise ValueError(f"{name}: dia={left['dia']}, coluna={col}; DuckDB={x!r}, Spark={y!r}")
    return {"comparison": name, "days": len(expected), "passed": True,
            "max_absolute_numeric_difference": biggest, "nulls_and_dates_equal": True}


def carregar_autoria(path):
    spec = importlib.util.spec_from_file_location("m07_autoria_aluno", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not isinstance(module.SQL_AUTORAL, str) or not module.SQL_AUTORAL.strip():
        raise ValueError("Preencha SQL_AUTORAL em notebooks/transformacao_spark.py antes de usar --autoria.")
    return module


def executar_caso(spark, path, meta, output, autoria=None):
    output.mkdir(parents=True, exist_ok=True)
    reference, timing = consultar_duckdb(path, meta, output)
    raw = spark.read.parquet(str(path))
    if raw.schema["din_instante"].dataType.typeName() != "timestamp_ntz":
        raise ValueError("Spark não preservou TIMESTAMP_NTZ; verifique a versão e o Parquet normalizado.")
    # Geração do calendário no próprio motor JVM; não abre workers Python.
    days = spark.range(meta["days"]).select(
        F.date_add(F.lit(date.fromisoformat(meta["first_day"])), F.col("id").cast("int")).alias("dia"))
    raw.createOrReplaceTempView("geracao_horaria")
    days.createOrReplaceTempView("calendario_dias")
    frame = diario_dataframe(raw, days)
    actual, spark_timing = coletar_spark(frame, meta, output, "spark_dataframe")
    checks = [comparar(reference, actual, "duckdb_vs_spark_dataframe")]
    timings = [timing, spark_timing]
    gravar_csv(output / "duckdb_diario.csv", reference, COLUNAS)
    gravar_csv(output / "spark_dataframe_diario.csv", actual, COLUNAS)
    if autoria is not None:
        statements = spark.sql(autoria.SQL_AUTORAL)
        sql_rows, sql_timing = coletar_spark(statements, meta, output, "spark_sql_autoral")
        checks.append(comparar(reference, sql_rows, "duckdb_vs_spark_sql_autoral"))
        timings.append(sql_timing)
        gravar_csv(output / "spark_sql_diario.csv", sql_rows, COLUNAS)
        classified = autoria.classificar_cobertura(frame)
        if set(classified.columns) != set(COLUNAS + ["qualidade"]) or len(classified.columns) != len(COLUNAS) + 1:
            raise ValueError("classificar_cobertura deve preservar as colunas e acrescentar apenas qualidade.")
        rows = [r.asDict() for r in classified.orderBy("dia").limit(meta["days"] + 1).collect()]
        comparar(reference, rows, "classificacao_preserva_dados")
        for row in rows:
            expected = "completo" if row["horas_validas"] == 24 else ("sem_dados" if row["horas_validas"] == 0 else "parcial")
            if row["qualidade"] != expected:
                raise ValueError(f"Classificação divergente em {row['dia']}: esperado {expected}")
        checks.append({"comparison": "classificacao_cobertura", "passed": True, "days": len(rows)})
        gravar_csv(output / "qualidade_diaria.csv", rows, COLUNAS + ["qualidade"])
    gravar_json(output / "comparacao.json", checks)
    gravar_json(output / "tempos.json", timings)
    return {"checks": checks, "timings": timings, "input_partitions": raw.rdd.getNumPartitions(),
            "days": len(reference), "complete_days": sum(r["horas_validas"] == 24 for r in reference),
            "missing_hours": sum(r["horas_ausentes"] for r in reference),
            "null_hours": sum(r["horas_nulas"] for r in reference)}


def preparar_caso_didatico(output):
    """Caso explícito: zero real, nulo, dia ausente, dia todo nulo, dia completo."""
    path = output / "caso_didatico.parquet"
    with conexao() as con:
        con.execute("CREATE TABLE exemplo(din_instante TIMESTAMP, val_geracao DOUBLE)")
        rows = [(datetime(2026, 1, 1, h), value) for h, value in ((0, 0.0), (1, None), (2, 12.0))]
        rows += [(datetime(2026, 1, 3, h), None) for h in range(24)]
        rows += [(datetime(2026, 1, 4, h), 10.0) for h in range(24)]
        con.executemany("INSERT INTO exemplo VALUES (?, ?)", rows)
        con.execute(f"COPY exemplo TO {sql_literal(path)} (FORMAT PARQUET)")
    normalized = output / "caso_normalizado.parquet"
    meta = preparar_entrada(path, normalized, "EXEMPLO_SINTETICO")
    return normalized, meta


def verificar_manual(output):
    # Valores escritos independentemente das implementações.
    expected = [
        [3, 2, 1, 21, 2/24, 6.0, 0.0, 12.0],
        [0, 0, 0, 24, 0.0, None, None, None],
        [24, 0, 24, 0, 0.0, None, None, None],
        [24, 24, 0, 0, 1.0, 10.0, 10.0, 10.0],
    ]
    with (output / "duckdb_diario.csv").open(encoding="utf-8", newline="") as h:
        actual = list(csv.DictReader(h))
    assert len(actual) == 4
    for i, (got, values) in enumerate(zip(actual, expected)):
        assert got["dia"] == f"2026-01-0{i+1}" and got["horas_esperadas"] == "24"
        for col, want in zip(COLUNAS[2:], values):
            assert (got[col] == "") if want is None else math.isclose(float(got[col]), want, abs_tol=1e-10), (col, got[col], want)


def executar(input_path, output, conjunto, partitions, author_path=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "verification.json").exists():
        raise ValueError("Execução já fechada. Utilize uma pasta nova.")
    normalized = output / "entrada_normalizada.parquet"
    meta = preparar_entrada(input_path, normalized, conjunto)
    module = carregar_autoria(author_path) if author_path else None
    print(f"Entrada real: {meta['rows']} linhas; {meta['days']} datas; {meta['null_generation']} valores nulos.", flush=True)
    start = time.perf_counter()
    spark = sessao(partitions)
    startup = time.perf_counter() - start
    startup_details = {"ivy_directory": spark.sparkContext.getConf().get("spark.jars.ivy"),
                       "driver_host": spark.sparkContext.getConf().get("spark.driver.host"),
                       "java_user_name": spark.sparkContext._jvm.java.lang.System.getProperty("user.name"),
                       "java_user_home": spark.sparkContext._jvm.java.lang.System.getProperty("user.home")}
    try:
        real = executar_caso(spark, normalized, meta, output / "real", module)
        edge_path, edge_meta = preparar_caso_didatico(output)
        edge = executar_caso(spark, edge_path, edge_meta, output / "caso_didatico", module)
        verificar_manual(output / "caso_didatico")
    finally:
        spark.stop()
    if sha(input_path) != meta["source_sha256"]:
        raise ValueError("A entrada foi alterada durante o processamento.")
    # Dados intermediários são pequenos e ficam identificados; os originais são somente leitura.
    receipt = {"schema": "renewcast-m07-spark-v1", "verified": True,
               "mode": "autoria" if module else "guiado", "source": meta,
               "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "runtime": {"python": platform.python_version(), "pyspark": pyspark.__version__,
                           "duckdb": duckdb.__version__, "platform": platform.platform(),
                           "java_version": subprocess.run(["java", "-version"], capture_output=True,
                                                          text=True, check=True).stderr.strip()},
               "config": {"master": "local[2]", "shuffle_partitions": partitions,
                          "adaptive_enabled": False, "spark_startup_seconds": startup,
                          "startup_details": startup_details},
               "real": real, "synthetic_edge_case": edge,
               "scope": "local transformation equivalence; not a cluster benchmark or model evaluation",
               "code_sha256": {"m07_transformacao.py": sha(__file__)},
               "author_implementation_executed": module is not None,
               "independent_authorship_not_proven_by_execution": True}
    if author_path:
        receipt["code_sha256"]["transformacao_spark.py"] = sha(author_path)
    receipt["output_sha256"] = {str(p.relative_to(output)).replace(os.sep, "/"): sha(p)
                               for p in sorted(output.rglob("*")) if p.is_file()}
    gravar_json(output / "verification.json", receipt)
    print(f"Conferência aprovada: {real['days']} dias; {real['complete_days']} completos; "
          f"{real['missing_hours']} horas ausentes; {real['null_hours']} nulas.", flush=True)
    print("Caso didático: zero real, nulo, dia ausente, dia todo nulo e dia completo conferidos.")
    print("Autoria SQL/PySpark conferida." if module else "Próxima autoria: notebooks/transformacao_spark.py.")
    print(f"Evidências: {output.resolve()}")
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--conjunto", default="CJU_BA5EIGT")
    parser.add_argument("--shuffle-partitions", type=int, default=2)
    parser.add_argument("--author", type=Path)
    args = parser.parse_args()
    try:
        executar(args.input, args.output, args.conjunto, args.shuffle_partitions, args.author)
    except Exception as exc:
        args.output.mkdir(parents=True, exist_ok=True)
        gravar_json(args.output / "failure.json", {"type": type(exc).__name__, "detail": str(exc)})
        raise
