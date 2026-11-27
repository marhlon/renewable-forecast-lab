"""Entrega aplicada M07-01/02/03 e M05-05; freeze deve preceder execute.

Uso: python notebooks/bloco3_dados_execucao.py freeze | execute
Não usa rede, Docker, Spark, GPU nem cadastros externos.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import psutil
from renewable_forecast.bloco3_data import (
    FEATURES, SCHEMA_VERSION, SOURCE_SHA256, IncrementalStore, causal_gold,
    immutable_bronze, logical_hash, make_silver, select_series, sha256, write_json,
)

BASE = ROOT / "reports/fechamento_m00_m09/bloco3_engenharia"
SOURCE = ROOT / "data/raw/bloco2_locked/geracao_2026_10.parquet"
IDS = ["M07-01", "M07-02", "M07-03", "M05-05"]
CODE = [ROOT / "src/renewable_forecast/bloco3_data.py", Path(__file__), ROOT / "tests/test_bloco3_data.py"]
TRAIN_CUTOFF = pd.Timestamp("2026-10-16")
VAL_END = pd.Timestamp("2026-10-22")
TEST_END = pd.Timestamp("2026-11-01")


def now():
    return pd.Timestamp.now(tz="UTC").isoformat()


def freeze():
    if (BASE / "M05-05/resultado.json").exists():
        raise ValueError("Resultados já existem: preserve protocolo original")
    raw = pd.read_parquet(SOURCE)
    if sha256(SOURCE) != SOURCE_SHA256:
        raise ValueError("Snapshot incorreto")
    selected = select_series(raw)
    universe = sorted(raw.id_ons.dropna().unique().tolist())
    cohorts = {str(k): universe[:math.ceil(len(universe)*k/3)] for k in [1, 2, 3]}
    code_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in CODE}
    common = {
        "frozen_at_utc": now(), "schema_version": SCHEMA_VERSION,
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": SOURCE_SHA256,
        "source_rows": len(raw), "code_sha256_before_execution": code_hashes,
        "attribution": "Código, execução e análise fornecidos por Codex; sem certificação de autonomia pessoal",
        "data_scope": "Outubro/2026 retrospectivo; fonte já no disco e CJU_BA5EIGT já examinada no bloco 2. Seleção nova por metadata não torna o mês intocado.",
        "availability": "event_time + 2h é hipótese, não chegada histórica comprovada; timestamps de calendário do arquivo sem fuso verificado",
        "operational_claim": False,
        "commands": ["python -m pytest tests/test_bloco3_data.py -q", "python notebooks/bloco3_dados_execucao.py freeze", "python notebooks/bloco3_dados_execucao.py execute"],
    }
    specifics = {
        "M07-01": {"design": "Bronze endereçada por SHA256 sem sobrescrita; silver chave id_ons/event_time, quarentena sem imputação; gold joins exatos causais por série", "criteria": ["bruto físico igual ao hash original", "quarentena explícita; linhagem source_row até fonte", "reprocessamento lógico e físico determinístico", "contraprovas declaradas em dados pequenos"]},
        "M07-02": {"design": "Escala local real, sem replicação sintética e sem alegar execução distribuída", "cohorts": cohorts, "series_universe": len(universe), "repetitions": 3, "resources": {"duckdb_threads": 1, "duckdb_memory_limit": "512MB", "pandas_threadpool_limit": 1, "pandas_memory": "RSS medido, limite 512 MiB verificado após execução; sem limite rígido do sistema operacional"}, "timer": "read silver parquet, filter cohort, lag exact previous hour by series, group aggregates, materialize output Parquet and SHA256; imports/startup excluded from elapsed/CPU; RSS baseline and peak sampled inside timer", "caching": "Três repetições em processos separados; ordem pandas/duckdb alternada. Cache de SO não foi esvaziado; não é cold-start de armazenamento", "criteria": ["mesmas chaves/contagens e agregados allclose rtol=1e-10 atol=1e-10", "reportar tempo CPU parede RSS e bytes", "EXPLAIN ANALYZE executado em mesma query; não inferir AQE/Spark"]},
        "M07-03": {"design": "Replay local incremental transacional por ponteiro atômico", "batches": "quatro lotes semanais, evento primeira série 2026-10-05 12h retido até lote seguinte; atraso sintético de +7 dias além da disponibilidade hipotética normal", "failure": "falha sintética depois do Parquet estágio, antes do commit do segundo lote; recuperar com nova instância", "criteria": ["repetição noop e conflito rejeitado", "commit falho não muda estado", "gold final incremental igual à referência as-of com o mesmo atraso", "features indisponíveis antes da chegada permanecem nulas e lags não cruzam séries"]},
        "M05-05": {"selected_series": selected.to_dict(orient="records"), "selection": "4 ids lexicograficamente primeiros EOL*, rows=744 e timestamps únicos=744; exclui CJU_BA5EIGT/CJUBA5EIGT; sem consultar geração/desempenho", "generalization": "Temporal nas mesmas quatro séries conhecidas; não mede série nova, transferência geográfica nem anual", "target": "Geração MW em t+1h", "features": FEATURES, "feature_groups": "história causal lag2/lag3/lag24/média t-2..t-7, calendário sen/cos, código categórico fixo por série", "cuts": {"train_origin_before": str(TRAIN_CUTOFF), "train_label_available_strictly_before": str(TRAIN_CUTOFF), "validation_origin": [str(TRAIN_CUTOFF), str(VAL_END)], "test_origin": [str(VAL_END), str(TEST_END)], "last_test_origin": "2026-10-31 22:00:00"}, "model": {"class": "HistGradientBoostingRegressor", "loss": "squared_error", "max_iter": 100, "learning_rate": 0.05, "max_leaf_nodes": 15, "l2_regularization": 1.0, "random_state": 0, "early_stopping": False, "categorical_features_global": ["series_code"]}, "comparison": "Um global, quatro locais mesmos hiperparâmetros e persistência disponível lag2 nas mesmas origens elegíveis; sem normalização, capacidade ou tuning; validação apenas diagnóstico", "criteria": ["fit usa apenas rótulos disponíveis estritamente antes do corte", "coorte pareada global/local/persistência por série e agregado", "métricas MW MAE/RMSE/viés, sem exigir ganho positivo", "nenhuma promoção de P1 ou aprovação operacional"]},
    }
    for item in IDS:
        write_json(BASE / item / "protocolo.json", {**common, "item": item, **specifics[item]})
    write_json(BASE / "M05-05/cortes.json", specifics["M05-05"])
    print(json.dumps({"frozen": now(), "series": selected.series_id.tolist(), "cohort_sizes": {k:len(v) for k,v in cohorts.items()}, "code":code_hashes}, indent=2), flush=True)


def load_protocol(item):
    return json.loads((BASE / item / "protocolo.json").read_text(encoding="utf-8"))


def verify_freeze():
    protocol = load_protocol("M07-01")
    for path, expected in protocol["code_sha256_before_execution"].items():
        if sha256(ROOT / path) != expected:
            raise ValueError(f"Código modificado após protocolo: {path}")
    if sha256(SOURCE) != SOURCE_SHA256:
        raise ValueError("Fonte alterada")
    return protocol


def layer_run():
    directory = BASE / "M07-01"
    bronze = immutable_bronze(SOURCE, directory / "bronze")
    raw = pd.read_parquet(bronze["path"])
    silver, quarantine = make_silver(raw)
    selected = [x["series_id"] for x in load_protocol("M05-05")["selected_series"]]
    gold = causal_gold(silver, selected)
    # Segunda construção efetiva verifica idempotência sem mutar primeira saída.
    silver2, quarantine2 = make_silver(pd.read_parquet(bronze["path"]))
    gold2 = causal_gold(silver2, selected)
    comparisons = {"silver": logical_hash(silver) == logical_hash(silver2), "quarantine": logical_hash(quarantine) == logical_hash(quarantine2), "gold": logical_hash(gold) == logical_hash(gold2)}
    outputs = {}
    for name, frame in [("silver",silver),("quarantine",quarantine),("gold",gold)]:
        path = directory / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        repeat = directory / f"{name}_reprocessed.parquet"
        {"silver":silver2,"quarantine":quarantine2,"gold":gold2}[name].to_parquet(repeat, index=False)
        outputs[name] = {"path":str(path.relative_to(ROOT)), "rows":len(frame), "sha256":sha256(path), "logical_sha256":logical_hash(frame), "physical_idempotent":sha256(path)==sha256(repeat)}
    negative = example_counterproof()
    reasons = quarantine.quarantine_reason.value_counts().to_dict()
    write_json(directory / "linhagem.json", {"source": str(SOURCE.relative_to(ROOT)), "bronze":bronze, "outputs":outputs, "silver_row_lineage":"source_row (posição zero-based na bronze) + SHA256 original", "gold_lineage":"series_id/forecast_origin; lag2=t-2, lag3=t-3, lag24=t-24, mean6=t-2..t-7; target=t+1; join exato em silver e available_at<=origin", "versions":importlib.metadata.version("pandas"), "schema":SCHEMA_VERSION})
    write_json(directory / "contratos_camadas.json", {"bronze":"conteúdo exato SHA256; reutilização só após revalidar hash", "silver":{"key":["series_id","event_time"], "invalid":"id ausente, timestamp inválido/não horário, MW não finito/negativo, todas as duplicatas de chave em quarentena", "availability":"hipótese event_time+2h", "quarantine_reasons":reasons}, "gold":{"key":["series_id","forecast_origin"], "availability":"cada componente temporal exige available_at<=origin; nulos preservados", "cadastro":"quatro ids escolhidos por metadata corrente, sem afirmar disponibilidade histórica"}})
    result = {"executed_at_utc":now(), "bronze":bronze, "outputs":outputs, "idempotency":comparisons, "bronze_replay":immutable_bronze(SOURCE,directory/"bronze")["reused"], "counterproof":negative, "quarantine_reasons":reasons, "limits":["Não Delta/ACID distribuído", "Não chegada histórica real", "Nenhum dado negativo imputado ou cortado"]}
    write_json(directory / "resultado.json",result)
    return silver, gold


def example_counterproof():
    raw = pd.DataFrame({"id_ons":["a","a","b",None,"c"], "din_instante":pd.to_datetime(["2026-10-01"]*5), "val_geracao":[1,2,3,4,-2], "nom_tipousina":"EOL", "nom_usina":"contraprova"})
    good,bad=make_silver(raw)
    assert len(good)==1 and len(bad)==4
    return {"synthetic":True,"description":"5 registros pequenos construídos para duplicata/id ausente/MW negativo; não incorporados ao dado real", "accepted":len(good),"quarantined":len(bad),"reasons":bad.quarantine_reason.tolist()}


def incremental_run(silver):
    directory = BASE / "M07-03"
    series = [x["series_id"] for x in load_protocol("M05-05")["selected_series"]]
    columns = ["series_id","event_time","generation_mw","available_at","source_row"]
    data = silver.loc[silver.series_id.isin(series),columns].copy()
    late_mask = data.series_id.eq(series[0]) & data.event_time.eq(pd.Timestamp("2026-10-05 12:00"))
    if late_mask.sum()!=1:
        raise ValueError("Evento atrasado predefinido não está elegível")
    data.loc[late_mask,"available_at"] += pd.Timedelta(days=7)
    # Lotes por disponibilidade; clocks/event_time não substituem arrival_at.
    cuts = [pd.Timestamp("2026-10-08"),pd.Timestamp("2026-10-16"),pd.Timestamp("2026-10-24"),pd.Timestamp("2026-11-02")]
    store = IncrementalStore(directory / "state")
    if store.state()["version"]:
        raise ValueError("Estado existe; preserve execução original e não fabrique novo recibo")
    runs=[]
    previous=pd.Timestamp("2026-10-01")
    failed_unchanged=False
    for number,cut in enumerate(cuts):
        batch = data.loc[data.available_at.ge(previous) & data.available_at.lt(cut)].copy()
        batch.to_parquet(directory / f"batch_{number+1}.parquet",index=False)
        if number==1:
            before=logical_hash(store.table())
            try:
                store.apply(f"batch-{number+1}",batch,fail_before_commit=True)
            except RuntimeError as error:
                store=IncrementalStore(directory/"state")
                failed_unchanged=logical_hash(store.table())==before
                runs.append({"batch":number+1,"injected_failure":str(error),"state_unchanged":failed_unchanged,"version_after_failure":store.state()["version"]})
        runs.append({"batch":number+1,"cutoff":str(cut),**store.apply(f"batch-{number+1}",batch)})
        runs.append({"batch":number+1,**store.apply(f"batch-{number+1}",batch)})
        previous=cut
    actual=store.table()
    expected=causal_gold(data,series)
    incremental=causal_gold(actual,series)
    gold_equal=logical_hash(expected)==logical_hash(incremental)
    state_equal=logical_hash(data)==logical_hash(actual)
    conflict=data.iloc[[0]].copy()
    conflict["generation_mw"] += 1
    rejected=False
    try:
        store.apply("contraprova-conflict",conflict)
    except ValueError:
        rejected=True
    origin=pd.Timestamp("2026-10-05 14:00")
    late=incremental.loc[incremental.series_id.eq(series[0]) & incremental.forecast_origin.eq(origin)].iloc[0]
    late_masked=bool(pd.isna(late.lag2))
    # Mutar só a segunda série não pode alterar a primeira em nenhuma origem.
    mutated=data.copy()
    mutated.loc[mutated.series_id.eq(series[1]),"generation_mw"] += 1e6
    no_cross=logical_hash(causal_gold(mutated,series).query("series_id == @series[0]"))==logical_hash(expected.query("series_id == @series[0]"))
    quality=data.groupby("series_id").agg(rows=("event_time","size"),unique_timestamps=("event_time","nunique"),first=("event_time","min"),last=("event_time","max"))
    quality["deliberately_late"]=[int(x==series[0]) for x in quality.index]
    quality.to_csv(directory/"qualidade_por_serie.csv")
    incremental.to_parquet(directory/"gold_incremental.parquet",index=False)
    write_json(directory/"execucoes_incrementais.json",runs)
    write_json(directory/"resultado.json",{"executed_at_utc":now(),"rows":len(actual),"versions":store.state()["version"],"state_equals_reference":state_equal,"gold_equals_reference":gold_equal,"failed_commit_unchanged":failed_unchanged,"conflicting_payload_rejected":rejected,"late_feature_masked":late_masked,"no_cross_series":no_cross,"logical_reference_sha256":logical_hash(expected),"logical_incremental_sha256":logical_hash(incremental),"late_simulation":{"series":series[0],"event":"2026-10-05 12:00:00","available":"2026-10-12 14:00:00","synthetic_delay":True},"limits":["replay local finito", "disponibilidade hipotética, atraso/falha sintéticos", "nenhum broker/shadow/serviço distribuído exercitado"]})
    assert all([state_equal,gold_equal,failed_unchanged,rejected,late_masked,no_cross])


SCALE_QUERY = """WITH lagged AS (
 SELECT series_id, event_time, generation_mw,
 LAG(generation_mw) OVER(PARTITION BY series_id ORDER BY event_time) AS previous_mw,
 LAG(event_time) OVER(PARTITION BY series_id ORDER BY event_time) AS previous_time
 FROM read_parquet(?) WHERE series_id IN (SELECT unnest(?))
)
SELECT series_id, count(*) AS rows, avg(generation_mw) AS mean_generation_mw,
 avg(CASE WHEN event_time-previous_time=INTERVAL '1 hour' THEN abs(generation_mw-previous_mw) END) AS mean_abs_change_mw
FROM lagged GROUP BY series_id ORDER BY series_id"""


def benchmark_worker(engine, cohort, repetition):
    import duckdb
    from threadpoolctl import threadpool_limits
    protocol=load_protocol("M07-02")
    chosen=protocol["cohorts"][str(cohort)]
    source=BASE/"M07-01/silver.parquet"
    directory=BASE/"M07-02"
    output=directory/f"materialized_{engine}_{cohort}_{repetition}.parquet"
    process=psutil.Process()
    base_rss=process.memory_info().rss
    peak=[base_rss]
    stop=threading.Event()
    def sample():
        while not stop.wait(.005):
            peak[0]=max(peak[0],process.memory_info().rss)
    sampler=threading.Thread(target=sample,daemon=True)
    con=duckdb.connect() if engine=="duckdb" else None
    if con:
        con.execute("SET threads=1")
        con.execute("SET memory_limit='512MB'")
    with threadpool_limits(limits=1):
        sampler.start()
        cpu=time.process_time(); start=time.perf_counter()
        if con:
            result=con.execute(SCALE_QUERY,[str(source),chosen]).df()
        else:
            data=pd.read_parquet(source,columns=["series_id","event_time","generation_mw"],use_threads=False)
            data=data.loc[data.series_id.isin(chosen)].sort_values(["series_id","event_time"])
            grouped=data.groupby("series_id",sort=False)
            previous=grouped.generation_mw.shift(1)
            previous_time=grouped.event_time.shift(1)
            data["change"]=(data.generation_mw-previous).abs().where((data.event_time-previous_time).eq(pd.Timedelta(hours=1)))
            result=data.groupby("series_id",sort=True).agg(rows=("generation_mw","size"),mean_generation_mw=("generation_mw","mean"),mean_abs_change_mw=("change","mean")).reset_index()
        result.to_parquet(output,index=False)
        digest=sha256(output)
        elapsed=time.perf_counter()-start; used_cpu=time.process_time()-cpu
        peak[0]=max(peak[0],process.memory_info().rss)
        stop.set(); sampler.join()
    if con:
        if repetition==1:
            plan=con.execute("EXPLAIN ANALYZE "+SCALE_QUERY,[str(source),chosen]).fetchall()
            (directory/f"plano_coorte_{cohort}.txt").write_text("\n".join(str(row[1]) for row in plan),encoding="utf-8")
        con.close()
    record={"engine":engine,"cohort":cohort,"repetition":repetition,"selected_series":len(chosen),"materialized_series":len(result),"input_rows_after_filter":int(result.rows.sum()),"wall_seconds":elapsed,"cpu_seconds":used_cpu,"baseline_rss_bytes":base_rss,"peak_rss_bytes":peak[0],"incremental_peak_rss_bytes":max(0,peak[0]-base_rss),"rss_below_512mib":peak[0]<=512*1024*1024,"output_bytes":output.stat().st_size,"output_sha256":digest,"output":str(output.relative_to(ROOT))}
    write_json(directory/f"trial_{engine}_{cohort}_{repetition}.json",record)
    print(json.dumps(record),flush=True)


def scale_run():
    directory=BASE/"M07-02"
    records=[]
    for cohort in [1,2,3]:
        for repetition in [1,2,3]:
            order=["pandas","duckdb"] if repetition%2 else ["duckdb","pandas"]
            for engine in order:
                command=[sys.executable,str(Path(__file__)),"worker","--engine",engine,"--cohort",str(cohort),"--repetition",str(repetition)]
                completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding="utf-8")
                if completed.returncode:
                    raise RuntimeError(completed.stderr+completed.stdout)
                record=json.loads((directory/f"trial_{engine}_{cohort}_{repetition}.json").read_text(encoding="utf-8"))
                records.append(record)
                print(f"Escala {engine} coorte={cohort} rep={repetition}: {record['wall_seconds']:.3f}s {record['input_rows_after_filter']} linhas",flush=True)
    metrics=pd.DataFrame(records)
    metrics.to_csv(directory/"benchmark_escala.csv",index=False)
    equivalence=[]
    for cohort in [1,2,3]:
        for rep in [1,2,3]:
            a=pd.read_parquet(directory/f"materialized_pandas_{cohort}_{rep}.parquet")
            b=pd.read_parquet(directory/f"materialized_duckdb_{cohort}_{rep}.parquet")
            equal=a.series_id.tolist()==b.series_id.tolist() and a.rows.tolist()==b.rows.tolist() and np.allclose(a.iloc[:,2:],b.iloc[:,2:],rtol=1e-10,atol=1e-10,equal_nan=True)
            equivalence.append({"cohort":cohort,"repetition":rep,"equivalent":equal,"max_abs_numeric_difference":float(np.nanmax(np.abs(a.iloc[:,2:].to_numpy()-b.iloc[:,2:].to_numpy())))})
    summary=metrics.groupby(["engine","cohort"]).agg(rows=("input_rows_after_filter","first"),wall_median=("wall_seconds","median"),wall_min=("wall_seconds","min"),wall_max=("wall_seconds","max"),cpu_median=("cpu_seconds","median"),rss_peak=("peak_rss_bytes","max"),output_bytes=("output_bytes","max")).reset_index()
    summary.to_csv(directory/"benchmark_resumo.csv",index=False)
    plans="\n\n".join(f"COORTE {k} — EXPLAIN ANALYZE realmente executado\n"+(directory/f"plano_coorte_{k}.txt").read_text(encoding="utf-8") for k in [1,2,3])
    (directory/"plano_final.txt").write_text(plans,encoding="utf-8")
    write_json(directory/"resultado.json",{"executed_at_utc":now(),"trials":len(records),"real_source":True,"synthetic_replication":False,"equivalence":equivalence,"summary":summary.to_dict(orient="records"),"all_rss_under_512mib":bool(metrics.rss_below_512mib.all()),"environment":{"platform":platform.platform(),"cpu_logical":os.cpu_count(),"python":sys.version,"packages":{p:importlib.metadata.version(p) for p in ["pandas","duckdb","numpy","pyarrow","psutil"]}},"limits":["Local single process/one thread; não mede rede/cluster/distribuição", "Fonte de 4.6 MB e 537k registros brutos, sem inferir big data", "warm OS cache possível", "DuckDB limite 512MB; pandas só RSS observado, sem imposição rígida", "EXPLAIN ANALYZE posterior aos trials não faz parte do tempo medido"]})
    assert all(x["equivalent"] for x in equivalence)


def model_run(gold):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from threadpoolctl import threadpool_limits
    directory=BASE/"M05-05"
    eligible=np.isfinite(gold[FEATURES+["target"]]).all(axis=1)
    train=eligible & gold.forecast_origin.lt(TRAIN_CUTOFF) & gold.label_available_at.lt(TRAIN_CUTOFF)
    val=eligible & gold.forecast_origin.ge(TRAIN_CUTOFF) & gold.forecast_origin.lt(VAL_END)
    test=eligible & gold.forecast_origin.ge(VAL_END) & gold.forecast_origin.lt(TEST_END)
    params={"max_iter":100,"learning_rate":.05,"max_leaf_nodes":15,"l2_regularization":1.,"random_state":0,"early_stopping":False}
    timings=[]
    predictions=[]
    with threadpool_limits(limits=1):
        global_model=HistGradientBoostingRegressor(**params,categorical_features=["series_code"])
        start=time.perf_counter(); cpu=time.process_time()
        global_model.fit(gold.loc[train,FEATURES],gold.loc[train,"target"])
        timings.append({"model":"global_hgb","series":"all","train_rows":int(train.sum()),"fit_wall_seconds":time.perf_counter()-start,"fit_cpu_seconds":time.process_time()-cpu})
        for sid in sorted(gold.series_id.unique()):
            local_train=train & gold.series_id.eq(sid)
            local=HistGradientBoostingRegressor(**params,categorical_features=None)
            local_features=[x for x in FEATURES if x!="series_code"]
            start=time.perf_counter(); cpu=time.process_time()
            local.fit(gold.loc[local_train,local_features],gold.loc[local_train,"target"])
            timings.append({"model":"local_hgb","series":sid,"train_rows":int(local_train.sum()),"fit_wall_seconds":time.perf_counter()-start,"fit_cpu_seconds":time.process_time()-cpu})
            for split,mask in [("validation",val),("test",test)]:
                cohort=gold.loc[mask & gold.series_id.eq(sid)].copy()
                for name,prediction in [("global_hgb",global_model.predict(cohort[FEATURES])),("local_hgb",local.predict(cohort[local_features])),("persistence",cohort.lag2.to_numpy())]:
                    part=cohort[["series_id","forecast_origin","target_time","label_available_at","target"]].copy()
                    part["split"]=split; part["model"]=name; part["prediction"]=prediction
                    predictions.append(part)
    predictions=pd.concat(predictions,ignore_index=True)
    predictions.to_csv(directory/"previsoes_pareadas.csv",index=False,float_format="%.12g")
    metrics=[]
    for (split,model,sid),frame in predictions.groupby(["split","model","series_id"]):
        error=frame.prediction-frame.target
        metrics.append({"split":split,"model":model,"series_id":sid,"n":len(frame),"mae_mw":float(error.abs().mean()),"rmse_mw":float(np.sqrt(np.mean(error**2))),"bias_mw":float(error.mean())})
    for (split,model),frame in predictions.groupby(["split","model"]):
        error=frame.prediction-frame.target
        metrics.append({"split":split,"model":model,"series_id":"ALL_micro","n":len(frame),"mae_mw":float(error.abs().mean()),"rmse_mw":float(np.sqrt(np.mean(error**2))),"bias_mw":float(error.mean())})
    table=pd.DataFrame(metrics)
    table.to_csv(directory/"metricas_por_serie.csv",index=False)
    pd.DataFrame(timings).to_csv(directory/"recursos_treino.csv",index=False)
    # Estado treinado preservado como artefato local; não substitui registro operacional.
    import joblib
    joblib.dump(global_model,directory/"global_hgb.joblib")
    write_json(directory/"resultado.json",{"executed_at_utc":now(),"series":sorted(gold.series_id.unique()),"cohorts":{"train":int(train.sum()),"validation":int(val.sum()),"test":int(test.sum())},"train_max_origin":str(gold.loc[train,"forecast_origin"].max()),"train_max_label_available":str(gold.loc[train,"label_available_at"].max()),"strict_label_purge":bool(gold.loc[train,"label_available_at"].lt(TRAIN_CUTOFF).all()),"test_last_origin":str(gold.loc[test,"forecast_origin"].max()),"metrics":metrics,"fit_resources":timings,"normalization":"nenhuma; geração em MW; código categórico atribuído antes do fit; sem capacidade/cadastro externo", "scope":"estudo exploratório retrospectivo, 1 mês, 4 séries; não benchmark final intocado", "model_artifact_sha256":sha256(directory/"global_hgb.joblib"),"positive_gain_required":False,"operational_approval":False,"packages":{"sklearn":importlib.metadata.version("scikit-learn")}})


def write_reports():
    results={item:json.loads((BASE/item/"resultado.json").read_text(encoding="utf-8")) for item in IDS}
    layer=results["M07-01"]; inc=results["M07-03"]; model=results["M05-05"]
    reports={
        "M07-01":f"# Parecer de engenharia — camadas\n\nExecução atribuída a Codex, não a resposta independente do usuário. Bronze preservou os {layer['bronze']['bytes']:,} bytes e SHA256 original; silver tem {layer['outputs']['silver']['rows']:,} linhas, quarentena {layer['outputs']['quarantine']['rows']:,}, gold {layer['outputs']['gold']['rows']:,}. Duplicatas inteiras, ids ausentes, MW negativos/não finitos e horários inválidos não recebem imputação. A linhagem usa source_row na bronze e joins exatos de série/tempo na gold.\n\nSegunda construção de silver/quarentena/gold efetivamente executada; hashes lógicos e físicos iguais registrados em resultado.json. A disponibilidade t+2h é hipótese de estudo, não fonte histórica. Contraprova sintética separada testa rejeição. Aceite técnico local dos critérios C1/C2; sem Delta distribuído nem aprovação operacional.\n",
        "M07-03":f"# Parecer de engenharia — incremento\n\nReplay local fornecido/executado por Codex em quatro versões de estado, {inc['rows']} eventos reais de quatro séries. Um evento foi atrasado sinteticamente por sete dias; suas contribuições indisponíveis em origens anteriores permanecem nulas mesmo depois do reprocessamento. Não se infere chegada histórica do arquivo.\n\nFalha sintética após materializar estágio e antes de trocar o ponteiro preservou o estado; nova instância recuperou e concluiu o lote. Repetições foram noop e conflito de mesma chave foi rejeitado. Gold incremental e referência compartilham SHA256 lógico {inc['logical_incremental_sha256']}; mutação de outra série não altera a primeira. Aceite técnico local C1/C2, sem comprovar serviço distribuído, broker ou shadow.\n",
        "M05-05":f"# Parecer de engenharia — global multissérie\n\nSolução fornecida, executada e analisada por Codex. Seleção prévia por metadata: {', '.join(model['series'])}; 744 registros por série na origem. O mesmo outubro já estava no disco e uma outra série já fora examinada no bloco 2. Este é estudo retrospectivo exploratório novo nas quatro séries, não teste final intocado.\n\nForam comparados um HGB global, quatro HGB locais e persistência disponível t−2, nas mesmas origens e alvo t+1h. Treino só com label_available_at estritamente anterior a 16/10; maior disponibilidade admitida {model['train_max_label_available']}. Não houve normalizador ou cadastro externo, ajuste em validação/teste ou promoção do P1. Coortes totais: {model['cohorts']}.\n\nErro em MW e viés são comparados por série e microagregado. Escalas diferentes tornam MAE agregado sensível ao porte das usinas. A comparação não mede generalização para séries nunca vistas, outras estações, fuso validado ou disponibilidade histórica. Ganho positivo não condiciona aceite de engenharia C1/C2. Métricas completas no CSV e resultado.json; operação continua separada.\n",
    }
    scale=results["M07-02"]
    reports["M07-02"]="# Parecer de engenharia — escala local real\n\nForam executados 18 trials (dois motores × três coortes reais × três repetições), em processos separados. Coortes são prefixos determinísticos de id_ons; nenhuma linha foi replicada para ampliar artificialmente volume. O cronômetro cobre leitura de silver, filtro, LAG por série com guarda de intervalo exato de uma hora, agregação, Parquet e hash. Importação/startup e EXPLAIN ANALYZE ficam fora do tempo reportado.\n\nAs nove comparações pareadas de saída tiveram equivalência numérica com tolerância 1e-10, chaves e contagens exatas. Os planos observados mostram scan/filtro, WINDOW e agregação do DuckDB local. Não demonstram AQE, Spark ou cluster. Recursos: DuckDB threads=1 e memory_limit 512MB; pandas com threadpool=1 e RSS amostrado (sem limite rígido de SO). RSS, CPU, tempo, bytes e hashes estão preservados. Cache de SO não foi limpo; três medições curtas não permitem inferência causal de arquitetura ou extrapolação a big data.\n\n"+"\n".join(f"- {r['engine']} coorte {r['cohort']}: {r['rows']:,} linhas, mediana {r['wall_median']:.4f}s, CPU {r['cpu_median']:.4f}s, pico RSS {r['rss_peak']/1024**2:.1f} MiB." for r in scale['summary'])+"\n\nAceite aplicado C1/C2 sob o recorte local real. O motor mais rápido neste arquivo pequeno não é uma recomendação para dados distribuídos.\n"
    for item,body in reports.items():
        (BASE/item/"parecer.md").write_text(body,encoding="utf-8")
        artifacts=[]
        for path in sorted((BASE/item).rglob("*")):
            if path.is_file() and path.name!="manifesto_sha256.json":
                artifacts.append({"path":str(path.relative_to(ROOT)).replace("\\","/"),"sha256":sha256(path),"bytes":path.stat().st_size})
        write_json(BASE/item/"manifesto_sha256.json",{"generated_at_utc":now(),"files":artifacts})
    doc=ROOT/"docs/roadmap_m00_m09/Bloco_3_Dados.md"
    doc.write_text("# Bloco 3 — engenharia de dados e modelo global\n\n"+"\n".join(reports[item].replace("# Parecer de engenharia —", "##") for item in IDS)+"\n\nProtocolos foram congelados antes de cálculos/fit; código e fonte estão hasheados. Artefatos em reports/fechamento_m00_m09/bloco3_engenharia/{M07-01,M07-02,M07-03,M05-05}. A fonte foi preservada. Os testes pequenos são contraprovas fornecidas, não respostas independentes do usuário. Cadastro e autorização operacional são coordenados na revisão integrada; este documento não os substitui.\n",encoding="utf-8")


def execute():
    verify_freeze()
    print("Congelamento conferido; construindo camadas",flush=True)
    silver,gold=layer_run()
    print("Camadas prontas; executando replay",flush=True)
    incremental_run(silver)
    print("Replay pronto; executando modelos congelados",flush=True)
    model_run(gold)
    print("Modelos prontos; executando escala real",flush=True)
    scale_run()
    write_reports()
    print("Entrega de dados executada e manifestos gravados",flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["freeze","execute","worker"])
    parser.add_argument("--engine",choices=["pandas","duckdb"])
    parser.add_argument("--cohort",type=int)
    parser.add_argument("--repetition",type=int)
    args=parser.parse_args()
    if args.action=="freeze":freeze()
    elif args.action=="execute":execute()
    else:benchmark_worker(args.engine,args.cohort,args.repetition)
