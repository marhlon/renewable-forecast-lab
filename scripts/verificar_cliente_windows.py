"""M06.5: executa o cliente copiado fora do projeto, sem Conda no processo filho."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from medir_concorrencia import PROJECT, check_files, compare, load_source, read_json, sha, write_json
from verificar_container import execute, http


def clean_environment():
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(("CONDA", "_CONDA", "_CE_", "PYTHON", "VIRTUAL_ENV"))}
    system = Path(os.environ["SystemRoot"])
    env["PATH"] = os.pathsep.join((str(system / "System32"), str(system)))
    return env


def run_case(app, folder, url, request, output_name, expected_exit, env, contract=None,
             presentation_mode="historical_replay"):
    output = folder / output_name
    command = [str(app / "renewcast.exe"), "--url", url, "--request", str(request),
               "--contract", str(contract or app / "contract.json"), "--output", str(output), "--timeout", "5",
               "--presentation-mode", presentation_mode]
    result = subprocess.run(command, cwd=folder, env=env, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=45)
    (folder / (output_name + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != expected_exit:
        raise ValueError(f"Caso {output_name}: esperado exit={expected_exit}; recebido={result.returncode}. Consulte {folder}.")
    record = read_json(output)
    if (record["schema"] != "renewcast-client-receipt-v2"
            or record["requested_presentation_mode"] != presentation_mode
            or record["exit_code"] != expected_exit or record["frozen"] is not True
            or record["conda_active"] or record["pythonpath_present"]
            or Path(record["executable"]).resolve() != (app / "renewcast.exe").resolve()
            or Path(record["working_directory"]).resolve() != folder.resolve()):
        raise ValueError(f"Execucao nao isolada ou recibo inconsistente em {output_name}.")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path)
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        raise RuntimeError("A prova do executavel Windows deve rodar em Windows.")
    if args.release is None:
        pointer = read_json(PROJECT / "dist/client_windows/latest_release.json")
        release = Path(pointer["directory"])
        if not release.is_absolute() or sha(release / "release.json") != pointer["release_sha256"]:
            raise ValueError("Ponteiro de release invalido.")
    else:
        release = args.release.resolve()
    manifest = read_json(release / "release.json")
    if manifest.get("schema") != "renewcast-windows-client-release-v1" or manifest.get("built") is not True:
        raise ValueError("Release de cliente ausente ou incompleto.")
    if manifest.get("client_version") != "1.1.0":
        raise ValueError("Este protocolo exige cliente 1.1.0. Construa a nova release primeiro.")
    check_files(release, manifest["files_sha256"])
    source, receipt, context, request, reference = load_source(manifest["source_container_run"])
    if datetime.fromisoformat(request["target_time"].replace("Z", "+00:00")) >= datetime.now(timezone.utc):
        raise ValueError("A prova usa um pedido histórico cujo alvo já passou; confira o relógio do computador.")
    if sha(source / "verification.json") != manifest["source_verification_sha256"] or receipt["image_id"] != manifest["image_id"]:
        raise ValueError("Release nao corresponde ao recibo Docker de origem.")
    if not shutil.which("docker"):
        raise RuntimeError("Abra o Docker Desktop com mecanismo Linux.")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = PROJECT / "reports/windows_client/CJU_BA5EIGT/h24_event_v1" / run_id
    output.mkdir(parents=True)
    log = output / "pipeline.log"
    external = Path(tempfile.mkdtemp(prefix="renewcast_cliente_"))
    if external.resolve().is_relative_to(PROJECT.resolve()):
        raise ValueError("TEMP esta dentro do projeto; configure destino externo antes de executar.")
    app = external / "renewcast"
    shutil.copytree(release / "renewcast", app)
    for name, expected in manifest["files_sha256"].items():
        copied = external / name
        if sha(copied) != expected:
            raise ValueError(f"Copia alterada: {name}")
    env = clean_environment()
    print(f"Destino externo: {external}\nExecutavel sem Conda/PYTHONPATH; API na imagem aprovada.", flush=True)
    execute(["docker", "image", "inspect", manifest["image_id"]], log)
    container_id = execute(["docker", "run", "-d", "--pull", "never", "--cpus", "2", "--memory", "1g",
                            "--read-only", "--tmpfs", "/tmp:rw,size=64m", "--cap-drop", "ALL",
                            "--security-opt", "no-new-privileges", "-p", "127.0.0.1::8000", manifest["image_id"]], log)
    removed = False
    cases = {}
    try:
        info = json.loads(execute(["docker", "inspect", container_id], log))[0]
        url = "http://127.0.0.1:" + info["NetworkSettings"]["Ports"]["8000/tcp"][0]["HostPort"]
        deadline = time.monotonic() + 90
        while True:
            try:
                code, health = http(url + "/health")
                if code == 200 and health.get("model_loaded"):
                    break
            except (OSError, ValueError):
                pass
            state = json.loads(execute(["docker", "inspect", container_id], log))[0]["State"]
            if not state["Running"] or time.monotonic() > deadline:
                raise RuntimeError("API nao iniciou; consulte server.log/pipeline.log.")
            time.sleep(0.5)
        cases["valid"] = run_case(app, external, url, app / "example_request.json", "valid.json", 0, env)
        if cases["valid"]["http_status"] != 200 or compare(reference, cases["valid"]["response"]):
            raise ValueError("O executavel nao preservou a resposta da referencia.")
        if (cases["valid"]["presentation"]["state"] != "historical_replay"
                or cases["valid"]["presentation"]["allowed"] is not True
                or cases["valid"]["presentation"]["operational_policy_approved"] is not False):
            raise ValueError("Reprodução histórica não foi explicitada.")
        cases["blocked"] = run_case(app, external, url, app / "example_request.json",
                                     "blocked.json", 7, env, presentation_mode="operational")
        blocked = cases["blocked"]
        if (blocked["http_status"] != 200 or blocked["state"] != "presentation_blocked"
                or blocked["response"] is not None or blocked["presentation"]["allowed"] is not False
                or blocked["presentation"]["state"] != "target_elapsed"
                or compare(reference, blocked["audit_response"])):
            raise ValueError("Resposta HTTP válida e antiga não foi bloqueada e preservada para auditoria.")
        bad = copy.deepcopy(request)
        del bad["features"]["lag_1h"]
        write_json(external / "missing_feature.json", bad)
        cases["rejected"] = run_case(app, external, url, external / "missing_feature.json", "rejected.json", 2, env)
        if cases["rejected"]["http_status"] != 422 or cases["rejected"]["state"] != "rejected":
            raise ValueError("Feature ausente nao foi identificada como rejeicao.")
        wrong_contract = read_json(app / "contract.json")
        current_sha = wrong_contract["fixed_response"]["model_sha256"]
        wrong_contract["fixed_response"]["model_sha256"] = ("0" if current_sha[0] != "0" else "1") + current_sha[1:]
        write_json(external / "wrong_contract.json", wrong_contract)
        cases["wrong_identity"] = run_case(app, external, url, app / "example_request.json",
                                           "wrong_identity.json", 4, env, external / "wrong_contract.json")
        if cases["wrong_identity"]["http_status"] != 200 or cases["wrong_identity"]["state"] != "invalid_response":
            raise ValueError("HTTP 200 com identidade divergente deveria ser recusado.")
        logs = subprocess.run(["docker", "logs", container_id], capture_output=True)
        (output / "server.log").write_bytes(logs.stdout + logs.stderr)
        execute(["docker", "rm", "-f", container_id], log)
        removed = True
        cases["unavailable"] = run_case(app, external, url, app / "example_request.json", "unavailable.json", 3, env)
        if cases["unavailable"]["state"] != "unavailable":
            raise ValueError("Servico encerrado nao foi identificado como indisponivel.")
        for name in ("rejected", "wrong_identity", "unavailable", "blocked"):
            if cases[name]["response"] is not None:
                raise ValueError("Falha nao pode fornecer uma decisao utilizavel.")
        for name, record in cases.items():
            write_json(output / f"{name}.json", record)
        check_files(release, manifest["files_sha256"])
        check_files(external, manifest["files_sha256"])
        verified = {"schema": "renewcast-windows-client-verification-v2", "verified": True,
                    "client_version": "1.1.0", "presentation_policy_verified": True,
                    "run_id": run_id, "release": str(release), "release_sha256": sha(release / "release.json"),
                    "external_directory": str(external), "source_container_run": str(source),
                    "source_verification_sha256": sha(source / "verification.json"), "image_id": manifest["image_id"],
                    "model_sha256": reference["model_sha256"], "policy_sha256": reference["policy_sha256"],
                    "absolute_probability_difference": abs(reference["p_event"] - cases["valid"]["response"]["p_event"]),
                    "expected_exits": {"valid": 0, "blocked": 7, "rejected": 2, "wrong_identity": 4, "unavailable": 3},
                    "child_path": env["PATH"], "verified_without_conda_in_child": True,
                    "client_controller_sha256": sha(Path(__file__)), "operational_policy_approved": False,
                    "scope": "Windows executable copied outside project on same PC; API still depends on Docker",
                    "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
        write_json(output / "verification.json", verified)
        write_json(output.parent / "latest_run.json", {"directory": str(output), "verification_sha256": sha(output / "verification.json")})
        print("Cliente 1.1: replay 200/exit0; mesmo pedido operacional 200/exit7 (target_elapsed).")
        print("Regressao: 422/exit2; identidade divergente/exit4; API encerrada/exit3.")
        print(f"Diferenca de probabilidade: {verified['absolute_probability_difference']:.3g}")
        print(f"Evidencias: {output}\nCopia utilizavel: {app}")
    finally:
        if not removed:
            logs = subprocess.run(["docker", "logs", container_id], capture_output=True)
            (output / "server.log").write_bytes(logs.stdout + logs.stderr)
            subprocess.run(["docker", "rm", "-f", container_id], capture_output=True, check=True)


if __name__ == "__main__":
    main()
