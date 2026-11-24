"""M07 — tabela temporal para previsao, com lacunas e disponibilidade explicitas.

Na raiz do projeto: python notebooks/laboratorio_temporal_spark.py
Leia docs/Aula_M07_Laboratorio_Temporal.md. A selecao autoral recebida esta incorporada.
O lancador reutiliza a imagem Spark da aula anterior; a entrada fica somente leitura.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
FEATURES = ("geracao_em_history_end", "media_historico_mwmed")
REVISAO = "20261027-selecao-incorporada"


def completar_horas(horaria):
    """Uma linha por hora, inclusive quando a observacao nao chegou."""
    from pyspark.sql import functions as F

    limites = horaria.agg(F.min("din_instante").alias("inicio"), F.max("din_instante").alias("fim"))
    grade = limites.select(F.explode(F.sequence("inicio", "fim", F.expr("INTERVAL 1 HOUR"))).alias("din_instante"))
    marcada = horaria.withColumn("registro_presente", F.lit(True))
    return grade.join(marcada, "din_instante", "left").fillna(False, subset=["registro_presente"])


def construir_features(grade, horizonte=24, atraso=2, janela=6):
    """Precondicao: grade horaria unica/completa; timestamps no mesmo eixo.

    Na origem o, observacoes ate o-atraso estao disponiveis (fronteira inclusiva).
    Uma media so e utilizavel quando todas as horas da janela tem valor.
    Alvo e disponibilidade do alvo sao metadados; nao pertencem a FEATURES.
    """
    from pyspark.sql import Window, functions as F

    ordem = Window.partitionBy("serie").orderBy("din_instante")
    historico = ordem.rowsBetween(-(atraso + janela - 1), -atraso)
    tabela = (
        grade.withColumn("serie", F.lit("CJU_BA5EIGT"))
        .withColumn("geracao_em_history_end", F.lag("val_geracao", atraso).over(ordem))
        .withColumn("horas_validas_historico", F.count("val_geracao").over(historico))
        .withColumn("media_parcial", F.avg("val_geracao").over(historico))
        .withColumn("media_historico_mwmed", F.when(F.col("horas_validas_historico") == janela, F.col("media_parcial")))
        .withColumn("target_generation", F.lead("val_geracao", horizonte).over(ordem))
        .withColumn("history_end", F.expr(f"din_instante - INTERVAL {atraso} HOURS"))
        .withColumn("target_time", F.expr(f"din_instante + INTERVAL {horizonte} HOURS"))
        .withColumn("target_available_at", F.expr(f"din_instante + INTERVAL {horizonte + atraso} HOURS"))
        .withColumn("features_validas", F.col("geracao_em_history_end").isNotNull() & F.col("media_historico_mwmed").isNotNull())
        .withColumnRenamed("din_instante", "forecast_origin")
    )
    return tabela.select(
        "serie", "forecast_origin", "history_end", "target_time", "target_available_at",
        "registro_presente", *FEATURES, "horas_validas_historico", "features_validas", "target_generation",
    )


def selecionar_treino(tabela, corte):
    """Implementacao autoral recebida: preserva colunas e seleciona linhas elegiveis.

    Regras: features_validas; target_generation preenchido;
    target_available_at ESTRITAMENTE anterior a corte.
    corte e datetime sem fuso, no mesmo eixo dos rotulos da serie.
    Esta funcao so e chamada quando voce informa --corte-treino.
    """
    from pyspark.sql import functions as F

    return tabela.filter(
        F.col("features_validas")
        & F.col("target_generation").isNotNull()
        & (F.col("target_available_at") < F.lit(corte))
    )


def ler_corte(texto):
    """Valida o corte antes de iniciar Spark ou gravar resultados."""
    if texto is None:
        return None
    corte = datetime.fromisoformat(texto)
    if corte.tzinfo is not None:
        raise ValueError("Use corte sem fuso, no mesmo eixo dos rotulos originais; nao foi validada uma conversao UTC.")
    return corte


def validar_entrada(horaria):
    from pyspark.sql import functions as F

    if set(horaria.columns) != {"din_instante", "val_geracao"}:
        raise ValueError("A entrada selecionada deve ter timestamp e geracao.")
    if not horaria.take(1):
        raise ValueError("Serie vazia.")
    invalida = horaria.filter(
        F.col("din_instante").isNull()
        | (F.date_trunc("hour", "din_instante") != F.col("din_instante"))
        | F.isnan("val_geracao") | (F.abs(F.col("val_geracao")) == float("inf"))
    )
    if invalida.take(1):
        raise ValueError("Ha timestamp ausente/fora da hora ou valor NaN/infinito; NULL de geracao e permitido.")
    if horaria.groupBy("din_instante").count().filter("count > 1").take(1):
        raise ValueError("Timestamp duplicado: resolva a origem da duplicidade antes de construir as features.")


def conferir_autoria(tabela, selecionada, corte):
    """Confere a selecao inteira, incluindo a fronteira, sem treinar estimador."""
    from pyspark.sql import functions as F

    referencia = tabela.filter(
        F.col("features_validas") & F.col("target_generation").isNotNull()
        & (F.col("target_available_at") < F.lit(corte))
    )
    if selecionada.columns != tabela.columns:
        raise ValueError("Preserve as colunas da tabela na selecao.")
    if selecionada.exceptAll(referencia).take(1) or referencia.exceptAll(selecionada).take(1):
        raise ValueError("Selecao divergente: confira features, alvo e disponibilidade estrita, inclusive a igualdade ao corte.")
    return selecionada.count()


def escrever_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def contraprovas(spark, output):
    """Dois experimentos identificados como sinteticos; nao alteram a entrada real."""
    from pyspark.sql import Window, functions as F

    inicio = datetime(2026, 1, 1)
    origem = inicio + timedelta(hours=32)
    base = spark.range(80).select(
        F.expr("TIMESTAMP_NTZ '2026-01-01 00:00:00' + id * INTERVAL 1 HOUR").alias("din_instante"),
        (F.col("id") + 100).cast("double").alias("val_geracao"),
    )
    faltante = base.filter(F.col("din_instante") != F.lit(inicio + timedelta(hours=30)))
    ingenua = faltante.withColumn("serie", F.lit("CJU_BA5EIGT")).withColumn(
        "geracao_em_history_end", F.lag("val_geracao", 2).over(Window.partitionBy("serie").orderBy("din_instante")),
    ).filter(F.col("din_instante") == F.lit(origem)).first()
    corrigida = construir_features(completar_horas(faltante)).filter(F.col("forecast_origin") == F.lit(origem)).first()
    lacuna = [
        {"cenario": "sem_grade_horaria", "origem": origem, "valor_usado": ingenua.geracao_em_history_end},
        {"cenario": "com_grade_horaria", "origem": origem, "valor_usado": corrigida.geracao_em_history_end},
    ]
    assert ingenua.geracao_em_history_end == 129.0 and corrigida.geracao_em_history_end is None
    escrever_csv(output / "contraprova_lacuna.csv", lacuna)

    alterada = base.withColumn("val_geracao", F.when(
        F.col("din_instante") > F.lit(origem - timedelta(hours=2)), F.col("val_geracao") + 1000,
    ).otherwise(F.col("val_geracao")))
    resultados = []
    for nome, entrada in (("original", base), ("futuro_alterado", alterada)):
        row = construir_features(completar_horas(entrada)).filter(F.col("forecast_origin") == F.lit(origem)).first()
        resultados.append({"cenario": nome, **{c: row[c] for c in (*FEATURES, "target_generation")}})
    assert all(resultados[0][c] == resultados[1][c] for c in FEATURES)
    assert resultados[0]["target_generation"] == 156.0 and resultados[1]["target_generation"] == 1156.0
    escrever_csv(output / "contraprova_futuro.csv", resultados)
    print("Contraprovas sinteticas: lag sem grade usa 129; com grade preserva NULL. Futuro alterado: features iguais, alvo diferente.", flush=True)


def executar(args):
    corte = ler_corte(args.corte_treino)
    from pyspark.sql import SparkSession, functions as F

    runtime = Path("/tmp/renewcast_temporal")
    runtime.mkdir(parents=True, exist_ok=True)
    spark = (SparkSession.builder.master("local[2]").appName("Renewcast-laboratorio-temporal")
        .config("spark.driver.host", "127.0.0.1").config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.jars.ivy", str(runtime / "ivy"))
        .config("spark.sql.warehouse.dir", (runtime / "warehouse").as_uri())
        .config("spark.sql.session.timeZone", "UTC").config("spark.sql.timestampType", "TIMESTAMP_NTZ")
        .config("spark.sql.shuffle.partitions", str(args.particoes))
        .config("spark.ui.enabled", "false").config("spark.ui.showConsoleProgress", "false").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        original = spark.read.parquet(str(args.input))
        if not {"din_instante", "val_geracao"}.issubset(original.columns):
            raise ValueError("Parquet sem din_instante/val_geracao.")
        tipos = dict(original.dtypes)
        if tipos["din_instante"] not in ("timestamp", "timestamp_ntz"):
            raise ValueError("din_instante deve ser timestamp no Parquet.")
        horaria = original.select(F.col("din_instante").cast("timestamp_ntz"), F.col("val_geracao").cast("double"))
        validar_entrada(horaria)
        grade = completar_horas(horaria)
        tabela = construir_features(grade, args.horizonte, args.atraso, args.janela).cache()
        texto = StringIO()
        with redirect_stdout(texto):
            tabela.explain(mode="formatted")
        medidas = tabela.agg(
            F.count("*").alias("horas_grade"),
            F.sum(F.col("registro_presente").cast("long")).alias("horas_presentes"),
            F.sum(F.col("features_validas").cast("long")).alias("origens_com_features"),
            F.sum((F.col("features_validas") & F.col("target_generation").isNotNull()).cast("long")).alias("linhas_com_features_e_alvo"),
            F.sum(F.col("target_generation").isNull().cast("long")).alias("alvos_sem_valor"),
        ).first().asDict()
        medidas.update({"horizonte": args.horizonte, "atraso": args.atraso, "janela": args.janela,
            "spark_version": spark.version, "particoes_configuradas": args.particoes,
            "semantica_temporal": "rotulos existentes; fuso e intervalo fisico nao verificados",
            "disponibilidade_assumida": True, "modelos_treinados": False})
        selecionada = None
        if corte is not None:
            selecionada = selecionar_treino(tabela, corte)
            medidas["linhas_treino_autoria"] = conferir_autoria(tabela, selecionada, corte)
            medidas["corte_treino"] = corte.isoformat()
            limites = selecionada.agg(
                F.min("forecast_origin").alias("primeira_origem_treino"),
                F.max("forecast_origin").alias("ultima_origem_treino"),
                F.max("target_available_at").alias("ultimo_alvo_disponivel_treino"),
            ).first().asDict()
            medidas.update({nome: valor.isoformat() if valor is not None else None
                            for nome, valor in limites.items()})
        # Confere a selecao antes de substituir qualquer arquivo de resultado.
        contraprovas(spark, args.output_dir)
        (args.output_dir / "plano_temporal.txt").write_text(texto.getvalue(), encoding="utf-8")
        tabela.write.mode("overwrite").parquet(str(args.output_dir / "tabela_features.parquet"))
        escrever_csv(args.output_dir / "amostra.csv", [r.asDict() for r in tabela.orderBy("forecast_origin").limit(36).collect()])
        if selecionada is not None:
            selecionada.write.mode("overwrite").parquet(str(args.output_dir / "treino_autoria.parquet"))
        (args.output_dir / "resumo.json").write_text(json.dumps(medidas, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        print(json.dumps(medidas, indent=2, ensure_ascii=False), flush=True)
    finally:
        spark.stop()


def abrir_docker(args):
    if not shutil.which("docker"):
        raise RuntimeError("Abra o Docker Desktop utilizado na aula anterior.")
    if not args.input.is_file():
        raise FileNotFoundError(f"Serie real nao encontrada: {args.input}")
    receipt = json.loads((args.run_dir / "host_verification.json").read_text(encoding="utf-8"))
    image = receipt.get("image_id", "")
    if receipt.get("verified") is not True or not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("Recibo Spark sem imagem verificada.")
    script = Path(__file__).resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = [script, args.input.resolve(), args.output_dir.resolve()]
    if any("," in str(p) for p in paths):
        raise ValueError("Os caminhos de montagem nao podem conter virgulas.")
    command = ["docker", "run", "--rm", "--pull", "never", "--platform", "linux/amd64",
        "--cpus", "2", "--memory", "3g", "--pids-limit", "512", "--network", "none",
        "--hostname", "renewcast-spark", "--add-host", "renewcast-spark:127.0.0.1",
        "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,nodev,size=512m",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--mount", f"type=bind,source={script},target=/work/aula.py,readonly",
        "--mount", f"type=bind,source={paths[1]},target=/input/geracao.parquet,readonly",
        "--mount", f"type=bind,source={paths[2]},target=/output",
        "--entrypoint", "python", image, "/work/aula.py", "--dentro-container",
        "--input", "/input/geracao.parquet", "--output-dir", "/output",
        "--horizonte", str(args.horizonte), "--atraso", str(args.atraso),
        "--janela", str(args.janela), "--particoes", str(args.particoes)]
    if args.corte_treino:
        command += ["--corte-treino", args.corte_treino]
    print("Serie real, imagem Spark existente e entrada somente leitura. Preparando features temporais...", flush=True)
    subprocess.run(command, check=True)
    print(f"Resultados: {args.output_dir.resolve()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PROJECT / "data/interim/CJU_BA5EIGT_hourly.parquet")
    parser.add_argument("--output-dir", type=Path, default=PROJECT / "reports/scale/CJU_BA5EIGT/laboratorio_temporal")
    parser.add_argument("--run-dir", type=Path, default=PROJECT / "reports/scale/CJU_BA5EIGT/m07_1/20261019T230058Z_cf2fe669")
    parser.add_argument("--horizonte", type=int, default=24)
    parser.add_argument("--atraso", type=int, default=2)
    parser.add_argument("--janela", type=int, default=6)
    parser.add_argument("--particoes", type=int, choices=(2, 4), default=2)
    parser.add_argument("--corte-treino", help="Seleciona o treino por disponibilidade; exemplo: '2026-07-11 06:00:00'.")
    parser.add_argument("--dentro-container", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.horizonte <= 0 or args.atraso < 0 or args.janela <= 0:
        parser.error("Horizonte/janela devem ser positivos; atraso deve ser nao negativo.")
    try:
        ler_corte(args.corte_treino)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Laboratorio temporal: {REVISAO}; selecionar_treino implementada.", flush=True)
    executar(args) if args.dentro_container else abrir_docker(args)


if __name__ == "__main__":
    main()
