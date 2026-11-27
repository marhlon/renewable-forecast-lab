"""Prepare protocolo; depois execute Registry/HTTP/replay/drift locais do bloco 3."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import socket
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "notebooks")]
BASE = ROOT / "reports/fechamento_m00_m09/bloco3_engenharia"
B2 = ROOT / "reports/fechamento_m00_m09/bloco2_engenharia/M03-03"
IDS = [f"M06-{n:02d}" for n in range(3, 10)]
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
os.environ.setdefault("MLFLOW_ENABLE_ASYNC_LOGGING", "false")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

from renewable_forecast.bloco3_ops import Jsonl, ShadowLedger, create_local_app, digest, drift_report


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")


def note(item, text):
    (BASE / item / "parecer.md").write_text(text + "\n", encoding="utf-8")


def prepare():
    destination = BASE / "M06-03/protocolo.json"
    if destination.exists():
        raise FileExistsError("Protocolo existente: não sobrescrever desenho após observar resultados.")
    selection = json.loads((B2 / "selection_manifest.json").read_text(encoding="utf-8"))
    bundle = B2 / "point_bundle.joblib"
    if digest(bundle) != selection["bundle_sha256"]:
        raise ValueError("bundle_hash_mismatch")
    source = ROOT / selection["source"]["path"]
    protocol = {"created_at": now(), "scope": IDS,
        "author": "Codex: construção, execução e análise assistidas; sem certificação de autonomia pessoal",
        "environment": "Windows local; socket 127.0.0.1; sem Docker/cloud/recursos pagos",
        "model": {"path": rel(bundle), "sha256": digest(bundle), "selected": selection["selected"],
                  "training_cut": selection["final_training_cut"], "retraining": False},
        "source": {"path": rel(source), "sha256": digest(source)},
        "availability": "UTC e atraso de duas horas são hipóteses de estudo do bloco 2; PIT operacional não comprovado",
        "sample": "Primeiras 48 linhas completas de junho/2026, já examinadas no desenvolvimento; nenhuma alegação de teste intocado",
        "registry": {"backend": "MLflow Model Registry com MlflowClient, SQLite local novo", "alias": "active",
                     "sequence": "version1 -> version2 -> version1 rollback", "versions": "duas versões do mesmo artefato congelado: ensaio de implantação, sem novo treinamento",
                     "promotion": "integridade do bundle, assinatura exata, igualdade de inferência e escopo local; não autoriza produção"},
        "security": {"bind": "127.0.0.1", "authentication": "x-api-key aleatória 256 bits somente em memória",
                     "body_bytes_max": 8192, "rate_per_second": 1000, "test_rate": 3,
                     "telemetry": "apenas timestamp, UUID gerado no servidor, status, bytes, duração e identidade de modelo; sem corpo/cabeçalho/token",
                     "threat": "acesso HTTP local sem chave, exaustão de corpo/taxa e contrato inválido; TLS/RBAC/multitenancy não avaliados"},
        "capacity": {"requests": 240, "concurrency": [1, 4], "timeout_seconds": 5,
                     "max_duration_seconds_per_case": 30, "p95_ms_max": 500, "error_fraction_max": 0.01,
                     "rss_mb_max": 2048, "abort_rss_mb": 3072, "cpu_threads": 2,
                     "spend_cap_brl": 0, "cost_scope": "nenhum recurso cloud criado; energia/depreciação local não tarifadas; não equivale a custo observado de produção"},
        "shadow": {"live_enabled": False, "reason": "M04-05/PIT, CI remoto e janela real ainda não comprovados",
                   "replay_rows": 48, "horizon_hours": 24, "assumed_input_delay_hours": 2,
                   "prospective_window": "7 dias consecutivos após autorização e fontes verificadas, mínimo 144 emissões e reconciliação posterior; não executada",
                   "intervals_classes": "M06-05 C3/C4 permanecem pendentes, nenhuma calibração ou ajuste aqui"},
        "drift": {"reference": "primeiras 24 amostras de junho já examinado", "current": "24 seguintes; contraprovas sintéticas separadas",
                  "min_samples": 20, "mean_shift_reference_sd": 1.5, "mae_ratio": 1.5,
                  "mae_absolute_increase_mw": 10, "max_missing_fraction": 0.05,
                  "max_label_delay_hours": 6, "false_alert_budget": "triagem determinística: no máximo uma investigação por janela diária/variável; não é limite probabilístico de falso positivo",
                  "automatic_retrain": False, "automatic_promotion": False},
        "cloud": {"create_resources": False, "approval_required": "conta/projeto, região, titular, teto monetário e janela antes da execução"},
        "code": {rel(ROOT / "src/renewable_forecast/bloco3_ops.py"): digest(ROOT / "src/renewable_forecast/bloco3_ops.py"),
                 rel(Path(__file__)): digest(__file__)}}
    for item in IDS:
        write(BASE / item / "protocolo.json", {**protocol, "scope": [item]})
    print(json.dumps({"prepared_at": protocol["created_at"], "protocol_sha256": digest(destination), "scope": IDS}))


@contextmanager
def local_server(app):
    import uvicorn
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                        log_level="critical", access_log=False, lifespan="off"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not server.started:
        raise RuntimeError("local_service_not_started")
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(10)
        listener.close()
        if thread.is_alive():
            raise RuntimeError("local_service_did_not_stop")


def registry(protocol, frame):
    import joblib
    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature, Model
    from mlflow.tracking import MlflowClient
    import numpy as np

    folder = BASE / "M06-03"
    execution = folder / "registry_run_02"
    execution.mkdir(parents=True, exist_ok=True)
    db = execution / "mlflow_registry.sqlite"
    if db.exists():
        raise FileExistsError("Registry existente: conservar execução, não criar recibo substituto.")
    tracking = "sqlite:///" + db.resolve().as_posix()
    mlflow.set_tracking_uri(tracking)
    mlflow.set_registry_uri(tracking)
    mlflow.set_experiment("bloco3_local_registry")
    client = MlflowClient(tracking_uri=tracking, registry_uri=tracking)
    bundle = joblib.load(ROOT / protocol["model"]["path"])
    features = bundle["features"]
    X = frame[features]
    predictions = bundle["model"].predict(X)
    X.to_csv(execution / "input_example.csv", index=False)
    signature = infer_signature(X, predictions)
    model_path = execution / "mlflow_model"
    mlflow.sklearn.save_model(bundle["model"], str(model_path), signature=signature,
                            skops_trusted_types=["sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"],
                            input_example=X.iloc[:2], pip_requirements=[f"scikit-learn=={__import__('sklearn').__version__}",
                                                                       f"pandas=={__import__('pandas').__version__}",
                                                                       f"numpy=={np.__version__}"])
    name = "renewcast_b3_frozen_hgb"
    client.create_registered_model(name, description="Registro local do artefato B2; promoção/rollback de empacotamento idêntico, sem homologação operacional.")
    with mlflow.start_run(run_name="frozen_artifact_registry_smoke") as run:
        mlflow.log_params({"scope": "local_engineering", "bundle_sha256": protocol["model"]["sha256"],
                           "sample_sha256": digest(execution / "input_example.csv"), "retrained": False})
        versions = []
        for label in ("initial", "identical_package_candidate"):
            version = client.create_model_version(name, source=model_path.resolve().as_uri(), run_id=run.info.run_id,
                       tags={"bundle_sha256": protocol["model"]["sha256"], "signature_sha256": hashlib.sha256(json.dumps(signature.to_dict(), sort_keys=True).encode()).hexdigest(),
                             "input_sha256": digest(execution / "input_example.csv"), "source_sha256": protocol["source"]["sha256"],
                             "scope": "local_engineering", "purpose": label})
            versions.append(str(version.version))
        transitions = []
        for action, version in (("activate_initial", versions[0]), ("promote_identical_package", versions[1]), ("rollback", versions[0])):
            client.set_registered_model_alias(name, "active", version)
            resolved = client.get_model_version_by_alias(name, "active")
            loaded = mlflow.pyfunc.load_model(f"models:/{name}@active")
            result = loaded.predict(X)
            if str(resolved.version) != version or not np.allclose(predictions, result, rtol=0, atol=1e-10):
                raise AssertionError("registry_resolution_or_prediction_mismatch")
            transitions.append({"recorded_at": now(), "action": action, "resolved_version": str(resolved.version),
                                "source": resolved.source, "run_id": resolved.run_id,
                                "max_prediction_difference": float(np.max(np.abs(predictions-result)))})
        run_id = run.info.run_id
    result = {"executed_at": now(), "execution_kind": "real_local_mlflow_model_registry", "mlflow_version": mlflow.__version__,
        "registry_uri": tracking, "registered_model": name, "versions": versions, "active_alias": "active", "active_version": versions[0],
        "run_id": run_id, "transitions": transitions, "input_identity": {"path": rel(execution / "input_example.csv"), "sha256": digest(execution / "input_example.csv"), "rows": len(X), "features": features},
        "model_identity": protocol["model"], "signature": Model.load(str(model_path / "MLmodel")).signature.to_dict(),
        "mlmodel_sha256": digest(model_path / "MLmodel"), "criteria": {"C1": True, "C2": True},
        "limits": ["SQLite é apenas backend desta instalação real do MLflow Registry; não reutiliza event_registry.",
                   "Duas versões apontam o mesmo modelo: prova resolução/rollback de implantação, não superioridade de candidato.",
                   "Sem autenticação do servidor MLflow, alta disponibilidade ou Registry remoto; API Python local, sem servidor público."]}
    write(folder / "registry_mlflow.json", result)
    write(folder / "resultado.json", result)
    note("M06-03", f"# Parecer técnico M06-03\n\nO MLflow {mlflow.__version__} criou modelo registrado e versões {versions}, com assinatura e identidades de entrada/bundle. O alias ativo foi resolvido após cada transição e voltou à versão {versions[0]}; as previsões coincidiram exatamente. O artefato não foi retreinado. As duas versões são empacotamentos idênticos usados para exercitar implantação/rollback. Critérios C1/C2 atendidos no ambiente local; nenhuma homologação de infraestrutura remota é inferida. Construção, execução e parecer: Codex.")
    return loaded, features, {"registry_model": name, "version": versions[0], "bundle_sha256": protocol["model"]["sha256"]}, predictions


def security_and_capacity(protocol, model, features, identity, frame):
    import httpx
    import numpy as np
    import pandas as pd
    import psutil
    sec, capacity = protocol["security"], protocol["capacity"]
    key = secrets.token_hex(32)
    payload = {"features": {name: float(frame.iloc[0][name]) for name in features}}
    headers = {"x-api-key": key}
    log_path = BASE / "M06-07/http_telemetry.jsonl"
    app = create_local_app(model, features, identity, key, Jsonl(log_path), max_body=sec["body_bytes_max"], rate=1000)
    observations = []
    with local_server(app) as url, httpx.Client(timeout=5, trust_env=False) as client:
        cases = [("missing_key", lambda: client.post(url+"/predict", json=payload), 401),
                 ("wrong_key", lambda: client.post(url+"/predict", json=payload, headers={"x-api-key": "wrong"}), 401),
                 ("valid", lambda: client.post(url+"/predict", json=payload, headers=headers), 200),
                 ("declared_oversized", lambda: client.post(url+"/predict", content=b"x"*9000, headers=headers), 413),
                 ("chunked_oversized", lambda: client.post(url+"/predict", content=iter([b"x"*5000, b"y"*4000]), headers=headers), 413),
                 ("invalid_features", lambda: client.post(url+"/predict", json={"features": {}}, headers=headers), 422),
                 ("malformed_json", lambda: client.post(url+"/predict", content=b"{", headers=headers), 422)]
        for name, request, expected in cases:
            response = request()
            observations.append({"case": name, "expected": expected, "status": response.status_code,
                                 "passed": response.status_code == expected, "request_id": response.headers.get("x-request-id")})
        process = psutil.Process()
        capacity_rows = []
        for concurrency in capacity["concurrency"]:
            timings, errors, rss = [], [], []
            initial_cpu = sum(process.cpu_times()[:2])
            started = time.perf_counter()
            stop = threading.Event()
            def sample():
                while not stop.wait(0.01):
                    rss.append(process.memory_info().rss/1024**2)
            sampler = threading.Thread(target=sample, daemon=True)
            sampler.start()
            def one(index):
                if time.perf_counter()-started > capacity["max_duration_seconds_per_case"]:
                    return None, "duration_budget"
                if process.memory_info().rss/1024**2 > capacity["abort_rss_mb"]:
                    return None, "rss_budget"
                before = time.perf_counter()
                try:
                    response = client.post(url+"/predict", json=payload, headers=headers)
                    valid = response.status_code == 200 and response.json().get("version") == identity["version"]
                    return (time.perf_counter()-before)*1000, None if valid else "status_or_identity"
                except (httpx.HTTPError, ValueError):
                    return (time.perf_counter()-before)*1000, "request_error"
            try:
                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    for duration, error in pool.map(one, range(capacity["requests"])):
                        if duration is not None:
                            timings.append(duration)
                        if error:
                            errors.append(error)
            finally:
                stop.set()
                sampler.join()
            elapsed = time.perf_counter()-started
            cpu = sum(process.cpu_times()[:2])-initial_cpu
            row = {"concurrency": concurrency, "attempts": capacity["requests"], "completed": len(timings),
                   "elapsed_seconds": elapsed, "requests_per_second": len(timings)/elapsed,
                   "p50_ms": float(np.quantile(timings, .5)), "p95_ms": float(np.quantile(timings, .95)),
                   "p99_ms": float(np.quantile(timings, .99)), "error_count": len(errors),
                   "error_fraction": len(errors)/capacity["requests"], "process_cpu_seconds": cpu,
                   "process_cpu_percent_one_core": 100*cpu/elapsed, "rss_peak_mb": max(rss or [process.memory_info().rss/1024**2]),
                   "resource_scope": "processo runner + cliente HTTP + servidor/modelo/MLflow; RSS total, sem subtração de baseline",
                   "cloud_invoice_observed": False, "cloud_resources_created": 0, "incremental_cloud_charge_brl": 0,
                   "local_energy_or_depreciation_brl": None}
            row["slo_passed"] = row["p95_ms"] <= capacity["p95_ms_max"] and row["error_fraction"] <= capacity["error_fraction_max"] and row["rss_peak_mb"] <= capacity["rss_mb_max"] and elapsed <= capacity["max_duration_seconds_per_case"]
            capacity_rows.append(row)
    rate_app = create_local_app(model, features, identity, key, Jsonl(log_path), rate=3, rate_window=60)
    with local_server(rate_app) as url, httpx.Client(timeout=5, trust_env=False) as client:
        codes = [client.get(url+"/health", headers=headers).status_code for _ in range(4)]
        observations.append({"case": "rate_limit", "expected_statuses": [200, 200, 200, 429],
                             "statuses": codes, "passed": codes == [200, 200, 200, 429]})
    leaked = key in log_path.read_text(encoding="utf-8")
    result = {"executed_at": now(), "scope": "real_http_loopback_only", "controls": sec,
              "contraprovas": observations, "secret_in_log": leaked,
              "all_passed": all(row["passed"] for row in observations) and not leaked,
              "service_stopped": True, "key_destroyed_with_process": "token não persistido; variável de memória liberada ao fim do processo",
              "production_security_certified": False}
    write(BASE / "M06-07/contraprovas.json", result)
    write(BASE / "M06-07/resultado.json", result)
    note("M06-07", "# Parecer técnico M06-07\n\nHTTP real em socket 127.0.0.1; chave efêmera somente em memória, comparação constante, limite de bytes lidos inclusive chunked, taxa limitada e contrato de atributos. Contraprovas registradas em contraprovas.json. O log exclui token/cabeçalhos/corpo e a ausência do token foi conferida. Sem portas públicas, TLS, RBAC ou certificação geral. Incidente: interromper processo, invalidar chave por reinício, preservar logs sem segredos e investigar antes de reabrir. Construção, execução e parecer: Codex.")
    (BASE / "M06-07/avaliacao_seguranca.md").write_text((BASE / "M06-07/parecer.md").read_text(encoding="utf-8"), encoding="utf-8")
    pd.DataFrame(capacity_rows).to_csv(BASE / "M06-08/capacidade_custo.csv", index=False)
    write(BASE / "M06-08/orcamento.json", capacity)
    result = {"executed_at": now(), "execution_kind": "bounded_local_http_load", "budget_predeclared": capacity,
              "measurements": capacity_rows, "all_local_slos_passed": all(r["slo_passed"] for r in capacity_rows),
              "sustained_operation_proven": False, "production_cost_measured": False,
              "limits": ["480 requisições finitas não demonstram operação contínua", "CPU/RSS incluem cliente e servidor no mesmo processo; nenhum processo de nuvem existe", "Nenhuma fatura foi observada; custo local de energia/depreciação não medido"]}
    write(BASE / "M06-08/resultado.json", result)
    note("M06-08", "# Parecer técnico M06-08\n\nBenchmark HTTP executado com orçamento e SLO fixados antes da medição, cargas de 240 requisições com concorrência 1 e 4. CSV registra latência, erros, CPU do processo, RSS total e resultado dos SLOs. Custo incremental de recursos cloud criados: zero, pois nenhum foi criado; não há fatura nem medição de energia/depreciação local. Este ensaio curto não encerra sustentaçao/custo operacional. Construção, execução e parecer: Codex.")
    return {"security_passed": result.get("all_passed"), "capacity": capacity_rows}


def replay_and_drift(protocol, frame, predictions):
    import numpy as np
    import pandas as pd
    folder = BASE / "M06-04"
    live_denied = False
    try:
        ShadowLedger(folder / "live_should_not_exist.jsonl", model_sha256=protocol["model"]["sha256"], mode="live")
    except ValueError as exc:
        live_denied = str(exc) == "M04_point_in_time_contract_not_verified"
    ledger = ShadowLedger(folder / "replay_ledger.jsonl", model_sha256=protocol["model"]["sha256"])
    emissions, reconciliations, incidents = [], [], []
    for index, row in frame.iterrows():
        origin = pd.Timestamp(row["forecast_origin"], tz="UTC")
        target = origin + pd.Timedelta(hours=24)
        origin_s, target_s = origin.isoformat(), target.isoformat()
        source_time = origin-pd.Timedelta(hours=2)
        source_arrival = origin-pd.Timedelta(minutes=1)
        record = ledger.emit(origin=origin_s, target_time=target_s,
            source_event_time=source_time.isoformat(), source_arrived_at=source_arrival.isoformat(),
            source_vintage=source_arrival.isoformat(), source_sha256=protocol["source"]["sha256"],
            prediction=float(predictions[len(emissions)]), trace_id=f"replay-{len(emissions):04d}", replay_clock=origin_s)
        emissions.append(record)
        arrival = target + pd.Timedelta(hours=2)
        reconciliations.append(ledger.reconcile(origin=origin_s, target_time=target_s, value=float(row["y24"]),
            arrived_at=arrival.isoformat(), source_vintage=arrival.isoformat(), source_sha256=protocol["source"]["sha256"], observed_at=arrival.isoformat()))
    # Contraprovas causais independentes: deliberadamente rejeitadas pelo mesmo coletor.
    first = emissions[0]
    for label, changes in [("future_arrival", {"source_arrived_at": "2099-01-01T00:00:00+00:00"}),
                           ("future_vintage", {"source_vintage": "2099-01-01T00:00:00+00:00"}),
                           ("stale_input", {"source_event_time": "2000-01-01T00:00:00+00:00"}),
                           ("duplicate_origin", {})]:
        arguments = {k: first[k] for k in ("origin", "target_time", "source_event_time", "source_arrived_at", "source_vintage", "source_sha256", "prediction", "trace_id")}
        arguments.update(replay_clock=first["emission_clock"], **changes)
        try:
            ledger.emit(**arguments)
            rejected, reason = False, "accepted_unexpectedly"
        except ValueError as exc:
            rejected, reason = True, str(exc)
        incidents.append({"case": label, "rejected": rejected, "reason": reason, "mode": "counterexample_replay"})
    pd.DataFrame(emissions).to_csv(folder / "shadow.csv", index=False)
    pd.DataFrame(incidents).to_csv(folder / "incidentes.csv", index=False)
    pd.DataFrame(reconciliations).to_csv(folder / "reconciliacao_replay.csv", index=False)
    result = {"executed_at": now(), "execution_kind": "historical_replay_of_collector_contract", "live_guard_rejected": live_denied,
              "replay_emissions": len(emissions), "replay_reconciliations": len(reconciliations),
              "all_counterexamples_rejected": all(r["rejected"] for r in incidents), "live_emissions": 0,
              "observed_live_hours": 0, "operational_criteria": {"C1": False, "C2": False},
              "source_arrivals": "simuladas no replay; received_at é horário real de gravação e não data de emissão histórica",
              "blocked_by": ["M04-05: fuso/vintage/chegada reais não certificados", "M06-02: CI remoto não demonstrado", "janela prospectiva não transcorrida"]}
    write(folder / "resultado.json", result)
    note("M06-04", "# Parecer técnico M06-04\n\nColetor real construído e exercitado em replay explicitamente marcado. Bloqueio fail-closed de modo live sem contrato M04 e contraprovas de chegada futura, vintage futuro, entrada antiga e duplicação conferidos. Cada emissão conserva origem/alvo, vintage/chegada, hash e trace; alvo é conciliado somente após sua chegada. source_arrived_at é simulado; received_at é relógio real local. Zero emissões live; C1/C2 operacionais não atendidos. Para operar, verificar fonte/PIT e CI, autorizar janela e coletar sete dias reais com conciliação posterior. Construção, execução e parecer: Codex.")
    monitoring = pd.DataFrame(reconciliations)
    monitoring["label_delay_is_assumption"] = True
    monitoring["live_continuity_proven"] = False
    monitoring.to_csv(BASE / "M06-05/monitoramento.csv", index=False)
    pd.DataFrame([{"scenario": "collector_restart", "response": "parar/coletar novo processo; journal preservado", "status": "contrato documentado; recuperação persistente exercitada em testes"},
                  {"scenario": "missing_arrival", "response": "não emitir até verificar chegada; registrar interrupção", "status": "contraprova local"}]).to_csv(BASE / "M06-05/incidentes.csv", index=False)
    write(BASE / "M06-05/resultado.json", {"executed_at": now(), "execution_kind": "replay_monitoring_readiness",
          "live_observation_hours": 0, "replay_rows": len(reconciliations), "assumed_label_delay_hours": 2,
          "continuous_service_proven": False, "prospective_intervals_proven": False, "prospective_probability_calibration_proven": False,
          "operational_criteria": {"C1": False, "C2": False, "C3": False, "C4": False},
          "incident_owner": "titular deve designar responsável e canal antes de iniciar operação; Codex não se atribui plantão"})
    note("M06-05", "# Parecer técnico M06-05\n\nMonitoramento do replay mede reconciliação, atraso de rótulo assumido e erro por emissão. Não se esperaram 26 horas reais nem sete dias; não se convertem minutos de execução em continuidade. C1–C4 permanecem falsos, incluindo intervalos/classes prospectivos transferidos de M05. O titular deve designar responsável/canal e iniciar janela real após contratos. Nenhum intervalo, calibrador ou política foi reajustado. Construção, execução e parecer: Codex.")
    reference = frame.iloc[:24]["lag_1h"].to_numpy(float)
    current = frame.iloc[24:]["lag_1h"].to_numpy(float)
    errors = np.asarray(predictions)-frame["y24"].to_numpy(float)
    kwargs = {"reference": reference, "current": current, "reference_errors": errors[:24], "current_errors": errors[24:],
              "missing_fraction": 0, "label_delay_hours": 2, "protocol": protocol["drift"]}
    rows = [{"case": "historical_reference_current", **drift_report(**kwargs)}]
    controls = [("no_change", {"current": reference, "current_errors": errors[:24]}),
                ("input_shift_only", {"current": reference+3*np.std(reference), "current_errors": errors[:24]}),
                ("performance_only", {"current": reference, "current_errors": np.abs(errors[:24])*3+20}),
                ("quality_missing", {"current": reference, "current_errors": errors[:24], "missing_fraction": .2}),
                ("label_delay", {"current": reference, "current_errors": errors[:24], "label_delay_hours": 12})]
    for label, changes in controls:
        rows.append({"case": label, **drift_report(**{**kwargs, **changes})})
    pd.DataFrame(rows).to_csv(BASE / "M06-06/drift.csv", index=False)
    write(BASE / "M06-06/resultado.json", {"executed_at": now(), "execution_kind": "frozen_local_drift_screen_and_counterexamples",
          "protocol": protocol["drift"], "results": rows, "operational_response_tested_live": False,
          "criteria_local_engineering": {"reference_and_thresholds_fixed_before_window": True, "separate_input_quality_performance": True},
          "automatic_retrain_or_promotion": False})
    response = "# Resposta a drift\n\nReferência e limiares foram fixados no protocolo antes do cálculo. Referência: primeiras 24 linhas completas de junho, já examinadas; corrente: 24 seguintes. Contraprovas alteram somente a variável descrita e não são dados de operação.\n\nAlertas de missing/atraso abrem investigação da fonte; não se atribui queda do modelo a rótulo ainda ausente. Mudança de entrada sem aumento de erro abre investigação de cobertura/distribuição; queda de desempenho com entrada estável abre investigação do modelo/coorte. Erro, viés, intervalos e classes requerem alvos realmente conciliados. No máximo uma investigação por variável/janela diária; esse orçamento de triagem não garante probabilidade de falso positivo e não foi calibrado numa sequência prospectiva. O protótipo retorna uma decisão por chamada; deduplicação entre dias/plantões deve ser integrada ao sistema de incidentes antes de operação.\n\nInterromper novas emissões quando origem/chegada/vintage falharem; preservar journal e identidade; avaliar o baseline congelado; rollback somente após revisão humana de integridade e efeito. Não retreinar, recalibrar ou promover automaticamente. Operação real depende de M06-05 e responsável designado.\n\nConstrução, execução e parecer: Codex."
    (BASE / "M06-06/resposta_drift.md").write_text(response, encoding="utf-8")
    note("M06-06", response.replace("# Resposta a drift", "# Parecer técnico M06-06"))


def cloud_readiness(protocol):
    folder = BASE / "M06-09"
    plan = {"prepared_at": now(), "kind": "reviewable_plan_only", "execution_authorized": False,
        "target": {"provider": "a escolher pelo titular", "account_project": None, "region": None,
                   "architecture": "uma VM/container isolado de CPU, rede privada, acesso por túnel autenticado; sem endpoint público no primeiro ensaio",
                   "model_bundle_sha256": protocol["model"]["sha256"], "max_instances": 1, "gpu": False},
        "required_before_provision": ["titular/conta/projeto/região confirmados", "teto financeiro numérico aprovado", "prazo TTL e alarme de orçamento", "credencial por secret manager/identidade de curta duração", "CI remoto clone limpo comprovado", "artefatos assinados/hash e storage privado", "responsável pelo incidente", "autorização explícita para criar e cobrar recursos"],
        "steps": ["validar plano e identidade sem credenciais em logs", "aplicar rede privada/identidade mínima/storage com TTL", "subir uma instância do artefato congelado", "testar auth/limites/smoke e rollback de versão", "medir latência/CPU/RSS/erros e serviços acessórios/fatura", "desligar VM, IP, storage temporário e identidades conforme inventário", "conferir inventário e custo após teardown"],
        "stop_rules": ["gasto chega a 80% do teto aprovado", "TTL expira", "falha de autenticação/rede privada/integridade", "erros ou latência ultrapassam SLO aprovado"],
        "resources_created": [], "endpoints_created": [], "invoice_observed": False, "criteria": {"C1_preparation_only": True, "C2": False}}
    write(folder / "deploy_cloud.json", plan)
    write(folder / "desligamento.json", {"recorded_at": now(), "execution_kind": "no_provisioning_occurred", "resources_created": [],
          "teardown_required": False, "teardown_executed": False, "cloud_inventory_verified": False,
          "note": "Nenhum comando/cloud API executado. Não é recibo de desligamento de recursos existentes."})
    write(folder / "resultado.json", {"recorded_at": now(), "engineering_preparation_completed": True, "deployment_executed": False,
          "actual_cloud_cost_observed": False, "operational_criteria": {"C1": False, "C2": False},
          "blocked_by": plan["required_before_provision"]})
    note("M06-09", "# Parecer técnico M06-09\n\nPlano de provisionamento delimitado, parâmetros pendentes, teto/TTL, rede privada, revisão, rollback e inventário de encerramento estão em deploy_cloud.json. Nenhuma conta, credencial ou teto foi fornecido/aprovado; nenhum recurso ou endpoint foi criado. desligamento.json declara que não houve provisionamento, não simula teardown. C1 operacional (ambiente preparado) e C2 (implantar/testar/encerrar/custo real) permanecem não comprovados. Construção e análise do plano: Codex.")


def run():
    protocol = json.loads((BASE / "M06-03/protocolo.json").read_text(encoding="utf-8"))
    repair = BASE / "M06-03/adendo_reparo_compatibilidade.json"
    code = dict(protocol["code"])
    if repair.exists():
        receipt = json.loads(repair.read_text(encoding="utf-8"))
        if receipt["original_protocol_sha256"] != digest(BASE / "M06-03/protocolo.json"):
            raise ValueError("repair_protocol_mismatch")
        code.update(receipt["code_after_repair"])
    for path, expected in code.items():
        if digest(ROOT / path) != expected:
            raise ValueError(f"protocol_code_changed:{path}")
    for key in ("source", "model"):
        if digest(ROOT / protocol[key]["path"]) != protocol[key]["sha256"]:
            raise ValueError(f"protocol_{key}_changed")
    import numpy as np
    from bloco2_modelagem_core import build_frame, load_series
    from threadpoolctl import threadpool_limits
    frame = build_frame(load_series(ROOT / protocol["source"]["path"]))
    frame = frame[(frame.forecast_origin >= "2026-06-01") & (frame.forecast_origin < "2026-07-01")]
    frame = frame[np.isfinite(frame.select_dtypes(include=[np.number])).all(axis=1)].iloc[:48].reset_index(drop=True)
    if len(frame) != 48:
        raise ValueError("insufficient_predeclared_sample")
    started = now()
    with threadpool_limits(limits=2):
        model, features, identity, predictions = registry(protocol, frame)
        security_and_capacity(protocol, model, features, identity, frame)
        replay_and_drift(protocol, frame, predictions)
    cloud_readiness(protocol)
    manifest = {"started_at": started, "finished_at": now(), "scope": IDS,
                "author": "Codex", "python": sys.version, "platform": platform.platform(),
                "artifacts": [{"path": rel(p), "sha256": digest(p)} for item in IDS for p in sorted((BASE / item).rglob("*"))
                              if p.is_file() and not p.name.endswith((".sqlite-wal", ".sqlite-shm"))],
                "live_shadow_proven": False, "cloud_deployment_proven": False,
                "service_stopped": True, "public_endpoint_created": False}
    write(BASE / "M06-03/manifesto_operacao_local.json", manifest)
    print(json.dumps({"started_at": started, "finished_at": manifest["finished_at"], "manifest": rel(BASE / "M06-03/manifesto_operacao_local.json"),
                      "items": IDS, "live_shadow_proven": False, "cloud_deployment_proven": False}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "run"])
    args = parser.parse_args()
    prepare() if args.action == "prepare" else run()
