"""Bootstrap real em previsoes salvas; usa a CLI congelada, sem refit."""
from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter
import hashlib
import json
import os
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent.parent
ITEMS = {24: "M02-08", 6: "M02-07"}
SOURCE_DIRS = {24: "july_development_h24", 6: "july_development"}
MODULE = "src/renewable_forecast/weather_gain_uncertainty.py"
PARAMETERS = {"block_hours": [6, 24, 48], "repetitions": 5000, "seed": 42}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, value):
    with Path(p).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def records(frame):
    return json.loads(frame.to_json(orient="records", double_precision=15))


def validate_saved_predictions(source_dir, horizon):
    frame = pd.read_csv(source_dir/"predictions.csv", float_precision="round_trip")
    metadata = json.loads((source_dir/"metadata.json").read_text(encoding="utf-8"))
    assert sha(source_dir/"predictions.csv") == metadata["output_sha256"]["predictions.csv"]
    assert sha(source_dir/"protocol.json") == metadata["protocol_sha256"]
    assert len(frame) == metadata["validation_rows"] == 504
    origin = pd.to_datetime(frame.forecast_origin, utc=True)
    target = pd.to_datetime(frame.target_time, utc=True)
    assert not origin.duplicated().any()
    assert (target-origin).eq(pd.Timedelta(hours=horizon)).all()
    assert (pd.to_datetime(frame.target_available_at,utc=True)-target).eq(pd.Timedelta(hours=2)).all()
    summary = pd.read_csv(source_dir/"summary.csv", float_precision="round_trip")
    y = frame.target_generation.to_numpy(float)
    maes = {m: float(np.abs(y-frame[m].to_numpy(float)).mean())
            for m in ["persistence","hgb_history","hgb_history_weather"]}
    metric_checks = []
    max_difference = 0.
    for model in maes:
        residual = y-frame[model].to_numpy(float)
        np.testing.assert_allclose(frame["absolute_error_"+model],np.abs(residual),rtol=1e-12,atol=1e-10)
        fold_bias = [abs(float((g.target_generation-g[model]).mean()))
                     for _,g in frame.groupby("fold",sort=True)]
        computed = {"rows":len(frame),"mae":maes[model],
            "rmse":float(np.sqrt(np.mean(residual**2))),"signed_bias":float(residual.mean()),
            "mae_gain_vs_history_pct":(maes["hgb_history"]-maes[model])/maes["hgb_history"]*100,
            "mae_gain_vs_persistence_pct":(maes["persistence"]-maes[model])/maes["persistence"]*100,
            "mean_absolute_fold_bias":float(np.mean(fold_bias))}
        saved = summary.loc[summary.method.eq(model)].iloc[0]
        for k,v in computed.items():
            np.testing.assert_allclose(v,saved[k],rtol=1e-12,atol=1e-10)
            max_difference=max(max_difference,abs(float(v)-float(saved[k])))
        metric_checks.append({"model":model,"recomputed":computed})
    delta = np.abs(y-frame.hgb_history)-np.abs(y-frame.hgb_history_weather)
    np.testing.assert_allclose(delta,frame.delta_absolute_error,rtol=1e-12,atol=1e-10)
    folds = pd.read_csv(source_dir/"folds.csv")
    for _,row in folds.iterrows():
        part = frame.loc[frame.fold.eq(row.fold)]
        times = pd.to_datetime(part.forecast_origin,utc=True)
        assert len(part)==int(row.valid_rows)==168
        assert times.min()==pd.Timestamp(row.valid_start)
        assert times.max()==pd.Timestamp(row.valid_end)
        assert times.sort_values().diff().iloc[1:].eq(pd.Timedelta(hours=1)).all()
    return frame,{"historical_summary_checks":metric_checks,
        "maximum_historical_summary_absolute_difference":max_difference,
        "fold_sizes":{str(int(fold)):len(g) for fold,g in frame.groupby("fold")},
        "origin_start":origin.min().isoformat(),"origin_end":origin.max().isoformat(),
        "targets_differ_by_horizon":True}


def persistence_adapter(frame, folder, source_path):
    cols=["forecast_origin","target_time","target_available_at","fold",
          "target_generation","persistence","hgb_history_weather"]
    derived=frame[cols].copy()
    derived["original_hgb_history"]=frame.hgb_history
    derived["hgb_history"]=frame.persistence
    derived["reference_model"]="persistence"
    derived["delta_absolute_error"]=(derived.target_generation-derived.hgb_history).abs()-(derived.target_generation-derived.hgb_history_weather).abs()
    for column in cols:
        pd.testing.assert_series_equal(derived[column],frame[column],check_exact=True)
    path=folder/"pareado_persistencia.csv"
    with path.open("x",encoding="utf-8",newline="") as f:
        derived.to_csv(f,index=False,float_format="%.17g")
    lineage={"source_path":source_path.relative_to(ROOT).as_posix(),"source_sha256":sha(source_path),
        "derived_path":path.relative_to(ROOT).as_posix(),"derived_sha256":sha(path),
        "rows":len(derived),"keys":["forecast_origin","target_time","fold"],
        "preserved_exactly":cols,"mapping":{"CLI_hgb_history":"source.persistence",
        "CLI_hgb_history_weather":"source.hgb_history_weather","original_hgb_history":"source.hgb_history"},
        "estimand":"abs(y-persistence) - abs(y-HGB_history_weather), MWmed",
        "source_delta_not_reused":"Derived delta is recomputed for the new reference; original source remains unchanged.",
        "new_training_or_predictions":False}
    write_json(folder/"linhagem_persistencia.json",lineage)
    return path,derived


def validate_cli_summary(summary, frame):
    assert len(summary)==12
    assert sorted(summary.block_hours.unique().tolist())==[6,24,48]
    assert not summary.duplicated(["scope","fold","block_hours"]).any()
    assert summary.repetitions.eq(5000).all() and summary.seed.eq(42).all()
    assert summary.confidence_level.eq(.95).all()
    assert summary.bootstrap_fraction_nonpositive.between(0,1).all()
    assert summary.ci95_low_mwmed.le(summary.ci95_high_mwmed).all()
    maximum=0.
    for block in [6,24,48]:
        for fold,part in [(None,frame),*list(frame.groupby("fold",sort=True))]:
            mask=summary.scope.eq("aggregate") if fold is None else summary.scope.eq("fold") & summary.fold.eq(fold)
            row=summary.loc[mask & summary.block_hours.eq(block)]
            assert len(row)==1
            row=row.iloc[0]
            assert int(row.n)==len(part)
            ref=float((part.target_generation-part.hgb_history).abs().mean())
            candidate=float((part.target_generation-part.hgb_history_weather).abs().mean())
            gain=float(((part.target_generation-part.hgb_history).abs()
                      -(part.target_generation-part.hgb_history_weather).abs()).mean())
            for k,v in {"mae_history_mwmed":ref,"mae_history_weather_mwmed":candidate,
                        "mean_gain_mwmed":gain}.items():
                np.testing.assert_allclose(row[k],v,rtol=1e-12,atol=1e-10)
                maximum=max(maximum,abs(float(row[k])-v))
        foldrows=summary.loc[summary.scope.eq("fold") & summary.block_hours.eq(block)]
        aggregate=summary.loc[summary.scope.eq("aggregate") & summary.block_hours.eq(block)].iloc[0]
        np.testing.assert_allclose(np.average(foldrows.mean_gain_mwmed,weights=foldrows.n),
                                   aggregate.mean_gain_mwmed,rtol=1e-12,atol=1e-10)
    assert np.isfinite(summary.select_dtypes(include="number").drop(columns="fold").to_numpy()).all()
    return {"summary_rows":12,"all_point_estimates_and_maes_match":True,
        "counts_and_fold_weights_match":True,"maximum_point_estimate_absolute_difference":maximum,
        "intervals_finite_and_ordered":True,"fraction_nonpositive_is_not_p_value":True,
        "bootstrap_replicas_not_persisted":"Quantiles are produced by the unchanged CLI covered by prior M02-05 tests; this audit checks saved summaries, hashes and point estimates without repeating bootstrap draws."}


def execute_cli(source, expected_frame, folder, comparison):
    out=folder/("cli_"+comparison)
    command=[sys.executable,"-m","renewable_forecast.weather_gain_uncertainty",
        "--predictions",str(source.resolve()),"--output-dir",str(out.resolve()),
        "--block-hours","6","24","48","--repetitions","5000","--seed","42"]
    env=dict(os.environ);env["PYTHONPATH"]=str(ROOT/"src")+os.pathsep+env.get("PYTHONPATH","")
    started=datetime.now(timezone.utc).isoformat()
    run=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",
                       errors="replace",cwd=ROOT,env=env,timeout=120)
    execution={"command":command,"started_at_utc":started,
        "finished_at_utc":datetime.now(timezone.utc).isoformat(),"exit_code":run.returncode,
        "stdout":run.stdout,"stderr":run.stderr}
    if run.returncode!=0:
        write_json(folder/("falha_"+comparison+".json"),execution)
        raise RuntimeError("CLI failed: "+run.stderr)
    receipt=json.loads((out/"receipt.json").read_text(encoding="utf-8"))
    assert receipt["completed"] and receipt["exit_code"]==0
    assert receipt["code"]["sha256"]==sha(ROOT/MODULE)
    assert receipt["input"]["sha256"]==sha(source)
    assert receipt["output_sha256"]["summary.csv"]==sha(out/"summary.csv")
    assert receipt["parameters"]=={**PARAMETERS,"confidence_level":.95}
    summary=pd.read_csv(out/"summary.csv",float_precision="round_trip")
    checks=validate_cli_summary(summary,expected_frame)
    name="bootstrap.csv" if comparison=="historia" else "bootstrap_vs_persistencia.csv"
    with (folder/name).open("xb") as f:f.write((out/"summary.csv").read_bytes())
    return {"execution":execution,"receipt_path":(out/"receipt.json").relative_to(ROOT).as_posix(),
        "receipt_sha256":sha(out/"receipt.json"),"summary_sha256":sha(out/"summary.csv"),
        "checks":checks,"all_summary_rows":records(summary),
        "aggregate_rows":records(summary.loc[summary.scope.eq("aggregate")])}


def main():
    started=datetime.now(timezone.utc).isoformat();timer=perf_counter()
    protocols={h:json.loads((BASE/item/"protocolo.json").read_text(encoding="utf-8")) for h,item in ITEMS.items()}
    for h,item in ITEMS.items():
        if (BASE/item/"resultado.json").exists():raise RuntimeError("Outputs already frozen.")
        for group in ["input_sha256","frozen_method_sha256","prior_construction_evidence_sha256"]:
            for name,value in protocols[h][group].items():assert sha(ROOT/name)==value,name
    prior_path=ROOT/"reports/fechamento_m00_m09/M02-05/resultado.json"
    prior=json.loads(prior_path.read_text(encoding="utf-8"))
    assert prior["completed"] and prior["exit_code"]==0
    assert prior["test_counts"]=={"passed":59,"failed":0,"skipped":0}
    assert prior["code_sha256"][MODULE]==sha(ROOT/MODULE)
    for name,value in prior["code_sha256"].items():assert sha(ROOT/name)==value
    for name,value in prior["output_sha256"].items():assert sha(prior_path.parent/name)==value
    results={}
    for horizon,item in ITEMS.items():
        folder=BASE/item
        source_dir=ROOT/"reports/weather_ablation/CJU_BA5EIGT"/SOURCE_DIRS[horizon]
        frame,input_checks=validate_saved_predictions(source_dir,horizon)
        historical=execute_cli(source_dir/"predictions.csv",frame,folder,"historia")
        adapted,derived=persistence_adapter(frame,folder,source_dir/"predictions.csv")
        persistence=execute_cli(adapted,derived,folder,"persistencia")
        results[horizon]={"horizon_hours":horizon,"source_checks":input_checks,
                          "history_reference":historical,"persistence_reference":persistence}
    # Confirm preservation of every frozen input after all four CLI executions.
    for horizon,item in ITEMS.items():
        for group in ["input_sha256","frozen_method_sha256","prior_construction_evidence_sha256"]:
            for name,value in protocols[horizon][group].items():assert sha(ROOT/name)==value,name
    completed=datetime.now(timezone.utc).isoformat()
    for horizon,item in ITEMS.items():
        folder=BASE/item
        data={"schema":"renewcast-bloco2-bootstrap-engineering-result-v1","item_id":item,
            "completed":True,"technical_status":"concluido_verificado","started_at_utc":started,
            "completed_at_utc":completed,"elapsed_seconds":perf_counter()-timer,
            "command":[sys.executable,str(Path(__file__).resolve())],"exit_code":0,
            "versions":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__},
            "runner_sha256":sha(__file__),"method_sha256":sha(ROOT/MODULE),
            "protocol_sha256":sha(folder/"protocolo.json"),"fixed_parameters":PARAMETERS,
            "input_sha256":protocols[horizon]["input_sha256"],
            "prior_59_tests_verified_not_rerun":{"receipt_sha256":sha(prior_path),"code_sha256":sha(ROOT/MODULE),"tests_passed":59},
            "primary_horizon":horizon,"analysis":results[horizon],
            "cross_horizon_analysis":results,
            "original_inputs_and_historical_runs_preserved":True,
            "conditional_on_saved_predictions_and_fixed_folds":True,
            "models_trained":False,"models_inferred":False,"new_data":False,
            "untouched_holdout":False,"operational_approval":False,"network_used":False,
            "nonpositive_bootstrap_fraction_is_p_value":False,
            "independent_authorship_claimed":False,"assistance":"Technical computation and interpretation supplied with Codex assistance.",
            "output_sha256":{p.relative_to(folder).as_posix():sha(p) for p in folder.rglob("*")
                if p.is_file() and p.name not in {"protocolo.json","resultado.json","executar.py"}}}
        write_json(folder/"resultado.json",data)
    print(json.dumps({"completed":True,"results":{h:{"history":r["history_reference"]["aggregate_rows"],
        "persistence":r["persistence_reference"]["aggregate_rows"],
        "source_checks":r["source_checks"]} for h,r in results.items()},
        "originals_preserved":True},ensure_ascii=True))


if __name__=="__main__":
    main()
