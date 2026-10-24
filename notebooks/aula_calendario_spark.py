"""M07.1 — calendario, cobertura e plano de execucao da agregacao.

Salvar em: C:/renewable-forecast-lab/notebooks/aula_calendario_spark.py
Executar: python notebooks/aula_calendario_spark.py

O Python local abre a imagem Spark ja usada no projeto. Nao instala pacotes,
nao reconstrui a imagem e nao le os dados reais de geracao.
Saidas em reports/scale/CJU_BA5EIGT/aula_calendario/:
- aula_calendario.csv: as quatro datas e suas classificacoes.
- plano_resumo.txt: plano fisico inicial da agregacao, antes do calendario.
Cada execucao substitui esses dois arquivos didaticos.

ROTEIRO DE LEITURA:
1. priorizar_dias: solucao do aluno, conferida no log de 22/10/2026.
2. montar_diario: transforma registros horarios em indicadores diarios.
3. exportar_plano: mostra como Spark pretende executar essa agregacao.
No plano, procure partial_avg, Exchange/hashpartitioning e a agregacao final.
O plano e inicial: a execucao adaptativa pode modifica-lo durante uma action.
As funcoes abaixo de executar_aula cuidam apenas de abrir o ambiente.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import date, datetime
from io import StringIO
from pathlib import Path


def completar_calendario(dias, resumo):
    """Mantem todas as datas; media desconhecida continua NULL."""
    com_calendario = dias.join(resumo, on="dia", how="left")
    return com_calendario.fillna(
        0, subset=["horas_presentes", "horas_validas"],
    )


def priorizar_dias(diario):
    """Solucao do aluno: prioridade das acoes conferida nos quatro casos.

    Preserve as colunas existentes e acrescente 'acao', nesta ordem:
    horas_presentes == 0 -> 'investigar_coleta'
    horas_validas == 0   -> 'investigar_medicao'
    horas_validas < 24   -> 'revisar_cobertura'
    demais casos        -> 'ok'

    Use withColumn, F.col, F.when e otherwise.
    A ordem importa: um dia sem registros tambem tem zero validas.
    """
    from pyspark.sql import functions as F

    return diario.withColumn(
        "acao",
        F.when(F.col("horas_presentes") == 0, "investigar_coleta")
        .when(F.col("horas_validas") == 0, "investigar_medicao")
        .when(F.col("horas_validas") < 24, "revisar_cobertura")
        .otherwise("ok"),
    )


def montar_diario(horaria, dias):
    """Cada operacao devolve um novo DataFrame; nao altera a entrada."""
    from pyspark.sql import functions as F

    # Extrai a data; o timestamp original continua existindo.
    com_dia = horaria.withColumn("dia", F.to_date("din_instante"))

    # Antes do JOIN, count(*) conta somente registros reais.
    resumo = com_dia.groupBy("dia").agg(
        F.count("*").alias("horas_presentes"),
        F.count("val_geracao").alias("horas_validas"),
        F.avg("val_geracao").alias("geracao_media_mwmed"),
    )
    diario = completar_calendario(dias, resumo)

    # F.col referencia uma coluna; F.lit coloca uma constante na expressao.
    diario = diario.withColumn("horas_esperadas", F.lit(24))
    diario = diario.withColumn(
        "horas_nulas", F.col("horas_presentes") - F.col("horas_validas"),
    )
    diario = diario.withColumn(
        "horas_ausentes", F.col("horas_esperadas") - F.col("horas_presentes"),
    )
    diario = diario.withColumn(
        "cobertura", F.col("horas_validas") / F.col("horas_esperadas"),
    )
    return resumo, diario.select(
        "dia", "horas_esperadas", "horas_presentes", "horas_validas",
        "horas_nulas", "horas_ausentes", "cobertura", "geracao_media_mwmed",
    )


def exportar_plano(resumo):
    """Inspeciona o plano inicial; nao coleta as linhas da agregacao.

    explain imprime o plano. StringIO/redirect_stdout apenas capturam esse
    texto para salva-lo no Windows pelo volume /output do Docker.
    Inspecionamos resumo, antes do JOIN e do orderBy, para isolar o groupBy.
    """
    texto = StringIO()
    with redirect_stdout(texto):
        resumo.explain(mode="formatted")

    plano = texto.getvalue()
    output = Path("/output/plano_resumo.txt")
    output.write_text(
        "Plano inicial da agregacao por dia, antes do JOIN com o calendario.\n"
        "Leitura: siga as entradas ate a agregacao parcial, o Exchange e a final.\n"
        "AQE pode mudar o plano durante a execucao; este arquivo nao e um benchmark.\n\n"
        + plano,
        encoding="utf-8",
    )
    print("\n0. PLANO DA AGREGACAO (antes de pedir as linhas):", flush=True)
    print(plano, flush=True)
    print(f"Plano salvo: {output}", flush=True)


def executar_aula():
    """Executada dentro do container; exemplo explicito de quatro datas."""
    from pyspark.sql import SparkSession

    runtime = Path("/tmp/renewcast_aula")
    runtime.mkdir(parents=True, exist_ok=True)
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("Renewcast-aula-calendario")
        .config("spark.driver.memory", "1g")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.jars.ivy", str(runtime / "ivy"))
        .config("spark.sql.warehouse.dir", (runtime / "warehouse").as_uri())
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.timestampType", "TIMESTAMP_NTZ")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    try:
        # 01/01: seu exemplo corrigido. 02/01: nenhuma linha.
        registros = [(datetime(2026, 1, 1, h), v) for h, v in enumerate((0.0, 6.0, 12.0))]
        # 03/01: 24 linhas com geracao desconhecida. 04/01: 24 valores conhecidos.
        registros += [(datetime(2026, 1, 3, h), None) for h in range(24)]
        registros += [(datetime(2026, 1, 4, h), 10.0) for h in range(24)]
        horaria = spark.createDataFrame(
            registros, "din_instante TIMESTAMP_NTZ, val_geracao DOUBLE",
        )
        dias = spark.createDataFrame(
            [(date(2026, 1, d),) for d in range(1, 5)], "dia DATE",
        )
        resumo, diario = montar_diario(horaria, dias)
        exportar_plano(resumo)
        print("\n1. RESUMO ANTES DO CALENDARIO: 02/01 ainda nao aparece.", flush=True)
        # show solicita resultados: aqui Spark executa o plano necessario.
        resumo.orderBy("dia").show(truncate=False)
        resultado = priorizar_dias(diario).orderBy("dia")

        # Quatro linhas didaticas: trazer esse resultado pequeno ao Python e intencional.
        rows = resultado.collect()
        if len(rows) != 4 or resultado.columns != [*diario.columns, "acao"]:
            raise ValueError("Preserve as quatro linhas e todas as colunas; acrescente somente acao.")
        output = Path("/output/aula_calendario.csv")
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=resultado.columns)
            writer.writeheader()
            writer.writerows(row.asDict() for row in rows)
        print("\n2. CALENDARIO COMPLETO E SUA CLASSIFICACAO:", flush=True)
        for row in rows:
            media = "NULL" if row.geracao_media_mwmed is None else f"{row.geracao_media_mwmed:g}"
            print(f"{row.dia}: presentes={row.horas_presentes}, validas={row.horas_validas}, "
                  f"ausentes={row.horas_ausentes}, media={media}, acao={row.acao}")
        expected = {
            date(2026, 1, 1): "revisar_cobertura",
            date(2026, 1, 2): "investigar_coleta",
            date(2026, 1, 3): "investigar_medicao",
            date(2026, 1, 4): "ok",
        }
        errors = [(str(row.dia), row.acao, expected[row.dia]) for row in rows
                  if row.acao != expected[row.dia]]
        if errors:
            raise ValueError(f"Acoes divergentes (dia, recebido, esperado): {errors}")
        print("\nAtividade conferida: as quatro acoes correspondem aos quatro casos.")
        print("CSV: /output/aula_calendario.csv; media vazia no CSV significa desconhecida.")
    finally:
        spark.stop()


def abrir_ambiente(run_dir=None):
    """Infraestrutura: reutiliza a imagem comprovada; sem build/download."""
    if not shutil.which("docker"):
        raise RuntimeError("Docker nao encontrado. Abra o Docker Desktop usado na etapa M07.1.")
    script = Path(__file__).resolve()
    project = script.parents[1]
    run_dir = Path(run_dir).resolve() if run_dir else project / (
        "reports/scale/CJU_BA5EIGT/m07_1/20261019T230058Z_cf2fe669"
    )
    receipt_path = run_dir / "host_verification.json"
    if not receipt_path.is_file():
        raise FileNotFoundError(f"Recibo nao encontrado: {receipt_path}. "
                                "Salve este script na pasta notebooks do projeto.")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    image_id = receipt.get("image_id", "")
    if receipt.get("verified") is not True or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
        raise ValueError("O recibo deve identificar uma imagem verificada por ID.")
    output = project / "reports/scale/CJU_BA5EIGT/aula_calendario"
    output.mkdir(parents=True, exist_ok=True)
    if any("," in str(path) for path in (script, output)):
        raise ValueError("Os caminhos usados pelo Docker nao podem conter virgulas.")
    command = [
        "docker", "run", "--rm", "--pull", "never", "--platform", "linux/amd64",
        "--cpus", "2", "--memory", "3g", "--pids-limit", "512", "--network", "none",
        "--hostname", "renewcast-spark", "--add-host", "renewcast-spark:127.0.0.1",
        "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,nodev,size=512m",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--mount", f"type=bind,source={script},target=/work/aula.py,readonly",
        "--mount", f"type=bind,source={output},target=/output",
        "--entrypoint", "python", image_id, "/work/aula.py", "--dentro-container",
    ]
    print("Abrindo a imagem Spark existente; exemplo didatico, sem treino ou build.", flush=True)
    status = subprocess.run(command, check=False).returncode
    if status:
        raise RuntimeError(f"A execucao terminou com codigo {status}; consulte a mensagem acima.")
    print(f"\nArquivo no Windows: {output / 'aula_calendario.csv'}", flush=True)
    print(f"Plano no Windows: {output / 'plano_resumo.txt'}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="Pasta de uma execucao M07.1 verificada.")
    parser.add_argument("--dentro-container", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        executar_aula() if args.dentro_container else abrir_ambiente(args.run_dir)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
