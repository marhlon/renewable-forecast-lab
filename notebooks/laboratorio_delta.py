"""M07.2: correcao simulada, MERGE, snapshot de treino e reproducao Delta.

Na raiz: python notebooks/laboratorio_delta.py
Leia docs/Aula_M07_2_Delta_Reproducao.md. O fluxo principal esta implementado.
Reutiliza a imagem Spark 4.0.1; baixa e confere dois JARs na primeira execucao.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

PROJECT = Path(__file__).resolve().parents[1]
DELTA_VERSION = '4.0.1'
JARS = [
    {
        "name": "delta-spark_2.13-4.0.1.jar",
        "url": "https://repo.maven.apache.org/maven2/io/delta/delta-spark_2.13/4.0.1/delta-spark_2.13-4.0.1.jar",
        "sha256": "a1e76860b19fe1e6b205a4ea7a9099a2f9575d39bb71d49b3e679b299d0efb91",
        "bytes": 7731162
    },
    {
        "name": "delta-storage-4.0.1.jar",
        "url": "https://repo.maven.apache.org/maven2/io/delta/delta-storage/4.0.1/delta-storage-4.0.1.jar",
        "sha256": "ecc42c5aaa51c423312d9e4e48aa4a12b34740bf2c37de0e8f279277ec3d12e4",
        "bytes": 78832
    }
]
KEYS = ['serie', 'forecast_origin']
COLUMNS = ['geracao_em_history_end', 'media_historico_mwmed', 'target_generation']
CORRECTION_TIME = datetime(2026, 7, 10, 1)
CUTOFF = datetime(2026, 7, 11, 6)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def salvar_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                  allow_nan=False, default=str) + '\n', encoding='utf-8')


def ler_snapshot(spark, path, version):
    """A versao e parte da entrada do experimento, nao uma escolha implicita."""
    return spark.read.format('delta').option('versionAsOf', version).load(str(path))


def versao_atual(spark, path):
    return int(spark.sql(f'DESCRIBE HISTORY delta.`{path}`').selectExpr('max(version)').first()[0])


def validar_correcoes(correcoes):
    """Neste contrato cada chave recebe uma unica revisao numerica positiva."""
    from pyspark.sql import functions as F
    if set(correcoes.columns) != {'din_instante', 'val_geracao', 'revisao'}:
        raise ValueError('Correcao deve ter somente din_instante, val_geracao e revisao.')
    if correcoes.filter(F.col('din_instante').isNull() | F.col('val_geracao').isNull()
                       | F.isnan('val_geracao') | (F.abs('val_geracao') == float('inf'))
                       | F.col('revisao').isNull() | (F.col('revisao') < 1)
                       | (F.col('revisao') % 1 != 0)).take(1):
        raise ValueError('Correcao com timestamp/valor/revisao invalidos.')
    if correcoes.groupBy('din_instante').count().filter('count > 1').take(1):
        raise ValueError('Duas correcoes para a mesma chave: resolva a ambiguidade antes do MERGE.')


def aplicar_correcao(spark, path, correcoes):
    """Atualizacao de chaves existentes; reenvio identico nao muda os dados."""
    from pyspark.sql import functions as F
    validar_correcoes(correcoes)
    atual = spark.read.format('delta').load(str(path))
    if correcoes.join(atual, 'din_instante', 'left_anti').take(1):
        raise ValueError('Este laboratorio corrige chaves existentes; nao insere horas novas.')
    pares = correcoes.alias('s').join(atual.alias('t'), 'din_instante')
    conflito = (F.col('s.revisao') < F.col('t.revisao')) | (
        (F.col('s.revisao') == F.col('t.revisao'))
        & ~F.col('s.val_geracao').eqNullSafe(F.col('t.val_geracao')))
    if pares.filter(conflito).take(1):
        raise ValueError('Revisao antiga ou mesmo numero de revisao com valor divergente.')
    correcoes.createOrReplaceTempView('correcoes')
    spark.sql(f'''
        MERGE INTO delta.`{path}` AS t
        USING correcoes AS s
        ON t.din_instante = s.din_instante
        WHEN MATCHED AND s.revisao > t.revisao THEN
          UPDATE SET val_geracao = s.val_geracao, revisao = s.revisao
    ''')


def diferencas(a, b):
    """Compara todas as colunas. Nulos sao iguais; doubles admitem 1e-9 MWmed."""
    from pyspark.sql import functions as F
    if a.columns != b.columns:
        raise ValueError('Colunas diferentes na comparacao.')
    aa = a.select(*KEYS, *[F.col(c).alias('a_' + c) for c in a.columns if c not in KEYS]).withColumn('a_existe', F.lit(True))
    bb = b.select(*KEYS, *[F.col(c).alias('b_' + c) for c in b.columns if c not in KEYS]).withColumn('b_existe', F.lit(True))
    juntos = aa.join(bb, KEYS, 'full')
    mudou = F.col('a_existe').isNull() | F.col('b_existe').isNull()
    for c, dtype in a.dtypes:
        if c in KEYS:
            continue
        x, y = F.col('a_' + c), F.col('b_' + c)
        if dtype == 'double':
            mudou = mudou | (x.isNull() != y.isNull()) | F.coalesce(F.abs(x - y) > 1e-9, F.lit(False))
        else:
            mudou = mudou | ~x.eqNullSafe(y)
    return juntos.filter(mudou)


def executar(args):
    from pyspark.sql import SparkSession, functions as F
    from pyspark.errors import AnalysisException
    import laboratorio_temporal_spark as temporal

    jars = [args.jars_dir / item['name'] for item in JARS]
    for path, item in zip(jars, JARS):
        if not path.is_file() or sha(path) != item['sha256']:
            raise ValueError(f'Dependencia ausente/alterada: {path.name}')
    runtime = Path('/tmp/renewcast_delta')
    runtime.mkdir(parents=True, exist_ok=True)
    spark = (SparkSession.builder.master('local[2]').appName('Renewcast-Delta-reproducao')
        .config('spark.jars', ','.join(str(p.resolve()) for p in jars))
        .config('spark.sql.extensions', 'io.delta.sql.DeltaSparkSessionExtension')
        .config('spark.sql.catalog.spark_catalog', 'org.apache.spark.sql.delta.catalog.DeltaCatalog')
        .config('spark.driver.host', '127.0.0.1').config('spark.driver.bindAddress', '127.0.0.1')
        .config('spark.jars.ivy', str(runtime / 'ivy'))
        .config('spark.sql.warehouse.dir', (runtime / 'warehouse').as_uri())
        .config('spark.sql.timestampType', 'TIMESTAMP_NTZ').config('spark.sql.session.timeZone', 'UTC')
        .config('spark.sql.shuffle.partitions', '2').config('spark.databricks.delta.snapshotPartitions', '2')
        .config('spark.databricks.delta.schema.autoMerge.enabled', 'false')
        .config('spark.ui.enabled', 'false').config('spark.ui.showConsoleProgress', 'false').getOrCreate())
    spark.sparkContext.setLogLevel('ERROR')
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    path = (out / 'geracao_delta').resolve()
    try:
        if spark.version != '4.0.1':
            raise ValueError(f'Esperado Spark 4.0.1; recebido {spark.version}.')
        raw = spark.read.parquet(str(args.input)).select(
            F.col('din_instante').cast('timestamp_ntz'), F.col('val_geracao').cast('double'))
        temporal.validar_entrada(raw)
        raw = raw.withColumn('revisao', F.lit(0).cast('long'))
        raw.write.format('delta').mode('errorifexists').save(str(path))
        v0 = versao_atual(spark, path)
        base = ler_snapshot(spark, path, v0)
        if base.exceptAll(raw).take(1) or raw.exceptAll(base).take(1):
            raise AssertionError('Delta inicial difere da entrada Parquet.')
        def features(version):
            source = ler_snapshot(spark, path, version).select('din_instante', 'val_geracao')
            return temporal.construir_features(temporal.completar_horas(source)).cache()
        before = features(v0)
        train0 = temporal.selecionar_treino(before, CUTOFF)
        delivered = spark.read.parquet(str(args.training_input)).select(*train0.columns)
        if diferencas(train0, delivered).take(1):
            raise AssertionError('Treino da versao inicial nao reproduz treino_autoria.parquet recebido.')
        manifest = {'schema': 'renewcast-training-snapshot-v1', 'table_relative_path': 'geracao_delta',
                    'delta_version': v0, 'cutoff': CUTOFF.isoformat(), 'horizon_hours': 24,
                    'availability_delay_hours_assumed': 2, 'window_hours': 6,
                    'features_code_sha256': sha(Path(temporal.__file__)), 'rows': train0.count(),
                    'historical_source_versions_verified': False, 'models_trained': False}
        salvar_json(out / 'snapshot_treino.json', manifest)
        point = base.filter(F.col('din_instante') == F.lit(CORRECTION_TIME))
        old = point.first()
        if old is None or old.val_geracao is None:
            raise ValueError('A hora da correcao precisa existir com geracao preenchida.')
        correction = point.select('din_instante', (F.col('val_geracao') + args.incremento).alias('val_geracao'),
                                  F.lit(1).cast('long').alias('revisao'))
        print(f'Versao {v0}: {base.count()} horas; treino reproduzido: {manifest["rows"]} linhas.', flush=True)
        # Contraprova de ambiguidade: deve falhar antes de publicar um commit.
        try:
            aplicar_correcao(spark, path, correction.union(correction))
        except ValueError as exc:
            if 'Duas correcoes' not in str(exc):
                raise
        else:
            raise AssertionError('Correcao duplicada foi aceita.')
        if versao_atual(spark, path) != v0:
            raise AssertionError('A rejeicao da duplicidade mudou a tabela.')
        # Contraprova de schema: uma coluna nao autorizada nao entra por append.
        spark.sparkContext.setLogLevel('FATAL')
        try:
            raw.limit(1).withColumn('coluna_inesperada', F.lit('erro')).write.format('delta').mode('append').save(str(path))
        except AnalysisException as exc:
            if 'schema' not in str(exc).lower():
                raise
        else:
            raise AssertionError('Schema inesperado foi aceito.')
        finally:
            spark.sparkContext.setLogLevel('ERROR')
        if versao_atual(spark, path) != v0:
            raise AssertionError('A rejeicao de schema publicou um commit.')
        aplicar_correcao(spark, path, correction)
        v1 = versao_atual(spark, path)
        current = ler_snapshot(spark, path, v1)
        point_after = current.filter(F.col('din_instante') == F.lit(CORRECTION_TIME)).first()
        if current.count() != base.count() or not math.isclose(point_after.val_geracao-old.val_geracao, args.incremento, abs_tol=1e-9):
            raise AssertionError('Correcao ou numero de linhas inesperado.')
        after = features(v1)
        changed = diferencas(before, after)
        impact = changed.select('forecast_origin',
            (F.col('b_geracao_em_history_end')-F.col('a_geracao_em_history_end')).alias('delta_historico_mwmed'),
            (F.col('b_media_historico_mwmed')-F.col('a_media_historico_mwmed')).alias('delta_media_mwmed'),
            (F.col('b_target_generation')-F.col('a_target_generation')).alias('delta_alvo_mwmed'),
            (F.col('a_features_validas') & F.col('a_target_generation').isNotNull()
             & (F.col('a_target_available_at') < F.lit(CUTOFF))).alias('pertence_ao_treino')).orderBy('forecast_origin')
        impact_rows = [r.asDict() for r in impact.collect()]
        temporal.escrever_csv(out / 'impacto_correcao.csv', impact_rows)
        train1 = temporal.selecionar_treino(after, CUTOFF)
        changed_training = diferencas(train0, train1).count()
        # Reabre o snapshot depois da correcao; nao reutiliza apenas o cache antigo.
        restored = temporal.selecionar_treino(features(manifest['delta_version']), CUTOFF)
        if diferencas(restored, delivered).take(1):
            raise AssertionError('Snapshot fixado nao reproduziu o treino original.')
        aplicar_correcao(spark, path, correction)
        v_repeat = versao_atual(spark, path)
        repeated = ler_snapshot(spark, path, v_repeat)
        if current.exceptAll(repeated).take(1) or repeated.exceptAll(current).take(1):
            raise AssertionError('Reenvio identico alterou dados.')
        history = [r.asDict(recursive=True) for r in spark.sql(f'DESCRIBE HISTORY delta.`{path}`').orderBy('version').collect()]
        salvar_json(out / 'historico_delta.json', history)
        conclusion = {'schema': 'renewcast-delta-lab-v1', 'completed': True,
            'spark_version': spark.version, 'delta_version': DELTA_VERSION,
            'snapshot_original': v0, 'snapshot_corrigido': v1, 'snapshot_apos_reenvio': v_repeat,
            'horas': base.count(), 'linhas_treino': manifest['rows'],
            'correcao_simulada': True, 'instante_corrigido': CORRECTION_TIME.isoformat(),
            'valor_original': old.val_geracao, 'valor_corrigido': point_after.val_geracao,
            'incremento_mwmed': args.incremento,
            'origens_com_mudanca': len(impact_rows), 'linhas_treino_com_mudanca': changed_training,
            'snapshot_original_reproduzido': True, 'reenvio_alterou_dados': False,
            'schema_incompativel_rejeitado': True, 'duplicidade_rejeitada': True,
            'disponibilidade_assumida': True, 'historical_source_versions_verified': False,
            'models_trained': False}
        salvar_json(out / 'conclusao.json', conclusion)
        print(json.dumps(conclusion, ensure_ascii=False, indent=2), flush=True)
    finally:
        spark.stop()


# Infraestrutura: nao exige PySpark/Java no Conda do Windows.
def preparar_dependencias(folder):
    folder.mkdir(parents=True, exist_ok=True)
    for item in JARS:
        dest = folder / item['name']
        if dest.is_file():
            if sha(dest) != item['sha256']:
                raise ValueError(f'JAR alterado: {dest}. Nenhuma substituicao automatica.')
            continue
        print(f'Obtendo dependencia Delta: {item["name"]}', flush=True)
        with urlopen(item['url'], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Hash da dependencia divergiu; download recusado.')
        temporary = dest.with_suffix('.download')
        temporary.write_bytes(data)
        temporary.replace(dest)


def abrir_docker(args):
    if not shutil.which('docker'):
        raise RuntimeError('Docker nao encontrado; abra o Docker Desktop do projeto.')
    script = Path(__file__).resolve()
    temporal = PROJECT / 'notebooks/laboratorio_temporal_spark.py'
    for source in [args.input, args.training_input, temporal]:
        if not source.exists():
            raise FileNotFoundError(f'Entrada necessaria ausente: {source}')
    receipt = json.loads((args.run_dir/'host_verification.json').read_text(encoding='utf-8'))
    image = receipt.get('image_id','')
    if receipt.get('verified') is not True or not re.fullmatch(r'sha256:[0-9a-f]{64}',image):
        raise ValueError('Recibo Spark nao identifica imagem verificada.')
    signature = {'input_sha256': sha(args.input), 'code_sha256': sha(script),
                 'temporal_code_sha256': sha(temporal), 'incremento': args.incremento, 'image_id': image,
                 'training_files': {p.name:sha(p) for p in sorted(args.training_input.glob('*.parquet'))}
                    if args.training_input.is_dir() else {args.training_input.name:sha(args.training_input)}}
    done = args.output_dir/'verification.json'
    if done.is_file():
        saved = json.loads(done.read_text(encoding='utf-8'))
        if saved.get('signature') != signature:
            raise ValueError('Entrada/configuracao mudou. Informe outro --output-dir para comparar experimentos.')
        for name, expected in saved['output_sha256'].items():
            path = (args.output_dir/name).resolve()
            if not path.is_relative_to(args.output_dir.resolve()) or sha(path) != expected:
                raise ValueError(f'Saida alterada: {name}')
        print('Execucao concluida existente, conferida e reutilizada. Nenhuma nova versao criada.')
        print((args.output_dir/'conclusao.json').read_text(encoding='utf-8'))
        return
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError('Pasta de saida parcial/ocupada. Preserve o diagnostico e use --output-dir com uma pasta nova.')
    preparar_dependencias(args.jars_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    mounts = [(script,'/work/laboratorio_delta.py',True),(temporal,'/work/laboratorio_temporal_spark.py',True),
              (args.input,'/input/geracao.parquet',True),(args.training_input,'/input/treino.parquet',True),
              (args.jars_dir,'/deps',True),(args.output_dir,'/output',False)]
    if any(',' in str(p.resolve()) for p,_,_ in mounts):
        raise ValueError('Caminhos de montagem nao podem conter virgula.')
    command=['docker','run','--rm','--pull','never','--platform','linux/amd64','--cpus','2','--memory','3g',
        '--pids-limit','512','--network','none','--hostname','renewcast-spark','--add-host','renewcast-spark:127.0.0.1',
        '--read-only','--tmpfs','/tmp:rw,exec,nosuid,nodev,size=512m','--cap-drop','ALL','--security-opt','no-new-privileges']
    for source,target,readonly in mounts:
        command += ['--mount',f'type=bind,source={source.resolve()},target={target}'+(',readonly' if readonly else '')]
    command += ['--entrypoint','python',image,'/work/laboratorio_delta.py','--dentro-container',
        '--input','/input/geracao.parquet','--training-input','/input/treino.parquet','--jars-dir','/deps',
        '--output-dir','/output','--incremento',str(args.incremento)]
    print('Mesma imagem Spark; entrada somente leitura; correcao SIMULADA em tabela Delta separada.',flush=True)
    result=subprocess.run(command,check=False)
    if result.returncode:
        raise RuntimeError(f'Laboratorio terminou com codigo {result.returncode}; veja o primeiro erro acima.')
    conclusion=json.loads((args.output_dir/'conclusao.json').read_text(encoding='utf-8'))
    if conclusion.get('completed') is not True:
        raise ValueError('Conclusao ausente ou incompleta.')
    after_signature={**signature,'input_sha256':sha(args.input),'temporal_code_sha256':sha(temporal)}
    if signature!=after_signature:
        raise ValueError('Uma entrada mudou durante a execucao.')
    outputs={str(p.relative_to(args.output_dir)).replace('\\','/'):sha(p)
             for p in sorted(args.output_dir.rglob('*')) if p.is_file() and not p.name.startswith('.')}
    salvar_json(done,{'verified':True,'signature':signature,'output_sha256':outputs})
    print(f'Resultados: {args.output_dir.resolve()}')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=PROJECT/'data/interim/CJU_BA5EIGT_hourly.parquet')
    parser.add_argument('--training-input',type=Path,default=PROJECT/'reports/scale/CJU_BA5EIGT/laboratorio_temporal/treino_autoria.parquet')
    parser.add_argument('--run-dir',type=Path,default=PROJECT/'reports/scale/CJU_BA5EIGT/m07_1/20261019T230058Z_cf2fe669')
    parser.add_argument('--output-dir',type=Path,default=PROJECT/'reports/scale/CJU_BA5EIGT/m07_2_delta')
    parser.add_argument('--jars-dir',type=Path,default=PROJECT/'data/external/runtime/delta_4_0_1')
    parser.add_argument('--incremento',type=float,default=12.0,help='Correcao hipotetica em MWmed, positiva e finita.')
    parser.add_argument('--dentro-container',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args(argv)
    if not math.isfinite(args.incremento) or args.incremento<=0:
        parser.error('--incremento deve ser positivo e finito.')
    try:
        executar(args) if args.dentro_container else abrir_docker(args)
    except Exception as exc:
        print(f'Erro: {exc}',file=sys.stderr)
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
