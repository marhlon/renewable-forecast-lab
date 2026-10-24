"""M06: produz um wheel de inferência e uma distribuição offline para esta plataforma.

Executar no ambiente renewable-forecast: python scripts/empacotar_servico.py
Não ajusta modelos, não altera pyproject.toml nem instala pacotes no ambiente atual.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.parser import BytesParser
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile

ROOTS = ("fastapi", "uvicorn", "pydantic", "numpy", "pandas", "scikit-learn", "joblib", "threadpoolctl")
PROJECT = Path(__file__).resolve().parents[1]
MODEL = "models/CJU_BA5EIGT/h24_event_api_v1"
POLICY = "reports/events/CJU_BA5EIGT/h24_d2_july_drop22p77_v1/decisions/policy.json"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def capture_dependencies():
    """Fecha Requires-Dist a partir das dependências de inferência já instaladas."""
    from packaging.markers import default_environment
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    env = default_environment()
    env["extra"] = ""
    todo = [Requirement(name) for name in ROOTS]
    found = {}
    while todo:
        req = todo.pop()
        if req.marker and not req.marker.evaluate(env):
            continue
        if req.extras or req.url:
            raise ValueError(f"Dependência com extra/URL exige revisão explícita: {req}")
        dist = metadata.distribution(req.name)
        name = canonicalize_name(dist.metadata["Name"])
        if req.specifier and not req.specifier.contains(dist.version, prereleases=True):
            raise ValueError(f"Ambiente inconsistente: {req}; instalado: {dist.version}")
        if name in found:
            continue
        found[name] = dist.version
        todo.extend(Requirement(r) for r in (dist.requires or []))
    return dict(sorted(found.items()))


def command(args, log, cwd=None):
    with log.open("a", encoding="utf-8") as stream:
        stream.write("\n" + subprocess.list2cmdline([str(a) for a in args]) + "\n")
        stream.flush()
        result = subprocess.run(args, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"Comando falhou ({result.returncode}). Leia {log}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=PROJECT)
    parser.add_argument("--model-dir", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    project = args.project_dir.resolve()
    model_dir = (args.model_dir or project / MODEL).resolve()
    policy_path = (args.policy or project / POLICY).resolve()
    output = (args.output_root or project / "dist/event_service").resolve()
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Use o Python 3.12 do ambiente renewable-forecast.")

    from renewable_forecast import decision_api, event_artifact
    from renewable_forecast.decision_api import DecisionPolicy
    from renewable_forecast.event_artifact import EventPredictRequest, EventRuntime
    sources = {f"{module.__name__.split('.')[-1]}.py": Path(module.__file__).resolve()
               for module in (decision_api, event_artifact)}
    for name, path in sources.items():
        expected = project / "src/renewable_forecast" / name
        if not expected.is_file() or sha(path) != sha(expected):
            raise ValueError(f"Importação não corresponde ao código deste projeto: {path}")
    policy = DecisionPolicy.model_validate_json(policy_path.read_bytes()).model_dump(mode="json")
    runtime = EventRuntime(model_dir, policy, sha(policy_path), threads=2)
    request = json.loads((model_dir / "example_request.json").read_text(encoding="utf-8"))
    reference = runtime.predict(EventPredictRequest.model_validate(request)).model_dump(mode="json")
    pins = capture_dependencies()
    build_backend = metadata.version("setuptools")
    output.mkdir(parents=True, exist_ok=True)
    release_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    release = output / release_id
    release.mkdir()
    wheelhouse = release / "wheelhouse"
    wheelhouse.mkdir()
    artifacts = release / "artifacts"
    artifacts.mkdir()
    for name in ("model.joblib", "manifest.json", "example_request.json"):
        shutil.copy2(model_dir / name, artifacts / name)
    shutil.copy2(policy_path, artifacts / "policy.json")
    write_json(release / "reference_response.json", reference)
    pins_file = release / "requirements.captured.txt"
    pins_file.write_text("".join(f"{name}=={version}\n" for name, version in pins.items()), encoding="utf-8")
    log = release / "build.log"
    print(f"Modelo preservado: {reference['model_sha256']}", flush=True)
    print(f"Capturadas {len(pins)} dependências de inferência. Baixando wheels desta plataforma...", flush=True)
    command([sys.executable, "-m", "pip", "download", "--disable-pip-version-check",
             "--only-binary=:all:", "--no-deps", "--dest", str(wheelhouse), "-r", str(pins_file)], log)

    version = "0.1.0+" + release_id.lower().replace("_", ".")
    project_toml = (
        '[build-system]\nrequires = ["setuptools==' + build_backend + '"]\n'
        'build-backend = "setuptools.build_meta"\n\n'
        '[project]\nname = "renewcast-event-service"\nversion = "' + version + '"\n'
        'requires-python = ">=3.12,<3.13"\n'
        'description = "Snapshot de inferência Renewcast; sem pipeline de treino"\n'
        'dependencies = ' + json.dumps([f"{name}=={pins[name]}" for name in ROOTS]) + '\n\n'
        '[tool.setuptools.packages.find]\nwhere = ["src"]\n'
    )
    with tempfile.TemporaryDirectory(prefix="renewcast_build_") as temp:
        staging = Path(temp)
        package = staging / "src/renewable_forecast"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text('"""Runtime de inferência empacotado pelo M06."""\n', encoding="utf-8")
        for name, path in sources.items():
            shutil.copy2(path, package / name)
        (staging / "pyproject.toml").write_text(project_toml, encoding="utf-8")
        shutil.copytree(staging, release / "source")
        print("Construindo wheel instalável do serviço...", flush=True)
        command([sys.executable, "-m", "pip", "wheel", "--disable-pip-version-check", "--no-deps",
                 "--wheel-dir", str(wheelhouse), str(staging)], log)

    # Cada wheel entra no lock com o hash dos bytes que serão instalados.
    from packaging.utils import canonicalize_name
    locked = {}
    for path in sorted(wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(path) as archive:
            candidates = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
            if len(candidates) != 1:
                raise ValueError(f"Wheel sem METADATA único: {path.name}")
            info = BytesParser().parsebytes(archive.read(candidates[0]))
        name = canonicalize_name(info["Name"])
        if name in locked:
            raise ValueError(f"Mais de um wheel para {name}")
        locked[name] = (info["Version"], sha(path))
    expected = {**pins, "renewcast-event-service": version}
    if {name: value[0] for name, value in locked.items()} != expected:
        raise ValueError("Os wheels não correspondem às versões capturadas.")
    (release / "requirements.lock").write_text(
        "".join(f"{name}=={v} --hash=sha256:{digest}\n" for name, (v, digest) in sorted(locked.items())), encoding="utf-8")
    shutil.copy2(Path(__file__), release / "empacotar_servico.py")
    manifest = {
        "schema": "renewcast-service-release-v1", "release_id": release_id,
        "distribution": "renewcast-event-service", "version": version,
        "platform": {"system": platform.system(), "machine": platform.machine(),
                     "python": platform.python_version(), "implementation": platform.python_implementation()},
        "dependencies": expected, "model_sha256": reference["model_sha256"],
        "policy_sha256": reference["policy_sha256"], "reference_probability": reference["p_event"],
        "source_sha256": {name: sha(path) for name, path in sources.items()},
        "model_retrained": False, "scope": "same-platform inference reproduction; not model promotion or performance evaluation",
        "files_sha256": {p.relative_to(release).as_posix(): sha(p) for p in sorted(release.rglob("*")) if p.is_file()},
    }
    write_json(release / "release.json", manifest)
    pointer = output / "latest_release.json"
    temp_pointer = output / (release_id + ".pointer.tmp")
    write_json(temp_pointer, {"directory": release_id, "release_sha256": sha(release / "release.json")})
    os.replace(temp_pointer, pointer)
    print(f"Distribuição: {release}")
    print(f"Ponteiro: {pointer}")
    print("Captura concluída. A reprodução em ambiente novo é a próxima etapa.")


if __name__ == "__main__":
    main()
