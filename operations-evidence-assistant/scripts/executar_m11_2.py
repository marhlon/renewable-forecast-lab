"""Usa o modelo e o ambiente da M11.1; prepara só o validador se necessário."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]
from executar_m11_1 import bin_python, preparar, tem_versoes  # M11.1 instalada no mesmo produto

LOCK = BASE / "docs/m11_2/requirements.lock.txt"


def versoes_ok(exe, private=None):
    wanted = dict(line.split("==",1) for line in LOCK.read_text(encoding="utf-8").splitlines() if line)
    code = (
        "import sys,json; from importlib.metadata import version; "
        + ("sys.path.insert(0,sys.argv[1]); " if private else "")
        + f"import pydantic, pydantic_core; print(json.dumps({{name:version(name) for name in {tuple(wanted)!r}}}));"
    )
    cmd = [str(exe), "-c", code]+([str(private)] if private else [])
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=18, check=False)
        return proc.returncode == 0 and json.loads(proc.stdout) == wanted
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def preparar_validador(exe, *, force_private):
    if not force_private and versoes_ok(exe):
        return None
    suffix = subprocess.check_output([str(exe), "-c",
                'import sys,sysconfig;print(f"{sys.implementation.cache_tag}-{sysconfig.get_platform()}")'],text=True).strip()
    target = BASE / ".cache/m11_2" / suffix
    if target.is_dir():
        if not versoes_ok(exe,target):
            raise ValueError(f"Validador incompleto em {target}. Remova apenas essa pasta e repita.")
        return target
    target.parent.mkdir(parents=True,exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="pydantic-",dir=target.parent))
    try:
        print("Preparando Pydantic em cache privado; não altera Conda nem o ambiente M09.3.",flush=True)
        subprocess.run([str(exe),"-m","pip","install","--disable-pip-version-check","--only-binary=:all:",
                        "--target",str(staging),"-r",str(LOCK)],check=True)
        if not versoes_ok(exe,staging):
            raise ValueError("Os pacotes isolados do validador não correspondem ao manifesto.")
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autoria", type=Path)
    parser.add_argument("--verificar", action="store_true", help="Só contraprovas de validação, sem carregar o LLM.")
    parser.add_argument("--python", type=Path, help="Interpretador da M11.1; por padrão procura os ambientes existentes.")
    parser.add_argument("--model-dir", type=Path, help="Snapshot da M11.1 já disponível; somente leitura.")
    parser.add_argument("--output-dir", type=Path, default=BASE/"reports/m11_2")
    parser.add_argument("--preparar-ambiente",action="store_true",help="Cria o ambiente privado M11.1 se ausente.")
    parser.add_argument("--validador-isolado",action="store_true",help="Usa cache próprio mesmo se a versão fixada já está instalada.")
    args=parser.parse_args(argv)
    if args.autoria is not None and (not args.autoria.is_file() or args.autoria.suffix.lower()!=".py"):
        raise ValueError(f"Arquivo autoral .py não encontrado: {args.autoria}")
    root=BASE.parent/".venvs"
    private=root/"m11_1_smol"
    if args.python:
        exe=args.python.absolute()  # Não resolver symlink para fora de um venv.
        if not exe.is_file() or (not args.verificar and not tem_versoes(exe)):
            raise ValueError(f"Interpretador indicado está ausente ou incompatível: {exe}")
    elif args.verificar:
        exe=Path(sys.executable)
    else:
        candidates=(bin_python(root/"m09_3_chronos"),bin_python(private),Path(sys.executable))
        exe=next((p for p in candidates if tem_versoes(p)),None)
        if exe is None and args.preparar_ambiente:
            exe=preparar(private)
        if exe is None or not tem_versoes(exe):
            raise ValueError("Ambiente M11.1 não encontrado; use --preparar-ambiente para criar só o ambiente privado.")
    deps=preparar_validador(exe,force_private=args.validador_isolado)
    cmd=[str(exe),str(BASE/"scripts/laboratorio_m11_2.py"),"--output-dir",str(args.output_dir.resolve())]
    for opt, path in (("--autoria",args.autoria),("--model-dir",args.model_dir),("--pydantic-dir",deps)):
        if path is not None:
            cmd += [opt,str(path.resolve())]
    if args.verificar:
        cmd += ["--verificar"]
    print(f"Interpretador: {exe}",flush=True)
    env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", HF_HUB_OFFLINE="1",
             TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    env.pop("PYTHONPATH",None)
    return subprocess.run(cmd,env=env,check=False).returncode


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        print(f"M11.2: {exc}",file=sys.stderr)
        raise SystemExit(1) from None
