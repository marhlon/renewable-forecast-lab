"""M06.2: lote histórico, registro SQLite e conciliação por disponibilidade.

python -m renewable_forecast.event_batch --help
O lote executa o EventRuntime da API, sem HTTP e sem ajuste do estimador.
Política retrospectiva e dados de desenvolvimento: não é novo holdout nem operação ao vivo.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from renewable_forecast.event_artifact import (
    EventPredictRequest, EventRuntime, canonical_hash, sha256, utc, write_json,
)

RELEASE = "2026.10.04-event-batch-1"
DEFAULT_DB = Path("reports/service/CJU_BA5EIGT/h24_event_batch_v1/ledger.sqlite")
TIME_COLUMNS = (
    "forecast_origin", "target_time", "history_end", "weather_latest_available_at",
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS configuration (
    id INTEGER PRIMARY KEY CHECK(id = 1), config_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS predictions (
    forecast_origin TEXT PRIMARY KEY,
    target_time TEXT NOT NULL UNIQUE,
    target_available_at TEXT NOT NULL,
    request_sha256 TEXT NOT NULL,
    request_json TEXT NOT NULL,
    response_json TEXT NOT NULL,
    p_event REAL NOT NULL CHECK(p_event BETWEEN 0 AND 1),
    threshold REAL NOT NULL CHECK(threshold BETWEEN 0 AND 1),
    alarm INTEGER NOT NULL CHECK(alarm IN (0, 1)),
    event_generation_at_or_below_mwmed REAL NOT NULL,
    registered_at_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assessments (
    as_of TEXT NOT NULL,
    forecast_origin TEXT NOT NULL REFERENCES predictions(forecast_origin),
    status TEXT NOT NULL CHECK(status IN ('observed', 'awaiting_label', 'missing_observation')),
    target_generation REAL,
    event_drop INTEGER CHECK(event_drop IN (0, 1)),
    brier REAL,
    cost REAL,
    PRIMARY KEY(as_of, forecast_origin),
    CHECK((status = 'observed' AND target_generation IS NOT NULL AND event_drop IS NOT NULL
           AND brier IS NOT NULL AND cost IS NOT NULL)
       OR (status != 'observed' AND target_generation IS NULL AND event_drop IS NULL
           AND brier IS NULL AND cost IS NULL))
);
"""


def iso(value):
    return utc(value).isoformat().replace("+00:00", "Z")


def json_text(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


@contextmanager
def connect(path, *, create=False):
    path = Path(path)
    if not create and not path.is_file():
        raise FileNotFoundError(f"Banco não encontrado: {path.resolve()}")
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, isolation_level=None, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys=ON")
        if create:
            con.executescript(SCHEMA)
        yield con
    finally:
        con.close()


@contextmanager
def transaction(con):
    con.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        con.rollback()
        raise
    else:
        con.commit()


def source_paths(input_dir):
    csv_path, meta_path = input_dir / "model_frame.csv", input_dir / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if sha256(csv_path) != meta["output_sha256"]:
        raise ValueError("model_frame.csv difere do hash da junção.")
    return csv_path, meta


def emit(input_dir, model_dir, policy_path, db, origin_start, origin_end, threads=2):
    from renewable_forecast.decision_api import DecisionPolicy

    start, end = utc(origin_start), utc(origin_end)
    if end < start or any(t.minute or t.second or t.microsecond for t in (start, end)):
        raise ValueError("Informe início <= fim, ambos em horas inteiras com fuso.")
    policy = DecisionPolicy.model_validate_json(policy_path.read_bytes()).model_dump(mode="json")
    runtime = EventRuntime(model_dir, policy, sha256(policy_path), threads=threads)
    if start < utc(runtime.manifest["training_cutoff"]):
        raise ValueError("Início do lote anterior ao corte do modelo. Use um artefato ajustado antes do lote.")
    csv_path, meta = source_paths(input_dir)
    for name in ("conjunto", "horizon_hours", "availability_delay_hours"):
        if meta[name] != runtime.manifest[name]:
            raise ValueError(f"Fonte e artefato divergem em {name}.")
    if meta["model_feature_columns"] != runtime.columns:
        raise ValueError("Features da fonte diferem do contrato do modelo.")
    # A leitura para prever exclui explicitamente target_generation e event_drop.
    frame = pd.read_csv(csv_path, usecols=[*TIME_COLUMNS, "weather_model", *runtime.columns])
    for name in TIME_COLUMNS:
        frame[name] = frame[name].map(utc)
    if frame.forecast_origin.duplicated().any():
        raise ValueError("Origem duplicada na fonte.")
    selected = frame.loc[frame.forecast_origin.between(start, end)].sort_values("forecast_origin")
    expected = pd.date_range(start, end, freq="h")
    if list(selected.forecast_origin) != list(expected):
        raise ValueError("A fonte não contém todas as emissões horárias solicitadas.")
    config = {
        "release": RELEASE, "code_sha256": sha256(Path(__file__)),
        "model_sha256": runtime.manifest["model_sha256"],
        "manifest_sha256": runtime.manifest_sha256,
        "policy_sha256": runtime.policy_sha256, "policy": policy,
        "source_frame_sha256": meta["output_sha256"],
        "origin_start": iso(start), "origin_end": iso(end),
        "scope": "historical engineering simulation; retrospective development policy",
        "availability_is_assumed": True, "independent_performance_evaluation": False,
        "capacity_enforced_at_runtime": False,
    }
    inserted = reused = 0
    with connect(db, create=True) as con:
        with transaction(con):
            previous = con.execute("SELECT config_json FROM configuration WHERE id=1").fetchone()
            if previous and previous[0] != json_text(config):
                raise ValueError("Banco vinculado a outro lote, modelo, código ou fonte. Use outra saída.")
            if not previous:
                con.execute("INSERT INTO configuration VALUES (1, ?)", (json_text(config),))
            for _, row in selected.iterrows():
                request = EventPredictRequest(
                    conjunto=policy["conjunto"], weather_model=row["weather_model"],
                    **{name: row[name] for name in TIME_COLUMNS},
                    features={name: float(row[name]) for name in runtime.columns},
                )
                request_dict = request.model_dump(mode="json")
                request_hash = canonical_hash(request_dict)
                origin = iso(request.forecast_origin)
                existing = con.execute(
                    "SELECT request_sha256 FROM predictions WHERE forecast_origin=?", (origin,),
                ).fetchone()
                if existing:
                    if existing[0] != request_hash:
                        raise ValueError(f"Pedido alterado para emissão já registrada: {origin}")
                    reused += 1
                    continue
                response = runtime.predict(request).model_dump(mode="json")
                available = request.target_time + timedelta(hours=policy["availability_delay_hours"])
                con.execute("INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    origin, iso(request.target_time), iso(available), request_hash,
                    json_text(request_dict), json_text(response), response["p_event"],
                    response["threshold"], int(response["alarm"]),
                    response["event_generation_at_or_below_mwmed"], iso(datetime.now(timezone.utc)),
                ))
                inserted += 1
        exported = pd.read_sql_query(
            "SELECT forecast_origin, target_time, target_available_at, p_event, threshold, alarm, "
            "event_generation_at_or_below_mwmed, request_sha256 FROM predictions ORDER BY forecast_origin", con,
        )
    output = Path(db).parent
    exported.to_csv(output / "predictions.csv", index=False)
    write_json(output / "batch_manifest.json", config)
    report = {"inserted": inserted, "reused": reused, "total": len(exported), "models_retrained": False}
    print(f"Lote: {inserted} inseridas; {reused} reutilizadas; {len(exported)} registradas.")
    print(f"Banco: {Path(db).resolve()}")
    return report


def reconcile(input_dir, db, as_of):
    cutoff = utc(as_of)
    stamp = iso(cutoff)
    csv_path, meta = source_paths(input_dir)
    # Observações são lidas somente nesta etapa; nunca voltam a runtime.predict.
    observations = pd.read_csv(csv_path, usecols=["target_time", "target_available_at", "target_generation"])
    observations["target_time"] = observations.target_time.map(iso)
    observations["target_available_at"] = observations.target_available_at.map(iso)
    observations["target_generation"] = pd.to_numeric(observations.target_generation, errors="raise")
    if observations.target_time.duplicated().any():
        raise ValueError("Alvo duplicado na fonte de observações.")
    observations = observations.set_index("target_time")
    with connect(db) as con:
        config_row = con.execute("SELECT config_json FROM configuration WHERE id=1").fetchone()
        if config_row is None:
            raise ValueError("Banco sem lote; execute emit primeiro.")
        config = json.loads(config_row[0])
        if config["release"] != RELEASE or config["code_sha256"] != sha256(Path(__file__)):
            raise ValueError("Versão do código diferente da que registrou este lote.")
        if config["source_frame_sha256"] != meta["output_sha256"]:
            raise ValueError("Fonte diferente da vinculada ao lote histórico.")
        predictions = con.execute("SELECT * FROM predictions ORDER BY forecast_origin").fetchall()
        if not predictions or cutoff < utc(predictions[-1]["forecast_origin"]):
            raise ValueError("as-of deve ser posterior ou igual à última emissão do lote.")
        policy = config["policy"]
        records = []
        for pred in predictions:
            result = {"as_of": stamp, "forecast_origin": pred["forecast_origin"],
                      "status": "awaiting_label", "target_generation": None,
                      "event_drop": None, "brier": None, "cost": None}
            if utc(pred["target_available_at"]) <= cutoff:
                result["status"] = "missing_observation"
                if pred["target_time"] in observations.index:
                    observed = observations.loc[pred["target_time"]]
                    if observed["target_available_at"] != pred["target_available_at"]:
                        raise ValueError("Disponibilidade observada difere da hipótese do lote.")
                    y = observed["target_generation"]
                    if pd.notna(y):
                        if not np.isfinite(y):
                            raise ValueError("Geração observada deve ser finita.")
                        event = int(y <= pred["event_generation_at_or_below_mwmed"])
                        fp = int(pred["alarm"] == 1 and event == 0)
                        fn = int(pred["alarm"] == 0 and event == 1)
                        result.update(status="observed", target_generation=float(y), event_drop=event,
                                      brier=(pred["p_event"] - event)**2,
                                      cost=fp*policy["cost_fp"] + fn*policy["cost_fn"])
            records.append(result)
        with transaction(con):
            for row in records:
                previous = con.execute(
                    "SELECT * FROM assessments WHERE as_of=? AND forecast_origin=?",
                    (stamp, row["forecast_origin"]),
                ).fetchone()
                if previous and dict(previous) != row:
                    raise ValueError("Tentativa de alterar uma avaliação já registrada.")
                if not previous:
                    con.execute("INSERT INTO assessments VALUES (?, ?, ?, ?, ?, ?, ?)", tuple(row.values()))
        frame = pd.read_sql_query(
            "SELECT a.*, p.target_time, p.target_available_at, p.p_event, p.threshold, p.alarm "
            "FROM assessments a JOIN predictions p USING(forecast_origin) "
            "WHERE a.as_of=? ORDER BY a.forecast_origin", con, params=(stamp,),
        )
    observed = frame.loc[frame.status.eq("observed")]
    alarm, event = observed.alarm.eq(1), observed.event_drop.eq(1)
    tp, fp = int((alarm & event).sum()), int((alarm & ~event).sum())
    fn, tn = int((~alarm & event).sum()), int((~alarm & ~event).sum())
    report = {
        "as_of": stamp, "rows": len(frame), "observed": len(observed),
        "awaiting_label": int(frame.status.eq("awaiting_label").sum()),
        "missing_observation": int(frame.status.eq("missing_observation").sum()),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "brier": float(observed.brier.mean()) if len(observed) else None,
        "precision": tp/(tp+fp) if tp+fp else None, "recall": tp/(tp+fn) if tp+fn else None,
        "cost_total": float(observed.cost.sum()) if len(observed) else None,
        "cost_per_observed_emission": float(observed.cost.mean()) if len(observed) else None,
        "cost_fp": policy["cost_fp"], "cost_fn": policy["cost_fn"],
        "metric_denominator": "observed only; pending labels are not zeros",
        "scope": config["scope"], "independent_performance_evaluation": False,
        "availability_is_assumed": True, "predictions_changed": False,
        "model_sha256": config["model_sha256"], "source_frame_sha256": meta["output_sha256"],
    }
    output = Path(db).parent / "snapshots" / cutoff.strftime("%Y%m%dT%H%M%SZ")
    output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output / "assessment.csv", index=False)
    write_json(output / "summary.json", report)
    print(f"Corte {stamp}: {len(observed)} avaliáveis; {report['awaiting_label']} aguardando rótulo; "
          f"{report['missing_observation']} sem observação após o prazo.")
    print(f"TP={tp}; FP={fp}; FN={fn}; TN={tn}; Brier={report['brier']}; custo={report['cost_total']}")
    print(f"Arquivos: {output.resolve()}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    emit_cli = commands.add_parser("emit", help="Emitir e registrar; repetição reutiliza previsões.")
    emit_cli.add_argument("--input-dir", type=Path, required=True)
    emit_cli.add_argument("--model-dir", type=Path, required=True)
    emit_cli.add_argument("--policy", type=Path, required=True)
    emit_cli.add_argument("--db", type=Path, default=DEFAULT_DB)
    emit_cli.add_argument("--origin-start", required=True)
    emit_cli.add_argument("--origin-end", required=True)
    emit_cli.add_argument("--threads", type=int, default=2)
    score_cli = commands.add_parser("reconcile", help="Avaliar somente os rótulos disponíveis no corte.")
    score_cli.add_argument("--input-dir", type=Path, required=True)
    score_cli.add_argument("--db", type=Path, default=DEFAULT_DB)
    score_cli.add_argument("--as-of", required=True)
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    if command == "emit":
        args["policy_path"] = args.pop("policy")
        emit(**args)
    else:
        reconcile(**args)


if __name__ == "__main__":
    main()
