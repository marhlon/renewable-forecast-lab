"""M06: verifica uma distribuição, instala offline em venv novo e executa a API.

Este controlador usa somente a biblioteca padrão. Não ativa ambientes nem treina.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

PROJECT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def checked_child(root, relative):
    child = (root / relative).resolve()
    if not child.is_relative_to(root.resolve()):
        raise ValueError(f"Caminho fora da distribuição: {relative}")
    return child


def load_release(path):
    path = path.resolve()
    if path.is_dir():
        release = path
    else:
        pointer = json.loads(path.read_text(encoding="utf-8"))
        release = checked_child(path.parent, pointer["directory"])
        if sha(release / "release.json") != pointer["release_sha256"]:
            raise ValueError("Hash do manifesto diverge do ponteiro.")
    manifest = json.loads((release / "release.json").read_text(encoding="utf-8"))
    if manifest["schema"] != "renewcast-service-release-v1":
        raise ValueError("Contrato de distribuição desconhecido.")
    for relative, expected in manifest["files_sha256"].items():
        target = checked_child(release, relative)
        if not target.is_file() or sha(target) != expected:
            raise ValueError(f"Integridade reprovada: {relative}")
    source = manifest["platform"]
    current = {"system": platform.system(), "machine": platform.machine(),
               "python": platform.python_version(), "implementation": platform.python_implementation()}
    if source != current:
        raise ValueError(f"Esta captura exige a mesma plataforma e versão Python. Origem={source}; atual={current}")
    return release, manifest


def clean_environment():
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("PYTHON") or key.startswith("PIP_") or key == "VIRTUAL_ENV":
            env.pop(key)
    env.update({"PIP_CONFIG_FILE": os.devnull, "PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"})
    return env


def run_command(args, log, cwd, env):
    result = subprocess.run(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    with log.open("a", encoding="utf-8") as stream:
        stream.write("\n" + subprocess.list2cmdline([str(a) for a in args]) + "\n" + result.stdout)
    if result.returncode:
        raise RuntimeError(f"Comando falhou ({result.returncode}). Leia {log}\n{result.stdout[-2500:]}")
    return result.stdout


def http(url, payload=None):
    data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=PROJECT / "dist/event_service/latest_release.json")
    parser.add_argument("--output-root", type=Path, default=PROJECT / "reports/packaging/CJU_BA5EIGT/h24_event_v1")
    parser.add_argument("--venv-root", type=Path, default=PROJECT / "venvs/m06_package")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)
    release, manifest = load_release(args.release)
    print(f"Integridade conferida: {len(manifest['files_sha256'])} arquivos; distribuição {manifest['release_id']}.", flush=True)
    if args.verify_only:
        print("Verificação de arquivos concluída; instalação e inferência não foram executadas.")
        return
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    output = args.output_root.resolve() / run_id
    work = output / "work"
    work.mkdir(parents=True)
    # Caminho curto reduz problemas de limite de comprimento no Windows.
    env_dir = args.venv_root.resolve() / uuid.uuid4().hex[:12]
    if env_dir.exists():
        raise ValueError("O destino do ambiente já existe; nenhum ambiente será reutilizado.")
    env = clean_environment()
    log = output / "installation.log"
    python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    print("Criando ambiente novo sem os pacotes do ambiente de desenvolvimento...", flush=True)
    run_command([sys.executable, "-I", "-m", "venv", str(env_dir)], log, work, env)
    started = time.perf_counter()
    run_command([str(python), "-I", "-m", "pip", "install", "--no-index", "--only-binary=:all:",
                 "--find-links", str(release / "wheelhouse"), "--require-hashes", "-r", str(release / "requirements.lock")], log, work, env)
    install_seconds = time.perf_counter() - started
    run_command([str(python), "-I", "-m", "pip", "check"], log, work, env)
    probe_code = (
        "import sys, json, importlib.metadata as m; from pathlib import Path; "
        "import renewable_forecast.decision_api as a; "
        "names=json.loads(sys.argv[1]); "
        "print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,"
        "'module_path':a.__file__,'isolated':sys.flags.isolated,'sys_path':sys.path,"
        "'versions':{n:m.version(n) for n in names}}))"
    )
    info = json.loads(run_command([str(python), "-I", "-c", probe_code, json.dumps(list(manifest["dependencies"]))], log, work, env))
    module_path = Path(info["module_path"]).resolve()
    if (info["prefix"] == info["base_prefix"] or info["isolated"] != 1
            or not module_path.is_relative_to(env_dir.resolve())
            or info["versions"] != manifest["dependencies"]):
        raise ValueError("O ambiente novo não cumpriu o isolamento ou as versões exigidas.")
    for name, expected in manifest["source_sha256"].items():
        if sha(module_path.parent / name) != expected:
            raise ValueError(f"Módulo instalado diverge da origem: {name}")
    write_json(output / "environment.json", info)
    print(f"Pacote importado de: {module_path}", flush=True)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    address = f"http://127.0.0.1:{port}"
    api_log = output / "server.log"
    started = time.perf_counter()
    with api_log.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen([str(python), "-I", "-m", "renewable_forecast.decision_api",
                                    "--policy", str(release / "artifacts/policy.json"),
                                    "--model-dir", str(release / "artifacts"), "--port", str(port), "--threads", "2"],
                                   cwd=work, env=env, stdout=stream, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 60
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"API encerrou ao iniciar. Leia {api_log}")
                try:
                    code, health = http(address + "/health")
                    if code == 200 and health.get("model_loaded"):
                        break
                except (urllib.error.URLError, TimeoutError):
                    pass
                if time.monotonic() > deadline:
                    raise TimeoutError(f"API não ficou pronta. Leia {api_log}")
                time.sleep(0.1)
            startup_seconds = time.perf_counter() - started
            request = json.loads((release / "artifacts/example_request.json").read_text(encoding="utf-8"))
            code, response = http(address + "/predict-decision", request)
            if code != 200:
                raise ValueError(f"Inferência falhou: HTTP {code}: {response}")
            reference = json.loads((release / "reference_response.json").read_text(encoding="utf-8"))
            if set(reference) != set(response):
                raise ValueError("Contrato da resposta mudou.")
            for key in reference:
                same = (math.isclose(reference[key], response[key], rel_tol=0.0, abs_tol=1e-12)
                        if key == "p_event" else reference[key] == response[key])
                if not same:
                    raise ValueError(f"Resposta diverge em {key}: {reference[key]!r} -> {response[key]!r}")
            bad = copy.deepcopy(request)
            del bad["features"][next(iter(bad["features"]))]
            bad_code, bad_response = http(address + "/predict-decision", bad)
            if bad_code != 422:
                raise ValueError(f"Contrato incompleto deveria ser recusado; recebido HTTP {bad_code}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    write_json(output / "response.json", response)
    write_json(output / "rejected_request.json", {"status_code": bad_code, "response": bad_response})
    receipt = {
        "verified": True, "run_id": run_id, "release_id": manifest["release_id"],
        "release_directory": str(release), "release_manifest_sha256": sha(release / "release.json"),
        "model_sha256": response["model_sha256"], "policy_sha256": response["policy_sha256"],
        "module_path": str(module_path), "venv_directory": str(env_dir), "installed_distribution": manifest["distribution"],
        "reference_probability": reference["p_event"], "reproduced_probability": response["p_event"],
        "absolute_difference": abs(reference["p_event"] - response["p_event"]),
        "probability_tolerance": 1e-12, "valid_request_status": code, "invalid_request_status": bad_code,
        "fresh_venv": True, "isolated_python": True, "installation_no_index": True,
        "model_retrained": False, "same_machine": True, "cross_platform_verified": False,
        "platform": manifest["platform"], "dependency_count_including_service": len(manifest["dependencies"]),
        "wheelhouse_bytes": sum(p.stat().st_size for p in (release / "wheelhouse").glob("*.whl")),
        "install_seconds": install_seconds, "startup_seconds": startup_seconds,
        "scope": "single-request software compatibility; not a new statistical validation or production approval",
        "output_sha256": {name: sha(output / name) for name in ("environment.json", "response.json", "rejected_request.json", "installation.log", "server.log")},
    }
    write_json(output / "verification.json", receipt)
    write_json(args.output_root.resolve() / "latest_run.json", {"directory": str(output), "verification_sha256": sha(output / "verification.json")})
    print(f"HTTP {code}; referência={reference['p_event']:.15f}; reproduzida={response['p_event']:.15f}")
    print(f"Diferença absoluta={receipt['absolute_difference']:.3g}; contrato inválido=HTTP {bad_code}.")
    print("Reprodução aprovada neste ambiente novo. Modelo e política preservados; sem novo treino.")
    print(f"Arquivos: {output}")


if __name__ == "__main__":
    main()
