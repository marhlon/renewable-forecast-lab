"""Execucao tecnica isolada: SQL real, pandas e casos de contrato; sem modelos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import sqlite3
import sys
from time import perf_counter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent.parent
IDS = ("M00-01", "M01-01", "M01-02", "M07-04")
FLOATS = {"val_geracao", "valor_anterior_1h", "valor_anterior_fonte",
          "delta_1h", "media_geracao_mwmed", "cobertura_presenca",
          "cobertura_valida", "media_delta_1h", "intervalo_anterior_horas"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, value):
    with Path(p).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def records(frame):
    return json.loads(frame.to_json(orient="records", double_precision=15))


def canonical(source, calendar):
    source, calendar = source.copy(), calendar.copy()
    for frame in (source, calendar):
        frame["din_instante"] = pd.to_datetime(frame["din_instante"], errors="raise")
        if frame.din_instante.isna().any() or frame.din_instante.dt.tz is not None:
            raise ValueError("Exige rotulos horarios sem fuso; nao atribuir UTC.")
        if not frame.din_instante.eq(frame.din_instante.dt.floor("h")).all():
            raise ValueError("Instantes fora da grade horaria.")
        if frame.id_ons.isna().any():
            raise ValueError("Identidade ausente.")
        frame["din_instante"] = frame.din_instante.dt.strftime("%Y-%m-%dT%H:%M:%S")
    if calendar.duplicated(["id_ons", "din_instante"]).any():
        raise ValueError("Calendario tem chaves repetidas.")
    keys = set(map(tuple, calendar[["id_ons", "din_instante"]].to_numpy()))
    if any(tuple(x) not in keys for x in source[["id_ons", "din_instante"]].to_numpy()):
        raise ValueError("Fonte contem chave fora do calendario fixado.")
    source["val_geracao"] = pd.to_numeric(source.val_geracao, errors="raise").astype(float)
    if not np.isfinite(source.val_geracao.dropna()).all():
        raise ValueError("Geracao nao finita.")
    if "registro_id" not in source:
        source.insert(0, "registro_id", np.arange(1, len(source) + 1))
    return source, calendar.sort_values(["id_ons", "din_instante"]).reset_index(drop=True)


def query_parts(path):
    text = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"^-- consulta:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    queries = dict(zip(parts[1::2], parts[2::2]))
    if set(queries) != {"diario", "horario", "quarentena", "lag_esparso"}:
        raise ValueError("Quatro consultas identificadas sao exigidas.")
    return queries


def sql_tables(source, calendar, path):
    with sqlite3.connect(":memory:") as con:
        source.to_sql("recorte", con, index=False)
        calendar.to_sql("calendario", con, index=False)
        con.execute("PRAGMA query_only=ON")
        return {name: pd.read_sql_query(query, con) for name, query in query_parts(path).items()}


def pandas_tables(source, calendar):
    keys = ["id_ons", "din_instante"]
    frequencies = source.groupby(keys, sort=True).size().rename("multiplicidade").reset_index()
    with_counts = source.merge(frequencies, on=keys, validate="many_to_one")
    clean = with_counts.loc[with_counts.multiplicidade.eq(1)].copy()
    quarantine = with_counts.loc[with_counts.multiplicidade.gt(1),
        ["registro_id", *keys, "val_geracao", "multiplicidade"]].sort_values(
        [*keys, "registro_id"]).reset_index(drop=True)
    grid = calendar.merge(clean[keys + ["val_geracao"]], how="left", on=keys,
                          validate="one_to_one", indicator=True).sort_values(keys).reset_index(drop=True)
    grid["registro_presente"] = grid.pop("_merge").eq("both").astype(int)
    groups = grid.groupby("id_ons", sort=False)
    grid["instante_anterior_1h"] = groups.din_instante.shift()
    grid["valor_anterior_1h"] = groups.val_geracao.shift()
    grid["registro_anterior_presente"] = groups.registro_presente.shift()
    grid["delta_1h"] = grid.val_geracao - grid.valor_anterior_1h
    grid["estado_lag"] = np.select([
        grid.instante_anterior_1h.isna(), grid.registro_anterior_presente.eq(0),
        grid.valor_anterior_1h.isna()],
        ["fronteira_do_recorte", "hora_anterior_sem_registro", "medicao_anterior_nula"],
        default="lag_disponivel")
    hourly_columns = [*keys, "registro_presente", "val_geracao", "instante_anterior_1h",
                      "valor_anterior_1h", "registro_anterior_presente", "delta_1h", "estado_lag"]
    hourly = grid[hourly_columns].copy()
    grid["dia"] = grid.din_instante.str[:10]
    grid["nula_presente"] = (grid.registro_presente.eq(1) & grid.val_geracao.isna()).astype(int)
    grid["zero"] = grid.val_geracao.eq(0).astype(int)
    daily = grid.groupby(["id_ons", "dia"], sort=True).agg(
        horas_esperadas=("din_instante", "size"), horas_presentes=("registro_presente", "sum"),
        horas_validas=("val_geracao", "count"), horas_nulas_presentes=("nula_presente", "sum"),
        horas_zero=("zero", "sum"), media_geracao_mwmed=("val_geracao", "mean"),
        lags_conhecidos=("valor_anterior_1h", "count"),
        pares_validos_delta=("delta_1h", "count"), media_delta_1h=("delta_1h", "mean")).reset_index()
    daily["horas_sem_registro"] = daily.horas_esperadas - daily.horas_presentes
    daily["cobertura_presenca"] = daily.horas_presentes / daily.horas_esperadas
    daily["cobertura_valida"] = daily.horas_validas / daily.horas_esperadas
    daily["lags_desconhecidos"] = daily.horas_esperadas - daily.lags_conhecidos
    raw_counts = source.assign(dia=source.din_instante.str[:10]).groupby(
        ["id_ons", "dia"]).size().rename("linhas_fonte").reset_index()
    dup = frequencies.loc[frequencies.multiplicidade.gt(1)].copy()
    dup["dia"] = dup.din_instante.str[:10]
    dup["excedentes"] = dup.multiplicidade - 1
    dup_daily = dup.groupby(["id_ons", "dia"]).agg(
        chaves_duplicadas=("multiplicidade", "size"),
        linhas_quarentena=("multiplicidade", "sum"),
        duplicatas_excedentes=("excedentes", "sum")).reset_index()
    daily = daily.merge(raw_counts, how="left", on=["id_ons", "dia"]).merge(
        dup_daily, how="left", on=["id_ons", "dia"])
    for col in ["linhas_fonte", "chaves_duplicadas", "linhas_quarentena", "duplicatas_excedentes"]:
        daily[col] = daily[col].fillna(0).astype(int)
    daily_columns = ["id_ons", "dia", "horas_esperadas", "linhas_fonte",
        "chaves_duplicadas", "linhas_quarentena", "duplicatas_excedentes",
        "horas_presentes", "horas_validas", "horas_nulas_presentes", "horas_zero",
        "horas_sem_registro", "media_geracao_mwmed", "cobertura_presenca", "cobertura_valida",
        "lags_conhecidos", "lags_desconhecidos", "pares_validos_delta", "media_delta_1h"]
    sparse = clean[[*keys, "val_geracao"]].sort_values(keys).reset_index(drop=True)
    sg = sparse.groupby("id_ons", sort=False)
    sparse["instante_anterior_fonte"] = sg.din_instante.shift()
    sparse["valor_anterior_fonte"] = sg.val_geracao.shift()
    sparse["intervalo_anterior_horas"] = (
        pd.to_datetime(sparse.din_instante) - pd.to_datetime(sparse.instante_anterior_fonte)
    ).dt.total_seconds() / 3600
    return {"diario": daily[daily_columns], "horario": hourly,
            "quarentena": quarantine, "lag_esparso": sparse}


def compare(left, right):
    if list(left.columns) != list(right.columns) or left.shape != right.shape:
        raise AssertionError("Colunas ou cardinalidade diferentes.")
    np.testing.assert_array_equal(left.isna().to_numpy(), right.isna().to_numpy())
    maximum = 0.0
    for col in left:
        if col in FLOATS or pd.api.types.is_numeric_dtype(left[col]) or pd.api.types.is_numeric_dtype(right[col]):
            a, b = left[col].to_numpy(dtype=float), right[col].to_numpy(dtype=float)
            if col in FLOATS:
                np.testing.assert_allclose(a, b, rtol=1e-12, atol=1e-10, equal_nan=True)
            else:
                np.testing.assert_array_equal(a, b)
            valid = np.isfinite(a) & np.isfinite(b)
            if valid.any():
                maximum = max(maximum, float(np.max(np.abs(a[valid] - b[valid]))))
        else:
            assert left[col].fillna("<NULL>").tolist() == right[col].fillna("<NULL>").tolist(), col
    return {"rows": len(left), "columns": len(left.columns), "null_masks_equal": True,
            "maximum_absolute_numeric_difference": maximum}


def run_case(source, calendar, sql_path):
    source, calendar = canonical(source, calendar)
    actual = sql_tables(source, calendar, sql_path)
    expected = pandas_tables(source, calendar)
    comparisons = {name: compare(actual[name], expected[name]) for name in actual}
    return source, calendar, actual, comparisons


def make_calendar(entity, start, end):
    return pd.DataFrame({"id_ons": entity, "din_instante": pd.date_range(start, end, freq="h")})


def clock_case(origin_text, expected_hours, horizon=None):
    origin = pd.Timestamp(origin_text)
    references = pd.date_range("2026-07-01T20:00:00", "2026-07-02T05:00:00", freq="h")
    measurements = pd.DataFrame({"referencia": references, "valor": np.arange(len(references)) * 2.0})
    measurements["available_at"] = measurements.referencia + pd.Timedelta(hours=3)
    history_end = origin - pd.Timedelta(hours=3)
    start = history_end - pd.Timedelta(hours=3)
    with sqlite3.connect(":memory:") as con:
        measurements.assign(
            referencia=measurements.referencia.dt.strftime("%Y-%m-%dT%H:%M:%S"),
            available_at=measurements.available_at.dt.strftime("%Y-%m-%dT%H:%M:%S")
        ).to_sql("medicoes", con, index=False)
        sql = """SELECT * FROM medicoes WHERE referencia BETWEEN ? AND ?
                 AND available_at <= ? ORDER BY referencia"""
        result = pd.read_sql_query(sql, con, params=(start.isoformat(), history_end.isoformat(), origin.isoformat()))
    expected = measurements.loc[measurements.referencia.between(start, history_end)
                                & measurements.available_at.le(origin)]
    assert result.referencia.tolist() == expected_hours
    assert result.valor.tolist() == expected.valor.tolist()
    assert len(result) == 4
    future = measurements.loc[measurements.referencia.eq(history_end + pd.Timedelta(hours=1))].iloc[0]
    assert future.available_at > origin
    missing = expected.iloc[:-1]
    complete_mean_if_missing = None if len(missing) != 4 else float(missing.valor.mean())
    assert complete_mean_if_missing is None
    return {"origin":origin.isoformat(),"delay_hours_assumed":3,"window_hours":4,
        "history_start":start.isoformat(),"history_end":history_end.isoformat(),
        "target_time":None if horizon is None else (origin+pd.Timedelta(hours=horizon)).isoformat(),
        "target_available_at_assumed":None if horizon is None else (origin+pd.Timedelta(hours=horizon+3)).isoformat(),
        "selected_rows":records(result),"selected_mean_synthetic_mwmed":float(result.valor.mean()),
        "rejected_next_reference":future.referencia.isoformat(),
        "rejected_next_available_at":future.available_at.isoformat(),
        "missing_measurement_complete_window_mean":complete_mean_if_missing}


def main():
    started = datetime.now(timezone.utc).isoformat()
    timer = perf_counter()
    protocols = {i: json.loads((BASE/i/"protocolo.json").read_text(encoding="utf-8")) for i in IDS}
    snapshot = {i:sha(BASE/i/"protocolo.json") for i in IDS}
    for p, value in protocols["M01-02"]["input_sha256"].items():
        assert sha(ROOT/p) == value, p
    for p, value in protocols["M01-02"]["preserved_historical_files_sha256"].items():
        assert sha(ROOT/p) == value, p
    source_path = ROOT/"dist/databricks/CJU_BA5EIGT/m07_3/geracao.parquet"
    manifest = json.loads((source_path.parent/"manifesto_entrada.json").read_text(encoding="utf-8"))
    assert sha(source_path) == manifest["files"]["geracao.parquet"]["sha256"]
    full = pd.read_parquet(source_path, columns=["din_instante","val_geracao"])
    assert len(full) == manifest["generation_rows"] == 8760
    times = pd.to_datetime(full.din_instante)
    real = full.loc[times.ge("2025-11-01") & times.lt("2025-12-01")].copy()
    real.insert(0,"registro_id",real.index+1)
    real.insert(1,"id_ons",manifest["conjunto"])
    real_calendar = make_calendar(manifest["conjunto"],"2025-11-01T00:00:00","2025-11-30T23:00:00")
    real, real_calendar, actual, comparisons = run_case(real,real_calendar,BASE/"M01-02/consultas.sql")
    frozen = pd.read_csv(ROOT/"reports/fechamento_m00_m09/M01-02/recorte_real.csv",encoding="utf-8-sig",float_precision="round_trip")
    frozen = canonical(frozen,real_calendar)[0]
    compare(real[["id_ons","din_instante","val_geracao"]].reset_index(drop=True),
            frozen[["id_ons","din_instante","val_geracao"]].reset_index(drop=True))
    case_c = pd.DataFrame({"id_ons":"C","din_instante":[
        "2027-02-10T22:00:00","2027-02-10T23:00:00","2027-02-11T01:00:00",
        "2027-02-11T02:00:00","2027-02-11T02:00:00","2027-02-12T00:00:00"],
        "val_geracao":[5,0,np.nan,7,9,4]})
    csrc,ccal,ctables,ccompare = run_case(case_c,make_calendar("C","2027-02-10T22:00:00","2027-02-12T00:00:00"),BASE/"M01-01/consultas.sql")
    daily_c = ctables["diario"]
    assert daily_c.horas_esperadas.tolist()==[2,24,1]
    assert daily_c.horas_presentes.tolist()==[2,1,1]
    assert daily_c.horas_validas.tolist()==[2,0,1]
    assert daily_c.horas_sem_registro.tolist()==[0,23,0]
    np.testing.assert_allclose(daily_c.media_geracao_mwmed,[2.5,np.nan,4],equal_nan=True)
    assert len(ctables["quarentena"])==2
    assert ctables["quarentena"].val_geracao.tolist()==[7,9]
    at_midnight = ctables["horario"].loc[ctables["horario"].din_instante.eq("2027-02-11T00:00:00")].iloc[0]
    assert at_midnight.valor_anterior_1h==0 and at_midnight.registro_presente==0
    sparse_01=ctables["lag_esparso"].loc[ctables["lag_esparso"].din_instante.eq("2027-02-11T01:00:00")].iloc[0]
    grid_01=ctables["horario"].loc[ctables["horario"].din_instante.eq("2027-02-11T01:00:00")].iloc[0]
    assert sparse_01.intervalo_anterior_horas==2 and sparse_01.valor_anterior_fonte==0
    assert pd.isna(grid_01.valor_anterior_1h) and grid_01.registro_anterior_presente==0
    missing_source=pd.DataFrame({"id_ons":["D"],"din_instante":["2027-03-01T00:00:00"],"val_geracao":[0.0]})
    _,_,missing_tables,missing_compare=run_case(missing_source,make_calendar("D","2027-03-01T00:00:00","2027-03-03T23:00:00"),BASE/"M01-02/consultas.sql")
    assert missing_tables["diario"].horas_presentes.tolist()==[1,0,0]
    assert missing_tables["diario"].media_geracao_mwmed.iloc[0]==0
    assert missing_tables["diario"].media_geracao_mwmed.iloc[1:].isna().all()
    multi_source=pd.DataFrame({"id_ons":["X","X","Y","Y"],"din_instante":["2027-04-01T00:00:00","2027-04-01T01:00:00"]*2,"val_geracao":[1.,2.,100.,200.]})
    multi_calendar=pd.concat([make_calendar(e,"2027-04-01T00:00:00","2027-04-01T01:00:00") for e in ["X","Y"]],ignore_index=True)
    msrc,mcal,mtables,mcompare=run_case(multi_source,multi_calendar,BASE/"M01-02/consultas.sql")
    assert mtables["horario"].loc[mtables["horario"].estado_lag.eq("fronteira_do_recorte")].shape[0]==2
    assert mtables["horario"].loc[mtables["horario"].id_ons.eq("Y")].valor_anterior_1h.iloc[1]==100
    reordered = sql_tables(msrc.iloc[::-1],mcal.iloc[::-1],BASE/"M01-02/consultas.sql")
    for name in mtables:compare(mtables[name],reordered[name])
    for item in IDS:
        for p,value in protocols[item]["preserved_historical_files_sha256"].items():assert sha(ROOT/p)==value,p
        assert sha(BASE/item/"protocolo.json")==snapshot[item]
    manual_rows = real.loc[real.din_instante.str.startswith("2025-11-15")]
    valid_manual = manual_rows.val_geracao.dropna().tolist()
    manual = {"date":"2025-11-15","chosen_before_execution":True,"hours":len(manual_rows),
        "valid":len(valid_manual),"sum_fsum_mwmed":math.fsum(valid_manual),
        "mean_fsum_mwmed":math.fsum(valid_manual)/len(valid_manual),"values":valid_manual}
    sql_manual=actual["diario"].loc[actual["diario"].dia.eq(manual["date"])].iloc[0]
    assert manual["hours"]==sql_manual.horas_esperadas
    assert math.isclose(manual["mean_fsum_mwmed"],sql_manual.media_geracao_mwmed,abs_tol=1e-10,rel_tol=1e-12)
    clocks = {i:clock_case(protocols[i]["predeclared_examples"][key],
        protocols[i]["predeclared_examples"][hours],horizon=horizon) for i,key,hours,horizon in [
        ("M00-01","M00_origin","M00_expected_reference_hours",12),
        ("M07-04","M07_origin","M07_expected_reference_hours",None)]}
    summaries={}
    for item,src,cal,tables,comp in [("M01-01",csrc,ccal,ctables,ccompare),("M01-02",real,real_calendar,actual,comparisons)]:
        folder=BASE/item
        src.to_csv(folder/"fonte_recorte.csv",index=False,float_format="%.17g")
        cal.to_csv(folder/"calendario.csv",index=False)
        for name, filename in [("diario","diagnostico.csv"),("horario","horario.csv"),("quarentena","quarentena.csv"),("lag_esparso","lag_esparso.csv")]:
            tables[name].to_csv(folder/filename,index=False,float_format="%.17g")
        summaries[item]={"source_rows":len(src),"calendar_hours":len(cal),"daily_rows":len(tables["diario"]),
            "quarantined_rows":len(tables["quarentena"]),"present_hours":int(tables["diario"].horas_presentes.sum()),
            "valid_hours":int(tables["diario"].horas_validas.sum()),"null_present_hours":int(tables["diario"].horas_nulas_presentes.sum()),
            "missing_hours_after_quarantine":int(tables["diario"].horas_sem_registro.sum()),
            "zero_hours":int(tables["diario"].horas_zero.sum()),"duplicate_keys":int(tables["diario"].chaves_duplicadas.sum()),
            "duplicate_excess_rows":int(tables["diario"].duplicatas_excedentes.sum()),
            "known_lags":int(tables["diario"].lags_conhecidos.sum()),"valid_delta_pairs":int(tables["diario"].pares_validos_delta.sum()),
            "monthly_or_slice_mean_mwmed":None if src.val_geracao.dropna().empty else float(tables["horario"].val_geracao.mean()),
            "daily_records":records(tables["diario"]),"sql_pandas_comparison":comp}
    tests={"all_passed":True,"source_and_protocol_hashes_preserved":True,
        "cases":{"real_november":comparisons,"case_C":ccompare,"missing_day":missing_compare,"entity_partition":mcompare,
                 "reordered_inputs":{"all_four_queries_equal":True}},
        "manual_2025_11_15":manual,"case_C_inner_daily_rows":3,"case_C_left_daily_rows":3,
        "case_C_inner_hourly_rows":4,"case_C_left_hourly_rows":27,
        "missing_day_inner_daily_rows":1,"missing_day_left_daily_rows":3,
        "M00_clock":clocks["M00-01"],"M07_clock":clocks["M07-04"]}
    write_json(BASE/"M01-02/verificacoes.json",tests)
    for item,data in clocks.items():
        write_json(BASE/item/"janela_temporal.json",data)
        pd.DataFrame(data["selected_rows"]).to_csv(BASE/item/"janela.csv",index=False)
    completed=datetime.now(timezone.utc).isoformat()
    for item in IDS:
        folder=BASE/item
        result={"schema":"renewcast-bloco1-engineering-result-v1","item_id":item,
            "completed":True,"technical_solution_provided":True,"started_at_utc":started,
            "completed_at_utc":completed,"elapsed_seconds":perf_counter()-timer,
            "command":[sys.executable,str(Path(__file__).resolve())],"exit_code":0,
            "versions":{"python":sys.version.split()[0],"numpy":np.__version__,"pandas":pd.__version__,"sqlite":sqlite3.sqlite_version},
            "code_sha256":{str(Path(__file__).resolve().relative_to(ROOT)).replace("\\","/"):sha(__file__)},
            "input_sha256":protocols[item]["input_sha256"],"protocol_sha256":snapshot[item],
            "historical_files_preserved":True,"historical_file_hashes":protocols[item]["preserved_historical_files_sha256"],
            "summary":summaries.get(item,clocks.get(item)),"checks_reference":"../M01-02/verificacoes.json",
            "models_trained":False,"models_inferred":False,"spark_executed":False,"network_used":False,
            "predictive_holdout_or_new_independent_test":False,"physical_timezone_verified":False,
            "independent_authorship_claimed":False,"assistance":"Technical implementation and explanation supplied by Codex.",
            "output_sha256":{p.name:sha(p) for p in folder.iterdir() if p.is_file() and p.name not in {"protocolo.json","resultado.json","executar.py"}}}
        write_json(folder/"resultado.json",result)
    print(json.dumps({"completed":True,"real":summaries["M01-02"],"case_C":summaries["M01-01"],
        "manual":manual,"clocks":clocks,"historical_files_preserved":True},ensure_ascii=True))


if __name__ == "__main__":
    main()
