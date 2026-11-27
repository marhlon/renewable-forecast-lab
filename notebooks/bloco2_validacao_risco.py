"""M05-01/02/03: ajuste separado, freeze e avaliacao temporal sem reescolha.

Usa somente geracao, sob os relogios hipoteticos do protocolo integrado.
Nao baixa dados; --avaliar exige um Parquet explicitamente liberado.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from bloco2_modelagem_core import FEATURES, PersistenceRegressor, build_frame, fit_mask, load_series, period_mask, sha256, timestamp
from bloco2_risco_core import (alarmes_causais, confiabilidade, correcao_cqr,
    logit_features, metricas_alarmes, metricas_intervalo, metricas_probabilidade,
    metricas_regressao, ordenar_quantis, selecionar_politica)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/fechamento_m00_m09/bloco2_engenharia"
IDS = ("M05-01", "M05-02", "M05-03")
CORE_PATHS = [Path(__file__).resolve(), ROOT / "notebooks/bloco2_modelagem_core.py",
              ROOT / "notebooks/bloco2_risco_core.py"]


def now():
    return datetime.now(timezone.utc).isoformat()


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (Path, pd.Timestamp)):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                   allow_nan=False, default=json_default) + "\n", encoding="utf-8")


def save_csv(path, rows):
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.to_csv(path, index=False, encoding="utf-8", float_format="%.15g")


def file_hashes(paths):
    return {relative(path): sha256(path) for path in paths}


def frame_rows(frame, start, end, target="y24"):
    return frame.loc[period_mask(frame, start, end, target)].copy().reset_index(drop=True)


def period_groups(frame, anchor):
    stamps = pd.to_datetime(frame["forecast_origin"])
    block = ((stamps - timestamp(anchor)).dt.total_seconds() // (7 * 86400)).astype(int)
    yield "total", frame, np.ones(len(frame), dtype=bool)
    for k in sorted(block.unique()):
        mask = (block == k).to_numpy()
        yield f"semana_{k+1:02}", frame.loc[mask], mask


def period_info(frame, name, plan):
    return {"period": name, "origin_min": str(frame["forecast_origin"].min()),
            "origin_max": str(frame["forecast_origin"].max()),
            "enough_rows_for_alert": len(frame) >= plan["interval_reporting"]["min_rows_per_period"],
            "partial_period": name != "total" and len(frame) < 168}


def bootstrap_coverage(y, raw, corrected):
    """Paired conditional percentile CI; fixed circular24h blocks, no iid claim."""
    observed=np.asarray(y,dtype=float)
    raw_hit=((observed>=raw[:,0]) & (observed<=raw[:,2])).astype(float)
    corrected_hit=((observed>=corrected[:,0]) & (observed<=corrected[:,2])).astype(float)
    n=len(observed); block=24; reps=2000
    rng=np.random.default_rng(17)
    starts=rng.integers(0,n,size=(reps,math.ceil(n/block)))
    indices=((starts[:,:,None]+np.arange(block))%n).reshape(reps,-1)[:,:n]
    sampled_raw=raw_hit[indices].mean(axis=1)
    sampled_cqr=corrected_hit[indices].mean(axis=1)
    rows=[]
    for method,estimate,values in [
        ("raw_sorted",raw_hit.mean(),sampled_raw),
        ("cqr_frozen",corrected_hit.mean(),sampled_cqr),
        ("paired_difference_cqr_minus_raw",(corrected_hit-raw_hit).mean(),sampled_cqr-sampled_raw)]:
        low,high=np.quantile(values,[0.025,0.975])
        rows.append({"method":method,"n":n,"estimate":float(estimate),
            "lower_percentile_2p5":float(low),"upper_percentile_97p5":float(high),
            "block_hours":block,"bootstrap_repetitions":reps,"seed":17,
            "same_resampled_indices_for_both_methods":True,
            "interpretation":"conditional retrospective block-bootstrap CI; not a conformal or iid guarantee"})
    return rows


def plan_and_paths():
    plan_path = BASE / "protocolo_integrado.json"
    plan = load_json(plan_path)
    source = ROOT / plan["old_series"]
    return plan, plan_path, source


def verify_new_contracts():
    raw=np.asarray([[1.,5.,9.],[1.,5.,9.]])
    expanded=np.asarray([[0.,5.,10.],[0.,5.,10.]])
    checked=bootstrap_coverage([0.,10.],raw,expanded)
    for row,value in zip(checked,[0.,1.,1.]):
        assert row["estimate"]==value
        assert row["lower_percentile_2p5"]==value
        assert row["upper_percentile_97p5"]==value
    repeated=bootstrap_coverage([0.,10.],raw,expanded)
    assert checked==repeated
    synthetic=pd.DataFrame({"forecast_origin":pd.date_range("2000-01-01",periods=695,freq="h")})
    groups=list(period_groups(synthetic,"2000-01-01"))
    assert [len(group) for name,group,_ in groups if name!="total"]==[168,168,168,168,23]
    print("Contraprovas: bootstrap pareado deterministico e semanas168/168/168/168/23 aprovados.",flush=True)


def prepare(args):
    plan, plan_path, source = plan_and_paths()
    verify_new_contracts()
    for item in IDS:
        directory = BASE / item
        directory.mkdir(parents=True, exist_ok=True)
        if (directory / "protocolo.json").exists():
            raise FileExistsError(f"Protocolo ja existe: {item}")
    shared = {
        "schema": "renewcast-bloco2-risk-protocol-v1", "created_at_utc": now(),
        "integrated_protocol": relative(plan_path), "integrated_protocol_sha256": sha256(plan_path),
        "source": relative(source), "source_sha256": sha256(source),
        "code_sha256": file_hashes(CORE_PATHS),
        "point_bundle": relative(args.point_bundle),
        "training_cutoff": plan["final_training_cutoff"],
        "features_rule": "Use selected point features; if persistence wins, use study_features of the learned candidate",
        "fit_labels": "strictly before Jul1 cutoff: y24 available origin+26h; ramp available origin+3h",
        "calibration": plan["calibration"], "policy_selection": plan["policy_selection"],
        "evaluation": plan["evaluation"], "interval_reporting": plan["interval_reporting"],
        "hgb_parameters": plan["hgb_parameters"], "ramp": plan["ramp"],
        "h26_class_label": "last_observed - y24 >= 22.77 MWmed; endpoints26h apart; not hourly ramp",
        "probability_models": ["raw_hgb", "platt_calibrated", "training_frequency"],
        "alarm_comparisons": ["raw_at_0.5", "calibrated_at_0.5", "frequency_at_0.5", "frozen_calibrated_policy"],
        "h26_alarm_comparisons_have_daily_budget": 6,
        "ramp_alarm_comparisons": "fixed classifier probability0.5 or regressor drop22.77; no daily budget",
        "coverage_bootstrap": {"scope":"695origins aggregated only","scheme":"circular blocks24h",
            "repetitions":2000,"seed":17,"interval":"conditional percentile2.5/97.5",
            "paired_raw_cqr_indices":True,"difference_cqr_minus_raw":True,
            "no_iid_or_exchangeability_guarantee":True},
        "weekly_anchor": plan["evaluation"]["origin_start"],
        "evaluation_source_contract": "exclusive CJU_BA5EIGT normalized two columns din_instante,val_geracao; exactly744 finite hourly rows Oct1_00 throughOct31_23; 695 common origins",
        "no_reselection_or_recalibration_on_evaluation": True,
        "costs_hypothetical": True, "operational_approval": False,
        "source_snapshot_limit": "retrospective newly obtained snapshot; not the historically published version at each forecast origin",
        "assistance": "Codex engineering implementation, execution and interpretation; no independent-user claim",
    }
    descriptions = {
        "M05-01": "HGB quantiles0.1/0.5/0.9, predefined row sorting and separate nonnegative CQR; coverage/width/score by fixed week",
        "M05-02": "HGB26h class, separately fitted Platt, reliability and causal daily-budget policy frozen before evaluation",
        "M05-03": "Actual one-hour ramp target regressor/classifier with persistence and training-frequency baselines",
    }
    for item in IDS:
        write_json(BASE / item / "protocolo.json", {**shared, "roadmap_id": item, "study": descriptions[item]})
        write_json(BASE / item / "resultado.json", {
            "schema": "renewcast-bloco2-risk-result-v1", "roadmap_id": item,
            "completed": False, "phase": "protocolado", "created_at_utc": now(),
            "source_sha256": shared["source_sha256"], "protocol_sha256": sha256(BASE/item/"protocolo.json"),
            "operational_approval": False, "independent_user_performance_claimed": False,
        })
    print("Protocolos M05-01/02/03 gravados antes do ajuste; nenhum dado de outubro aberto.", flush=True)


def fit(args):
    plan, plan_path, source = plan_and_paths()
    for item in IDS:
        protocol = load_json(BASE/item/"protocolo.json")
        if protocol["integrated_protocol_sha256"] != sha256(plan_path) or protocol["source_sha256"] != sha256(source):
            raise ValueError("Protocolo ou fonte alterados antes do ajuste")
        if protocol["code_sha256"] != file_hashes(CORE_PATHS):
            raise ValueError("Codigo mudou apos protocolar; revisar antes do ajuste")
        if (BASE/item/"freeze.json").exists() or (BASE/item/"protocolo_ajuste.json").exists():
            raise FileExistsError(f"Ajuste ja iniciado/congelado: {item}")
    bundle = joblib.load(args.point_bundle)
    if bundle["source_sha256"] != sha256(source):
        raise ValueError("Bundle pontual usa outra fonte")
    if timestamp(bundle["train_cutoff"]) != timestamp(plan["final_training_cutoff"]):
        raise ValueError("Bundle pontual usa outro corte")
    use_study = isinstance(bundle["model"], PersistenceRegressor)
    features = list(bundle["study_features"] if use_study else bundle["features"])
    if not features or not set(features).issubset(FEATURES):
        raise ValueError("Features nao reconhecidas")
    training_protocol = {
        "created_at_utc": now(), "point_bundle": relative(args.point_bundle),
        "point_bundle_sha256": sha256(args.point_bundle), "features": features,
        "persistence_winner_requires_learned_features": use_study,
        "source_sha256": sha256(source), "code_sha256": file_hashes(CORE_PATHS),
        "integrated_protocol_sha256": sha256(plan_path),
        "training_cutoff": plan["final_training_cutoff"],
        "evaluation_data_read": False,
    }
    for item in IDS:
        write_json(BASE/item/"protocolo_ajuste.json", {"roadmap_id":item, **training_protocol})
    frame = build_frame(load_series(source))
    train = frame.loc[fit_mask(frame, plan["final_training_cutoff"])].copy()
    ramp_train = frame.loc[fit_mask(frame, plan["final_training_cutoff"], "ramp_down_1h")].copy()
    cal = frame_rows(frame, plan["calibration"]["origin_start"], plan["calibration"]["origin_end_exclusive"])
    policy = frame_rows(frame, plan["policy_selection"]["origin_start"], plan["policy_selection"]["origin_end_exclusive"])
    if len(cal) != 312 or len(policy) != 360 or len(train) < 1000:
        raise ValueError(f"Coortes inesperadas: treino{len(train)},cal{len(cal)},politica{len(policy)}")
    if not train["label_available_at"].lt(timestamp(plan["final_training_cutoff"])).all():
        raise ValueError("Rotulo pontual cruza corte")
    if not ramp_train["ramp_label_available_at"].lt(timestamp(plan["final_training_cutoff"])).all():
        raise ValueError("Rotulo de rampa cruza corte")
    if not cal["label_available_at"].lt(timestamp(plan["policy_selection"]["origin_start"])).all():
        raise ValueError("Calibracao nao estava conhecida na selecao da politica")
    if not policy["label_available_at"].lt(timestamp(plan["policy_selection"]["all_labels_known_before"])).all():
        raise ValueError("Rotulos da politica nao estavam conhecidos antes do prazo declarado")
    xtrain, xcal, xp = train[features], cal[features], policy[features]
    params = plan["hgb_parameters"]
    print(f"Treino y24={len(train)},rampa={len(ramp_train)},cal={len(cal)},politica={len(policy)},features={len(features)}", flush=True)
    quantiles = []
    for tau in (0.1, 0.5, 0.9):
        model = HistGradientBoostingRegressor(loss="quantile", quantile=tau, **params)
        model.fit(xtrain, train["y24"])
        quantiles.append(model)
        print(f"Quantil {tau} ajustado.", flush=True)
    qcal_unsorted = np.column_stack([model.predict(xcal) for model in quantiles])
    qcal = ordenar_quantis(qcal_unsorted)
    correction, rank = correcao_cqr(cal["y24"].to_numpy(), qcal)
    interval_bundle = {"models": quantiles, "features": features, "correction": correction,
                       "rank": rank, "calibration_rows": len(cal), **training_protocol}
    joblib.dump(interval_bundle, BASE/"M05-01/interval_bundle.joblib")
    interval_cal = cal[["forecast_origin", "history_end", "target_time", "label_available_at", "y24"]].copy()
    interval_cal[["p10", "p50", "p90"]] = qcal
    interval_cal["cqr_lower"], interval_cal["cqr_upper"] = qcal[:,0]-correction, qcal[:,2]+correction
    save_csv(BASE/"M05-01/predicoes_calibracao.csv", interval_cal)
    write_json(BASE/"M05-01/calibracao_congelada.json", {
        "created_at_utc": now(), "n":len(cal), "rank":rank, "alpha":0.2,
        "nonnegative_expansion":correction, "quantile_crossings_before_sort":int((np.diff(qcal_unsorted,axis=1)<0).any(axis=1).sum()),
        "raw":metricas_intervalo(cal["y24"],qcal), "cqr":metricas_intervalo(cal["y24"],np.column_stack([qcal[:,0]-correction,qcal[:,1],qcal[:,2]+correction])),
        "serial_dependence_prevents_exchangeability_guarantee": True,
    })

    ytrain = (train["last_observed"]-train["y24"] >= plan["ramp"]["threshold_mwmed"]).astype(int)
    ycal = (cal["last_observed"]-cal["y24"] >= plan["ramp"]["threshold_mwmed"]).astype(int)
    if ytrain.nunique()!=2 or ycal.nunique()!=2:
        raise ValueError("Ambas as classes sao necessarias no treino e calibracao")
    classifier = HistGradientBoostingClassifier(**params).fit(xtrain, ytrain)
    raw_cal = classifier.predict_proba(xcal)[:,1]
    calibrator = LogisticRegression(C=1,max_iter=200,random_state=17).fit(logit_features(raw_cal),ycal)
    frequency = float(ytrain.mean())
    probability_bundle = {"model":classifier,"calibrator":calibrator,"frequency":frequency,**training_protocol}
    joblib.dump(probability_bundle, BASE/"M05-02/probability_bundle.joblib")
    prob_cal = cal[["forecast_origin","history_end","target_time","label_available_at"]].copy()
    prob_cal["event"] = ycal.to_numpy()
    prob_cal["p_raw"] = raw_cal
    prob_cal["p_calibrated"] = calibrator.predict_proba(logit_features(raw_cal))[:,1]
    prob_cal["p_training_frequency"] = frequency
    save_csv(BASE/"M05-02/predicoes_calibracao.csv",prob_cal)
    raw_policy = classifier.predict_proba(xp)[:,1]
    calibrated_policy = calibrator.predict_proba(logit_features(raw_policy))[:,1]
    yp = (policy["last_observed"]-policy["y24"] >= plan["ramp"]["threshold_mwmed"]).to_numpy().astype(int)
    chosen, candidates = selecionar_politica(policy["forecast_origin"],yp,calibrated_policy,
        plan["policy_selection"]["thresholds"],plan["policy_selection"]["daily_alarm_budget"])
    frozen_policy = {"created_at_utc":now(),"input_probability":"platt_calibrated",
        "threshold":chosen["threshold"],"daily_budget":6,"cost_fp":1,"cost_fn":4,
        "selection":chosen,"selection_origins":len(policy),
        "selection_origin_start":str(policy["forecast_origin"].min()),
        "selection_origin_end":str(policy["forecast_origin"].max()),
        "maximum_label_available_at":str(policy["label_available_at"].max()),
        "ordering":"first six eligible chronologically each laboratory UTC day; no daily ranking",
        "tie_break":plan["policy_selection"]["tie_break"], "no_reselection_on_evaluation":True}
    write_json(BASE/"M05-02/politica_congelada.json",frozen_policy)
    save_csv(BASE/"M05-02/candidatos_politica.csv",candidates)
    policy_pred = policy[["forecast_origin","target_time","label_available_at"]].copy()
    policy_pred["event"],policy_pred["p_raw"],policy_pred["p_calibrated"] = yp,raw_policy,calibrated_policy
    policy_pred["alarm"] = alarmes_causais(policy["forecast_origin"],calibrated_policy,chosen["threshold"],6)
    save_csv(BASE/"M05-02/predicoes_selecao_politica.csv",policy_pred)
    print(f"Classificador/Platt ajustados; politica corte={chosen['threshold']}, custo={chosen['cost']}, alarmes={chosen['alarms']}",flush=True)

    ramp_y = ramp_train["ramp_down_1h"]
    ramp_event = (ramp_y >= plan["ramp"]["threshold_mwmed"]).astype(int)
    if ramp_event.nunique()!=2:
        raise ValueError("Rampa requer duas classes no treino")
    ramp_reg = HistGradientBoostingRegressor(loss="squared_error",**params).fit(ramp_train[features],ramp_y)
    ramp_class = HistGradientBoostingClassifier(**params).fit(ramp_train[features],ramp_event)
    joblib.dump({"regressor":ramp_reg,"classifier":ramp_class,"frequency":float(ramp_event.mean()),
                 "features":features,**training_protocol},BASE/"M05-03/ramp_bundle.joblib")
    print("Regressor e classificador de rampa horaria ajustados.",flush=True)

    model_files = {"M05-01":["interval_bundle.joblib","calibracao_congelada.json"],
                   "M05-02":["probability_bundle.joblib","politica_congelada.json"],
                   "M05-03":["ramp_bundle.joblib"]}
    for item in IDS:
        directory=BASE/item
        paths = [*CORE_PATHS,plan_path,source,args.point_bundle,directory/"protocolo.json",directory/"protocolo_ajuste.json",
                 *[directory/name for name in model_files[item]]]
        freeze={"schema":"renewcast-bloco2-risk-freeze-v1","roadmap_id":item,
                "frozen_at_utc":now(),"files":file_hashes(paths),"evaluation_data_read":False,
                "source_sha256":sha256(source),"features":features,
                "no_retraining_recalibration_or_reselection_allowed":True}
        write_json(directory/"freeze.json",freeze)
        result=load_json(directory/"resultado.json")
        result.update({"phase":"ajuste_congelado","fitted":True,"completed":False,
            "fitted_at_utc":now(),"train_rows":len(train),"ramp_train_rows":len(ramp_train),
            "train_max_label_available_at":str(train["label_available_at"].max()),
            "ramp_train_max_label_available_at":str(ramp_train["ramp_label_available_at"].max()),
            "calibration_rows":len(cal),"policy_rows":len(policy),"features":features,
            "freeze_sha256":sha256(directory/"freeze.json"),"code_sha256":file_hashes(CORE_PATHS),
            "versions":{"python":sys.version,"numpy":np.__version__,"pandas":pd.__version__,"sklearn":sklearn.__version__},
            "training_performed":True,"evaluation_performed":False,
            "retrospective_snapshot_not_operational_point_in_time":True})
        write_json(directory/"resultado.json",result)
    print("Freeze M05-01/02/03 gravado. Nenhum dado de outubro foi lido.",flush=True)


def verify_freezes():
    for item in IDS:
        freeze=load_json(BASE/item/"freeze.json")
        for name,expected in freeze["files"].items():
            if sha256(ROOT/name)!=expected:
                raise ValueError(f"Artefato congelado alterado: {name}")
        result=load_json(BASE/item/"resultado.json")
        if result.get("evaluation_performed"):
            raise FileExistsError("Avaliacao ja realizada; nao repetir automaticamente")
        if sha256(BASE/item/"freeze.json")!=result["freeze_sha256"]:
            raise ValueError("Selo local do ajuste alterado")


def evaluate(args):
    if args.evaluation_parquet is None:
        raise ValueError("--avaliar exige --evaluation-parquet liberado apos o freeze conjunto")
    verify_freezes()
    plan,_,_=plan_and_paths()
    source=load_series(args.evaluation_parquet)
    expected=pd.date_range("2026-10-01","2026-10-31 23:00:00",freq="h")
    if not pd.DatetimeIndex(source["din_instante"]).equals(expected) or not np.isfinite(source["val_geracao"]).all():
        raise ValueError("Fonte de avaliacao nao contem exatamente as744horas finitas previstas para outubro")
    # Exact input schema prevents silently evaluating an unfiltered multi-plant resource.
    if list(pd.read_parquet(args.evaluation_parquet).columns)!=["din_instante","val_geracao"]:
        raise ValueError("Parquet deve ser a serie exclusiva normalizada com as duas colunas declaradas")
    frame=build_frame(source)
    evaluation=plan["evaluation"]
    mask=period_mask(frame,evaluation["origin_start"],evaluation["origin_end_exclusive"])
    mask &= period_mask(frame,evaluation["origin_start"],evaluation["origin_end_exclusive"],"ramp_down_1h")
    cohort=frame.loc[mask].copy().reset_index(drop=True)
    origins=pd.date_range(timestamp(evaluation["origin_start"]),timestamp(evaluation["origin_end_exclusive"]),freq="h",inclusive="left")
    if len(cohort)!=695 or not pd.DatetimeIndex(cohort["forecast_origin"]).equals(origins):
        raise ValueError("Coorte comum nao coincide com as695origens predefinidas; abortar sem trocar mes")
    if not ((cohort["target_time"]-cohort["history_end"])==pd.Timedelta(hours=26)).all():
        raise ValueError("Relogios h24/d2 invalidos")
    print("Contrato aprovado:744horas e695origens comuns; iniciando somente inferencia congelada.",flush=True)
    source_sha=sha256(args.evaluation_parquet)
    common_cols=["forecast_origin","history_end","target_time","label_available_at","y24"]
    interval=joblib.load(BASE/"M05-01/interval_bundle.joblib")
    raw_unsorted=np.column_stack([model.predict(cohort[interval["features"]]) for model in interval["models"]])
    q=ordenar_quantis(raw_unsorted)
    correction=interval["correction"]
    cqr=np.column_stack([q[:,0]-correction,q[:,1],q[:,2]+correction])
    interval_pred=cohort[common_cols].copy()
    interval_pred[["raw_p10","raw_p50","raw_p90"]]=q
    interval_pred[["cqr_lower","cqr_median","cqr_upper"]]=cqr
    save_csv(BASE/"M05-01/predicoes_avaliacao.csv",interval_pred)
    interval_rows=[]
    for name,group,selection in period_groups(cohort,evaluation["origin_start"]):
        for method,values in [("raw_sorted",q),("cqr_frozen",cqr)]:
            metrics=metricas_intervalo(group["y24"],values[selection])
            eligible=len(group)>=plan["interval_reporting"]["min_rows_per_period"]
            interval_rows.append({**period_info(group,name,plan),"method":method,**metrics,
                "frozen_expansion":correction if method=="cqr_frozen" else 0,
                "coverage_alert":bool(abs(metrics["coverage"]-0.8)>0.1) if eligible else None})
    save_csv(BASE/"M05-01/metricas_intervalos.csv",interval_rows)
    save_csv(BASE/"M05-01/incerteza_cobertura.csv",bootstrap_coverage(cohort["y24"],q,cqr))

    prob=joblib.load(BASE/"M05-02/probability_bundle.joblib")
    frozen_policy=load_json(BASE/"M05-02/politica_congelada.json")
    y=(cohort["last_observed"]-cohort["y24"]>=22.77).to_numpy().astype(int)
    p_raw=prob["model"].predict_proba(cohort[prob["features"]])[:,1]
    p_cal=prob["calibrator"].predict_proba(logit_features(p_raw))[:,1]
    probabilities={"raw_hgb":p_raw,"platt_calibrated":p_cal,"training_frequency":np.full(len(y),prob["frequency"])}
    alarms={"raw_at_0.5":alarmes_causais(cohort["forecast_origin"],p_raw,0.5,6),
            "calibrated_at_0.5":alarmes_causais(cohort["forecast_origin"],p_cal,0.5,6),
            "frequency_at_0.5":alarmes_causais(cohort["forecast_origin"],probabilities["training_frequency"],0.5,6),
            "frozen_calibrated_policy":alarmes_causais(cohort["forecast_origin"],p_cal,frozen_policy["threshold"],6)}
    prob_pred=cohort[common_cols+["last_observed"]].copy()
    prob_pred["event_26h"]=y
    for method,values in probabilities.items():prob_pred["p_"+method]=values
    for method,values in alarms.items():prob_pred["alarm_"+method]=values
    save_csv(BASE/"M05-02/predicoes_avaliacao.csv",prob_pred)
    probability_rows=[]; reliability_rows=[]; alarm_rows=[]; daily_rows=[]
    for name,group,selection in period_groups(cohort,evaluation["origin_start"]):
        for method,values in probabilities.items():
            probability_rows.append({**period_info(group,name,plan),"method":method,**metricas_probabilidade(y[selection],values[selection])})
            reliability_rows.extend({"period":name,**row} for row in confiabilidade(y[selection],values[selection],method))
        for method,values in alarms.items():
            alarm_rows.append({**period_info(group,name,plan),"method":method,"cost_fp":1,"cost_fn":4,
                               **metricas_alarmes(y[selection],values[selection])})
    dates=cohort["forecast_origin"].dt.date
    for day in sorted(dates.unique()):
        select=(dates==day).to_numpy()
        for method,values in alarms.items():
            metrics=metricas_alarmes(y[select],values[select])
            if metrics["alarms"]>6:raise AssertionError("Orcamento diario violado")
            daily_rows.append({"laboratory_day":str(day),"method":method,"budget":6,**metrics})
    save_csv(BASE/"M05-02/metricas_probabilidades.csv",probability_rows)
    save_csv(BASE/"M05-02/confiabilidade.csv",reliability_rows)
    save_csv(BASE/"M05-02/metricas_alarmes.csv",alarm_rows)
    save_csv(BASE/"M05-02/orcamento_diario.csv",daily_rows)

    ramp=joblib.load(BASE/"M05-03/ramp_bundle.joblib")
    ry=cohort["ramp_down_1h"].to_numpy()
    revent=(ry>=22.77).astype(int)
    ramp_predictions={"hgb_ramp":ramp["regressor"].predict(cohort[ramp["features"]]),
                      "rampa_zero":np.zeros(len(ry)),
                      "ultima_rampa_observada":(cohort["previous_observed"]-cohort["last_observed"]).to_numpy()}
    ramp_probabilities={"hgb_ramp":ramp["classifier"].predict_proba(cohort[ramp["features"]])[:,1],
                        "training_frequency":np.full(len(ry),ramp["frequency"])}
    ramp_pred=cohort[["forecast_origin","history_end","ramp_label_available_at","last_observed","previous_observed","ramp_down_1h"]].copy()
    ramp_pred["event_1h"]=revent
    for method,values in ramp_predictions.items():ramp_pred["prediction_"+method]=values
    for method,values in ramp_probabilities.items():ramp_pred["p_"+method]=values
    save_csv(BASE/"M05-03/predicoes_avaliacao.csv",ramp_pred)
    regression_rows=[]; ramp_prob_rows=[]; ramp_alarm_rows=[]
    for name,group,selection in period_groups(cohort,evaluation["origin_start"]):
        for method,values in ramp_predictions.items():
            regression_rows.append({**period_info(group,name,plan),"method":method,**metricas_regressao(ry[selection],values[selection])})
            ramp_alarm_rows.append({**period_info(group,name,plan),"method":"regressor_"+method,
                "threshold_mwmed":22.77,"daily_budget_applied":False,
                **metricas_alarmes(revent[selection],values[selection]>=22.77)})
        for method,values in ramp_probabilities.items():
            ramp_prob_rows.append({**period_info(group,name,plan),"method":method,**metricas_probabilidade(revent[selection],values[selection])})
            ramp_alarm_rows.append({**period_info(group,name,plan),"method":"classifier_"+method,
                "threshold_probability":0.5,"daily_budget_applied":False,
                **metricas_alarmes(revent[selection],values[selection]>=0.5)})
    save_csv(BASE/"M05-03/metricas_regressao_rampa.csv",regression_rows)
    save_csv(BASE/"M05-03/metricas_probabilidade_rampa.csv",ramp_prob_rows)
    save_csv(BASE/"M05-03/metricas_alarmes_rampa.csv",ramp_alarm_rows)
    for item in IDS:
        result=load_json(BASE/item/"resultado.json")
        result.update({"phase":"avaliado","completed":True,"evaluation_performed":True,
            "evaluated_at_utc":now(),"evaluation_source_path":relative(args.evaluation_parquet),
            "evaluation_source_sha256":source_sha,"evaluation_source_rows":len(source),
            "evaluation_origins":len(cohort),"evaluation_origin_min":str(cohort["forecast_origin"].min()),
            "evaluation_origin_max":str(cohort["forecast_origin"].max()),
            "same_695_origins_for_all_M05_studies":True,"training_during_evaluation":False,
            "recalibration_during_evaluation":False,"policy_reselection_during_evaluation":False,
            "weekly_rows":[len(group) for name,group,_ in period_groups(cohort,evaluation["origin_start"]) if name!="total"],
            "snapshot_is_historically_point_in_time":False,"live_shadow_demonstrated":False,
            "operational_approval":False,"independent_user_performance_claimed":False,
            "source_contract_checks_passed":True})
        write_json(BASE/item/"resultado.json",result)
    print("Avaliacao695 concluida sem ajuste, recalibracao ou troca da politica; semanas168/168/168/168/23.",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preparar",action="store_true")
    modes.add_argument("--ajustar",action="store_true")
    modes.add_argument("--avaliar",action="store_true")
    parser.add_argument("--point-bundle",type=Path,default=BASE/"M03-03/point_bundle.joblib")
    parser.add_argument("--evaluation-parquet",type=Path)
    args=parser.parse_args()
    phase="preparar" if args.preparar else "ajustar" if args.ajustar else "avaliar"
    start=now(); messages=[]
    class Tee:
        def __init__(self,original):self.original=original
        def write(self,text):messages.append(text);return self.original.write(text)
        def flush(self):return self.original.flush()
    success=False
    with contextlib.redirect_stdout(Tee(sys.stdout)),contextlib.redirect_stderr(Tee(sys.stderr)):
        try:
            with threadpool_limits(limits=1):
                (prepare if args.preparar else fit if args.ajustar else evaluate)(args)
            success=True
        except Exception:
            traceback.print_exc()
    finished=now()
    for item in IDS:
        directory=BASE/item
        if not directory.exists():continue
        log=directory/f"execucao_{phase}.log"
        if log.exists():log=directory/f"execucao_{phase}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log"
        metadata={"command":[sys.executable,*sys.argv],"started_at_utc":start,
                  "finished_at_utc":finished,"exit_code":0 if success else 1}
        log.write_text(json.dumps(metadata,ensure_ascii=False)+"\n"+"".join(messages),encoding="utf-8")
        if success and (directory/"resultado.json").exists():
            result=load_json(directory/"resultado.json")
            result.setdefault("executions",[]).append({**metadata,"log":log.name,"log_sha256":sha256(log)})
            result["output_sha256"]={p.name:sha256(p) for p in directory.iterdir() if p.is_file() and p.name!="resultado.json"}
            write_json(directory/"resultado.json",result)
    return 0 if success else 1


if __name__=="__main__":
    raise SystemExit(main())
