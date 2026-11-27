"""Suplemento isolado: LAG antes do filtro mensal, sem repetir a agregacao diaria."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import hashlib
import json
import sqlite3
import sys
from time import perf_counter
import numpy as np
import pandas as pd


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    root = folder.parents[3]
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    if (folder/"contexto_resultado.json").exists() or (folder/"lag_com_contexto.csv").exists():
        raise ValueError("Suplemento ja existe; preservar os arquivos.")
    protocol = json.loads((folder/"adendo_contexto.json").read_text(encoding="utf-8"))
    source = root/protocol["source"]
    assert sha(source)==protocol["source_sha256"]
    assert sha(folder/"horario.csv")==protocol["original_hourly_sha256"]
    assert sha(folder/"lag_com_contexto.sql")==protocol["sql_sha256"]
    full = pd.read_parquet(source,columns=["din_instante","val_geracao"])
    times = pd.to_datetime(full.din_instante)
    selected = full.loc[times.ge(protocol["context_start_inclusive"])
                        & times.lt(protocol["analysis_end_exclusive"])].copy()
    selected.insert(0,"registro_id",selected.index+1)
    selected.insert(1,"id_ons","CJU_BA5EIGT")
    selected["din_instante"]=pd.to_datetime(selected.din_instante).dt.strftime("%Y-%m-%dT%H:%M:%S")
    calendar=pd.DataFrame({"id_ons":"CJU_BA5EIGT","din_instante":pd.date_range(
        protocol["context_start_inclusive"],protocol["analysis_end_exclusive"],freq="h",inclusive="left").strftime("%Y-%m-%dT%H:%M:%S")})
    with sqlite3.connect(":memory:") as con:
        selected.to_sql("recorte",con,index=False);calendar.to_sql("calendario",con,index=False)
        con.execute("PRAGMA query_only=ON")
        actual=pd.read_sql_query((folder/"lag_com_contexto.sql").read_text(encoding="utf-8"),con)
    counts=selected.groupby(["id_ons","din_instante"]).val_geracao.transform("size")
    clean=selected.loc[counts.eq(1)]
    expected=calendar.merge(clean[["id_ons","din_instante","val_geracao"]],
        how="left",on=["id_ons","din_instante"],validate="one_to_one",indicator=True)
    expected["registro_presente"]=expected.pop("_merge").eq("both").astype(int)
    expected=expected.sort_values(["id_ons","din_instante"]).reset_index(drop=True)
    groups=expected.groupby("id_ons")
    expected["instante_anterior_1h"]=groups.din_instante.shift()
    expected["valor_anterior_1h"]=groups.val_geracao.shift()
    expected["registro_anterior_presente"]=groups.registro_presente.shift()
    expected["delta_1h"]=expected.val_geracao-expected.valor_anterior_1h
    expected["estado_lag"]=np.select([
        expected.instante_anterior_1h.isna(),expected.registro_anterior_presente.eq(0),
        expected.valor_anterior_1h.isna()],
        ["fronteira_do_recorte","hora_anterior_sem_registro","medicao_anterior_nula"],default="lag_disponivel")
    # Janela ja calculada. So agora o recorte mensal.
    expected=expected.loc[expected.din_instante.ge(protocol["analysis_start_inclusive"])
        & expected.din_instante.lt(protocol["analysis_end_exclusive"]),actual.columns].reset_index(drop=True)
    module_spec=importlib.util.spec_from_file_location("engineering_sql_checks",folder/"executar.py")
    checks=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(checks)
    comparison=checks.compare(actual,expected)
    assert len(actual)==720
    first=actual.iloc[0]
    previous=selected.loc[selected.din_instante.eq(protocol["context_start_inclusive"])]
    previous_is_valid=len(previous)==1 and pd.notna(previous.val_geracao.iloc[0])
    if previous_is_valid:
        assert first.instante_anterior_1h==protocol["context_start_inclusive"]
        assert first.valor_anterior_1h==float(previous.val_geracao.iloc[0])
        assert int(actual.valor_anterior_1h.notna().sum())==720
        assert int(actual.delta_1h.notna().sum())==720
    with (folder/"lag_com_contexto.csv").open("x",encoding="utf-8",newline="") as f:
        actual.to_csv(f,index=False,float_format="%.17g")
    assert sha(source)==protocol["source_sha256"]
    assert sha(folder/"horario.csv")==protocol["original_hourly_sha256"]
    result={"schema":"renewcast-lag-context-engineering-result-v1","completed":True,
        "started_at_utc":started,"completed_at_utc":datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds":perf_counter()-timer,"command":[sys.executable,str(Path(__file__).resolve())],"exit_code":0,
        "versions":{"python":sys.version.split()[0],"pandas":pd.__version__,"numpy":np.__version__,"sqlite":sqlite3.sqlite_version},
        "adendo_sha256":sha(folder/"adendo_contexto.json"),
        "code_sha256":{Path(__file__).name:sha(__file__),"executar.py":sha(folder/"executar.py")},
        "input_sha256":{protocol["source"]:sha(source),"lag_com_contexto.sql":sha(folder/"lag_com_contexto.sql")},
        "source_rows_with_context":len(selected),"calendar_rows_with_context":len(calendar),
        "analysis_rows":len(actual),"known_lags":int(actual.valor_anterior_1h.notna().sum()),
        "valid_delta_pairs":int(actual.delta_1h.notna().sum()),"previous_hour_present_and_valid":bool(previous_is_valid),
        "first_november_hour":json.loads(actual.iloc[:1].to_json(orient="records",double_precision=15))[0],
        "sql_pandas_comparison":comparison,"output_sha256":{"lag_com_contexto.csv":sha(folder/"lag_com_contexto.csv")},
        "original_no_context_output_preserved":True,"original_known_lags":719,
        "models_trained":False,"models_inferred":False,"new_predictive_test":False,
        "assistance":"Technical implementation and analysis supplied by Codex."}
    with (folder/"contexto_resultado.json").open("x",encoding="utf-8",newline="\n") as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
    print(json.dumps(result,ensure_ascii=True))


if __name__=="__main__":
    main()
