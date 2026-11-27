"""Auditoria documental de M05; nao executa modelos ou muda a politica."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE.parents[2]
IDS=("M05-01","M05-02","M05-03")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def total_rows(path):
    frame=pd.read_csv(path)
    return json.loads(frame.loc[frame["period"].eq("total")].to_json(orient="records",double_precision=15))


def main():
    results={item:load(BASE/item/"resultado.json") for item in IDS}
    for item,result in results.items():
        assert result["completed"] and result["evaluation_performed"]
        if "documentation_finalization" in result:
            raise FileExistsError("Evidencias ja finalizadas; nao sobrescrever automaticamente")
        assert result["executions"][-1]["exit_code"]==0
        for name,expected in result["output_sha256"].items():
            assert sha(BASE/item/name)==expected,(item,name)
        frozen=load(BASE/item/"freeze.json")
        assert sha(BASE/item/"freeze.json")==result["freeze_sha256"]
        for name,expected in frozen["files"].items():
            assert sha(ROOT/name)==expected,name
    source_path=ROOT/results["M05-01"]["evaluation_source_path"]
    source_sha=sha(source_path)
    assert source_sha=="aecb3a89ff306b93fa694d800b9659aa7d4d551763930589b5abad70931a87ab"
    source_receipt_path=source_path.parent/"fonte.json"
    source_receipt=load(source_receipt_path)
    assert source_receipt["filtered_sha256"]==source_sha
    assert datetime.fromisoformat(source_receipt["freeze_created_at_utc"])<datetime.fromisoformat(source_receipt["downloaded_at_utc"])
    tables={item:pd.read_csv(BASE/item/"predicoes_avaliacao.csv") for item in IDS}
    origin_text=tables["M05-01"]["forecast_origin"]
    origins=pd.DatetimeIndex(pd.to_datetime(origin_text))
    assert len(origins)==695 and origins.is_unique and origins.is_monotonic_increasing
    assert all(t["forecast_origin"].equals(origin_text) for t in tables.values())
    source=pd.read_parquet(source_path).set_index("din_instante")["val_geracao"]
    source.index=pd.to_datetime(source.index)
    y24=source.reindex(origins+pd.Timedelta(hours=24)).to_numpy()
    last=source.reindex(origins-pd.Timedelta(hours=2)).to_numpy()
    ramp=source.reindex(origins).to_numpy()-source.reindex(origins+pd.Timedelta(hours=1)).to_numpy()
    np.testing.assert_allclose(tables["M05-01"]["y24"],y24,rtol=0,atol=1e-10)
    np.testing.assert_allclose(tables["M05-02"]["y24"],y24,rtol=0,atol=1e-10)
    np.testing.assert_allclose(tables["M05-03"]["ramp_down_1h"],ramp,rtol=0,atol=1e-10)
    np.testing.assert_array_equal(tables["M05-02"]["event_26h"],(last-y24>=22.77).astype(int))
    np.testing.assert_array_equal(tables["M05-03"]["event_1h"],(ramp>=22.77).astype(int))
    budgets=pd.read_csv(BASE/"M05-02/orcamento_diario.csv")
    assert budgets["alarms"].le(6).all()
    for item,result in results.items():
        assert result["weekly_rows"]==[168,168,168,168,23]
        assert result["evaluation_source_sha256"]==source_sha
        assert datetime.fromisoformat(source_receipt["downloaded_at_utc"])<datetime.fromisoformat(result["executions"][-1]["started_at_utc"])
    aliases={"M05-01":{"cobertura_por_periodo.csv":"metricas_intervalos.csv"},
             "M05-02":{"calibracao_classe.csv":"metricas_probabilidades.csv","alarmes.csv":"metricas_alarmes.csv"},
             "M05-03":{"rampas.csv":"predicoes_avaliacao.csv"}}
    for item,mapping in aliases.items():
        for destination,original in mapping.items():
            target=BASE/item/destination
            if target.exists():raise FileExistsError(target)
            target.write_bytes((BASE/item/original).read_bytes())
            assert sha(target)==sha(BASE/item/original)
    write(BASE/"M05-03/contrato_rampa.json",{
        "documented_at_utc":datetime.now(timezone.utc).isoformat(),
        "role":"Explanatory extraction of the contract fixed before model fitting; not a new definition after evaluation",
        "definition_fixed_in":"protocolo.json","protocol_sha256":sha(BASE/"M05-03/protocolo.json"),
        "freeze_sha256":sha(BASE/"M05-03/freeze.json"),
        "target":"generation(origin)-generation(origin+1h)","positive_means":"drop",
        "event":"drop>=22.77 MWmed","latest_input":"generation(origin-2h)",
        "label_available_at":"origin+3h under the fixed2h availability assumption",
        "last_ramp_baseline":"generation(origin-3h)-generation(origin-2h)",
        "training_rows":results["M05-03"]["ramp_train_rows"],
        "training_label_cutoff_exclusive":"2026-07-01T00:00:00Z",
        "evaluation_origins":695,"classifier_probability_threshold":0.5,
        "regression_alarm_threshold":22.77,"daily_budget_applied":False,
        "recalibration_or_reselection_performed":False,"operational_approval":False,
    })
    summaries={"M05-01":{"interval_metrics":total_rows(BASE/"M05-01/metricas_intervalos.csv")},
               "M05-02":{"probability_metrics":total_rows(BASE/"M05-02/metricas_probabilidades.csv"),
                           "alarm_metrics":total_rows(BASE/"M05-02/metricas_alarmes.csv")},
               "M05-03":{"ramp_regression_metrics":total_rows(BASE/"M05-03/metricas_regressao_rampa.csv"),
                           "ramp_probability_metrics":total_rows(BASE/"M05-03/metricas_probabilidade_rampa.csv"),
                           "ramp_alarm_metrics":total_rows(BASE/"M05-03/metricas_alarmes_rampa.csv")}}
    link_count=0
    for item,result in results.items():
        directory=BASE/item
        for document in [directory/"parecer.md",directory/"metodo_ajuste.md"]:
            for target in re.findall(r"\]\(([^)]+)\)",document.read_text(encoding="utf-8")):
                if "://" not in target:
                    assert (document.parent/target).exists(),target
                    link_count+=1
        result["summary"]=summaries[item]
        result["source_receipt"]={"path":source_receipt_path.relative_to(ROOT).as_posix(),"sha256":sha(source_receipt_path)}
        result["documentation_finalization"]={
            "finished_at_utc":datetime.now(timezone.utc).isoformat(),
            "reviewed_by":"Codex engineering assistance",
            "review_scope":"Artifact hashes, independent target reconstruction, same695origins, daily budget, documentation and exact-copy aliases; no model replay",
            "frozen_artifacts_preserved":True,"source_hash_matches_download_receipt":True,
            "source_download_after_freeze_and_before_evaluation":True,
            "h26_targets_reconstructed_from_source":True,"one_hour_targets_reconstructed_from_source":True,
            "event_counts":{"h26":117,"ramp1h":39},
            "compatibility_aliases":aliases[item],
            "alias_files_are_byte_identical":True,
            "finalizer_path":Path(__file__).relative_to(ROOT).as_posix(),"finalizer_sha256":sha(Path(__file__)),
            "operational_approval":False,
        }
        result["output_sha256"]={path.name:sha(path) for path in directory.iterdir()
                                if path.is_file() and path.name!="resultado.json"}
        write(directory/"resultado.json",result)
    print(json.dumps({"completed":True,"ids":list(IDS),"common_origins":695,
        "h26_events":117,"ramp_events":39,"daily_budget_maximum":int(budgets["alarms"].max()),
        "local_links_checked":link_count,"frozen_artifacts_preserved":True},ensure_ascii=True))


if __name__=="__main__":
    main()
