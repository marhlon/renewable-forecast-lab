"""M06.5: cria cliente Windows em pasta, com PyInstaller em venv separado."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import uuid
import venv

from medir_concorrencia import PROJECT, load_source, sha, write_json


PYINSTALLER_VERSION = "6.22.3"


def execute(command, log):
    with log.open("a", encoding="utf-8") as stream:
        stream.write("\n" + subprocess.list2cmdline(command) + "\n")
        stream.flush()
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"Comando falhou ({result.returncode}). Consulte {log}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container-run", type=Path)
    args = parser.parse_args(argv)
    if sys.platform != "win32" or sys.version_info[:2] != (3, 12) or struct.calcsize("P") != 8:
        raise RuntimeError("Construa em Windows 64 bits com Python 3.12. Este comando nao faz cross-compilation.")
    source, receipt, context, request, reference = load_source(args.container_run)
    client = PROJECT / "tools/renewcast_client.py"
    temporal = client.with_name("politica_atualidade.py")
    launcher = client.with_name("Consultar_Renewcast.ps1")
    for required in (client, temporal, launcher):
        if not required.is_file():
            raise FileNotFoundError(f"Extraia o pacote na raiz do projeto: {required}")
    spec = importlib.util.spec_from_file_location("renewcast_client", client)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(client.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    contract = {"schema": "renewcast-client-contract-v1", "conjunto": request["conjunto"],
                "fixed_response": {key: reference[key] for key in module.FIXED_FIELDS}}
    module.validar_resposta(reference, request, contract)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    build = PROJECT / "build/client_windows" / run_id
    release = PROJECT / "dist/client_windows" / run_id
    build.mkdir(parents=True)
    release.mkdir(parents=True)
    log = build / "build.log"
    work_source = build / "renewcast_client.py"
    shutil.copyfile(client, work_source)
    shutil.copyfile(temporal, build / temporal.name)
    env_dir = build / "venv"
    print(f"Build: {build}\nCriando ambiente exclusivo do empacotador...", flush=True)
    venv.EnvBuilder(with_pip=True).create(env_dir)
    python = env_dir / "Scripts/python.exe"
    wheels = build / "wheelhouse"
    wheels.mkdir()
    print(f"Obtendo PyInstaller {PYINSTALLER_VERSION} e dependencias de build...", flush=True)
    execute([str(python), "-m", "pip", "download", "--only-binary=:all:", "--dest", str(wheels),
             f"pyinstaller=={PYINSTALLER_VERSION}"], log)
    execute([str(python), "-m", "pip", "install", "--no-index", "--find-links", str(wheels),
             f"pyinstaller=={PYINSTALLER_VERSION}"], log)
    execute([str(python), "-m", "pip", "check"], log)
    frozen = subprocess.check_output([str(python), "-m", "pip", "freeze", "--all"], text=True)
    (build / "requirements.build.lock").write_text(frozen, encoding="utf-8")
    print("Gerando renewcast.exe e dependencias na mesma pasta (onedir)...", flush=True)
    execute([str(python), "-m", "PyInstaller", "--noconfirm", "--clean", "--noupx", "--onedir",
             "--console", "--name", "renewcast", "--distpath", str(release),
             "--workpath", str(build / "work"), "--specpath", str(build), str(work_source)], log)
    app = release / "renewcast"
    executable = app / "renewcast.exe"
    if not executable.is_file():
        raise FileNotFoundError(f"Build nao produziu o executavel: {executable}")
    write_json(app / "contract.json", contract)
    write_json(app / "example_request.json", request)
    shutil.copyfile(launcher, app / launcher.name)
    (app / "LEIA.txt").write_text(
        "Cliente Renewcast de desenvolvimento. Copie a pasta inteira, incluindo _internal.\n"
        "Nao precisa de Conda/Python instalado. Precisa de API local ativa.\n"
        "Exemplo (terminal nesta pasta, API na porta 8000):\n"
        ".\\renewcast.exe --url http://127.0.0.1:8000 --request example_request.json "
        "--contract contract.json --output consulta_001.json --presentation-mode historical_replay\n"
        "Lancador: .\\Consultar_Renewcast.ps1 -Request .\\example_request.json -Mode historical_replay\n"
        "Use -Mode operational para aplicar a regra temporal com o relogio real.\n"
        "Cada consulta usa um arquivo de saida novo. Codigos: 0=decisao, 2=rejeicao HTTP, "
        "3=indisponivel, 4=resposta incompativel, 5=entrada local invalida, "
        "7=apresentacao bloqueada. O lancador reserva 6 para falha propria.\n"
        "O pedido de exemplo e historico; operational deve bloquea-lo quando o alvo passou.\n"
        "0 com alarm=false nao e o mesmo que indisponivel. Sem nova aprovacao operacional.\n",
        encoding="utf-8")
    manifest = {"schema": "renewcast-windows-client-release-v1", "run_id": run_id,
                "built": True, "windows_execution_verified": False,
                "python": platform.python_version(), "platform": platform.platform(),
                "pyinstaller_version": PYINSTALLER_VERSION, "mode": "onedir",
                "source_container_run": str(source), "source_verification_sha256": sha(source / "verification.json"),
                "image_id": receipt["image_id"], "model_sha256": reference["model_sha256"],
                "policy_sha256": reference["policy_sha256"], "client_source_sha256": sha(work_source),
                "client_version": module.VERSION,
                "temporal_policy_sha256": sha(build / temporal.name),
                "launcher_sha256": sha(launcher),
                "build_controller_sha256": sha(Path(__file__)), "build_directory": str(build),
                "build_wheel_sha256": {p.name: sha(p) for p in sorted(wheels.glob("*.whl"))},
                "requirements_build_sha256": sha(build / "requirements.build.lock"),
                "files_sha256": {p.relative_to(release).as_posix(): sha(p)
                                 for p in sorted(app.rglob("*")) if p.is_file()},
                "scope": "Portable Windows API client; model and API remain external"}
    write_json(release / "release.json", manifest)
    write_json(release.parent / "latest_release.json", {"directory": str(release), "release_sha256": sha(release / "release.json")})
    print(f"Cliente criado: {executable}\nExecucao fora do projeto ainda pendente.")
    print("Proximo comando: python scripts/verificar_cliente_windows.py")


if __name__ == "__main__":
    main()
