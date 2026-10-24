"""M06: mede concorrencia na imagem aprovada, sem build, download ou treino.

Na raiz do projeto: python scripts/medir_concorrencia.py
Usa somente a biblioteca padrao. O cliente usa carga fechada e destino local.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
from pathlib import Path
import platform
import re
import shutil
import statistics
import subprocess
import threading
import time
import uuid
import csv


PROJECT = Path(__file__).resolve().parents[1]
RUN_ROOT = PROJECT / "reports/containers/CJU_BA5EIGT/h24_event_v1"
OUTPUT_ROOT = PROJECT / "reports/performance/CJU_BA5EIGT/h24_event_concurrency_v1"
LEVELS = (1, 4, 8)
TOLERANCE = 1e-12


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def child(root, name):
    root = Path(root).resolve()
    result = (root / name).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"Caminho fora da pasta declarada: {name}")
    return result


def check_files(root, hashes):
    for name, expected in hashes.items():
        path = child(root, name)
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"Arquivo ausente ou alterado: {path}")


def load_source(run_dir=None, project=PROJECT):
    """Relaciona recibo, contexto e resposta; nao escolhe outro experimento."""
    project = Path(project).resolve()
    if run_dir is None:
        pointer = read_json(project / "reports/containers/CJU_BA5EIGT/h24_event_v1/latest_run.json")
        run_dir = Path(pointer["directory"])
        if not run_dir.is_absolute() or sha(run_dir / "verification.json") != pointer["verification_sha256"]:
            raise ValueError("Ponteiro de execucao invalido.")
    run_dir = Path(run_dir).resolve()
    receipt = read_json(run_dir / "verification.json")
    if receipt["verified"] is not True or receipt["platform"] != "linux/amd64":
        raise ValueError("Esta unidade exige uma execucao Linux aprovada.")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", receipt["image_id"]):
        raise ValueError("image_id invalido.")
    check_files(run_dir, receipt["output_sha256"])
    context = child(project / "dist/container_service", receipt["context_id"])
    if sha(context / "context.json") != receipt["context_sha256"]:
        raise ValueError("O contexto nao corresponde a execucao aprovada.")
    metadata = read_json(context / "context.json")
    if metadata["context_id"] != receipt["context_id"] or metadata["source_release_id"] != receipt["source_release_id"]:
        raise ValueError("Contexto e recibo pertencem a releases diferentes.")
    check_files(context, metadata["files_sha256"])
    request = read_json(context / "artifacts/example_request.json")
    reference = read_json(run_dir / "response.json")
    if compare(reference, read_json(context / "reference_response.json")):
        raise ValueError("Referencia do contexto e resposta aprovada divergem.")
    for key in ("model_sha256", "policy_sha256"):
        if reference[key] != receipt[key]:
            raise ValueError(f"Identidade divergente em {key}.")
    return run_dir, receipt, context, request, reference


def compare(reference, actual):
    """Retorna erro ou string vazia; preserva campos e tipos, com tolerancia so em p."""
    if not isinstance(actual, dict) or set(actual) != set(reference):
        return "response_schema"
    for key, expected in reference.items():
        value = actual[key]
        if key == "p_event":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                return "non_finite_probability"
            if not 0 <= value <= 1 or not math.isclose(expected, value, rel_tol=0, abs_tol=TOLERANCE):
                return "probability_mismatch"
        elif type(value) is not type(expected) or value != expected:
            return "changed_" + key
    return ""


def quantile(values, probability):
    """Quantil linear: indice (n-1)*p; equivalente ao metodo linear do NumPy."""
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    low = math.floor(index)
    high = math.ceil(index)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def post(connection, body, reference, sequence, worker, phase_start):
    started_utc = utc_now()
    start = time.perf_counter()
    status, response, error = None, None, ""
    try:
        connection.request("POST", "/predict-decision", body=body, headers={"Content-Type": "application/json"})
        reply = connection.getresponse()
        status = reply.status
        raw = reply.read()
        stop = time.perf_counter()
        if status == 200:
            try:
                response = json.loads(raw)
                error = compare(reference, response)
                outcome = "ok" if not error else "response_mismatch"
            except (ValueError, UnicodeDecodeError):
                outcome, error = "invalid_json", "invalid_json"
        else:
            outcome = "http_5xx" if 500 <= status < 600 else "http_4xx" if 400 <= status < 500 else "http_other"
    except (OSError, http.client.HTTPException) as exc:
        stop = time.perf_counter()
        outcome, error = "transport_error", type(exc).__name__
        connection.close()  # Proxima tentativa abre outra conexao; nao ha retry oculto.
    value = response.get("p_event") if isinstance(response, dict) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        value = None
    return {
        "sequence": sequence, "worker": worker, "started_utc": started_utc,
        "start_offset_ms": (start - phase_start) * 1000,
        "duration_ms": (stop - start) * 1000, "status_code": status,
        "outcome": outcome, "error": error, "p_event": value,
        "absolute_difference": abs(value - reference["p_event"]) if value is not None else None,
    }


def run_phase(port, request, reference, concurrency, calls, timeout=10.0):
    """C workers persistentes, uma chamada em voo por worker; sem fila de N futures."""
    if concurrency < 1 or calls < concurrency:
        raise ValueError("A fase exige calls >= concurrency >= 1.")
    body = json.dumps(request, allow_nan=False).encode("utf-8")
    clock = []
    barrier = threading.Barrier(concurrency + 1, action=lambda: clock.append(time.perf_counter()), timeout=15)

    def worker(number):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        try:
            barrier.wait()
            return [post(connection, body, reference, seq, number, clock[0])
                    for seq in range(number, calls, concurrency)]
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(worker, i) for i in range(concurrency)]
        barrier.wait()
        rows = [row for future in futures for row in future.result()]
    duration = time.perf_counter() - clock[0]
    rows.sort(key=lambda row: row["sequence"])
    return rows, summarize(rows, duration, concurrency)


def summarize(rows, duration, concurrency):
    if not rows or duration <= 0:
        raise ValueError("Amostra vazia ou duracao invalida.")
    good = [r["duration_ms"] for r in rows if r["outcome"] == "ok"]
    failures = len(rows) - len(good)
    return {
        "concurrency": concurrency, "attempts": len(rows), "correct_200": len(good),
        "failed": failures, "failure_rate": failures / len(rows),
        "http_4xx": sum(r["outcome"] == "http_4xx" for r in rows),
        "http_5xx": sum(r["outcome"] == "http_5xx" for r in rows),
        "transport_errors": sum(r["outcome"] == "transport_error" for r in rows),
        "incorrect_200": sum(r["status_code"] == 200 and r["outcome"] != "ok" for r in rows),
        "wall_seconds": duration, "attempts_per_second": len(rows) / duration,
        "correct_per_second": len(good) / duration,
        "mean_correct_ms": statistics.mean(good) if good else None,
        "p50_correct_ms": quantile(good, .5), "p95_correct_ms": quantile(good, .95),
        "p95_attempt_elapsed_ms": quantile([r["duration_ms"] for r in rows], .95),
        "mean_in_flight": sum(r["duration_ms"] for r in rows) / 1000 / duration,
    }


def execute(args, log):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", timeout=45)
    with Path(log).open("a", encoding="utf-8") as handle:
        handle.write("\n" + subprocess.list2cmdline(args) + "\n" + result.stdout)
    if result.returncode:
        raise RuntimeError(f"Comando falhou: {subprocess.list2cmdline(args)}\n{result.stdout[-2000:]}")
    return result.stdout.strip()


def wait_ready(port, container_id, log):
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        try:
            connection.request("GET", "/health")
            response = connection.getresponse()
            if response.status == 200 and json.loads(response.read()).get("model_loaded"):
                return
        except (OSError, http.client.HTTPException, ValueError):
            pass
        finally:
            connection.close()
        state = json.loads(execute(["docker", "inspect", container_id], log))[0]["State"]
        if not state["Running"]:
            raise RuntimeError(f"Conteiner encerrou: {state}")
        time.sleep(.5)
    raise TimeoutError("API nao iniciou em 90 segundos.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--calls-per-phase", type=int, default=120)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args(argv)
    if not 24 <= args.calls_per_phase <= 1000 or args.calls_per_phase % 8:
        parser.error("--calls-per-phase deve ser multiplo de 8, entre 24 e 1000.")
    if not math.isfinite(args.timeout_seconds) or not 1 <= args.timeout_seconds <= 30:
        parser.error("--timeout-seconds deve estar entre 1 e 30.")
    source, receipt, context, request, reference = load_source(args.run_dir)
    if not shutil.which("docker"):
        raise RuntimeError("Docker nao encontrado. Abra Docker Desktop com conteineres Linux.")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = args.output_root.resolve() / run_id
    output.mkdir(parents=True, exist_ok=False)
    log = output / "pipeline.log"
    phases = [(r + 1, c) for r in range(3) for c in LEVELS[r:] + LEVELS[:r]]
    protocol = {
        "schema": "renewcast-concurrency-v1", "run_id": run_id,
        "source_run": str(source), "source_verification_sha256": sha(source / "verification.json"),
        "image_id": receipt["image_id"], "context_sha256": receipt["context_sha256"],
        "model_sha256": receipt["model_sha256"], "policy_sha256": receipt["policy_sha256"],
        "client_python": platform.python_version(), "client_system": platform.system(),
        "cpus_limit": 2, "memory_limit_bytes": 1024**3, "server_workers": 1,
        "calls_per_phase": args.calls_per_phase, "rounds": 3,
        "phases": [{"round": r, "concurrency": c} for r, c in phases],
        "load_model": "closed_loop_one_request_in_flight_per_client",
        "connection_policy": "one_HTTPConnection_per_worker_per_phase_no_retries",
        "timeout_seconds": args.timeout_seconds, "probability_tolerance": TOLERANCE,
        "warmup_calls_excluded": 8, "workload": "one_fixed_valid_request_repeated",
        "exploratory_rule": {"p95_ms_max": 250, "failures_max": 0, "throughput_retained_fraction": .95},
        "code_sha256": sha(Path(__file__)), "operational_policy_approved": False,
    }
    write_json(output / "protocol.json", protocol)
    write_json(output / "request.json", request)
    write_json(output / "reference_response.json", reference)
    rows, summaries, container = [], [], None
    try:
        if execute(["docker", "info", "--format", "{{.OSType}}"], log) != "linux":
            raise ValueError("Docker precisa operar em modo Linux.")
        image = json.loads(execute(["docker", "image", "inspect", receipt["image_id"]], log))[0]
        if image["Id"] != receipt["image_id"] or (image["Os"], image["Architecture"]) != ("linux", "amd64"):
            raise ValueError("A imagem aprovada nao corresponde ao destino.")
        write_json(output / "image.json", image)
        print("Mesma imagem; limite 2 CPUs/1 GiB; 1, 4 e 8 clientes, tres rodadas.", flush=True)
        container = execute([
            "docker", "run", "-d", "--pull", "never", "--read-only",
            "--cpus", "2", "--memory", "1g", "--memory-swap", "1g",
            "--tmpfs", "/tmp:rw,size=64m", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "-p", "127.0.0.1::8000", receipt["image_id"],
        ], log)
        info = json.loads(execute(["docker", "inspect", container], log))[0]
        config = info["HostConfig"]
        if config["NanoCpus"] != 2_000_000_000 or config["Memory"] != 1024**3:
            raise ValueError("Limites de recursos nao foram aplicados.")
        write_json(output / "container.json", info)
        binding = info["NetworkSettings"]["Ports"]["8000/tcp"][0]
        if binding["HostIp"] != "127.0.0.1":
            raise ValueError("Porta deveria estar publicada somente no host local.")
        port = int(binding["HostPort"])
        wait_ready(port, container, log)
        # Leitura da implementacao realmente contida na imagem para a autoria.
        api_code = execute(["docker", "exec", container, "python", "-c",
                            "import inspect; import renewable_forecast.decision_api as a; print(inspect.getsource(a.create_app))"], log)
        (output / "api_source.txt").write_text(api_code + "\n", encoding="utf-8")
        warmup, warm_summary = run_phase(port, request, reference, 1, 8, args.timeout_seconds)
        write_csv(output / "warmup.csv", warmup)
        if warm_summary["failed"]:
            raise RuntimeError("Aquecimento falhou; examine warmup.csv e server.log.")
        for index, (round_number, concurrency) in enumerate(phases, start=1):
            phase_rows, summary = run_phase(port, request, reference, concurrency, args.calls_per_phase, args.timeout_seconds)
            rows.extend({"phase": index, "round": round_number, "concurrency": concurrency, **row} for row in phase_rows)
            summary = {"phase": index, "round": round_number, **summary}
            summaries.append(summary)
            # Checkpoints de cada fase preservam a evidencia se uma fase posterior falhar.
            write_csv(output / "requests.csv", rows)
            write_csv(output / "summary.csv", summaries)
            p95 = summary["p95_correct_ms"]
            p95_text = "indefinido" if p95 is None else f"{p95:.2f} ms"
            print(f"Rodada {round_number}; clientes={concurrency}; corretas={summary['correct_200']}/{summary['attempts']}; "
                  f"p95={p95_text}; vazao={summary['correct_per_second']:.2f}/s", flush=True)
            # Depois de timeout ha trabalho de estado desconhecido: nao contaminar a fase seguinte.
            if summary["transport_errors"]:
                raise RuntimeError("Falha de transporte: execucao interrompida para evitar sobreposicao entre fases.")
        if len(rows) != 9 * args.calls_per_phase:
            raise ValueError("Numero de chamadas divergente do protocolo.")
        check_files(source, receipt["output_sha256"])
        check_files(context, read_json(context / "context.json")["files_sha256"])
    except BaseException as exc:
        write_json(output / "failure.json", {"status": "incomplete", "error_type": type(exc).__name__, "message": str(exc)})
        print(f"Execucao incompleta; evidencias preservadas: {output}", flush=True)
        raise
    finally:
        if container:
            try:
                (output / "server.log").write_text(execute(["docker", "logs", container], log) + "\n", encoding="utf-8")
                write_json(output / "container_final.json", json.loads(execute(["docker", "inspect", container], log))[0])
            finally:
                execute(["docker", "rm", "-f", container], log)
    result = {
        "schema": "renewcast-concurrency-receipt-v1", "run_id": run_id,
        "measurement_complete": True, "phase_count": len(summaries), "attempts": len(rows),
        "all_responses_correct": all(r["outcome"] == "ok" for r in rows),
        "image_id": receipt["image_id"], "model_retrained": False,
        "protocol_sha256": sha(output / "protocol.json"), "operational_policy_approved": False,
        "scope": "closed-loop local benchmark; one payload; no production capacity or model-accuracy claim",
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
    }
    write_json(output / "verification.json", result)
    write_json(args.output_root.resolve() / "latest_run.json", {"directory": str(output), "verification_sha256": sha(output / "verification.json")})
    print(f"Medicao concluida. Analise a regra nas tres rodadas; conclusao operacional nao automatizada.\nArquivos: {output}")
    return 0 if result["all_responses_correct"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
